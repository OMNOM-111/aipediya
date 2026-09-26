"""Deploy a code-only AIpedia release on the existing host. Never copies SQLite."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

DENIED_SUFFIXES = (".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".env")
# Shared with /srv/aipedia/bin/indexnow-dispatch-loop (flock -n): while a deploy
# holds it, scheduled IndexNow dispatch is skipped, so it never runs during
# migrate / publication-state / app switch / rollback.
DISPATCH_LOCK = "/srv/aipedia/data/indexnow-dispatch.lock"
DISPATCH_LOCK_TIMEOUT = 600


def acquire_dispatch_lock(path=DISPATCH_LOCK, timeout=DISPATCH_LOCK_TIMEOUT, owner="aipedia"):
    """Take the IndexNow dispatch lock exclusively; wait for a running dispatch.

    Returns an open file descriptor; the lock lasts until it is closed or the
    process exits (the kernel releases it even on a crash). Raises SystemExit
    before any change if the lock cannot be taken in time.
    """
    import fcntl
    created = not os.path.exists(path)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    if created and owner:
        import pwd
        account = pwd.getpwnam(owner)
        os.chown(path, account.pw_uid, account.pw_gid)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            if time.monotonic() >= deadline:
                os.close(fd)
                raise SystemExit("IndexNow dispatch still running; deploy aborted before any change")
            time.sleep(2)
DENIED_NAMES = {"secret.key", "secret.env", "aipedia.pid"}


def inspect_archive(archive, expected_sha256):
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise SystemExit("Release archive digest mismatch")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("MANIFEST.json"))
        commit = manifest["commit"]
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
            raise SystemExit("Invalid commit in manifest")
        # "code-candidate": HEAD + listed verified working-tree files; its 40-hex id
        # is the digest of those files (see tools/build_code_release.py).
        if manifest.get("kind") not in {None, "code", "code-candidate"}:
            raise SystemExit("This command only accepts code-only archives")
        names = list(manifest["files"])
        for name in names:
            lower = name.lower().replace("\\", "/")
            if lower.endswith(DENIED_SUFFIXES) or Path(lower).name in DENIED_NAMES:
                raise SystemExit("Refusing archive that contains a database or secret: " + name)
            if "data/local/" in lower or lower.endswith(".sqlite3"):
                raise SystemExit("Refusing archive that contains Local SQLite")
            content = z.read(name)
            if hashlib.sha256(content).hexdigest() != manifest["files"][name]:
                raise SystemExit("File digest mismatch: " + name)
        return manifest, commit, names


def planned_steps(commit, publication_state=None, catalog_plan=None, translations=None):
    steps = [
        "verify archive SHA256 and secret-free manifest",
        "stage code under /srv/aipedia/releases/code-" + commit[:12],
        "take " + DISPATCH_LOCK + " (pauses scheduled IndexNow dispatch until the end, incl. rollback)",
        "stop only supervisor program aipedia",
        "online-backup /srv/aipedia/data/aipedia.sqlite3; never copy Local SQLite onto it",
        "manage.py check && collectstatic --noinput && migrate --noinput",
    ]
    if catalog_plan:
        steps.append("manage.py catalog_master apply-plan --plan-out " + catalog_plan
                     + " (dry check, then --apply: verifies every expected old value by Record ID,"
                     " writes atomically with revisions, renumbers; already applied -> no writes; mismatch -> abort)")
    if translations:
        steps.append("manage.py import_translations " + translations
                     + " (only where the English source hash matches; no provider calls)")
    if publication_state:
        steps.append("manage.py sync_publication_state apply " + publication_state
                     + " --apply (approved Local published flags; aborts on any number mismatch)")
    return steps + [
        "switch /srv/aipedia/app, start only aipedia, check /healthz release=" + commit,
        "on failure before start: restore previous app and restore DB from the backup",
        "on failure after start: leave DB in place for reviewed rollback",
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publication-state", help="Approved state manifest inside the release, e.g. data/release_state.json")
    parser.add_argument("--catalog-plan", help="Catalog release plan inside the release (catalog_master release-plan)")
    parser.add_argument("--translations", help="Translations export inside the release (export_translations)")
    args = parser.parse_args()
    archive = Path(args.archive)
    manifest, commit, names = inspect_archive(archive, args.sha256)
    for label, value in (("Publication state manifest", args.publication_state),
                         ("Catalog plan", args.catalog_plan), ("Translations export", args.translations)):
        if value and "app/" + value not in names:
            raise SystemExit(label + " is not in the release archive: " + value)
    report = {"commit": commit, "files": len(names),
              "steps": planned_steps(commit, args.publication_state, args.catalog_plan, args.translations),
              "copies_sqlite": False}
    if args.dry_run:
        print(json.dumps(report, indent=2))
        raise SystemExit(0)

    import pwd
    import shutil

    ROOT = Path("/srv/aipedia")
    DB = ROOT / "data/aipedia.sqlite3"
    SUPERVISOR = ["supervisorctl", "-c", str(ROOT / "supervisord.conf")]

    def backup(source, destination):
        if destination.exists():
            raise RuntimeError("Backup path already exists")
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(destination) as dst:
            src.backup(dst)
            assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        os.chmod(destination, 0o600)
        account = pwd.getpwnam("aipedia")
        os.chown(destination, account.pw_uid, account.pw_gid)

    def own_tree(path):
        account = pwd.getpwnam("aipedia")
        for item in [path, *path.rglob("*")]:
            os.chown(item, account.pw_uid, account.pw_gid)
            os.chmod(item, 0o750 if item.is_dir() else 0o640)

    stage = ROOT / "releases" / ("code-" + commit[:12])
    stage.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        for name, digest in manifest["files"].items():
            target = (stage / name).resolve()
            assert target.is_relative_to(stage.resolve()) and not name.startswith("/")
            content = z.read(name)
            assert hashlib.sha256(content).hexdigest() == digest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    if (ROOT / "app/public-release").exists():
        shutil.copytree(ROOT / "app/public-release", stage / "app" / "public-release")
    own_tree(stage)
    app = stage / "app"

    def manage(*cmd):
        result = subprocess.run(
            ["runuser", "-u", "aipedia", "--", "env", "AIPEDIA_ENV=local",
             "AIPEDIA_DB=" + str(DB), str(ROOT / "venv/bin/python"), str(app / "manage.py"), *cmd],
            cwd=app, text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + "\n" + result.stderr)
        print(result.stdout.strip(), flush=True)

    manage("check")
    manage("collectstatic", "--noinput")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    before = ROOT / "backups" / ("aipedia-before-code-" + stamp + ".sqlite3")
    previous = ROOT / "releases" / ("before-code-" + stamp)
    switched = stopped = started = old_renamed = False
    dispatch_lock = acquire_dispatch_lock()
    try:
        subprocess.run(SUPERVISOR + ["stop", "aipedia"], check=True)
        stopped = True
        backup(DB, before)
        manage("migrate", "--noinput")
        if args.catalog_plan:
            manage("catalog_master", "apply-plan", "--plan-out", args.catalog_plan)
            manage("catalog_master", "apply-plan", "--plan-out", args.catalog_plan, "--apply")
        if args.translations:
            manage("import_translations", args.translations)
        if args.publication_state:
            manage("sync_publication_state", "apply", args.publication_state, "--apply")
        os.rename(ROOT / "app", previous)
        old_renamed = True
        os.rename(app, ROOT / "app")
        switched = True
        subprocess.run(SUPERVISOR + ["start", "aipedia"], check=True)
        started = True
        for attempt in range(15):
            try:
                request = urllib.request.Request(
                    "http://127.0.0.1:18810/healthz",
                    headers={"Host": "aipediya.com", "X-Forwarded-Proto": "https"},
                )
                payload = json.loads(urllib.request.urlopen(request, timeout=10).read())
                assert payload["release"] == commit, payload
                break
            except Exception:
                if attempt == 14:
                    raise
                time.sleep(1)
        after = ROOT / "backups" / ("aipedia-after-code-" + stamp + ".sqlite3")
        backup(DB, after)
        state = {
            "commit": commit,
            "before_database": str(before),
            "after_database": str(after),
            "previous_app": str(previous),
            "current_app": str(ROOT / "app"),
            "status": "deployed-origin-verified",
            "copied_sqlite": False,
            "publication_state": args.publication_state or None,
            "catalog_plan": args.catalog_plan or None,
            "translations": args.translations or None,
        }
        (stage / "DEPLOYMENT.json").write_text(json.dumps(state, indent=2))
        own_tree(stage)
        print(json.dumps(state), flush=True)
    except Exception:
        if started:
            print("DEPLOYMENT NEEDS REVIEW: app was started; database retained to protect intervening writes.", flush=True)
        elif stopped and before.exists():
            if switched:
                failed = ROOT / "releases" / ("failed-code-" + stamp)
                os.rename(ROOT / "app", failed)
                os.rename(previous, ROOT / "app")
            elif old_renamed:
                os.rename(previous, ROOT / "app")
            failed_db = ROOT / "backups" / ("aipedia-failed-code-" + stamp + ".sqlite3")
            backup(DB, failed_db)
            with sqlite3.connect(before.as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(DB) as dst:
                src.backup(dst)
            subprocess.run(SUPERVISOR + ["start", "aipedia"], check=True)
        raise
    finally:
        # Scheduled dispatch resumes on its next cycle, after success or rollback.
        os.close(dispatch_lock)

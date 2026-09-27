"""Canonical AIpediya Production entrypoint. SSH credentials live in host alias.

Only the ``aipediya-prod`` SSH alias is used. This tool never reads an SSH key,
changes SSH configuration, or accepts arbitrary remote paths or commands.
Application deployment still requires a separately approved release.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from deploy_code_release import inspect_archive


ROOT = Path(__file__).resolve().parent.parent
ALIAS = "aipediya-prod"
REMOTE_ROOT = "/srv/aipedia"
SERVICE = "aipedia"
PLAN = "data/release/tools-chronology-csp-20260927/catalog_plan.json"
PUBLICATION = "data/release_state.json"
REPORT_DIR = ROOT / "artifacts" / "server-access"

# This program is sent to the configured host over SSH stdin. It only reads
# AIpediya state. Any failure is returned as a concrete field in its JSON.
OBSERVE = r'''
import getpass, json, os, subprocess, sys, urllib.request
mode = sys.argv[1]
root = "/srv/aipedia"
result = {"mode": mode, "hostname": os.uname().nodename, "remote_user": getpass.getuser()}
def command(*args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return {"ok": p.returncode == 0, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
if mode in ("preflight", "status"):
    result["service"] = command("sudo", "-n", "supervisorctl", "-c", root + "/supervisord.conf", "status", "aipedia")
if mode in ("preflight", "health"):
    try:
        request = urllib.request.Request("http://127.0.0.1:18810/healthz",
            headers={"Host": "aipediya.com", "X-Forwarded-Proto": "https"})
        with urllib.request.urlopen(request, timeout=10) as response:
            result["health"] = {"status": response.status, "payload": json.load(response)}
    except Exception as exc:
        result["health"] = {"error": str(exc)}
if mode == "preflight":
    result["root_exists"] = os.path.isdir(root)
    result["database_exists"] = command("sudo", "-n", "test", "-f", root + "/data/aipedia.sqlite3")["ok"]
    result["release_tool_exists"] = command("sudo", "-n", "test", "-f", root + "/app/tools/deploy_code_release.py")["ok"]
    result["venv_exists"] = command("sudo", "-n", "test", "-f", root + "/venv/bin/python")["ok"]
    try:
        stat = os.statvfs(root)
        result["free_bytes"] = stat.f_bavail * stat.f_frsize
    except Exception as exc:
        result["free_space_error"] = str(exc)
if mode == "catalog":
    query = """import json, sqlite3
db=sqlite3.connect("file:/srv/aipedia/data/aipedia.sqlite3?mode=ro",uri=True)
rows=db.execute("SELECT released,approx_released,public_number FROM catalog_tool WHERE published=1").fetchall()
numbers=sorted(row[2] for row in rows if row[2] is not None)
print(json.dumps({"integrity":db.execute("PRAGMA integrity_check").fetchone()[0],
"foreign_keys":len(db.execute("PRAGMA foreign_key_check").fetchall()),
"published_tools":len(rows),"numbered_tools":len(numbers),
"numbers_continuous":numbers==list(range(1,len(rows)+1)),
"exact_dates":sum(bool(row[0]) for row in rows),
"approximate_dates":sum(bool(row[1]) for row in rows),
"without_date":sum(not row[0] and not row[1] for row in rows),
"published_models":db.execute("SELECT COUNT(*) FROM catalog_modelversion WHERE published=1 AND entry_type='model'").fetchone()[0]}))"""
    check = command("sudo", "-n", "python3", "-c", query)
    result["catalog"] = json.loads(check["stdout"]) if check["ok"] else check
result["ok"] = (result.get("service", {"ok": True})["ok"]
    and "RUNNING" in result.get("service", {"stdout": "RUNNING"})["stdout"]
    and result.get("health", {"status": 200}).get("status") == 200
    and all(result.get(k, True) for k in ("root_exists", "database_exists", "release_tool_exists", "venv_exists"))
    and "free_space_error" not in result)
if mode == "catalog":
    catalog = result["catalog"]
    result["ok"] = (catalog.get("integrity") == "ok" and catalog.get("foreign_keys") == 0
        and catalog.get("published_tools") == 143 and catalog.get("numbered_tools") == 143
        and catalog.get("numbers_continuous") and catalog.get("exact_dates") == 60
        and catalog.get("approximate_dates") == 83 and catalog.get("without_date") == 0
        and catalog.get("published_models") == 321)
print(json.dumps(result, sort_keys=True))
'''


def run(args, *, input_text=None, timeout=120):
    try:
        return subprocess.run(args, input=input_text, text=True, capture_output=True,
                              timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"SERVER ACCESS = FAIL: {exc}") from exc


def observe(mode):
    result = run(["ssh", ALIAS, "python3", "-", mode], input_text=OBSERVE)
    if result.returncode:
        raise SystemExit("SERVER ACCESS = FAIL: " + (result.stderr.strip() or result.stdout.strip()))
    try:
        report = json.loads(result.stdout)
    except ValueError as exc:
        raise SystemExit("SERVER ACCESS = FAIL: invalid server response: " + result.stdout[:500]) from exc
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit("SERVER ACCESS = FAIL: see failed preflight fields above")
    print("SERVER ACCESS = PASS")


def release_archive(path, digest):
    artifact_dir = (ROOT / "artifacts" / "code-release").resolve()
    archive = Path(path).resolve()
    if not archive.is_file() or not archive.is_relative_to(artifact_dir):
        raise SystemExit("Only an existing artifacts/code-release archive may be uploaded")
    if not re.fullmatch(r"aipedia-code-[0-9a-f]{12}\.zip", archive.name):
        raise SystemExit("Archive filename is not a canonical AIpediya code release")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SystemExit("--sha256 must be a lowercase SHA-256 digest")
    manifest, commit, _names = inspect_archive(archive, digest)
    if manifest.get("kind") != "code" or commit[:12] not in archive.name:
        raise SystemExit("Expected an exact committed code release archive")
    remote = f"/tmp/aipedia-code-{commit[:12]}-{digest[:12]}.zip"
    return archive, remote, commit


def remote_digest(remote, digest):
    result = run(["ssh", ALIAS, "sha256sum", remote])
    actual = result.stdout.split()[0] if result.returncode == 0 and result.stdout.split() else ""
    if actual != digest:
        raise SystemExit("SERVER ACCESS = FAIL: remote archive SHA-256 differs: " +
                         (result.stderr.strip() or actual or "file absent"))


def upload(archive, remote, digest):
    result = run(["scp", "-B", str(archive), f"{ALIAS}:{remote}"], timeout=300)
    if result.returncode:
        raise SystemExit("SERVER ACCESS = FAIL: upload: " + (result.stderr.strip() or result.stdout.strip()))
    remote_digest(remote, digest)
    print(json.dumps({"upload": remote, "sha256": digest, "verified": True}))


def release_preflight(remote, digest, commit, plan, publication):
    remote_digest(remote, digest)
    script = (ROOT / "tools" / "server_release_preflight.py").read_text(encoding="utf-8")
    result = run(["ssh", ALIAS, "sudo", "-n", "python3", "-", remote, digest, commit,
                  plan, publication], input_text=script, timeout=900)
    if result.returncode:
        raise SystemExit("RELEASE PREFLIGHT = FAIL: " + (result.stderr.strip() or result.stdout.strip()))
    try:
        report = json.loads(result.stdout)
    except ValueError as exc:
        raise SystemExit("RELEASE PREFLIGHT = FAIL: invalid report: " + result.stdout[:1000]) from exc
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"preflight-{digest[:12]}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report.get("status") != "PASS":
        raise SystemExit("RELEASE PREFLIGHT = FAIL: " + str(path))
    print("RELEASE PREFLIGHT = PASS; report: " + str(path))


def deploy(remote, digest, commit, dry_run, plan, publication):
    remote_digest(remote, digest)
    report_path = REPORT_DIR / f"preflight-{digest[:12]}.json"
    if not dry_run:
        if not report_path.is_file():
            raise SystemExit("Live deploy requires the matching successful release-preflight report")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (report.get("status"), report.get("sha256"), report.get("commit"),
                report.get("catalog_plan"), report.get("publication_state")) != (
                    "PASS", digest, commit, plan, publication):
            raise SystemExit("Release-preflight report does not match the archive")
    args = ["ssh", ALIAS, "sudo", "-n", "python3",
            REMOTE_ROOT + "/app/tools/deploy_code_release.py", remote, "--sha256", digest,
            "--catalog-plan", plan, "--publication-state", publication]
    if dry_run:
        args.append("--dry-run")
    result = run(args, timeout=1200)
    if result.stdout:
        print(result.stdout)
    if result.returncode:
        raise SystemExit("CODE DEPLOY = FAIL: " + result.stderr.strip())
    print("CODE DEPLOY = " + ("DRY-RUN PASS" if dry_run else "PASS"))


def verify_release(backup_name):
    if not re.fullmatch(r"aipedia-before-code-[0-9]{8}T[0-9]{6}Z\.sqlite3", backup_name):
        raise SystemExit("Expected an AIpediya pre-release backup filename")
    script = (ROOT / "tools/server_compare.py").read_text(encoding="utf-8")
    result = run(["ssh", ALIAS, "sudo", "-n", "python3", "-", backup_name],
                 input_text=script, timeout=180)
    if result.returncode:
        raise SystemExit("RELEASE COMPARE = FAIL: " + (result.stderr.strip() or result.stdout.strip()))
    report = json.loads(result.stdout)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report.get("ok"):
        raise SystemExit("RELEASE COMPARE = FAIL")
    print("RELEASE COMPARE = PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "health", "status", "catalog"):
        commands.add_parser(name)
    comparison = commands.add_parser("verify-release")
    comparison.add_argument("backup_name")
    for name in ("upload", "release-preflight", "deploy"):
        sub = commands.add_parser(name)
        sub.add_argument("archive")
        sub.add_argument("--sha256", required=True)
        if name in ("release-preflight", "deploy"):
            sub.add_argument("--catalog-plan", default=PLAN)
            sub.add_argument("--publication-state", default=PUBLICATION)
        if name == "deploy":
            sub.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command in ("preflight", "health", "status", "catalog"):
        observe(args.command)
        return
    if args.command == "verify-release":
        verify_release(args.backup_name)
        return
    archive, remote, commit = release_archive(args.archive, args.sha256)
    if args.command == "upload":
        upload(archive, remote, args.sha256)
    else:
        import zipfile
        for value in (args.catalog_plan, args.publication_state):
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or not value.startswith("data/"):
                raise SystemExit("Release manifests must be safe data/ paths in the archive")
        with zipfile.ZipFile(archive) as release:
            names = set(release.namelist())
        if any("app/" + value not in names for value in (args.catalog_plan, args.publication_state)):
            raise SystemExit("Release manifests are absent from the archive")
        if args.command == "release-preflight":
            release_preflight(remote, args.sha256, commit, args.catalog_plan, args.publication_state)
        else:
            deploy(remote, args.sha256, commit, args.dry_run, args.catalog_plan, args.publication_state)


if __name__ == "__main__":
    main()

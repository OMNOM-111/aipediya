"""Create a secret-free code-only release archive from the current Git commit.

``--candidate LIST`` builds a *release candidate* instead: the committed tree
of HEAD plus the working-tree versions of exactly the files named in LIST (one
path per line; a missing file means "deleted in the candidate"). This lets a
verified package be identified before it is committed, without picking up
unrelated uncommitted work: the archive records the base commit and the
sha256 of every candidate file, and its release id (``commit`` in the
manifest, reported by /healthz) is derived from those hashes, not from HEAD
alone.
"""
import argparse
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENIED_PARTS = {".venv", "backups", "artifacts", "data/local", "__pycache__"}
DENIED_SUFFIXES = {".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".log", ".env", ".zip", ".pyc"}
DENIED_NAMES = {"secret.key", "secret.env", "aipedia.pid", "port.txt", ".env"}


def deny(name):
    path = name.replace("\\", "/")
    if any(part in path.split("/") for part in (".venv", "__pycache__")):
        return True
    if path.startswith("backups/") or path.startswith("artifacts/") or path.startswith("data/local/"):
        return True
    suffix = Path(path).suffix
    if suffix in DENIED_SUFFIXES or path.endswith(".sqlite3-wal") or path.endswith(".sqlite3-shm"):
        return True
    return Path(path).name in DENIED_NAMES


def candidate_files(list_path):
    entries = {}
    for line in Path(list_path).read_text(encoding="utf-8").splitlines():
        rel = line.strip().replace("\\", "/")
        if not rel or rel.startswith("#"):
            continue
        if deny(rel):
            raise SystemExit("Refusing a denied path in the candidate list: " + rel)
        target = ROOT / rel
        entries[rel] = target.read_bytes() if target.exists() else None
    return entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", help="File listing the working-tree paths of a release candidate.")
    args = parser.parse_args()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    files = {}
    committed = subprocess.check_output(["git", "archive", "--format=zip", head], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(committed)) as tracked:
        for rel in tracked.namelist():
            if rel.endswith("/") or deny(rel):
                continue
            files["app/" + rel] = tracked.read(rel)
    build = {"commit": head, "kind": "code"}
    if args.candidate:
        overlay = candidate_files(args.candidate)
        hashes = {}
        for rel, content in sorted(overlay.items()):
            if content is None:
                files.pop("app/" + rel, None)
                hashes[rel] = None
            else:
                files["app/" + rel] = content
                hashes[rel] = hashlib.sha256(content).hexdigest()
        digest = hashlib.sha256(json.dumps({"base": head, "files": hashes}, sort_keys=True).encode()).hexdigest()
        build = {"commit": digest[:40], "kind": "code-candidate", "base_commit": head,
                 "candidate_files": hashes}
    files["app/BUILD.json"] = json.dumps(build, sort_keys=True).encode()
    if any(deny(name[4:]) or name.endswith(".sqlite3") for name in files):
        raise SystemExit("Refusing to pack a database or secret")
    manifest = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    out_dir = ROOT / "artifacts" / "code-release"
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"aipedia-code-{build['commit'][:12]}.zip"
    if archive.exists():
        archive.unlink()
    files["MANIFEST.json"] = json.dumps({**build, "files": manifest}, indent=2).encode()
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    print(json.dumps({
        "archive": str(archive),
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "commit": build["commit"],
        "base_commit": head,
        "files": len(manifest),
        "kind": build["kind"],
        "candidate_files": len(build.get("candidate_files", {})),
    }))

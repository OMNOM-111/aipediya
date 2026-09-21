"""Create a secret-free code-only release archive from the current Git commit."""
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


if __name__ == "__main__":
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out_dir = ROOT / "artifacts" / "code-release"
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"aipedia-code-{commit[:12]}.zip"
    if archive.exists():
        archive.unlink()
    files = {}
    committed = subprocess.check_output(["git", "archive", "--format=zip", commit], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(committed)) as tracked:
        for rel in tracked.namelist():
            if rel.endswith("/") or deny(rel):
                continue
            files["app/" + rel] = tracked.read(rel)
    files["app/BUILD.json"] = json.dumps({"commit": commit, "kind": "code"}).encode()
    if any(deny(name[4:]) or name.endswith(".sqlite3") for name in files):
        raise SystemExit("Refusing to pack a database or secret")
    manifest = {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
    files["MANIFEST.json"] = json.dumps({"commit": commit, "kind": "code", "files": manifest}, indent=2).encode()
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    print(json.dumps({
        "archive": str(archive),
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "commit": commit,
        "files": len(manifest),
        "kind": "code",
    }))

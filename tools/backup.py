import argparse
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root / "backups")
    args = parser.parse_args()
    db = Path(os.environ.get("AIPEDIA_DB", root / "data" / "aipedia.sqlite3")).resolve()
    if not db.is_file():
        raise SystemExit("Database does not exist")
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / ("aipedia-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".sqlite3")
    os.umask(0o077)
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(target) as backup:
        source.backup(backup)
        if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Backup integrity check failed")
    print(target)

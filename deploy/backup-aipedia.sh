#!/bin/sh
set -eu

: "${AIPEDIA_DB:?AIPEDIA_DB must be set}"
backup_dir=/srv/aipedia/backups
python=/srv/aipedia/venv/bin/python
retention_days=${AIPEDIA_BACKUP_RETENTION_DAYS:-14}

umask 077
cd /
mkdir -p "$backup_dir"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
temporary="$backup_dir/.aipedia-scheduled-$stamp-$$.sqlite3"
destination="$backup_dir/aipedia-scheduled-$stamp.sqlite3"

"$python" - "$AIPEDIA_DB" "$temporary" <<'PY'
import sqlite3
import sys

source_path, backup_path = sys.argv[1:]
with sqlite3.connect(source_path) as source, sqlite3.connect(backup_path) as backup:
    source.backup(backup)
with sqlite3.connect(backup_path) as check:
    if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise SystemExit("SQLite integrity check failed")
PY

mv "$temporary" "$destination"
find "$backup_dir" -maxdepth 1 -type f -name 'aipedia-scheduled-*.sqlite3' -mtime +"$retention_days" -delete
printf '%s\n' "$destination"

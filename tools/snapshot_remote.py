"""Read AIpedia state and make a consistent, private online backup; never read secrets."""
import hashlib
import json
import os
import pwd
import sqlite3
from pathlib import Path

root = Path('/srv/aipedia')
destination = root / 'backups' / 'aipedia-acceptance-baseline-20260920.sqlite3'
if destination.exists():
    raise SystemExit('Refusing to overwrite baseline backup')
connection = sqlite3.connect('file:/srv/aipedia/data/aipedia.sqlite3?mode=ro', uri=True)
with sqlite3.connect(destination) as target:
    connection.backup(target)
    assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
os.chmod(destination, 0o600)
account = pwd.getpwnam('aipedia')
os.chown(destination, account.pw_uid, account.pw_gid)
transfer = Path('/tmp/aipedia-acceptance-baseline-20260920.sqlite3')
with destination.open('rb') as src, transfer.open('xb') as dst:
    import shutil
    shutil.copyfileobj(src, dst)
account = pwd.getpwnam('stratforge')
os.chmod(transfer, 0o600)
os.chown(transfer, account.pw_uid, account.pw_gid)
counts = {}
for table in ['catalog_modelversion', 'catalog_offer', 'catalog_evaluation', 'catalog_researchrecord', 'catalog_revision', 'catalog_publicationrevision']:
    counts[table] = connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
files = {}
for directory in ['aipedia', 'catalog', 'contributions', 'templates', 'static']:
    for path in (root / 'app' / directory).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            files[str(path.relative_to(root / 'app'))] = hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps({'backup': str(destination), 'transfer': str(transfer), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'counts': counts, 'migrations': connection.execute("SELECT app,name FROM django_migrations WHERE app IN ('catalog','contributions')").fetchall(), 'files': files}, ensure_ascii=False))

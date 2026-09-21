"""Deploy a reviewed chronology release only within the existing AIpedia service."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path
from deploy_release import ROOT, DB, SUPERVISOR, backup, own_tree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive'); parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    archive = Path(args.archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == args.sha256
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read('MANIFEST.json')); commit = manifest['commit']
        assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
        stage = ROOT / 'releases' / ('chronology-' + commit[:12])
        stage.mkdir(exist_ok=False)
        for name, digest in manifest['files'].items():
            assert not name.endswith(('.sqlite3', '.env'))
            target = (stage / name).resolve()
            assert target.is_relative_to(stage.resolve())
            content = z.read(name); assert hashlib.sha256(content).hexdigest() == digest
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
    app = stage / 'app'
    if (ROOT / 'app/public-release').exists():
        shutil.copytree(ROOT / 'app/public-release', app / 'public-release')
    own_tree(stage)

    def manage(*command):
        subprocess.run(['runuser', '-u', 'aipedia', '--', 'env', 'AIPEDIA_ENV=local', 'AIPEDIA_DB=' + str(DB),
                        str(ROOT / 'venv/bin/python'), str(app / 'manage.py'), *command], cwd=app, check=True)

    manage('check'); manage('collectstatic', '--noinput')
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    before = ROOT / 'backups' / ('aipedia-before-chronology-' + stamp + '.sqlite3')
    previous = ROOT / 'releases' / ('before-chronology-' + stamp)
    stopped = switched = renamed = started = False
    try:
        subprocess.run(SUPERVISOR + ['stop', 'aipedia'], check=True); stopped = True
        backup(DB, before)
        manage('migrate', '--noinput')
        manage('apply_release_chronology', str(app / 'data/release_dates.json'), '--dry-run')
        manage('apply_release_chronology', str(app / 'data/release_dates.json'))
        subprocess.run([str(ROOT / 'venv/bin/python'), str(app / 'tools/verify_chronology.py'), str(before), str(DB)], check=True)
        manage('apply_release_chronology', str(app / 'data/release_dates.json'))
        os.rename(ROOT / 'app', previous); renamed = True
        os.rename(app, ROOT / 'app'); switched = True
        subprocess.run(SUPERVISOR + ['start', 'aipedia'], check=True); started = True
        for attempt in range(15):
            try:
                request = urllib.request.Request('http://127.0.0.1:18810/healthz', headers={'Host': 'aipediya.com', 'X-Forwarded-Proto': 'https'})
                payload = json.loads(urllib.request.urlopen(request, timeout=10).read())
                assert payload['release'] == commit
                break
            except Exception:
                if attempt == 14: raise
                time.sleep(1)
        after = ROOT / 'backups' / ('aipedia-after-chronology-' + stamp + '.sqlite3'); backup(DB, after)
        result = {'commit': commit, 'before_database': str(before), 'after_database': str(after),
                  'previous_app': str(previous), 'status': 'deployed-origin-verified'}
        (stage / 'DEPLOYMENT.json').write_text(json.dumps(result, indent=2))
        own_tree(stage)
        print(json.dumps(result))
    except Exception:
        if started:
            print('App exposed; preserve database for reviewed rollback to protect intervening writes.')
        elif stopped and before.exists():
            if switched:
                os.rename(ROOT / 'app', ROOT / 'releases' / ('failed-chronology-' + stamp)); os.rename(previous, ROOT / 'app')
            elif renamed:
                os.rename(previous, ROOT / 'app')
            backup(DB, ROOT / 'backups' / ('failed-chronology-' + stamp + '.sqlite3'))
            with sqlite3.connect(before.as_uri() + '?mode=ro', uri=True) as src, sqlite3.connect(DB) as dst:
                src.backup(dst)
            subprocess.run(SUPERVISOR + ['start', 'aipedia'], check=True)
        raise

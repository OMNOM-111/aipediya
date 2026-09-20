"""Run as root on existing AIpedia host. Never alters tunnel or other services."""
import argparse
import hashlib
import json
import os
import pwd
import shutil
import sqlite3
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT=Path('/srv/aipedia')
DB=ROOT/'data/aipedia.sqlite3'
SUPERVISOR=['supervisorctl','-c',str(ROOT/'supervisord.conf')]


def backup(source, destination):
    if destination.exists(): raise RuntimeError('Backup path already exists')
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
        assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    os.chmod(destination,0o600)
    account=pwd.getpwnam('aipedia');os.chown(destination,account.pw_uid,account.pw_gid)


def own_tree(path):
    account=pwd.getpwnam('aipedia')
    for p in [path,*path.rglob('*')]:
        os.chown(p,account.pw_uid,account.pw_gid)
        os.chmod(p,0o750 if p.is_dir() else 0o640)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--sha256',required=True);args=p.parse_args()
    archive=Path(args.archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==args.sha256,'Release archive digest mismatch'
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('MANIFEST.json'));commit=manifest['commit']
        assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
        stage=ROOT/'releases'/('20260920-'+commit[:12]);stage.mkdir(parents=True,exist_ok=False)
        for name,digest in manifest['files'].items():
            target=(stage/name).resolve()
            assert target.is_relative_to(stage.resolve()) and not name.startswith('/'),'Unsafe archive entry'
            content=z.read(name);assert hashlib.sha256(content).hexdigest()==digest,name
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    own_tree(stage)
    app=stage/'app';sources=stage/'sources'
    def manage(*cmd):
        result=subprocess.run(['runuser','-u','aipedia','--','env','AIPEDIA_ENV=local','AIPEDIA_DB='+str(DB),
            str(ROOT/'venv/bin/python'),str(app/'manage.py'),*cmd],cwd=app,text=True,capture_output=True)
        if result.returncode: raise RuntimeError(result.stdout+'\n'+result.stderr)
        print(result.stdout.strip(),flush=True)
    manage('check');manage('collectstatic','--noinput')
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    before=ROOT/'backups'/('aipedia-before-'+stamp+'.sqlite3')
    previous=ROOT/'releases'/('before-'+stamp)
    switched=False;stopped=False;started=False;old_renamed=False
    try:
        subprocess.run(SUPERVISOR+['stop','aipedia'],check=True);stopped=True
        backup(DB,before)
        manage('migrate','--noinput')
        manage('import_epoch_snapshot',str(sources),'--dry-run')
        manage('import_epoch_snapshot',str(sources))
        # Validate preserving every original price, identity and history before exposing the release.
        subprocess.run([str(ROOT/'venv/bin/python'),str(app/'tools/verify_preservation.py'),str(before),str(DB)],check=True)
        manage('import_epoch_snapshot',str(sources))
        os.rename(ROOT/'app',previous)
        old_renamed=True
        os.rename(app,ROOT/'app');switched=True
        subprocess.run(SUPERVISOR+['start','aipedia'],check=True);started=True
        for attempt in range(15):
            try:
                request=urllib.request.Request('http://127.0.0.1:18810/healthz',headers={'Host':'aipediya.com','X-Forwarded-Proto':'https'})
                payload=json.loads(urllib.request.urlopen(request,timeout=10).read())
                assert payload['release']==commit,payload
                break
            except Exception:
                if attempt==14: raise
                time.sleep(1)
        after=ROOT/'backups'/('aipedia-after-'+stamp+'.sqlite3');backup(DB,after)
        state={'commit':commit,'before_database':str(before),'after_database':str(after),'previous_app':str(previous),
            'current_app':str(ROOT/'app'),'status':'deployed-origin-verified','public_acceptance':'pending'}
        (stage/'DEPLOYMENT.json').write_text(json.dumps(state,indent=2))
        own_tree(stage)
        print(json.dumps(state),flush=True)
    except Exception:
        # Before exposure no other writer can enter through the stopped app.
        # Once started, preserve DB for a reviewed rollback instead of risking new edits.
        if started:
            print('DEPLOYMENT NEEDS REVIEW: app was started; database retained to protect intervening writes.',flush=True)
        elif stopped and before.exists():
            if switched:
                failed=ROOT/'releases'/('failed-'+stamp);os.rename(ROOT/'app',failed);os.rename(previous,ROOT/'app')
            elif old_renamed:
                os.rename(previous,ROOT/'app')
            failed_db=ROOT/'backups'/('aipedia-failed-'+stamp+'.sqlite3');backup(DB,failed_db)
            with sqlite3.connect(before.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(DB) as dst: src.backup(dst)
            subprocess.run(SUPERVISOR+['start','aipedia'],check=True)
        raise

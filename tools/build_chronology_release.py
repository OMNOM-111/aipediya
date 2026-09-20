import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'artifacts/chronology-20260920'

if __name__ == '__main__':
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    contents = subprocess.check_output(['git', 'archive', '--format=zip', commit], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        files = {'app/' + name: z.read(name) for name in z.namelist()
                 if not name.endswith('/') and not name.startswith('data/research/')}
    assert 'app/data/release_dates.json' in files
    files['app/BUILD.json'] = json.dumps({'commit': commit, 'release': '20260920-chronology'}).encode()
    files['MANIFEST.json'] = json.dumps({'commit': commit,
        'files': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}, indent=2).encode()
    archive = BASE / ('aipedia-chronology-' + commit[:12] + '.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items(): z.writestr(name, content)
    report = {'archive': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'commit': commit}
    (BASE / 'build.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))

"""Create an allowlisted, secret-free code/source release archive."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'artifacts/acceptance-20260920/sources-audit'
OWN_FILES = {'gpqa_diamond.csv','otis_mock_aime_2024_2025.csv','frontiermath.csv','frontiermath_tier_4.csv',
    'frontiermath_tiers_1_3_v2.csv','frontiermath_tier_4_v2.csv','frontiermath_erdos.csv','swe_bench_verified.csv',
    'math_level_5.csv','simpleqa_verified.csv','chess_puzzles.csv','ebr_bench.csv','mystery_game_puzzles.csv','mirrorcode.csv',
    'benchmark_metadata.csv','model_metadata.csv'}

if __name__ == '__main__':
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive = ROOT / 'artifacts/acceptance-20260920' / f'aipedia-release-{commit[:12]}.zip'
    files = {}
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    for rel in tracked:
        if not rel or rel.startswith('data/research/'): continue
        path=ROOT/rel
        if path.is_file(): files['app/'+rel]=path.read_bytes()
    for name in ['verified-alias-registry.json','verified-new-models.json','eci_scores.csv']:
        files['sources/'+name]=(SOURCE/name).read_bytes()
    for name in OWN_FILES: files['sources/epoch-export/'+name]=(SOURCE/'epoch-export'/name).read_bytes()
    files['app/BUILD.json']=json.dumps({'commit':commit,'release':'20260920','source_snapshot':'2026-09-20'}).encode()
    manifest={name:hashlib.sha256(content).hexdigest() for name,content in files.items()}
    files['MANIFEST.json']=json.dumps({'commit':commit,'files':manifest},indent=2).encode()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name,content in files.items(): z.writestr(name,content)
    print(json.dumps({'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'commit':commit,'files':len(manifest)}))

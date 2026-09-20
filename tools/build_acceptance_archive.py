"""Build the public acceptance deliverable from an explicit, reviewed allowlist."""
import hashlib
import json
import zipfile
from pathlib import Path

OWN_FILES = {
    'chess_puzzles.csv', 'ebr_bench.csv', 'frontiermath.csv', 'frontiermath_erdos.csv',
    'frontiermath_tiers_1_3_v2.csv', 'frontiermath_tier_4.csv', 'frontiermath_tier_4_v2.csv',
    'gpqa_diamond.csv', 'math_level_5.csv', 'mirrorcode.csv', 'mystery_game_puzzles.csv',
    'otis_mock_aime_2024_2025.csv', 'simpleqa_verified.csv', 'swe_bench_verified.csv',
}

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'artifacts/acceptance-20260920'
SOURCE = BASE / 'sources-audit'


def digest(content):
    return hashlib.sha256(content).hexdigest()


if __name__ == '__main__':
    build = json.loads((BASE / 'build.json').read_text(encoding='utf-8-sig'))
    results = json.loads((BASE / 'ui/public-final/results.json').read_text(encoding='utf-8'))
    coverage = json.loads((SOURCE / 'coverage-summary.json').read_text(encoding='utf-8-sig'))
    assert coverage['production_after_verified'] is True
    assert results['summary'] == {'PASS': 289, 'FAIL': 0, 'BLOCKED': 0}, results['summary']
    files = {}

    def add(path, name):
        assert path.is_file(), path
        assert name not in files, name
        files[name] = path.read_bytes()

    for name in ['RELEASE_ACCEPTANCE.md', 'ROLLBACK.md']:
        add(BASE / name, name)
    add(ROOT / 'docs/COMPARISON_RULES.md', 'COMPARISON_RULES.md')
    for name in ['coverage.csv', 'coverage-summary.json', 'SOURCES_AUDIT.md',
                 'source-manifest.json', 'downloads-manifest.json', 'verified-alias-registry.json', 'verified-new-models.json',
                 'public-gap-notes.json', 'legacy-observations-audit.json', 'eci_scores.csv']:
        add(SOURCE / name, 'sources/' + name)
    for name in sorted(OWN_FILES):
        add(SOURCE / 'epoch-export' / name, 'sources/epoch-own/' + name)
    files['sources/ATTRIBUTION.md'] = (
        '# Attribution\n\nEpoch AI, Capabilities & Benchmarking; Epoch Capabilities Index. '
        'Accessed 2026-09-20. Own-run CSVs and the final ECI model scores are included unchanged. '
        'AIpedia alias mapping, gap explanations and presentation are separate annotations.\n\n'
        'Licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). '
        'Rights: https://epoch.ai/benchmarks/use-this-data and https://epoch.ai/eci.\n\n'
        'Sources: https://epoch.ai/data/benchmark_data.zip (only the14 own-run files) and '
        'https://epoch.ai/data/eci_scores.csv. External components are excluded.\n'
    ).encode('utf-8')
    for name in ['tests.txt', 'import-tests-final.txt', 'import-final.json', 'import-final-repeat.json',
                 'preservation-public.json', 'restore-verification.json', 'supervisor-final.txt',
                 'deployment-final.log']:
        add(BASE / name, 'verification/' + name)
    qa = BASE / 'ui/public-final'
    for name in ['results.json', 'qa-matrix.csv', 'PUBLIC_QA_REVIEW.md']:
        add(qa / name, 'qa/' + name)
    add(BASE / 'ui/public-recordings.json', 'recordings/manifest.json')
    review = files['qa/PUBLIC_QA_REVIEW.md'].decode('utf-8-sig')
    review = review.replace('Файл относительно `ui/`', 'Файл относительно корня архива')
    review = review.replace('../public-recordings.json', '../recordings/manifest.json')
    review = review.replace('`tools/release_ui_acceptance.mjs` от корня проекта',
                            '`verification/scripts/release_ui_acceptance.mjs` от корня архива')
    review = review.replace('оригинальные PNG и `contact-sheets/`',
                            'оригинальные PNG в `../screenshots/` и просмотренные листы в `contact-sheets/`')
    review = review.replace('Проверка скачивания финального архива будет отдельным шагом после его публикации ведущим агентом.',
                            'Скачивание финального ZIP проверяется отдельно после упаковки; результат и SHA-256 фиксируются в итоговом сообщении владельцу.')
    recording_manifest = json.loads(files['recordings/manifest.json'])
    for item in recording_manifest:
        item['original_file'] = item['file']
        item['file'] = item['lang'] + '/headers-both-directions.webm'
    files['recordings/manifest.json'] = json.dumps(recording_manifest, ensure_ascii=False, indent=2).encode()
    for name in ['firefox-table-2.jpg', 'webkit-table-3.jpg', 'chromium-card-2.jpg', 'webkit-card-1.jpg']:
        add(qa / 'contact-sheets' / name, 'qa/contact-sheets/' + name)
    screenshots = sorted(qa.glob('*.png'))
    assert len(screenshots) >= 272
    for path in screenshots:
        add(path, 'screenshots/' + path.name)
    for lang in ['ru', 'en']:
        folder = BASE / ('ui/public-recording-' + lang)
        for name in ['results.json', 'qa-matrix.csv']:
            add(folder / name, 'recordings/' + lang + '/' + name)
        videos = [p for p in folder.glob('*.webm') if not p.name.startswith('page@')]
        assert len(videos) == 1, [str(p) for p in videos]
        add(videos[0], 'recordings/' + lang + '/headers-both-directions.webm')
        add(folder / 'proof-last-second.png', 'recordings/' + lang + '/proof-last-second.png')
        review = review.replace('public-recording-' + lang + '/chromium-header-clicks.webm',
                                'recordings/' + lang + '/headers-both-directions.webm')
    files['qa/PUBLIC_QA_REVIEW.md'] = review.encode('utf-8')
    for name in ['release_ui_acceptance.mjs', 'verify_preservation.py', 'build_acceptance_archive.py']:
        add(ROOT / 'tools' / name, 'verification/scripts/' + name)
    version = {
        'site': 'https://aipediya.com', 'release': '20260920', 'commit': build['commit'],
        'code_archive_sha256': build['sha256'], 'source_snapshot': '2026-09-20',
        'public_qa_started': results['started'], 'public_qa_completed': results['completed'],
        'public_qa_summary': results['summary'], 'engines': results['engines'],
        'physical_devices': results['physicalDevices'], 'zoom_method': results['textZoomMethod'],
        'production_after_verified': coverage['production_after_verified'],
        'public_archive_url': 'https://aipediya.com/releases/20260920/acceptance.zip',
    }
    files['VERSION.json'] = json.dumps(version, indent=2, ensure_ascii=False).encode('utf-8')
    files['MANIFEST.sha256.json'] = json.dumps({name: digest(content) for name, content in sorted(files.items())}, indent=2).encode()
    archive = BASE / 'aipedia-acceptance-20260920.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in sorted(files.items()):
            assert not name.endswith(('.sqlite3', '.env', '.pem', '.key')) and '_external.csv' not in name
            z.writestr(name, content)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('MANIFEST.sha256.json'))
        assert all(digest(z.read(name)) == sha for name, sha in manifest.items())
    report = {'path': str(archive), 'bytes': archive.stat().st_size,
              'sha256': digest(archive.read_bytes()), 'files': len(files), 'commit': build['commit']}
    (BASE / 'acceptance-archive.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))

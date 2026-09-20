import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'artifacts/chronology-20260920'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output'); args = parser.parse_args()
    a = json.loads((BASE / 'release-date-audit.json').read_text(encoding='utf-8-sig'))
    b = json.loads((BASE / 'media-product-date-audit.json').read_text(encoding='utf-8-sig'))
    first = {r['slug']: r for r in a['rows']}
    second = {r['slug']: r for r in b['records']}
    db = sqlite3.connect((ROOT / 'backups/chronology-baseline-20260920.sqlite3').as_uri() + '?mode=ro', uri=True)
    rows, conflicts = [], []
    for slug, name in db.execute('SELECT slug,name FROM catalog_modelversion WHERE published=1 ORDER BY id'):
        candidates = []
        r = first.get(slug, {})
        if r.get('status') == 'confirmed':
            candidates.append({'released': r['release_date'], 'source_url': r['source_url'],
                               'evidence': r['evidence'], 'date_kind': r.get('date_semantics', ''),
                               'notes': r.get('notes', []), 'audit': 'release-date-audit.json'})
        s = second.get(slug, {})
        if s.get('status') == 'confirmed':
            candidates.append({'released': s['date'], 'source_url': s['sourceURL'],
                               'evidence': s['evidence'], 'date_kind': s.get('date_kind', ''),
                               'audit': 'media-product-date-audit.json'})
        if len({c['released'] for c in candidates}) > 1:
            conflicts.append({'slug': slug, 'name': name, 'candidates': candidates})
            continue
        if candidates:
            row = {'slug': slug, 'name': name, 'checked': '2026-09-20', **candidates[-1]}
            if len(candidates) > 1: row['corroboration'] = candidates[0]
        else:
            row = {'slug': slug, 'name': name, 'released': None, 'checked': '2026-09-20',
                   'reason': 'No verified exact-version public release date in checked sources; no chronological rank assigned.',
                   'checked_sources': list(dict.fromkeys(x for x in [r.get('source_url'), r.get('candidate_primary_url'),
                       s.get('sourceURL'), s.get('catalog_source_url'),
                       *[e.get('source_url') for e in r.get('evidence', []) if isinstance(e, dict)]] if x)),
                   'audit_notes': {'text': r.get('reason') or r.get('notes') or r.get('status'),
                                   'media': s.get('evidence') or s.get('status')}}
        rows.append(row)
    (BASE / 'date-conflicts.json').write_text(json.dumps(conflicts, ensure_ascii=False, indent=2), encoding='utf8')
    assert not conflicts, 'Conflicting dates require explicit evidence review: date-conflicts.json'
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    document = {'policy': 'Verified exact-version public release date; same date alphabetical name; unknown date unnumbered and last.',
                'checked': '2026-09-20', 'models': rows}
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'cards': len(rows), 'dated': sum(bool(r['released']) for r in rows),
                      'unknown': sum(not r['released'] for r in rows), 'path': str(output)}))

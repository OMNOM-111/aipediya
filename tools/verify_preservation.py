"""Compare a release database with its fresh baseline; never modify either."""
import argparse
import json
import sqlite3
from pathlib import Path


def connect(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def verify(before, after):
    b, a = connect(before), connect(after)
    results = {}
    for table, columns in [('catalog_modelversion', 'id,slug,public_number,name,version,published'),
                           ('catalog_offer', '*'), ('catalog_revision', '*'), ('catalog_publicationrevision', '*')]:
        old = b.execute(f'SELECT {columns} FROM {table} ORDER BY id').fetchall()
        current = a.execute(f'SELECT {columns} FROM {table} WHERE id <= ? ORDER BY id', (max(r[0] for r in old),)).fetchall()
        results[table] = {'preserved': old == current, 'original_rows': len(old)}
    old = b.execute('SELECT id,score,public,conditions FROM catalog_evaluation WHERE public=1 ORDER BY id').fetchall()
    current = [a.execute('SELECT id,score,public,conditions FROM catalog_evaluation WHERE id=?', (r[0],)).fetchone() for r in old]
    results['published_evaluation_values'] = {'preserved': old == current, 'original_rows': len(old)}
    results['integrity'] = a.execute('PRAGMA integrity_check').fetchone()[0]
    results['counts'] = {'cards': a.execute('SELECT COUNT(*) FROM catalog_modelversion WHERE published=1').fetchone()[0],
        'offers': a.execute('SELECT COUNT(*) FROM catalog_offer').fetchone()[0],
        'observations': a.execute('SELECT COUNT(*) FROM catalog_evaluation WHERE public=1').fetchone()[0],
        'models_with_score': a.execute('SELECT COUNT(DISTINCT model_id) FROM catalog_evaluation WHERE public=1').fetchone()[0]}
    assert results['integrity'] == 'ok' and all(r['preserved'] for r in results.values() if isinstance(r, dict) and 'preserved' in r), results
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('before'); parser.add_argument('after')
    args = parser.parse_args()
    print(json.dumps(verify(args.before, args.after), indent=2))

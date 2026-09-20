"""Verify that chronology changes preserve every unrelated production value."""
import csv
import json
import sqlite3
import sys
from pathlib import Path


def verify(before, after):
    b = sqlite3.connect(Path(before).resolve().as_uri() + '?mode=ro', uri=True)
    a = sqlite3.connect(Path(after).resolve().as_uri() + '?mode=ro', uri=True)
    report = {'integrity': a.execute('PRAGMA integrity_check').fetchone()[0], 'tables': {}}
    for table in ['catalog_modelversion', 'catalog_offer', 'catalog_evaluation', 'catalog_access',
                  'catalog_source', 'catalog_researchrecord', 'catalog_researchrevision',
                  'catalog_revision', 'catalog_publicationrevision']:
        columns = [r[1] for r in b.execute('PRAGMA table_info(' + table + ')')]
        if table == 'catalog_modelversion':
            columns = [c for c in columns if c not in {'released', 'public_number', 'release_evidence'}]
        select = ','.join('"' + c + '"' for c in columns)
        old = b.execute(f'SELECT {select} FROM {table} ORDER BY id').fetchall()
        newest = max((r[0] for r in old), default=0)
        current = a.execute(f'SELECT {select} FROM {table} WHERE id<=? ORDER BY id', (newest,)).fetchall()
        report['tables'][table] = {'original_rows': len(old), 'preserved': old == current}
        assert old == current, table
    rows = a.execute('SELECT id,slug,name,released,public_number FROM catalog_modelversion WHERE published=1 ORDER BY public_number').fetchall()
    dated = [r for r in rows if r[3]]
    unknown = [r for r in rows if not r[3]]
    assert [r[4] for r in dated] == list(range(1, len(dated) + 1))
    assert [r[3] for r in dated] == sorted(r[3] for r in dated)
    assert all(r[4] is None for r in unknown)
    assert report['integrity'] == 'ok'
    assert len(rows) == b.execute('SELECT COUNT(*) FROM catalog_modelversion WHERE published=1').fetchone()[0]
    report.update(dated=len(dated), undated=len(unknown), cards=len(rows), first=dated[:3], last=dated[-5:])
    return report


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))

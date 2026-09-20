import csv
import json
import sqlite3
import sys
from pathlib import Path

before, after, destination = map(Path, sys.argv[1:4])
b = sqlite3.connect(before.resolve().as_uri() + '?mode=ro', uri=True)
a = sqlite3.connect(after.resolve().as_uri() + '?mode=ro', uri=True)
old = dict(b.execute('SELECT slug,public_number FROM catalog_modelversion'))
with destination.open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['old_number', 'new_number', 'name', 'version', 'release_date', 'status', 'url', 'release_source', 'date_notes'])
    for slug, number, name, version, released, evidence in a.execute(
            'SELECT slug,public_number,name,version,released,release_evidence FROM catalog_modelversion WHERE published=1 ORDER BY public_number IS NULL,public_number,id'):
        evidence = json.loads(evidence)
        writer.writerow([old[slug], number, name, version, released, 'verified' if released else 'date_unverified',
                         'https://aipediya.com/models/' + slug, evidence.get('source_url', ''),
                         json.dumps(evidence.get('notes') or evidence.get('audit_notes') or evidence.get('date_kind'), ensure_ascii=False)])
print(destination)

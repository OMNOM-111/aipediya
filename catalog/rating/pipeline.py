"""Local catalog pipeline. Publish all profiles together only after validation."""
import hashlib
import json
from pathlib import Path
from .checks import check_frozen, check_snapshot, params_hash

PROFILES=('BALANCED','QUALITY_FIRST','ECONOMY')
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/rating/snapshots'

def rebuild(master, output=OUTPUT):
    from .builder import build_snapshot
    from catalog.management.commands.rating import save_json
    errors=check_frozen()
    if errors:raise ValueError('; '.join(errors))
    built=[]
    for profile in PROFILES:
        snapshot, contexts, *_=build_snapshot(master,profile)
        errors=check_snapshot(snapshot)
        if errors:raise ValueError('; '.join(errors))
        built.append((snapshot,contexts))
    output=Path(output)
    index={'schema_version':'aipediya-rating-index/1','profiles':{}}
    for snapshot,contexts in built:
        name=snapshot['snapshot']['snapshot_id']
        path=output/(name+'.json')
        if path.exists():
            old=json.loads(path.read_text(encoding='utf-8'))
            if old['snapshot']['content_sha256']!=snapshot['snapshot']['content_sha256']:
                raise ValueError('Immutable snapshot collision: '+name)
        else:save_json(path,snapshot)
        save_json(output/(name+'.contexts.json'),contexts)
        index['profiles'][snapshot['snapshot']['profile']]=path.name
    save_json(output/'current.json',index)
    return [s['snapshot'] for s,_ in built]

def canonical_update(master):
    from django.conf import settings
    from catalog.catalog_master import WORKBOOK_PATH
    if settings.AIPEDIA_ENV=='local' and Path(master).resolve()==WORKBOOK_PATH.resolve():
        return rebuild(master)

def coverage_errors(master, model_ids, tool_ids, output=OUTPUT):
    errors=check_frozen(); master_hash=hashlib.sha256(Path(master).read_bytes()).hexdigest()
    try:
        index=json.loads((Path(output)/'current.json').read_text(encoding='utf-8'))
        for profile in PROFILES:
            name=index['profiles'][profile]
            if Path(name).name!=name:raise ValueError('Invalid snapshot filename')
            snapshot=json.loads((Path(output)/name).read_text(encoding='utf-8'))
            errors.extend(profile+': '+e for e in check_snapshot(snapshot))
            meta=snapshot['snapshot']; ids={m['model_id'] for m in snapshot['models']}
            if ids!=set(model_ids):errors.append(profile+': published Model coverage mismatch')
            if ids & set(tool_ids):errors.append(profile+': Tool has Model rating')
            if meta.get('master_sha256')!=master_hash:errors.append(profile+': stale master hash')
            if meta.get('params_hash')!=params_hash():errors.append(profile+': stale parameters')
            if not meta.get('estimate_policy'):errors.append(profile+': missing numeric estimate policy')
    except (OSError,KeyError,ValueError,TypeError) as exc:errors.append('Rating snapshot unavailable: '+str(exc))
    return errors

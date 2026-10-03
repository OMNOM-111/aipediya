"""Append-only new-item binding on the immutable v1.0 theta scale."""
import copy
import hashlib
import json
import math

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def validate_ledger(ledger, calibration):
    if ledger.get('methodology_version') != calibration['methodology_version']:
        raise ValueError('Ledger methodology mismatch')
    seen=set(calibration['items']); previous=None
    for entry in ledger['entries']:
        payload={k:v for k,v in entry.items() if k!='entry_sha256'}
        if entry.get('previous_sha256')!=previous or entry.get('entry_sha256')!=digest(payload):
            raise ValueError('Item ledger chain/hash mismatch')
        if entry['benchmark'] in seen or len(set(entry['anchor_model_ids']))<5:
            raise ValueError('Item already bound or fewer than five frozen-scale anchors')
        if not 0.1<=entry['a']<=4 or not math.isfinite(entry['c']):
            raise ValueError('Invalid item coefficients')
        if entry['kind']=='arena' and not entry.get('arena_z',{}).get('sd',0)>0:
            raise ValueError('Arena binding requires frozen mean and positive SD')
        if not entry.get('source_urls') or not entry.get('family') or not entry.get('domain'):
            raise ValueError('Binding requires provenance, family and domain')
        seen.add(entry['benchmark']); previous=entry['entry_sha256']

def merged_calibration(calibration,ledger):
    validate_ledger(ledger,calibration)
    result=copy.deepcopy(calibration)
    for entry in ledger['entries']:
        result['items'][entry['benchmark']]={'a':entry['a'],'c':entry['c']}
        if entry['kind']=='arena':result['arena_z'][entry['benchmark']]=entry['arena_z']
    return result

def bind_item(calibration,methodology,ledger,benchmark,observations,family,domain,kind,source_urls,arena_z=None):
    """Ridge binding using ≥5 existing frozen reference theta anchors.

    Observations: model_id, transformed y, sigma, weight. The caller must
    supply permitted/public model-level observations from the canonical master.
    No existing coefficient or Q-basket entry is recalibrated.
    """
    import numpy as np
    validate_ledger(ledger,calibration)
    if benchmark in merged_calibration(calibration,ledger)['items']:
        raise ValueError('Item is already bound; use a new methodology to change it')
    anchors=calibration['reference_theta']
    rows=[x for x in observations if x['model_id'] in anchors]
    ids=sorted({x['model_id'] for x in rows})
    if len(ids)<5:raise ValueError('At least five distinct frozen-theta models are required')
    E=methodology['engine']; pa=1/E['prior_a_sd']**2; pc=1/E['prior_c_sd']**2
    theta=np.array([anchors[x['model_id']]['theta'] for x in rows])
    y=np.array([x['y'] for x in rows]); w=np.array([x.get('weight',1)/x['sigma']**2 for x in rows])
    matrix=np.array([[(w*theta**2).sum()+pa,(w*theta).sum()],[(w*theta).sum(),w.sum()+pc]])
    rhs=np.array([(w*theta*y).sum()+pa*E['prior_a_mean'],(w*y).sum()])
    a,c=np.linalg.solve(matrix,rhs)
    entry=dict(benchmark=benchmark,family=family,domain=domain,kind=kind,a=float(np.clip(a,*E['a_bounds'])),c=float(c),
        anchor_model_ids=ids,source_urls=source_urls,observations_sha256=digest(rows),
        previous_sha256=ledger['entries'][-1]['entry_sha256'] if ledger['entries'] else None)
    if arena_z:entry['arena_z']=arena_z
    entry['entry_sha256']=digest(entry)
    result=copy.deepcopy(ledger); result['entries'].append(entry)
    validate_ledger(result,calibration)
    return result

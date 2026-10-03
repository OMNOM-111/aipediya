"""Fail-closed snapshot validation; no Excel or scientific imports at runtime."""
import copy
import hashlib
import json
import math
from pathlib import Path

CONFIG=Path(__file__).resolve().parents[2]/'data/rating/v1.0'

def content_hash(snapshot):
    payload=copy.deepcopy(snapshot)
    for key in ('created_at','snapshot_id','content_sha256'):payload['snapshot'].pop(key,None)
    for record in payload.get('models',[]):record.pop('rating_snapshot_id',None)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def check_frozen(config=CONFIG):
    manifest=json.loads((config/'frozen-manifest.json').read_text(encoding='utf-8'))
    errors=[]
    for name,sha in manifest.items():
        if hashlib.sha256((config/name).read_bytes()).hexdigest()!=sha:errors.append('Frozen artifact changed: '+name)
    return errors

def params_hash(config=CONFIG):
    from .ledger import merged_calibration,digest
    load=lambda name:json.loads((config/name).read_text(encoding='utf-8'))
    ledger=load('rating_item_ledger.json')
    calibration=merged_calibration(load('calibration_v1.0.json'),ledger)
    calibration.pop('reference_theta',None)
    base=digest(dict(methodology=load('methodology_v1.0.json'),mappings=load('mappings_v1.0.json'),
                       calibration=calibration,registry=load('context_registry_v1.0.json'),item_ledger=ledger))
    if (config/'owner_estimation_priors.json').exists():return digest({'base':base,'estimation_priors':load('owner_estimation_priors.json')})
    return base

def check_snapshot(snapshot):
    errors=[]; meta=snapshot.get('snapshot',{}); models=snapshot.get('models',[])
    def require(ok,message):
        if not ok:errors.append(message)
    require(meta.get('schema_version')=='aipediya-rating-snapshot/1','Snapshot schema version')
    require(meta.get('content_sha256')==content_hash(snapshot),'Snapshot content hash')
    require(meta.get('n_draws') in (6000,12000),'Draw count')
    require(meta.get('methodology_version')=='AIpediya Rating v1.0','Methodology version')
    ids=[m['model_id'] for m in models]; require(ids==sorted(set(ids)),'Model IDs must be unique and sorted')
    if meta.get('estimate_policy'):
        require(meta.get('published_model_ids')==ids,'Published Model coverage mismatch')
        for m in models:
            require(bool(m.get('primary_rating_context')),m['model_id']+': missing primary context')
            require(isinstance(m.get('aipediya_rating'),(int,float)) and math.isfinite(m['aipediya_rating']) and 0<=m['aipediya_rating']<=100,m['model_id']+': numeric Rating')
            require(m.get('rating_state') in ('verified','partial','estimated'),m['model_id']+': rating state')
            expected_state='estimated' if m.get('missing_estimate_inputs') else ('partial' if m.get('missing_enhancers') else 'verified')
            require(m.get('rating_state')==expected_state,m['model_id']+': confidence state contradicts evidence gaps')
            require(m.get('rating_snapshot_id')==meta.get('snapshot_id'),m['model_id']+': snapshot ID')
            require(m.get('primary_rating_context')=='LLM.OVERALL' or m.get('public_context_rank') is None,m['model_id']+': cross-context rank')
        numeric_counts={k:sum(m.get('rating_state')==k for m in models) for k in ('verified','partial','estimated')}
        numeric_counts.update(total=len(models),numeric=len(models),missing_independent=sum('independent' in m.get('missing_estimate_inputs',[]) for m in models),
                              missing_price=sum('price' in m.get('missing_estimate_inputs',[]) for m in models),missing_resource=sum('resource' in m.get('missing_estimate_inputs',[]) for m in models))
        require(meta.get('numeric_counts')==numeric_counts,'Numeric rating counts mismatch')
    for m in models:
        label=m['model_id']+': '
        require(m.get('status') in ('Rated','Provisional','NR'),label+'status')
        if m['status']!='Rated':
            require(all(m.get(k) is None for k in ('overall_rank','overall_cons','overall_central','overall_min','overall_max','P_no1')),label+'non-Rated numerical rank/Overall')
            continue
        required=('theta','sd_stat','sd_support','sd_total','Q_cons','Q_central','P_no1','P_no1_mcse','P_in_frontier',
                  'rating_coverage_pct','evidence','score_type','no1_eligible','overall_rank','overall_cons','overall_central','overall_min','overall_max')
        missing=[key for key in required if key not in m]
        require(not missing,label+'missing required fields: '+','.join(missing))
        if missing:continue
        for key in ('theta','sd_stat','sd_support','sd_total','Q_cons','Q_central','P_no1','P_no1_mcse','P_in_frontier','rating_coverage_pct'):
            require(isinstance(m.get(key),(int,float)) and math.isfinite(m[key]),label+key)
        require(m['evidence']['fam_non_arena']>=2 and m['evidence']['dom_non_arena']>=2,label+'Evidence Gate')
        require(not ('swebench' in m['evidence'].get('families',[])),label+'forbidden SWE-bench')
        require(m['sd_support']==0,label+'locked support sigma')
        require(m['P_no1_mcse']<=0.01,label+'MCSE')
        require(0<=m['P_no1']<=1 and 0<=m['Q_cons']<=m['Q_central']<=1,label+'probabilities')
        if m['score_type']=='bounded':
            require(m['overall_rank'] is None and m['overall_cons'] is None and m['overall_central'] is None,label+'bounded single rank/score')
            require(m['overall_min'] is not None and m['overall_max'] is not None and m['overall_min']<=m['overall_max'],label+'bounded range')
            require(not m['no1_eligible'] and m['P_no1']==0,label+'bounded eligibility')
        else:require(m['score_type']=='exact' and isinstance(m['overall_rank'],int),label+'exact rank')
    rated=[m for m in models if m['status']=='Rated']; counts=dict(rated=len(rated),exact=sum(m['score_type']=='exact' for m in rated),
        bounded=sum(m['score_type']=='bounded' for m in rated),provisional=sum(m['status']=='Provisional' for m in models),nr=sum(m['status']=='NR' for m in models))
    require(meta.get('counts')==counts,'Counts mismatch')
    badge=meta.get('badge')
    if badge:
        winner=next((m for m in models if m['model_id']==badge['model_id']),{})
        p=winner.get('P_no1',0); se=winner.get('P_no1_mcse',1)
        require(winner.get('no1_eligible') and p>=0.5 and abs(p-0.5)>=2*se,'Badge threshold zone/eligibility')
    require(sum(m.get('P_no1',0) for m in rated)<=1+1e-12,'Winner probability total')
    return errors

"""Snapshot-only runtime presentation. No scientific or Excel imports."""
from functools import lru_cache
import json
from pathlib import Path
from .checks import check_snapshot

DIRECTORY=Path(__file__).resolve().parents[2]/'data/rating/snapshots'
PROFILES=('BALANCED','QUALITY_FIRST','ECONOMY')
STATES={'Ready':'ready','Ready (условно)':'conditional','Beta':'beta','Insufficient Data':'insufficient','Out of scope v1':'out_of_scope'}
ICONS={'verified':'✓','partial':'◐','estimated':'!'}

@lru_cache(maxsize=12)
def _read(path,stamp):return json.loads(Path(path).read_text(encoding='utf-8'))

def read(path):return _read(str(path),path.stat().st_mtime_ns)

@lru_cache(maxsize=8)
def _validated(path,stamp):
    value=_read(path,stamp)
    return None if check_snapshot(value) else value

def snapshot(profile='BALANCED'):
    try:
        index=read(DIRECTORY/'current.json')
        name=index['profiles'][profile if profile in PROFILES else 'BALANCED']
        if Path(name).name!=name:return None
        path=DIRECTORY/name
        return _validated(str(path),path.stat().st_mtime_ns)
    except (OSError,ValueError,KeyError,TypeError):return None

def template_text(code,lang,params=None,section='text'):
    from catalog.context import t
    values=dict(params or {})
    if 'missing' in values:values['missing']=', '.join(t('rating_tpl_missing_fact_labels_'+x,lang) for x in values['missing'])
    if 'fact' in values:values['fact']=t('rating_tpl_missing_fact_labels_'+values['fact'],lang)
    formatted=t(f'rating_tpl_{section}_{code}',lang).format(**values)
    from catalog.i18n import RTL_CODES
    if lang in RTL_CODES:
        import re
        # Keep dates and numeric intervals in their original left-to-right order.
        formatted=re.sub(r'\d+(?:\.\d+)?[–-]\d+(?:\.\d+)?(?:-\d+)?',
                         lambda m:'\u2066'+m.group()+'\u2069',formatted)
    return formatted

def model_rating(model_id,lang,profile='BALANCED'):
    from catalog.context import t
    data=snapshot(profile)
    if not data:return None
    record=next((m for m in data['models'] if m['model_id']==model_id),None)
    if not record:return None
    result=dict(record);result['metadata']=data['snapshot'];result['icon']=ICONS[record['rating_state']]
    result['value']=f"{record['aipediya_rating']:.1f}";result['status_label']=t('rating_'+record['rating_state'],lang)
    result['context_label']=t('rating_context_'+record['primary_rating_context'].replace('.','_').lower(),lang)
    ev=record['numeric_evidence'];considered=[]
    if ev['independent']:considered.append(t('rating_independent_n',lang).format(n=ev['independent']))
    if ev['developer']:considered.append(t('rating_developer_evidence',lang))
    for fact in ('price','resource'):
        if record['component_facts'][fact] is not None:considered.append(t('rating_fact_'+fact,lang))
    if record['capability_basis']!='direct':considered.append(t('rating_basis_'+record['capability_basis'],lang))
    missing=[t('rating_gap_'+key,lang) for key in record['missing_estimate_inputs']+record['missing_enhancers']]
    result['considered']=considered;result['missing']=missing
    result['considered_text']=' · '.join(considered);result['missing_text']=' · '.join(missing) or t('rating_no_gaps',lang)
    result['audit']=[{'icon':'✓','text':text} for text in considered]+[{'icon':'!','text':text} for text in missing]
    for item in record['tooltip']['checklist']:
        if item.get('code')=='price':result['audit'].append({'icon':'✓','text':template_text('price',lang,item.get('params'),section='checklist')})
    tip_keys=[key for key in record['missing_estimate_inputs'] if key not in ('direct_evidence','configuration')]
    if 'aipediya' in record['missing_enhancers']:tip_keys.append('aipediya')
    result['tip_missing_text']=' · '.join(t('rating_gap_'+key,lang) for key in tip_keys) or t('rating_no_gaps',lang)
    result['audit_text']=[]
    for key,source in [('q_pct','capability'),('c_pct','price'),('k_pct','resource')]:result[key]=round(record['component_estimates'][source]*100,1)
    result['interval_label']='–'.join(f'{n:.1f}' for n in record['rating_interval'])
    result['probability_pct']=round(record.get('P_no1',0)*100,2);result['mcse_pct']=round(record.get('P_no1_mcse',0)*100,2)
    result['freshness_rows']=[{'label':t({'price':'rating_price','resource':'rating_resource','config':'rating_configuration','availability':'rating_available','licence':'rating_licence'}[key],lang),
                             'state':t('rating_'+value['state'],lang),'checked':value.get('checked')} for key,value in record['freshness'].items()]
    return result

def summary(lang,profile='BALANCED'):
    from catalog.context import t
    data=snapshot(profile)
    if not data:return None
    meta=data['snapshot'];result=dict(meta)
    import datetime
    days=(datetime.datetime.now(datetime.timezone.utc).date()-datetime.date.fromisoformat(meta['data_cutoff'])).days
    result['snapshot_stale']=days>7
    result['snapshot_age_label']=t('rating_snapshot_old' if days>14 else 'rating_snapshot_stale',lang) if days>7 else ''
    result['status_label']=t('rating_'+STATES[meta['context_status']['status']],lang)
    result['leader_label']=t('rating_tpl_leader_badge' if meta['badge'] else 'rating_tpl_leader_indistinguishable',lang)
    result['candidates']=[dict(c,probability_pct=round(c['P_no1']*100,2),mcse_pct=round(c['mcse']*100,2)) for c in meta['frontier_candidates']]
    path=DIRECTORY/(meta['snapshot_id']+'.contexts.json')
    result['contexts']=[dict(value,status_label=t('rating_'+STATES[value['status']],lang)) for value in read(path).values()]
    return result

def methodology_blocks(lang):
    from catalog.context import t
    from .content import METHOD
    return [(t(f'rating_method_h{i}',lang),t(f'rating_method_p{i}',lang)) for i in range(len(METHOD))]

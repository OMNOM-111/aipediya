"""Offline contextual estimates; frozen reference scoring and facts stay intact.

Priors are an explicit, versioned empirical extension of the owner-frozen scale.
They are built once from permitted reference data, never refitted by daily builds.
"""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from . import evidence as R
from .primary_context import primary_context, EXTRA_CONTEXTS
from .policy import permission_valid, valid

POLICY = 'model-estimates-v1-owner-fix-2026-10-03'
PRIOR_FILE = 'owner_estimation_priors.json'

def all_models(ms):
    return ms['Models'][ms['Models'].Status=='PUBLISHED'].set_index('Record ID')

def observations(ms, models, calibration, contexts):
    """Only permitted, comparable observations. Unlinked LLM items stay excluded."""
    rows=[]
    cutoff=R.data_cutoff(ms)
    for e in ms['Evaluations'].to_dict('records'):
        mid=e['Record ID']
        if mid not in models.index or e['Public']!='YES' or e['Result Kind']=='composite': continue
        extra=json.loads(e['Conditions Extra (JSON)'] or '{}')
        if 'superseded_duplicate_of' in extra or not permission_valid(extra,cutoff): continue
        bench=str(e['Benchmark']); cid=contexts[mid]
        if bench=='SWE-bench Verified': continue
        value=extra.get('normalized_percent')
        if value is None and e['Unit']=='%':value=e['Score']
        kind='dev' if e['Result Kind']=='developer' else ('aipediya' if extra.get('evidence_layer')=='aipediya' and extra.get('reproducible') else 'ind')
        if cid=='LLM.OVERALL':
            if bench not in calibration['items']:continue
            if e['Unit']=='Arena score':
                z=calibration['arena_z'].get(bench)
                if not z:continue
                y=(float(e['Score'])-z['mean'])/z['sd']
            elif value is not None and e['Higher Is Better']!='NO': y=float(logit(np.clip(float(value)/100,.01,.99)))
            else:continue
            item=calibration['items'][bench]
        elif value is not None and e['Higher Is Better']!='NO':
            y=float(logit(np.clip(float(value)/100,.01,.99)));item={'a':1.,'c':0.}
        elif e['Unit']=='Arena score' and bench in calibration.get('context_items',{}):
            z=calibration['context_items'][bench];y=(float(e['Score'])-z['mean'])/z['sd'];item={'a':1.,'c':0.}
        else:continue
        if not np.isfinite(y):continue
        rows.append(dict(m=mid,b=bench,kind=kind,runner=e['Evaluator'] if kind!='dev' else 'developer',
                         y=y,a=item['a'],c=item['c'],checked=e['Checked'],source=e['Source URL']))
    return rows

def reference_facts(ms, models, meth, mapping, contexts):
    """Use explicit units; missing, expired and incompatible facts remain None."""
    import re
    exclude=re.compile(mapping['reference_offer']['exclude_conditions_regex'],re.I)
    cutoff=R.data_cutoff(ms);out={}
    offers=ms['Offers']
    for mid,r in models.iterrows():
        cid=contexts[mid];rows=offers[(offers['Record ID']==mid)&(offers.Active=='YES')]
        rows=rows[~rows['Conditions EN'].fillna('').str.contains(exclude)]
        rows=rows[pd.to_numeric(rows.Amount,errors='coerce').notna()]
        rows=rows.loc[rows.Checked.map(lambda d:valid(d,cutoff,meth['freshness']['price'])).astype(bool)]
        pair=None
        if cid=='LLM.OVERALL':
            for svc in list(dict.fromkeys(list(rows[rows.Primary=='YES'].Service)+list(rows.Service))):
                s=rows[rows.Service==svc]
                for _,g in s.groupby('Conditions EN',sort=False):
                    inp=pd.to_numeric(g[g.Unit=='input'].Amount,errors='coerce').min();o=pd.to_numeric(g[g.Unit=='output'].Amount,errors='coerce').min()
                    if pd.notna(inp) and pd.notna(o):pair=(float((3*inp+o)/4),'LLM blend');break
                if pair:break
                i=s[s.Unit=='input'];o=s[s.Unit=='output']
                if i.Amount.nunique()==1 and o.Amount.nunique()==1:pair=(float((3*float(i.Amount.iloc[0])+float(o.Amount.iloc[0]))/4),'LLM blend');break
        elif len(rows):
            chosen=rows[rows.Primary=='YES']
            if chosen.empty:chosen=rows
            first=chosen.iloc[0];pair=(float(first.Amount),str(first.Unit))
        ctx=pd.to_numeric(r.Context,errors='coerce')
        if pd.isna(ctx) or ctx<=0 or not valid(r['Last Verified'],cutoff,meth['freshness']['resource']):ctx=None
        out[mid]={'price':pair[0] if pair else None,'unit':pair[1] if pair else None,'resource':float(ctx) if ctx is not None else None}
    return out

def distribution(values, floor):
    a=np.asarray(values,float)
    return {'mean':float(np.mean(a)), 'sd':float(max(floor,np.std(a))), 'n':len(a)}

def create_priors(master, reference, config):
    """One-time owner correction calibration. The resulting JSON is then frozen."""
    ms=R.read_master(master);models=all_models(ms);contexts={m:primary_context(r) for m,r in models.iterrows()}
    meth=R.load_json(config/'methodology_v1.0.json');cal=R.load_json(config/'calibration_v1.0.json');mapping=R.load_json(config/'mappings_v1.0.json')
    q_samples=[r['Q_central'] for r in reference['models'] if r['status']=='Rated']
    ref={r['model_id']:r for r in reference['models'] if r['status']=='Rated'}
    # Arena categories outside LLM: freeze the first permitted independent cohort.
    context_items={}
    for bench,g in ms['Evaluations'].groupby('Benchmark',sort=True):
        g=g[(g.Public=='YES')&(g['Result Kind']!='developer')&(g.Unit=='Arena score')&g['Record ID'].isin(models.index)]
        if g.empty or not any(contexts[m]!='LLM.OVERALL' for m in g['Record ID']):continue
        keep=g['Conditions Extra (JSON)'].map(lambda x:permission_valid(json.loads(x or '{}'),R.data_cutoff(ms)) and 'superseded_duplicate_of' not in json.loads(x or '{}'))
        g=g[keep];a=pd.to_numeric(g.Score,errors='coerce').dropna()
        if len(a)>=2 and a.std(ddof=0)>0:context_items[bench]={'mean':float(a.mean()),'sd':float(a.std(ddof=0)),'sources':sorted(set(g['Source URL'].dropna()))}
    cal['context_items']=context_items;obs=observations(ms,models,cal,contexts)
    facts=reference_facts(ms,models,meth,mapping,contexts)
    all_c=[r['C'] for r in ref.values() if r.get('C') is not None];all_k=[r['K'] for r in ref.values() if r.get('K') is not None]
    sigma=meth['engine']['sigma']['independent'];floor=meth['engine']['theta_prior_precision']**-.5
    global_prior={'theta':distribution(logit(np.clip(q_samples,.01,.99)),floor),
        'price':distribution(logit(np.clip(all_c,.01,.99)),sigma),'resource':distribution(logit(np.clip(all_k,.01,.99)),sigma),
        'source_models':sorted(ref)}
    priors={};families={}
    registry=R.load_json(config/'context_registry_v1.0.json')
    context_ids=sorted(set(x['context_id'] for x in registry['contexts'])|set(EXTRA_CONTEXTS))
    for cid in context_ids:
        ids=[m for m in models.index if contexts[m]==cid];direct=[o for o in obs if contexts[o['m']]==cid and o['kind']!='dev']
        vals=[ref[m]['theta'] for m in ids if m in ref] if cid=='LLM.OVERALL' else [o['y'] for o in direct]
        th=distribution(vals,floor) if vals else copy.deepcopy(global_prior['theta'])
        price_values=[facts[m] for m in ids if facts[m]['price'] is not None]
        unit=None;anchors=None;cs=[]
        if cid=='LLM.OVERALL':
            unit='LLM blend';anchors=[meth['price']['LLM']['anchor_low_usd'],meth['price']['LLM']['anchor_high_usd']]
        elif price_values:
            units=[x['unit'] for x in price_values];unit=sorted(set(units),key=lambda x:(-units.count(x),x))[0]
            a=[x['price'] for x in price_values if x['unit']==unit and x['price']>0]
            if len(a)>=2:
                # Fixed 1-2-5 scale anchors prescribed by the base methodology.
                def rounded(x,up):
                    power=10**np.floor(np.log10(x));v=x/power;allowed=[1,2,5,10]
                    return float(power*(min(t for t in allowed if t>=v) if up else max(t for t in allowed if t<=v)))
                lo,hi=np.percentile(a,[5,95]);anchors=[rounded(lo,False),rounded(hi,True)]
                if anchors[0]==anchors[1]:anchors=None
        if anchors:
            cs=[float(np.clip(np.log(anchors[1]/max(x['price'],anchors[0]))/np.log(anchors[1]/anchors[0]),0,1)) for x in price_values if x['unit']==unit]
        ks=[float(np.clip(np.log(facts[m]['resource']/8000)/np.log(1000000/8000),0,1)) for m in ids if facts[m]['resource'] is not None]
        priors[cid]={'theta':th,'capability_basis':'context' if vals else 'global','price':distribution(logit(np.clip(cs,.01,.99)),sigma) if cs else copy.deepcopy(global_prior['price']),
                     'resource':distribution(logit(np.clip(ks,.01,.99)),sigma) if ks else copy.deepcopy(global_prior['resource']),
                     'price_anchors':anchors,'price_unit':unit,'source_models':sorted(set(o['m'] for o in direct)|set(m for m in ids if m in ref)),
                     'resource_metric':'token_context' if cid=='LLM.OVERALL' else ('document_context' if ks else None)}
        for fam in sorted(set(str(models.loc[m,'Family'] or '') for m in ids)):
            if not fam:continue
            anchors_f=[m for m in ids if str(models.loc[m,'Family'] or '')==fam and m in ref]
            ys=[ref[m]['theta'] if cid=='LLM.OVERALL' else float(logit(np.clip(ref[m]['Q_central'],.01,.99))) for m in anchors_f]
            if ys:
                families[cid+'|'+fam]={'mean':float((sum(ys)+th['mean'])/(len(ys)+1)),
                    'sd':float(np.sqrt(th['sd']**2+th['sd']**2/(len(ys)+1))), 'n':len(ys),'source_models':anchors_f}
    return {'policy_version':POLICY,'source_master_sha256':R.sha256_file(master),'data_cutoff':reference['snapshot']['data_cutoff'],
            'source_reference_content_sha256':reference['snapshot']['content_sha256'],'global':global_prior,'contexts':priors,'families':families,
            'context_items':context_items,'extra_contexts':EXTRA_CONTEXTS,'reference_model_ids':sorted(ref)}

def extend_snapshot(master, snap, context_statuses, used, config=None):
    config=Path(config or Path(__file__).resolve().parents[2]/'data/rating/v1.0')
    priors=R.load_json(config/PRIOR_FILE);ms=R.read_master(master);models=all_models(ms)
    contexts={m:primary_context(r) for m,r in models.iterrows()};meth=R.load_json(config/'methodology_v1.0.json');cal=R.load_json(config/'calibration_v1.0.json')
    from .ledger import merged_calibration
    cal=merged_calibration(cal,R.load_json(config/'rating_item_ledger.json'));cal['context_items']=priors['context_items']
    mapping=R.load_json(config/'mappings_v1.0.json');facts=reference_facts(ms,models,meth,mapping,contexts);obs=observations(ms,models,cal,contexts)
    old={r['model_id']:r for r in snap['models']};rows=[];profile=snap['snapshot']['profile'];w=np.asarray(meth['overall']['profiles'][profile]);w=w/w.sum()
    draws=snap['snapshot']['n_draws'];cutoff=snap['snapshot']['data_cutoff'];sigma=meth['engine']['sigma'];z=meth['engine']['conservative_z']
    for mid,r in models.sort_index().iterrows():
        rec=copy.deepcopy(old.get(mid,{'model_id':mid,'name':r.Name,'status':'NR','score_type':'NR','profile':profile,'segment':'historical',
                                     'evidence':{},'freshness':{},'tooltip':{'checklist':[],'text':[]}}))
        cid=contexts[mid];prior=priors['contexts'][cid];rec['primary_rating_context']=cid;rec['context_id']=cid
        family=priors['families'].get(cid+'|'+str(r.Family or ''));mu=(family or prior['theta'])['mean'];sd=(family or prior['theta'])['sd']
        basis='family' if family else prior['capability_basis'];group=[o for o in obs if o['m']==mid]
        independent=[o for o in group if o['kind']!='dev'];developers=[o for o in group if o['kind']=='dev']
        preserved=rec['status']=='Rated' and cid=='LLM.OVERALL'
        if preserved:
            mu=rec['theta'];sd=rec['sd_total'];basis='direct'
        else:
            num=mu/sd**2;den=1/sd**2
            if cid=='LLM.OVERALL':
                data=used[used.m==mid]
                if len(data):
                    precision=(data.weff*data.a**2/data.sig**2).sum();num+=(data.weff*data.a*(data.y-data.c)/data.sig**2).sum();den+=precision;basis='direct' if independent else 'developer'
                elif group:
                    for o in group:
                        variance=sigma['developer' if o['kind']=='dev' else 'independent']**2
                        num+=o['a']*(o['y']-o['c'])/variance;den+=o['a']**2/variance
                    basis='developer' if not independent else 'direct'
            elif group:
                # Family and runner caps; developer precision <=20% of nondeveloper,
                # or one weak observation with no independent evidence.
                counts={k:sum(o['runner']==k for o in group) for k in set(o['runner'] for o in group)}
                devscale=min(1.,(.2/.8)*len(independent)/max(1,len(developers))) if independent else 1/max(1,len(developers))
                for o in group:
                    weight=min(1.,meth['caps']['runner_default']/counts[o['runner']]);weight*=devscale if o['kind']=='dev' else 1.
                    variance=(sigma['developer'] if o['kind']=='dev' else sigma['independent']*(sigma['aipediya_multiplier'] if o['kind']=='aipediya' else 1))**2
                    num+=weight*o['a']*(o['y']-o['c'])/variance;den+=weight*o['a']**2/variance
                basis='direct' if independent else 'developer'
            mu=float(num/den);sd=float(den**-.5)
        seed=int(hashlib.sha256((str(snap['snapshot']['rng_seed'])+'|'+mid).encode()).hexdigest()[:16],16)
        rng=np.random.default_rng(seed);theta=rng.normal(mu,sd,draws)
        def q(t):
            if cid=='LLM.OVERALL':return expit(np.asarray(t)[...,None]*np.array([b['a'] for b in cal['q_basket']])+np.array([b['c'] for b in cal['q_basket']])).mean(-1)
            return expit(t)
        qcentral=float(q(mu));qd=q(theta);fact=facts[mid]
        C=rec.get('C') if preserved else None;K=rec.get('K') if preserved else None
        if not preserved:
            a=prior['price_anchors']
            if a and fact['price'] is not None and fact['unit']==prior['price_unit']:
                C=float(np.clip(np.log(a[1]/max(fact['price'],a[0]))/np.log(a[1]/a[0]),0,1))
            if prior['resource_metric'] and fact['resource'] is not None:K=float(np.clip(np.log(fact['resource']/8000)/np.log(1000000/8000),0,1))
        cp=prior['price'];kp=prior['resource'];cd=np.full(draws,C) if C is not None else expit(rng.normal(cp['mean'],cp['sd'],draws))
        kd=np.full(draws,K) if K is not None else expit(rng.normal(kp['mean'],kp['sd'],draws))
        cc=float(C if C is not None else expit(cp['mean']));kk=float(K if K is not None else expit(kp['mean']))
        scores=100*qd**w[0]*(.2+.8*cd)**w[1]*(.3+.7*kd)**w[2]
        central=float(100*qcentral**w[0]*(.2+.8*cc)**w[1]*(.3+.7*kk)**w[2]);estimate=float(np.percentile(scores,meth['overall']['conservative_percentile']))
        low,high=map(float,np.percentile(scores,[10,90]))
        if preserved and rec['score_type']=='exact':estimate=rec['overall_cons'];central=rec['overall_central'];low=estimate
        missing=[]
        non_arena=[o for o in independent if o['b'] not in cal.get('arena_z',{}) and o['b'] not in cal.get('context_items',{})]
        if not non_arena:missing.append('independent')
        if C is None:missing.append('price')
        if K is None:missing.append('resource')
        if basis not in ('direct',) or (not preserved and len(independent)<2):missing.append('direct_evidence')
        enhancers=[]
        if not any(o['kind']=='aipediya' for o in group):enhancers.append('aipediya')
        if len(set(o['runner'] for o in non_arena))<2:enhancers.append('runners')
        if rec.get('configuration') is None:rec['configuration']='context prior' if not group else 'permitted evidence'
        if preserved and any(x.get('fact')=='config_match' for x in rec.get('missing_critical',[])):missing.append('configuration')
        state='estimated' if missing else ('partial' if enhancers else 'verified')
        cw=meth['coverage_weights'];coverage=float(cw['A_gate']*(bool(independent))+cw['B_price']*(C is not None)+cw['B_resource']*(K is not None)+cw['B_config']*(bool(group))+cw['C_runners']*(len(set(o['runner'] for o in independent))>=2)+cw['C_aipediya']*(any(o['kind']=='aipediya' for o in group))+cw['C_breadth']*(len(set(o['b'] for o in independent))>=5))
        if preserved:coverage=rec['rating_coverage_pct']
        precision=rec.get('precision_grade') if preserved else ('B' if sd<=meth['grades']['precision']['B']['sigma_stat_max'] and len(non_arena)>=meth['grades']['precision']['B']['fam_non_arena_min'] else 'C')
        support=rec.get('support_grade') if preserved else ('B' if len(set(o['runner'] for o in non_arena))>=2 else 'C')
        rec.update(aipediya_rating=estimate,rating_central=central,rating_interval=[low,high],rating_state=state,
            rating_snapshot_id=None,capability_basis=basis,prior_source_models=(family or prior).get('source_models',[]),
            posterior={'theta':mu,'sd':sd},component_estimates={'capability':qcentral,'price':cc,'resource':kk},
            component_facts={'price':C,'resource':K},missing_estimate_inputs=missing,missing_enhancers=enhancers,
            precision_grade=precision or 'C',support_grade=support or 'C',rating_coverage_pct=coverage,
            numeric_evidence={'independent':len(non_arena),'developer':len(developers),'aipediya':sum(o['kind']=='aipediya' for o in group)},
            public_context_rank=rec.get('overall_rank') if preserved else None)
        rows.append(rec)
    # Rank is restricted to one context and a proven reference cohort. No cross-type #N.
    context_statuses.update(copy.deepcopy(priors['extra_contexts']))
    snap['models']=rows;meta=snap['snapshot'];meta['estimate_policy']=POLICY;meta['estimate_priors_sha256']=R.canon_hash(priors)
    meta['params_hash']=R.canon_hash({'base':meta['params_hash'],'estimation_priors':priors})
    meta['counts']['nr']=sum(r['status']=='NR' for r in rows)
    meta['numeric_counts']={k:sum(r['rating_state']==k for r in rows) for k in ('verified','partial','estimated')}
    meta['numeric_counts'].update(total=len(rows),numeric=len(rows),missing_independent=sum('independent' in r['missing_estimate_inputs'] for r in rows),
        missing_price=sum('price' in r['missing_estimate_inputs'] for r in rows),missing_resource=sum('resource' in r['missing_estimate_inputs'] for r in rows))
    meta['published_model_ids']=sorted(models.index)
    for k in ('snapshot_id','content_sha256'):meta.pop(k,None)
    # IDs are carried in every record but excluded while generating their own ID/hash.
    from .checks import content_hash
    h=content_hash(snap);sid=f"MODELS@{profile}-v1.0-{cutoff}-{h[:12]}"
    meta['snapshot_id']=sid
    for r in rows:r['rating_snapshot_id']=sid
    meta['content_sha256']=content_hash(snap)
    return snap

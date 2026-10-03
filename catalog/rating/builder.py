"""Offline v1.0 snapshot builder adapted from the owner-accepted Reference Pack.

All evidence dates use data_cutoff; only created_at uses the clock.
Do not import from views: pandas/numpy/Excel are build-time dependencies.
"""
import datetime
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from . import evidence as R

def build_reference_snapshot(master, profile='BALANCED', seed=None, config=None, ledger=None):
    config = Path(config or Path(__file__).resolve().parents[2]/'data/rating/v1.0')
    ledger = ledger if ledger is not None else R.load_json(config/'rating_item_ledger.json')
    METH=R.load_json(f'{config}/methodology_v1.0.json'); MAP=R.load_json(f'{config}/mappings_v1.0.json'); CAL=R.load_json(f'{config}/calibration_v1.0.json')
    REG=R.load_json(f'{config}/context_registry_v1.0.json'); TPL=R.load_json(f'{config}/tooltip_templates_v1.0.json')
    from .ledger import merged_calibration
    CAL=merged_calibration(CAL,ledger)
    mp=R.Mapper(MAP)
    for entry in ledger['entries']:
        mp.fam.insert(0,(re.compile('^'+re.escape(entry['benchmark'])+'$'),entry['family'],entry['domain']))
    SEED=seed if seed is not None else METH['frontier']['monte_carlo']['seed']
    MS=R.read_master(master); CUT=R.data_cutoff(MS); P=R.model_table(MS); RAW=R.evidence_rows(MS,P,mp); SEG=R.segment_of(P,RAW,MAP)
    L,choice,_=R.prepare(RAW,SEG,mp,METH,CAL['arena_z'],linked=CAL['items'])
    W=R.weights(L,METH); FT,_,D=R.fit(W,METH,items=CAL['items'])
    E=METH['engine']; Z=E['conservative_z']
    # ---------------- evidence summary (по строкам, реально участвующим в расчёте)
    ind=D[D.kind.isin(['ind','aipediya'])]; ar=D[D.kind=='arena']; allind=D[D.kind!='dev']
    EV=pd.DataFrame({'fam_non_arena':ind.groupby('m').fam.nunique(),'dom_non_arena':ind[ind.dom!='unclassified'].groupby('m').dom.nunique(),
        'arena_subcats':ar.groupby('m').fam.nunique(),'independent_orgs':allind.groupby('m').runner.nunique(),
        'non_arena_runners':ind[ind.kind=='ind'].groupby('m').runner.nunique(),'aipediya_tests':ind[ind.kind=='aipediya'].groupby('m').b.nunique(),
        'channels':ind.groupby('m').channel.nunique()})
    devn=RAW[RAW.kind=='dev'].groupby('m').b.nunique()
    ids=sorted(P.index)
    S=pd.DataFrame(index=ids); S.index.name='id'
    S['name']=P.Name; S['developer']=P.Developer; S['segment']=pd.Series(SEG)
    S=S.join(EV).join(FT)
    for c in EV.columns: S[c]=S[c].fillna(0).astype(int)
    S['dev_tests']=devn.reindex(S.index).fillna(0).astype(int); S['config']=pd.Series(choice)
    G=METH['gates']['LLM.OVERALL']['model']
    def status(r):
        if r.segment!='llm': return 'NR'
        if r.fam_non_arena==0: return 'Provisional' if (r.dev_tests>0 or r.arena_subcats>0) else 'NR'
        return 'Rated' if (r.fam_non_arena>=G['fam_non_arena_min'] and r.dom_non_arena>=G['dom_non_arena_min']) else 'Provisional'
    S['status']=S.apply(status,axis=1)
    # ---------------- ранние доказательства (от data_cutoff)
    EE=E['early_evidence']; li=L[L.kind.isin(['ind','aipediya'])]; first=li.groupby('m').meas.min(); span=(li.groupby('m').meas.max()-first).dt.days
    early=((CUT-first).dt.days<EE['max_age_days'])&(span<=EE['single_batch_span_days'])
    S['early_evidence']=early.reindex(S.index).eq(True)
    S['sd_stat']=np.where(S.early_evidence,S.sd*EE['k_new'],S.sd)
    prec=(ind.weff*ind.a**2/ind.sig**2); sh=prec.groupby([ind.m,ind.runner]).sum(); sh=sh/sh.groupby(level=0).transform('sum'); hhi=(sh**2).groupby(level=0).sum()
    S['sd_support']=E['sigma_runner']*np.sqrt(hhi.reindex(S.index).fillna(1.0))
    S['sd_total']=np.sqrt(S.sd_stat**2+S.sd_support**2); S['theta_cons']=S.theta-Z*S.sd_total
    GR=METH['grades']['precision']
    def pgrade(r):
        if r.status!='Rated': return None
        a=GR['A']; b=GR['B']
        if r.fam_non_arena>=a['fam_non_arena_min'] and r.dom_non_arena>=a['dom_non_arena_min'] and r.independent_orgs>=a['independent_orgs_min'] and r.sd_stat<=a['sigma_stat_max']: return 'A'
        if r.fam_non_arena>=b['fam_non_arena_min'] and r.dom_non_arena>=b['dom_non_arena_min'] and r.sd_stat<=b['sigma_stat_max']: return 'B'
        return 'C'
    S['precision_grade']=S.apply(pgrade,axis=1)
    paths=S.non_arena_runners+S.aipediya_tests
    S['support_paths']=paths; S['support_grade']=np.where(S.status!='Rated',None,np.select([paths>=3,paths==2],['A','B'],'C'))
    for c in ['theta','sd','sd_stat','sd_support','sd_total','theta_cons']: S.loc[S.status!='Rated',c]=np.nan
    # ---------------- эталонная цена
    RO=MAP['reference_offer']; EXCL=re.compile(RO['exclude_conditions_regex'],re.I)
    O=MS['Offers']; O=O[(O['Record Type']=='model')&(O.Active=='YES')&O.Unit.isin(['input','output'])].copy(); O['amt']=pd.to_numeric(O.Amount,errors='coerce')
    def ref_offer(m):
        x=O[(O['Record ID']==m)&~O['Conditions EN'].fillna('').str.contains(EXCL)]
        if x.empty: return None
        for svc in list(dict.fromkeys(list(x[x.Primary=='YES'].Service)+list(x.Service))):
            y=x[x.Service==svc]
            for cond,g in y.groupby('Conditions EN',sort=False):
                i=g[g.Unit=='input'].amt.min(); o=g[g.Unit=='output'].amt.min()
                if pd.notna(i) and pd.notna(o): return dict(service=svc,tier=cond,input=float(i),output=float(o),checked=str(pd.to_datetime(g.Checked,errors='coerce').min().date()))
            yi=y[y.Unit=='input']; yo=y[y.Unit=='output']
            if yi.amt.nunique()==1 and yo.amt.nunique()==1:
                return dict(service=svc,tier=f"{yi['Conditions EN'].iloc[0]} | {yo['Conditions EN'].iloc[0]}",input=float(yi.amt.iloc[0]),output=float(yo.amt.iloc[0]),
                            checked=str(pd.to_datetime(pd.concat([yi.Checked,yo.Checked]),errors='coerce').min().date()))
        return None
    PR=METH['price']['LLM']; wl=PR['workload_default']
    S['price_ref']=[ref_offer(m) for m in S.index]
    S['blend']=[ (wl['input']*p['input']+wl['output']*p['output'])/(wl['input']+wl['output']) if p else np.nan for p in S.price_ref]
    S['ctx']=pd.to_numeric(P.Context,errors='coerce').reindex(S.index)
    S['ctx_checked']=pd.to_datetime(P['Last Verified'],errors='coerce').reindex(S.index)
    S['config_match']=S.blend.notna()   # tariff configuration-specific facts may invalidate this below
    from .policy import valid
    cfg_checked=L[L.kind.isin(['ind','aipediya'])].groupby('m').checked.max()
    access_checked=pd.to_datetime(MS['Access'].Checked,errors='coerce').groupby(MS['Access']['Record ID']).max()
    for model_id in S.index:
        pref=S.at[model_id,'price_ref']
        if pref and (not valid(pref['checked'],CUT,METH['freshness']['price']) or
                     (model_id in access_checked and not valid(access_checked[model_id],CUT,METH['freshness']['availability']))):
            S.at[model_id,'blend']=np.nan
            S.at[model_id,'config_match']=False
        if pd.notna(S.at[model_id,'ctx']) and not valid(S.at[model_id,'ctx_checked'],CUT,METH['freshness']['resource']):
            S.at[model_id,'ctx']=np.nan
        if model_id in cfg_checked and not valid(cfg_checked[model_id],CUT,METH['freshness']['config']):
            S.at[model_id,'config_match']=False
    def Cf(bl):
        bl=np.asarray(bl,float); safe=np.maximum(bl,PR['anchor_low_usd'])   # $0 стандартный тариф -> C = 1 без log(0)
        return np.clip((np.log(PR['anchor_high_usd'])-np.log(safe))/(np.log(PR['anchor_high_usd'])-np.log(PR['anchor_low_usd'])),0,1)
    RS=METH['resource']['LLM']
    def Kf(c): return np.clip(np.log(c/RS['ctx_low'])/np.log(RS['ctx_high']/RS['ctx_low']),0,1)
    BK=CAL['q_basket']; ba=np.array([x['a'] for x in BK]); bc=np.array([x['c'] for x in BK])
    def Q(th): th=np.asarray(th,float); return expit(th[...,None]*ba+bc).mean(-1)
    wq,wc,wk=METH['overall']['profiles'][profile]
    def OV(q,c,k,w=(wq,wc,wk)):
        s=sum(w); return 100*q**(w[0]/s)*(0.2+0.8*c)**(w[1]/s)*(0.3+0.7*k)**(w[2]/s)
    # ---------------- Monte Carlo (порядок генерации зафиксирован)
    U=S[S.status=='Rated'].copy()
    MC=METH['frontier']['monte_carlo']; DELTA=METH['frontier']['delta_theta']; pct=METH['overall']['conservative_percentile']
    known_c=U.blend.notna().values; known_k=U.ctx.notna().values
    C=np.where(known_c,Cf(U.blend.fillna(1).values),np.nan); K=np.where(known_k,Kf(U.ctx.fillna(1).values),np.nan)
    gradeAB=U.precision_grade.isin(['A','B']).values
    NS=METH['frontier']['no1_static']
    static=gradeAB&known_c&known_k&U.config_match.values&(U.independent_orgs.values>=NS['min_independent_orgs'])
    def run_mc(n):
        rng=np.random.default_rng(SEED)
        TH=U.theta.values+U.sd_total.values*rng.standard_normal((n,len(U)))
        F=rng.uniform(*MC['weight_jitter'],size=(n,3))
        QD=Q(TH)
        if not len(U):
            return TH,QD,np.zeros((n,0),dtype=bool),np.zeros(0),0.0
        lead=TH[:,gradeAB].max(1,keepdims=True) if gradeAB.any() else np.full((n,1),np.inf)
        FR=(TH>=lead-DELTA)&gradeAB
        s=wq*F[:,0]+wc*F[:,1]+wk*F[:,2]
        Oj=100*QD**((wq*F[:,0]/s)[:,None])*(0.2+0.8*np.nan_to_num(C))[None,:]**((wc*F[:,1]/s)[:,None])*(0.3+0.7*np.nan_to_num(K))[None,:]**((wk*F[:,2]/s)[:,None])
        cand=FR&static[None,:]; Oj=np.where(cand,Oj,-1); has=cand.any(1)
        win=Oj.argmax(1); cnt=np.bincount(win[has],minlength=len(U))
        return TH,QD,FR,cnt/n,has.mean()
    from .monte_carlo import resolve_threshold,badge_passes
    BR=METH['frontier']['badge_borderline_rule']
    (TH,QD,FR,PN,P_has),ndraws=resolve_threshold(run_mc,MC['draws'],BR['max_draws'],BR['band_mcse_multiplier'])
    mcse=lambda p,n:np.sqrt(p*(1-p)/n)
    U['P_no1']=PN; U['P_no1_mcse']=mcse(PN,ndraws); U['P_in_frontier']=FR.mean(0)
    lead=TH[:,gradeAB].max(1,keepdims=True) if gradeAB.any() else (TH.max(1,keepdims=True) if len(U) else np.zeros((ndraws,1)))
    U['tier']=np.median(np.floor((lead-TH)/DELTA).clip(0)+1,axis=0).astype(int)
    U['Q_central']=Q(U.theta.values); U['Q_cons']=Q(U.theta_cons.values); U['C']=C; U['K']=K
    exact=known_c&known_k&U.config_match.values
    U['score_type']=np.where(exact,'exact','bounded')
    U['overall_central']=np.where(exact,OV(U.Q_central.values,np.nan_to_num(C),np.nan_to_num(K)),np.nan)
    U['overall_cons']=np.where(exact,np.percentile(OV(QD,np.nan_to_num(C),np.nan_to_num(K)),pct,axis=0),np.nan)
    U['overall_min']=np.where(~exact,np.percentile(OV(QD,np.where(known_c,C,0),np.where(known_k,K,0)),pct,axis=0),np.nan)
    U['overall_max']=np.where(~exact,np.percentile(OV(QD,np.where(known_c,C,1),np.where(known_k,K,1)),pct,axis=0),np.nan)
    EX=U[U.score_type=='exact'].sort_values(['tier','overall_cons'],ascending=[True,False])
    U['overall_rank']=pd.Series(range(1,len(EX)+1),index=EX.index)
    def above(t,v,pool_t,pool_v): return int(((pool_t<t)|((pool_t==t)&(pool_v>v))).sum())
    BD=U[U.score_type=='bounded']
    def rrange(m,r):
        if r.score_type=='exact': return str(int(r.overall_rank))
        o=BD.drop(index=m)
        best=1+above(r.tier,r.overall_max,EX.tier.values,EX.overall_cons.values)+above(r.tier,r.overall_max,o.tier.values,o.overall_min.values)
        worst=1+above(r.tier,r.overall_min,EX.tier.values,EX.overall_cons.values)+above(r.tier,r.overall_min,o.tier.values,o.overall_max.values)
        return f'{best}–{worst}' if best!=worst else str(best)
    U['overall_rank_range']=[rrange(m,r) for m,r in U.iterrows()]
    top=U.sort_values('P_no1',ascending=False)
    badge=top.index[0] if len(top) and badge_passes(top.P_no1.iloc[0],top.P_no1_mcse.iloc[0]) else None
    # ---------------- №1 причины, свежесть, пропуски, coverage, tooltip
    FRS=METH['freshness']
    def age(d): return None if d is None or pd.isna(d) else int((CUT-pd.Timestamp(d)).days)
    def fstate(days,k):
        if days is None: return 'unknown'
        t=FRS[k]; return 'fresh' if days<=t['fresh'] else ('stale' if days<=t['stale'] else 'expired')
    AC=MS['Access']; acc=pd.to_datetime(AC.Checked,errors='coerce').groupby(AC['Record ID']).max()
    cfgchk=pd.to_datetime(L[L.kind=='ind'].checked,errors='coerce').groupby(L[L.kind=='ind'].m).max()
    recs=[]
    for m,r in S.iterrows():
        rec={'model_id':m,'name':r['name'],'context_id':'LLM.OVERALL','profile':profile,'segment':r.segment,'status':r.status,
             'score_type':'NR' if r.status=='NR' else ('provisional' if r.status=='Provisional' else None),'configuration':r.config if isinstance(r.config,str) else None}
        pref=r.price_ref
        fr={'price':{'state':fstate(age(pref['checked']) if pref else None,'price'),'checked':pref['checked'] if pref else None},
            'resource':{'state':fstate(age(r.ctx_checked) if pd.notna(r.ctx) else None,'resource'),'checked':str(r.ctx_checked.date()) if pd.notna(r.ctx_checked) and pd.notna(r.ctx) else None},
            'config':{'state':fstate(age(cfgchk.get(m)),'config'),'checked':str(cfgchk[m].date()) if m in cfgchk else None},
            'availability':{'state':fstate(age(acc.get(m)),'availability'),'checked':str(acc[m].date()) if m in acc and pd.notna(acc[m]) else None},
            'licence':{'state':'fresh','basis':'open licences of rating-eligible sources'}}
        rec['freshness']=fr
        crit=[]; conf=[]; info=[]
        if r.status!='Rated':
            if r.segment!='llm': crit.append({'fact':'context_not_applicable','state':'n/a','effect':'NR'})
            elif r.fam_non_arena==0: crit.append({'fact':'independent_non_arena_evidence','state':'unknown','effect':r.status})
            else: crit.append({'fact':'evidence_gate','state':'unconfirmed','effect':'Provisional','params':{'families':int(r.fam_non_arena),'domains':int(r.dom_non_arena),'need_families':G['fam_non_arena_min'],'need_domains':G['dom_non_arena_min']}})
        else:
            for fact,ok,st in [('price',pd.notna(r.blend),fr['price']['state']),('resource',pd.notna(r.ctx),fr['resource']['state']),('config_match',bool(r.config_match),fr['config']['state'])]:
                if not ok: crit.append({'fact':fact,'state':'unconfirmed' if st=='expired' or fact=='config_match' else 'unknown','effect':'bounded'})
                elif st=='expired': crit.append({'fact':fact,'state':'unconfirmed','since':'expired','effect':'bounded'})
                elif st=='stale': conf.append({'fact':fact,'state':'stale','effect':'warning'})
            if r.non_arena_runners<2: conf.append({'fact':'second_independent_runner','state':'unknown','effect':'support_grade'})
            if r.aipediya_tests==0: conf.append({'fact':'aipediya_reproducible_test','state':'unknown','systemic':True,'effect':'support_grade'})
            if not (r.fam_non_arena>=5 and r.dom_non_arena>=4): conf.append({'fact':'breadth','state':'unknown','effect':'already_in_sigma_stat'})
        if r.dev_tests==0: info.append({'fact':'developer_reported_results','state':'unknown','effect':'none'})
        if pd.isna(P.loc[m,'Exact Release Date']): info.append({'fact':'exact_release_date','state':'unknown','effect':'none'})
        rec.update(missing_critical=crit,missing_confidence=conf,missing_informational=info)
        if r.status=='Rated':
            u=U.loc[m]; cw=METH['coverage_weights']
            cov=cw['A_gate']+cw['B_price']*pd.notna(r.blend)+cw['B_resource']*pd.notna(r.ctx)+cw['B_config']*bool(r.config_match)+cw['C_runners']*(r.non_arena_runners>=2)+cw['C_aipediya']*(r.aipediya_tests>0)+cw['C_breadth']*(r.fam_non_arena>=5 and r.dom_non_arena>=4)
            rec['score_type']=u.score_type
            if any(x['effect']=='bounded' for x in crit): rec['score_type']='bounded'
            ui='material' if crit else ('minor' if conf else 'complete')
            rec.update(ui_state=ui,price_ref=pref,blend_usd_per_1m=None if pd.isna(r.blend) else round(float(r.blend),6),resource={'ctx':None if pd.isna(r.ctx) else int(r.ctx)},
              theta=float(r.theta),sd_stat=float(r.sd_stat),sd_support=float(r.sd_support),sd_total=float(r.sd_total),misfit=float(r.misfit),early_evidence=bool(r.early_evidence),theta_cons=float(r.theta_cons),
              Q_central=float(u.Q_central),Q_cons=float(u.Q_cons),C=None if pd.isna(u.C) else float(u.C),K=None if pd.isna(u.K) else float(u.K),
              overall_central=None if pd.isna(u.overall_central) else float(u.overall_central),overall_cons=None if pd.isna(u.overall_cons) else float(u.overall_cons),
              overall_min=None if pd.isna(u.overall_min) else float(u.overall_min),overall_max=None if pd.isna(u.overall_max) else float(u.overall_max),
              overall_rank=None if pd.isna(u.overall_rank) else int(u.overall_rank),overall_rank_range=u.overall_rank_range,tier=int(u.tier),
              P_no1=float(u.P_no1),P_no1_mcse=float(u.P_no1_mcse),P_in_frontier=float(u.P_in_frontier),
              precision_grade=r.precision_grade,support_grade=r.support_grade,rating_coverage_pct=float(cov))
            reasons=[]
            if r.precision_grade not in NS['precision_grades']: reasons.append({'code':'precision_grade','params':{'grade':r.precision_grade}})
            if r.independent_orgs<NS['min_independent_orgs']: reasons.append({'code':'independent_orgs','params':{'n':int(r.independent_orgs)}})
            for x in crit: reasons.append({'code':'unconfirmed_'+x['fact']})
            if u.P_in_frontier<0.5 and not reasons: reasons.append({'code':'outside_frontier_mostly','params':{'P_in_frontier':round(float(u.P_in_frontier),3)}})
            rec['no1_eligible']=bool(static[list(U.index).index(m)]); rec['no1_reasons']=reasons
        else:
            rec['ui_state']='provisional'
        meta_items=[r.dev_tests>0,pd.notna(P.loc[m,'Exact Release Date'])]; rec['catalog_metadata_pct']=50.0*sum(meta_items)
        rec['evidence']={k:int(r[k]) for k in ['fam_non_arena','dom_non_arena','arena_subcats','independent_orgs','non_arena_runners','channels','dev_tests','aipediya_tests']}
        # tooltip: структурированные коды; текст рендерит i18n по config/tooltip_templates_v1.0.json
        t=[]
        if r.status=='Rated':
            t.append({'icon':'ok','code':'evidence','params':{'families':int(r.fam_non_arena),'domains':int(r.dom_non_arena)}})
            t.append({'icon':'ok' if r.non_arena_runners>=2 else 'gap','code':'runners','params':{'n':int(r.non_arena_runners)}})
            t.append({'icon':'gap','code':'aipediya_test_absent_systemic'})
            t.append({'icon':{'fresh':'ok','stale':'stale'}.get(fr['price']['state'],'gap') if pref else 'gap','code':'price' if pref else 'price_unknown','params':({'input':pref['input'],'output':pref['output'],'service':pref['service'],'checked':pref['checked']} if pref else {})})
            t.append({'icon':{'fresh':'ok','stale':'stale'}.get(fr['resource']['state'],'gap') if pd.notna(r.ctx) else 'gap','code':'context' if pd.notna(r.ctx) else 'context_unknown','params':({'ctx':int(r.ctx)} if pd.notna(r.ctx) else {})})
            t.append({'icon':'ok' if r.config_match else 'gap','code':'config_match' if r.config_match else 'config_unconfirmed','params':{'config':r.config}})
            t.append({'icon':'info','code':'grades','params':{'precision':r.precision_grade,'support':r.support_grade}})
            text=[{'code':'text_no_aipediya_test','params':{'dq_pp':round(100*(Q(r.theta-Z*r.sd_stat)-Q(r.theta_cons)),2)}}]
            if rec['score_type']=='bounded': text.append({'code':'text_bounded','params':{'min':round(rec['overall_min'],1),'max':round(rec['overall_max'],1),'range':rec['overall_rank_range'],'missing':[x['fact'] for x in crit]}})
            if rec.get('overall_rank') and U.loc[m,'tier']>1: text.append({'code':'text_tier_order'})
            if r.early_evidence: text.append({'code':'text_early_evidence','params':{'k_new':EE['k_new']}})
            for x in conf:
                if x['state']=='stale': text.append({'code':'text_stale','params':{'fact':x['fact'],'since':fr[{'price':'price','resource':'resource','config_match':'config'}[x['fact']]]['checked']}})
            if not rec['no1_eligible']: text.append({'code':'text_not_eligible','params':{'reasons':[x['code'] for x in reasons]}})
        else:
            t.append({'icon':'none','code':'provisional' if r.status=='Provisional' else 'nr'}); text=[{'code':'text_'+('provisional' if r.status=='Provisional' else 'nr'),'params':{'missing':[x['fact'] for x in crit]}}]
        rec['tooltip']={'checklist':t,'text':text}
        recs.append(rec)
    # ---------------- статусы контекстов (вычисляются, не хардкодятся)
    from .contexts import context_statuses
    CTX=context_statuses(REG,METH,S,D,RAW,SEG)
    # ---------------- снимок
    for rec in recs:
        ev=D[(D.m==rec['model_id']) & D.kind.isin(['ind','aipediya'])]
        rec['evidence']['families']=sorted(ev.fam.unique().tolist())
        rec['evidence']['domains']=sorted(ev[ev.dom!='unclassified'].dom.unique().tolist())
        rec['evidence']['runners']=sorted(D[(D.m==rec['model_id']) & (D.kind!='dev')].runner.unique().tolist())
    params={'methodology':METH,'mappings':MAP,'calibration':{k:CAL[k] for k in CAL if k!='reference_theta'},'registry':REG,'item_ledger':ledger}
    cands=[{'model_id':m,'name':S.loc[m,'name'],'P_no1':round(float(U.loc[m,'P_no1']),4),'mcse':round(float(U.loc[m,'P_no1_mcse']),4)} for m in top.index[:3]]
    snap={'snapshot':{'methodology_version':METH['methodology_version'],'context_id':'LLM.OVERALL','profile':profile,'data_cutoff':str(CUT.date()),
            'master_sha256':R.sha256_file(master),'params_hash':R.canon_hash(params),'rng_seed':SEED,'n_draws':ndraws,
            'schema_version':'aipediya-rating-snapshot/1',
            'item_ledger_sha256':R.canon_hash(ledger),
            'anchors':{'q_basket':CAL['q_basket'],'delta_theta':DELTA,'price':PR,'resource':RS,'weights':METH['overall']['profiles'][profile]},
            'context_status':CTX['LLM.OVERALL'],
            'badge':None if badge is None else {'model_id':badge,'name':S.loc[badge,'name']},
            'badge_reason':'P_no1>=0.5' if badge else 'leaders_statistically_indistinguishable',
            'frontier_candidates':cands,'P_no_eligible_winner':round(float(1-P_has),4),
            'counts':{'rated':int((S.status=='Rated').sum()),'exact':int(sum(1 for x in recs if x['score_type']=='exact')),'bounded':int(sum(1 for x in recs if x['score_type']=='bounded')),
                      'provisional':int((S.status=='Provisional').sum()),'nr':int((S.status=='NR').sum())}},
          'models':sorted(recs,key=lambda x:x['model_id'])}
    content_sha=R.canon_hash(snap)
    snap['snapshot']['snapshot_id']=f"LLM.OVERALL@{profile}-v1.0-{str(CUT.date())}-{content_sha[:12]}"
    snap['snapshot']['content_sha256']=content_sha
    snap['snapshot']['created_at']=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    return snap,CTX,D,RAW


def build_snapshot(master, profile='BALANCED', seed=None, config=None, ledger=None):
    """Owner correction: evidence gates never suppress a published Model's estimate."""
    from .estimation import extend_snapshot
    snap, contexts, used, raw = build_reference_snapshot(master, profile, seed, config, ledger)
    return extend_snapshot(master, snap, contexts, used, config), contexts, used, raw

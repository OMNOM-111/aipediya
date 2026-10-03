"""Вычисление статусов контекстов Registry: Evidence Gate (модель/публикация) и Distinctiveness Gate (F14–F15).
Статус не хардкодится — он результат каждой сборки. Out of scope задаётся в Registry явно."""
import numpy as np, pandas as pd
from scipy.stats import chi2, spearmanr

def distinctiveness(S,D,fams,seed=7):
    rated=set(S[S.status=='Rated'].index)
    X=D[(D.kind=='ind')&D.m.isin(rated)].copy()
    g=X[X.fam.isin(fams)].copy(); g['prec']=g.weff*g.a**2/g.sig**2
    rest=D[D.m.isin(rated)&~D.fam.isin(fams)&(D.kind!='dev')]
    num=(rest.weff*rest.a*(rest.y-rest.c)/rest.sig**2).groupby(rest.m).sum(); den=1+(rest.weff*rest.a**2/rest.sig**2).groupby(rest.m).sum()
    th_wo=num/den; sd_wo=den**-0.5
    g=g[g.m.isin(th_wo.index)]; g['r']=g.y-(g.a*g.m.map(th_wo)+g.c)
    sw=(g.weff*g.a*g.r/g.sig**2).groupby(g.m).sum(); sp=g.prec.groupby(g.m).sum()
    u=sw/sp; v=1/sp+sd_wo[u.index]**2
    Qs=float((u**2/v).sum()); k=len(u); p=float(1-chi2.cdf(Qs,k)); tau2=max(0.0,float((u**2-v).mean()))
    se_g=[]; se_s=[]
    for m,gm in g.groupby('m'):
        fs=gm.fam.unique()
        if len(fs)<2: continue
        for f in fs:
            ho=gm[gm.fam==f]; tr=gm[gm.fam!=f]
            sh=(tr.weff*tr.a*tr.r/tr.sig**2).sum()/((1/tau2)+tr.prec.sum()) if tau2>0 else 0.0
            se_g+=list((ho.y-(ho.a*th_wo[m]+ho.c))**2); se_s+=list((ho.y-(ho.a*(th_wo[m]+sh)+ho.c))**2)
    se_g=np.array(se_g); se_s=np.array(se_s); diff=se_g-se_s
    rng=np.random.default_rng(seed); boot=[diff[rng.integers(0,len(diff),len(diff))].mean() for _ in range(2000)] if len(diff) else [0]
    impr=float(1-np.sqrt(se_s.mean())/np.sqrt(se_g.mean())) if len(diff) else 0.0
    ci=(float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5)))
    fam_n=g.groupby('m').fam.nunique(); gate=fam_n[fam_n>=2].index
    shr=sw/((1/tau2)+sp) if tau2>0 else u*0
    th_sc=S.theta[u.index]+shr
    sd_sc=np.sqrt(S.sd_total[u.index]**2+(1/((1/tau2)+sp) if tau2>0 else 0))
    qs=(th_sc-1.2816*sd_sc)[gate].sort_values(ascending=False); qg=S.theta_cons[gate].sort_values(ascending=False)
    rho=float(spearmanr(qs.rank(),qg[qs.index].rank()).correlation) if len(gate)>2 else 1.0
    top_changes=10-len(set(qs.index[:10])&set(qg.index[:10]))
    D1=(p<0.05) or (impr>=0.05 and ci[0]>0); D2=(rho<0.95) or (top_changes>=3) or (len(gate)>0 and qs.index[0]!=qg.index[0])
    return {'p_heterogeneity':round(p,4),'tau':round(float(np.sqrt(tau2)),3),'oos_improvement':round(impr,4),'oos_ci95_dmse':[round(ci[0],4),round(ci[1],4)],
            'spearman_vs_parent':round(rho,4),'top10_changes':int(top_changes),'same_no1':bool(qs.index[0]==qg.index[0]) if len(gate) else None,'D1':bool(D1),'D2':bool(D2),'passed':bool(D1 and D2)}

def context_statuses(REG,METH,S,D,RAW,SEG):
    out={}; rated=S[S.status=='Rated']
    for c in REG['contexts']:
        cid=c['context_id']; r={'context_id':cid}
        if c.get('fixed_status'):
            r.update(status=c['fixed_status'],reason=c.get('reason')); out[cid]=r; continue
        if cid=='LLM.OVERALL':
            g=METH['gates']['LLM.OVERALL']['publish']; X=D[D.kind.isin(['ind','aipediya'])&D.m.isin(rated.index)]
            n=len(rated); fams=X.fam.nunique(); runners=X.runner.nunique()
            external=X[X.kind=='ind'].runner.nunique()
            ok=n>=g['models_min'] and fams>=g['families_min'] and runners>=g['runners_min'] and external>=g['external_runners_min']
            shareC=float((rated.support_grade=='C').mean()) if n else 1.0
            st=('Ready (условно)' if shareC>0.5 else 'Ready') if ok else 'Insufficient Data'
            r.update(status=st,models_passing=n,families=int(fams),runners=int(runners),share_support_C=round(shareC,3)); out[cid]=r; continue
        fams=c.get('families',[])
        if c['segment']=='LLM':
            X=D[(D.kind=='ind')&D.fam.isin(fams)&D.m.isin(rated.index)]
        else:
            X=RAW[RAW.fam.isin(fams)&(RAW.kind!='dev')].rename(columns={}) if fams else RAW.iloc[:0]
        per=X.groupby('m').fam.nunique() if len(X) else pd.Series(dtype=int)
        gm=c.get('model_gate_families',2); npass=int((per>=gm).sum()); nf=int(X.fam.nunique()) if len(X) else 0; nr=int(X.runner.nunique()) if len(X) else 0
        pub=c.get('publish_models_min',10)
        if npass>=pub and nf>=2:
            dist=distinctiveness(S[S.status=='Rated'].assign(theta_cons=S.theta_cons),D,fams) if c['segment']=='LLM' else None
            ready=(nr>=2) and (dist is None or dist['passed'])
            r.update(status='Ready' if ready else 'Beta',distinctiveness=dist)
        else:
            r.update(status='Insufficient Data')
        r.update(models_passing_model_gate=npass,families_present=nf,runners=nr,next_step=c.get('next_step'))
        out[cid]=r
    return out

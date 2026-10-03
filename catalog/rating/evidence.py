"""AIpediya Rating v1.0 — эталонная (исполняемая) спецификация движка.
Параметры: config/methodology_v1.0.json, config/mappings_v1.0.json, config/calibration_v1.0.json.
Режимы: calibrate (однократно на версию методики) и score (каждая сборка снимка; параметры тестов заморожены)."""
import json, re, hashlib
import numpy as np, pandas as pd, openpyxl

def load_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for ch in iter(lambda:f.read(1<<20),b''): h.update(ch)
    return h.hexdigest()
def canon_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def read_master(path):
    wb=openpyxl.load_workbook(path,read_only=True)
    def df(n):
        rows=list(wb[n].iter_rows(values_only=True)); return pd.DataFrame(rows[1:],columns=rows[0])
    result={n:df(n) for n in ['Models','Offers','Evaluations','Access']}
    wb.close()
    return result

def data_cutoff(MS):
    d=[pd.to_datetime(MS['Offers'].Checked,errors='coerce').max(),pd.to_datetime(MS['Evaluations'].Checked,errors='coerce').max(),
       pd.to_datetime(MS['Models']['Last Verified'],errors='coerce').max(),pd.to_datetime(MS['Access'].Checked,errors='coerce').max()]
    return max(x for x in d if pd.notna(x)).normalize()

class Mapper:
    def __init__(self,MAP):
        self.MAP=MAP
        self.fam=[(re.compile(x['regex']),x['family'],x['domain']) for x in MAP['llm_families']]
        self.gen={x['benchmark']:(x['family'],x['segment'],x['domain']) for x in MAP['generation_families']}
        self.effort=MAP['effort_order']
    def family(self,b):
        for rx,f,d in self.fam:
            if rx.match(b): return f,d
        return None,None
    def effort_rank(self,c): return self.effort.get(c,self.MAP['effort_default_rank'])

def model_table(MS):
    M=MS['Models']; P=M[(M.Status=='PUBLISHED')&(M['Catalog Status']=='active')].copy()
    return P.set_index('Record ID')

def evidence_rows(MS,P,mp):
    E=MS['Evaluations']; E=E[E['Record ID'].isin(P.index)&(E.Public=='YES')].copy()
    J=E['Conditions Extra (JSON)'].map(lambda x: json.loads(x) if x else {})
    E['dup']=J.map(lambda d:'superseded_duplicate_of' in d); E['npct']=J.map(lambda d:d.get('normalized_percent')); E['via']=J.map(lambda d:d.get('retrieved_via'))
    # Explicit numeric dtype preserves the accepted reference display counts.
    E['npct']=pd.to_numeric(E['npct'],errors='coerce')
    from .policy import permission_valid
    cutoff=data_cutoff(MS)
    permitted=J.map(lambda d:permission_valid(d,cutoff))
    E=E[permitted]
    E=E[~E.dup&(E['Result Kind']!='composite')]
    rows=[]
    for _,r in E.iterrows():
        b=str(r.Benchmark); kind='dev' if r['Result Kind']=='developer' else 'ind'
        extra=json.loads(r['Conditions Extra (JSON)']) if r['Conditions Extra (JSON)'] else {}
        if kind=='ind' and extra.get('evidence_layer')=='aipediya' and extra.get('reproducible') is True:
            kind='aipediya'
        base=dict(m=r['Record ID'],b=b,runner=r.Evaluator if kind in ('ind','aipediya') else 'developer',
                  channel=('Epoch AI hub' if (r.via and 'Epoch' in str(r.via)) else r.Evaluator) if kind in ('ind','aipediya') else 'developer',
                  meas=pd.to_datetime(r.Measured,errors='coerce'),checked=pd.to_datetime(r.Checked,errors='coerce'),cfg=r.Configuration or 'default')
        if b in mp.gen:
            f,seg,d=mp.gen[b]; rows.append({**base,'fam':f,'dom':d,'seg':seg,'kind':'arena','v':float(r.Score)}); continue
        if b.startswith('MTEB'): rows.append({**base,'fam':'mteb','dom':'embedding','seg':'embedding','kind':'mteb','v':np.nan}); continue
        if r['Higher Is Better']=='NO': continue
        f,d=mp.family(b)
        if kind in ('ind','aipediya'):
            if f is None: continue
            if r.Unit=='Arena score': rows.append({**base,'fam':f,'dom':d,'seg':'llm','kind':'arena','v':float(r.Score)}); continue
            v=r.npct if pd.notna(r.npct) else (float(r.Score) if r.Unit=='%' else None)
            if v is None: continue
            rows.append({**base,'fam':f,'dom':d,'seg':'llm','kind':kind,'v':float(v)})
        else:
            if r.npct is None: continue
            rows.append({**base,'fam':'dev:'+b,'dom':'developer','seg':'llm','kind':'dev','v':float(r.npct)})
    return pd.DataFrame(rows,columns=['m','b','runner','channel','meas','checked','cfg','fam','dom','seg','kind','v'])

def segment_of(P,RAW,MAP):
    llm_ev=set(RAW[(RAW.seg=='llm')&(RAW.kind!='dev')].m); S=MAP['segment_rules']; seg={}
    for m,row in P.iterrows():
        out=str(row['Output Modalities'] or '').lower(); inp=str(row['Input Modalities'] or '').lower(); tasks=str(row.Tasks or '').lower(); cat=row.Category; name=str(row.Name).lower()
        if 'embed' in out or 'embed' in name: s='embedding'
        elif m in llm_ev: s='llm'
        elif re.search(S['audio_gen_tasks'],tasks): s='audio_gen'
        elif cat=='audio':
            if out.startswith('audio') and 'text' not in out: s='tts'
            elif 'audio' in inp and out=='text': s='stt'
            elif re.search(S['speech_llm_tasks'],tasks) or ('text' in out and 'audio' in out): s='speech_llm'
            else: s='speech_other'
        elif 'video' in out or re.search(S['video_tasks'],tasks): s='video_gen'
        elif ('image' in out and 'text' not in out) or re.search(S['image_tasks'],tasks): s='image_gen'
        elif re.search(S['specialized_tasks'],tasks) and 'text' not in out: s='specialized'
        elif 'text' in out or cat=='text' or re.search(S['llm_tasks'],tasks): s='llm'
        else: s='other'
        seg[m]=s
    return seg

def select_config(L,mp):
    ind=L[L.kind.isin(['ind','aipediya'])]; choice={}
    for m,g in ind.groupby('m'):
        cov=g.groupby('cfg').fam.nunique()
        choice[m]=sorted(cov.index,key=lambda c:(-cov[c],-mp.effort_rank(c)))[0]
    keep=(~L.kind.isin(['ind','aipediya']))|pd.Series([c==choice.get(m) for m,c in zip(L.m,L.cfg)],index=L.index)
    return L[keep],choice

def prepare(RAW,SEG,mp,METH,arena_z=None,linked=None):
    """arena_z=None — режим калибровки: z по текущему снимку и возврат параметров для заморозки."""
    L=RAW[(RAW.seg=='llm')&(RAW.m.map(SEG)=='llm')]
    L=L[~L.fam.isin(METH['evidence']['excluded_families_llm_overall'])]
    if linked is not None: L=L[L.b.isin(linked)|(L.kind=='dev')]   # непривязанные тесты исключаются ДО caps и выбора конфигурации
    L,choice=select_config(L,mp)
    L=L.groupby(['m','b','fam','dom','runner','channel','kind'],as_index=False).agg(v=('v','mean'),meas=('meas','min'),checked=('checked','max'))
    ar=L.kind=='arena'; z_out={}
    if arena_z is None:
        for b in L[ar].b.unique():
            s=L.b==b; z_out[b]={'mean':float(L.loc[s,'v'].mean()),'sd':float(L.loc[s,'v'].std(ddof=0))}
        arena_z=z_out
    L.loc[ar,'y']=[(v-arena_z[b]['mean'])/arena_z[b]['sd'] if b in arena_z else np.nan for b,v in zip(L.loc[ar,'b'],L.loc[ar,'v'])]
    lo,hi=METH['engine']['logit_clip']
    p=np.clip(L.loc[~ar,'v']/100,lo,hi); L.loc[~ar,'y']=np.log(p/(1-p))
    S=METH['engine']['sigma']; L['sig']=L.kind.map({'ind':S['independent'],'arena':S['arena'],'dev':S['developer'],'aipediya':S['independent']*S['aipediya_multiplier']})
    return L.dropna(subset=['y']),choice,z_out

def weights(L,METH):
    C=METH['caps']; ind=L[L.kind.isin(['ind','aipediya'])].copy(); ar=L[L.kind=='arena'].copy()
    n=ind.groupby(['m','fam']).b.transform('count'); ind['w']=np.minimum(1,C['family']/n)
    tot=ind.groupby(['m','runner']).w.transform('sum'); cap=ind.runner.map(lambda e:C['runner'].get(e,C['runner_default']))
    ind['w']=ind.w*np.minimum(1,cap/tot); parts=[ind]
    if C['arena_eff_obs']>0 and len(ar):
        ar=ar[ar.m.isin(set(ind.m))]; n=ar.groupby('m').b.transform('count'); ar['w']=np.minimum(1,C['arena_eff_obs']/n); parts.append(ar)
    dev=L[(L.kind=='dev')&L.m.isin(set(ind.m))].copy()
    if len(dev):
        dev=dev[dev.groupby('b').m.transform('nunique')>=C['developer_min_models_per_test']]
        if len(dev):
            n=dev.groupby(['m','fam']).b.transform('count'); dev['w']=np.minimum(1,C['developer_per_test']/n); parts.append(dev)
    return pd.concat(parts)

def _share(D,prec,kind,share):
    pk=prec.where(D.kind==kind,0).groupby(D.m).sum(); po=prec.where(D.kind.isin(['ind','aipediya']),0).groupby(D.m).sum()
    sc=np.minimum(1,(share/(1-share))*po/pk.replace(0,np.nan)).fillna(1)
    return np.where(D.kind==kind,D.m.map(sc),1)

def fit(D,METH,items=None,cohort=None):
    """items=None — калибровка версии; items=dict — frozen scoring (production)."""
    if items is None: raise ValueError('v1.0 only permits frozen scoring; release a new methodology to calibrate')
    E=METH['engine']; C=METH['caps']; D=D.copy(); frozen=True
    if frozen: D=D[D.b.isin(items)]
    a={b:1.0 for b in D.b.unique()}; c={b:0.0 for b in D.b.unique()}
    if frozen: a={b:items[b]['a'] for b in a}; c={b:items[b]['c'] for b in c}
    for _ in range(1 if frozen else E['calibration_iterations']):
        D['a']=D.b.map(a); D['c']=D.b.map(c); prec=D.w*D.a**2/D.sig**2
        weff=D.w*_share(D,prec,'dev',C['developer_share'])*_share(D,prec,'arena',C['arena_share'])
        num=(weff*D.a*(D.y-D.c)/D.sig**2).groupby(D.m).sum(); den=E['theta_prior_precision']+(weff*D.a**2/D.sig**2).groupby(D.m).sum()
        th=num/den
        if not frozen:
            ref=th[[m for m in th.index if (cohort is None or m in cohort) and m in set(D[D.kind=='ind'].m)]]
            th=(th-ref.mean())/ref.std(ddof=0); D['t']=D.m.map(th); w=weff/D.sig**2
            g=pd.DataFrame({'b':D.b,'w':w,'t':D.t,'y':D.y}).assign(wt=lambda x:x.w*x.t,wtt=lambda x:x.w*x.t**2,wy=lambda x:x.w*x.y,wty=lambda x:x.w*x.t*x.y).groupby('b').sum()
            pa=1/E['prior_a_sd']**2; pc=1/E['prior_c_sd']**2
            A11=g.wtt+pa; A12=g.wt; A22=g.w+pc; r1=g.wty+pa*E['prior_a_mean']; r2=g.wy
            det=A11*A22-A12**2; aa=(r1*A22-A12*r2)/det; cc=(A11*r2-A12*r1)/det
            a=aa.clip(*E['a_bounds']).to_dict(); c=cc.to_dict()
    D['a']=D.b.map(a); D['c']=D.b.map(c); D['weff']=weff; D['t']=D.m.map(th)
    res=D.y-(D.a*D.t+D.c); Pm=E['theta_prior_precision']+(D.weff*D.a**2/D.sig**2).groupby(D.m).sum()
    chi=(D.weff*res**2/D.sig**2).groupby(D.m).sum(); dof=D.weff.groupby(D.m).sum()
    infl=np.sqrt(np.maximum(1,(chi/np.maximum(dof,1)).where(dof>=E['misfit_min_dof'],1)))
    out=pd.DataFrame({'theta':th,'sd':Pm**-0.5*infl,'misfit':infl})
    return out,{b:{'a':float(a[b]),'c':float(c[b])} for b in a},D

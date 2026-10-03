"""Offline build/check/report for derived, versioned Rating v1.0 snapshots."""
import json
import os
from pathlib import Path
import tempfile
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from catalog.rating.checks import CONFIG,check_frozen,check_snapshot,params_hash

DEFAULT_MASTER=Path(settings.BASE_DIR)/'AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx'
OUTPUT=Path(settings.BASE_DIR)/'data/rating/snapshots'

def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    handle,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    with os.fdopen(handle,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=1,allow_nan=False);f.write('\n')
    os.replace(tmp,path)

class Command(BaseCommand):
    help='Offline Rating v1.0 snapshot build/check/report (never deploys)'
    def add_arguments(self,parser):
        parser.add_argument('action',choices=['build','check','report','bind-item'])
        parser.add_argument('--master',default=str(DEFAULT_MASTER))
        parser.add_argument('--profile',choices=['BALANCED','QUALITY_FIRST','ECONOMY'],default='BALANCED')
        parser.add_argument('--seed',type=int,default=20261003)
        parser.add_argument('--out',default=str(OUTPUT))
        parser.add_argument('--snapshot',default='')
        parser.add_argument('--rebuild',action='store_true')
        parser.add_argument('--benchmark',default='')
        parser.add_argument('--family',default='')
        parser.add_argument('--domain',default='')
        parser.add_argument('--item-kind',choices=['ind','arena'],default='ind')
    def handle(self,*args,**opts):
        if settings.AIPEDIA_ENV!='local':raise CommandError('Rating commands are offline Local-only')
        errors=check_frozen()
        if errors:raise CommandError('; '.join(errors))
        if opts['action']=='bind-item':
            return self.bind_item(opts)
        out=Path(opts['out']); manifest_path=out/'current.json'
        if opts['action']=='build':
            from catalog.rating.builder import build_snapshot
            snapshot,contexts,used,raw=build_snapshot(opts['master'],opts['profile'],opts['seed'])
            errors=check_snapshot(snapshot)
            if errors:raise CommandError('; '.join(errors))
            path=out/(snapshot['snapshot']['snapshot_id']+'.json')
            if path.exists():
                old=json.loads(path.read_text(encoding='utf-8'))
                if old['snapshot']['content_sha256']!=snapshot['snapshot']['content_sha256']:raise CommandError('Immutable snapshot collision')
                snapshot=old
            else:save_json(path,snapshot)
            save_json(out/(path.stem+'.contexts.json'),contexts)
            manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'schema_version':'aipediya-rating-index/1','profiles':{}}
            manifest['profiles'][opts['profile']]=path.name
            save_json(manifest_path,manifest)
            self.stdout.write(json.dumps(snapshot['snapshot'],ensure_ascii=False,indent=1))
            return
        if opts['snapshot']:path=Path(opts['snapshot'])
        else:
            if not manifest_path.exists():raise CommandError('No built rating snapshot')
            manifest=json.loads(manifest_path.read_text(encoding='utf-8'));path=out/manifest['profiles'][opts['profile']]
        snapshot=json.loads(path.read_text(encoding='utf-8'))
        errors+=check_snapshot(snapshot)
        if snapshot['snapshot']['params_hash']!=params_hash():errors.append('Snapshot methodology/ledger hash mismatch')
        if opts['rebuild'] or opts['action']=='check':
            from catalog.rating.builder import build_snapshot
            rebuilt,*_=build_snapshot(opts['master'],snapshot['snapshot']['profile'],snapshot['snapshot']['rng_seed'])
            if rebuilt['snapshot']['content_sha256']!=snapshot['snapshot']['content_sha256']:errors.append('Deterministic rebuild/master/config mismatch')
        if errors:raise CommandError('; '.join(errors))
        if opts['action']=='check':self.stdout.write('RATING CHECK PASS '+snapshot['snapshot']['content_sha256'])
        else:
            meta=snapshot['snapshot'];self.stdout.write(f"{meta['snapshot_id']}\nData: {meta['data_cutoff']}\n{meta['counts']}\nBadge: {meta['badge']} ({meta['badge_reason']})")
            for m in sorted((m for m in snapshot['models'] if m['status']=='Rated'),key=lambda m:(m['tier'],-(m.get('overall_cons') or m['overall_max']))):
                value=f"{m['overall_cons']:.1f}" if m['score_type']=='exact' else f"{m['overall_min']:.1f}–{m['overall_max']:.1f}"
                self.stdout.write(f"{m['name']}: {value}; rank {m['overall_rank_range']} / tier {m['tier']}; Precision {m['precision_grade']} / Support {m['support_grade']}")

    def bind_item(self,opts):
        import re
        import numpy as np
        from catalog.rating import evidence as R
        from catalog.rating.ledger import bind_item
        if not all(opts[key] for key in ('benchmark','family','domain')):raise CommandError('Supply benchmark, approved family and domain mapping')
        MS=R.read_master(opts['master']);cal=R.load_json(CONFIG/'calibration_v1.0.json');meth=R.load_json(CONFIG/'methodology_v1.0.json')
        mp=R.Mapper(R.load_json(CONFIG/'mappings_v1.0.json'))
        mp.fam.insert(0,(re.compile('^'+re.escape(opts['benchmark'])+'$'),opts['family'],opts['domain']))
        raw=R.evidence_rows(MS,R.model_table(MS),mp)
        raw=raw[(raw.b==opts['benchmark'])&(raw.kind==opts['item_kind'])].dropna(subset=['v'])
        theta=cal['reference_theta'];raw=raw[raw.m.isin(theta)]
        if raw.m.nunique()<5:raise CommandError('Need ≥5 permitted independent canonical-master observations on known frozen-theta models')
        rows=[];z=None
        if opts['item_kind']=='arena':
            z=dict(mean=float(raw.v.mean()),sd=float(raw.v.std(ddof=0)))
            if not z['sd']>0:raise CommandError('Arena calibration SD must be positive')
        for _,r in raw.iterrows():
            if z:y=(r.v-z['mean'])/z['sd'];sigma=meth['engine']['sigma']['arena']
            else:
                p=float(np.clip(r.v/100,*meth['engine']['logit_clip']));y=float(np.log(p/(1-p)));sigma=meth['engine']['sigma']['independent']
            rows.append(dict(model_id=r.m,y=float(y),sigma=sigma,weight=1.0))
        E=MS['Evaluations'];sources=sorted(set(E[(E.Benchmark==opts['benchmark'])&(E.Public=='YES')]['Source URL'].dropna()))
        ledger=R.load_json(CONFIG/'rating_item_ledger.json')
        try:updated=bind_item(cal,meth,ledger,opts['benchmark'],rows,opts['family'],opts['domain'],opts['item_kind'],sources,z)
        except ValueError as exc:raise CommandError(str(exc))
        save_json(CONFIG/'rating_item_ledger.json',updated)
        self.stdout.write('Bound item (append-only): '+updated['entries'][-1]['entry_sha256'])

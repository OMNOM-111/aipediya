"""Numerical and presentation regression gates for the owner-frozen v1.0."""
import copy
import json
import math
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from django.conf import settings
from django.test import SimpleTestCase
from catalog.rating import evidence as R
from catalog.rating.builder import build_snapshot
from catalog.rating.checks import CONFIG,check_frozen,check_snapshot,content_hash
from catalog.rating.ledger import bind_item,merged_calibration,validate_ledger
from catalog.rating.policy import fact_state,permission_valid

ROOT=Path(settings.BASE_DIR)

class FrozenRatingTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.master=ROOT/'AI_CONTEXT/AIpediya_Model_Verification_Master.xlsx'
        cls.ms=R.read_master(cls.master);cls.meth=R.load_json(CONFIG/'methodology_v1.0.json')
        cls.cal=R.load_json(CONFIG/'calibration_v1.0.json');cls.mapping=R.load_json(CONFIG/'mappings_v1.0.json')
        cls.mp=R.Mapper(cls.mapping);cls.p=R.model_table(cls.ms)
        cls.raw=R.evidence_rows(cls.ms,cls.p,cls.mp);cls.seg=R.segment_of(cls.p,cls.raw,cls.mapping)
        cls.snapshot,cls.contexts,cls.used,_=build_snapshot(cls.master)
        cls.expected=R.load_json(ROOT/'catalog/tests/fixtures/rating_v1/LLM.OVERALL@BALANCED.snapshot.json')
    def score(self,raw):
        L,choice,_=R.prepare(raw,self.seg,self.mp,self.meth,self.cal['arena_z'],linked=self.cal['items'])
        fitted,_,used=R.fit(R.weights(L,self.meth),self.meth,items=self.cal['items'])
        return fitted,used,choice
    def test_reference_counts_and_all_numerical_tolerances(self):
        self.assertEqual(self.snapshot['snapshot']['counts'],dict(rated=59,exact=27,bounded=32,provisional=66,nr=162))
        current={m['model_id']:m for m in self.snapshot['models']}
        for old in self.expected['models']:
            new=current[old['model_id']]
            for key in ('status','score_type','configuration','tier','overall_rank','overall_rank_range','precision_grade','support_grade','no1_eligible'):
                self.assertEqual(new.get(key),old.get(key),(old['model_id'],key))
            for key in ('theta','Q_central','Q_cons','overall_cons','overall_min','overall_max','P_no1','P_no1_mcse'):
                if old.get(key) is not None:self.assertAlmostEqual(new[key],old[key],places=10)
    def test_reference_contexts_are_computed(self):
        expected=R.load_json(ROOT/'catalog/tests/fixtures/rating_v1/context_status.json')
        self.assertEqual(self.contexts,expected)
    def test_frozen_artifact_hashes_and_snapshot_schema(self):
        self.assertEqual(check_frozen(),[]);self.assertEqual(check_snapshot(self.snapshot),[])
    def test_forbidden_evidence_and_developer_independence(self):
        self.assertFalse(self.used.fam.isin(['swebench']).any())
        developer=self.used[self.used.kind=='dev']
        self.assertTrue((developer.runner=='developer').all())
        self.assertTrue((developer.sig==1.8).all())
        # The executable reference includes three developer Cybench results.
        # They remain developer evidence; never count in independent gates.
        independent=self.used[self.used.kind.isin(['ind','aipediya'])]
        self.assertFalse((independent.runner=='developer').any())
        E=self.ms['Evaluations']; public=set(zip(E[E.Public=='YES']['Record ID'],E[E.Public=='YES'].Benchmark))
        self.assertTrue(set(zip(self.used.m,self.used.b)).issubset(public))
    def test_independent_percentage_without_normalized_field_is_usable(self):
        ms=copy.deepcopy(self.ms)
        source=ms['Evaluations'][(ms['Evaluations'].Benchmark=='GPQA Diamond')&(ms['Evaluations']['Result Kind']!='developer')].iloc[0].copy()
        source['Conditions Extra (JSON)']='{}';source['Unit']='%';source['Score']=75
        source['Public']='YES';source['Record ID']=self.p.index[0]
        ms['Evaluations']=pd.DataFrame([source])
        raw=R.evidence_rows(ms,self.p,self.mp)
        self.assertEqual(raw.v.tolist(),[75.0])

    def test_frozen_scores_do_not_change_when_leader_removed(self):
        fitted,_,_=self.score(self.raw);victim=fitted.theta.idxmax()
        other,_,_=self.score(self.raw[self.raw.m!=victim])
        self.assertLess(float((fitted.theta[other.index]-other.theta).abs().max()),1e-12)
    def test_unknown_item_excluded_before_caps_and_configuration(self):
        fitted,used,choice=self.score(self.raw)
        extra=self.raw[(self.raw.kind=='ind')&(self.raw.fam=='gpqa')].copy()
        extra['b']='UNKNOWN-ITEM';extra['cfg']='high';extra['v']=100
        newer,used2,choice2=self.score(pd.concat([self.raw,extra]*2,ignore_index=True))
        self.assertEqual(choice,choice2)
        self.assertFalse((used2.b=='UNKNOWN-ITEM').any())
        self.assertLess(float((fitted.theta-newer.theta).abs().max()),1e-12)
    def test_arena_z_is_frozen(self):
        L,_,_=R.prepare(self.raw,self.seg,self.mp,self.meth,self.cal['arena_z'],linked=self.cal['items'])
        for _,row in L[L.kind=='arena'].iterrows():
            z=self.cal['arena_z'][row.b];self.assertAlmostEqual(row.y,(row.v-z['mean'])/z['sd'])
        extra=self.raw[self.raw.kind=='arena'].iloc[:1].copy();extra['m']='synthetic-new-arena-model';extra['v']=100000
        seg=dict(self.seg,**{'synthetic-new-arena-model':'llm'})
        newer,_,_=R.prepare(pd.concat([self.raw,extra]),seg,self.mp,self.meth,self.cal['arena_z'],linked=self.cal['items'])
        joined=L[L.kind=='arena'].merge(newer[newer.kind=='arena'],on=['m','b','runner'],suffixes=('_old','_new'))
        np.testing.assert_array_equal(joined.y_old,joined.y_new)
    def test_family_runner_and_arena_caps(self):
        L,_,_=R.prepare(self.raw,self.seg,self.mp,self.meth,self.cal['arena_z'],linked=self.cal['items'])
        weights=R.weights(L,self.meth);ind=weights[weights.kind=='ind']
        self.assertLessEqual(ind.groupby(['m','fam']).w.sum().max(),1.5+1e-12)
        for (_,runner),weight in ind.groupby(['m','runner']).w.sum().items():self.assertLessEqual(weight,self.meth['caps']['runner'].get(runner,2)+1e-12)
        ar=weights[weights.kind=='arena'];self.assertLessEqual(ar.groupby('m').w.sum().max(),1+1e-12)
        used=self.used;precision=used.weff*used.a**2/used.sig**2
        total=precision.groupby(used.m).sum();arena=precision.where(used.kind=='arena',0).groupby(used.m).sum()
        self.assertLessEqual((arena/total).max(),0.25+1e-12)
    def test_no_calibrate_in_daily_scoring(self):
        with self.assertRaisesRegex(ValueError,'frozen scoring'):R.fit(self.used,self.meth)
    def test_permanent_zero_api_and_promotional_exclusion(self):
        ms=copy.deepcopy(self.ms);leader='gpt-6-astra-d05a172f'
        offers=ms['Offers'];chosen=(offers['Record ID']==leader)&offers.Unit.isin(['input','output'])
        offers.loc[chosen,'Amount']=0
        with patch.object(R,'read_master',return_value=ms):result,*_=build_snapshot(self.master)
        row=next(m for m in result['models'] if m['model_id']==leader)
        self.assertEqual(row['C'],1);self.assertEqual(row['blend_usd_per_1m'],0);self.assertEqual(row['score_type'],'exact')
        import re
        rx=re.compile(self.mapping['reference_offer']['exclude_conditions_regex'],re.I)
        for condition in ('Batch','off-peak','temporary promotional offer'):self.assertTrue(rx.search(condition))
    def test_early_evidence_misfit_and_precision_support(self):
        fitted,_,_=self.score(self.raw)
        cutoff=R.data_cutoff(self.ms)
        for m in self.snapshot['models']:
            if m['status']!='Rated':continue
            expected=fitted.loc[m['model_id'],'sd']*(1.29 if m['early_evidence'] else 1)
            self.assertAlmostEqual(m['sd_stat'],expected)
            self.assertEqual(m['sd_support'],0);self.assertEqual(m['sd_stat'],m['sd_total'])
            self.assertAlmostEqual(m['theta_cons'],m['theta']-1.2816*m['sd_total'])
    def test_bounded_global_rank_and_no_fake_scores(self):
        rated=[m for m in self.snapshot['models'] if m['status']=='Rated']
        for m in self.snapshot['models']:
            if m['status']!='Rated':self.assertIsNone(m.get('overall_cons'));self.assertIsNone(m.get('overall_rank'));continue
            if m['score_type']!='bounded':continue
            self.assertIsNone(m['overall_rank']);self.assertIsNone(m['overall_cons']);self.assertFalse(m['no1_eligible'])
            other=[r for r in rated if r['model_id']!=m['model_id']]
            best=1+sum(r['tier']<m['tier'] or (r['tier']==m['tier'] and (r['overall_cons'] if r['score_type']=='exact' else r['overall_min'])>m['overall_max']) for r in other)
            worst=1+sum(r['tier']<m['tier'] or (r['tier']==m['tier'] and (r['overall_cons'] if r['score_type']=='exact' else r['overall_max'])>m['overall_min']) for r in other)
            self.assertEqual(m['overall_rank_range'],str(best) if best==worst else f'{best}–{worst}')
    def test_no_badge_and_mcse(self):
        self.assertIsNone(self.snapshot['snapshot']['badge'])
        self.assertEqual(self.snapshot['snapshot']['badge_reason'],'leaders_statistically_indistinguishable')
        for m in self.snapshot['models']:
            if m['status']=='Rated':self.assertAlmostEqual(m['P_no1_mcse'],math.sqrt(m['P_no1']*(1-m['P_no1'])/6000))
    def test_hash_ignores_system_clock_and_snapshot_id(self):
        modified=copy.deepcopy(self.snapshot);modified['snapshot']['created_at']='2100-01-01';modified['snapshot']['snapshot_id']='different'
        self.assertEqual(content_hash(self.snapshot),content_hash(modified))
        with patch.object(R,'read_master',return_value=self.ms):rebuilt,*_=build_snapshot(self.master)
        self.assertEqual(rebuilt['snapshot']['content_sha256'],self.snapshot['snapshot']['content_sha256'])
    def test_profile_never_changes_capability(self):
        with patch.object(R,'read_master',return_value=self.ms):other,*_=build_snapshot(self.master,'ECONOMY')
        for a,b in zip(self.snapshot['models'],other['models']):
            for key in ('theta','Q_cons','Q_central','sd_stat','configuration','tier'):self.assertEqual(a.get(key),b.get(key))
    def test_expired_required_input_becomes_bounded_before_ranking(self):
        ms=copy.deepcopy(self.ms);id='gpt-6-astra-d05a172f';mask=ms['Offers']['Record ID']==id
        ms['Offers'].loc[mask,'Checked']='2026-01-01'
        with patch.object(R,'read_master',return_value=ms):result,*_=build_snapshot(self.master)
        row=next(m for m in result['models'] if m['model_id']==id)
        self.assertEqual(row['score_type'],'bounded');self.assertIsNone(row['overall_rank']);self.assertIsNone(row['overall_cons']);self.assertEqual(row['P_no1'],0)
    def test_freshness_and_source_permission_states(self):
        rules={'fresh':30,'stale':60}
        for checked,state in [(None,'unknown'),('2026-10-01','fresh'),('2026-08-15','stale'),('2026-01-01','expired')]:self.assertEqual(fact_state(checked,'2026-10-02',rules),state)
        self.assertEqual(fact_state('2026-10-01','2026-10-02',rules,True),'unconfirmed')
        self.assertFalse(permission_valid({'permission_expires':'2026-09-01'},'2026-10-02'))
    def test_item_binding_is_append_only_and_requires_five_anchors(self):
        ledger={'methodology_version':self.cal['methodology_version'],'entries':[]}
        ids=list(self.cal['reference_theta'])[:5]
        observations=[dict(model_id=m,y=self.cal['reference_theta'][m]['theta']*1.2+0.5,sigma=0.9) for m in ids]
        with self.assertRaisesRegex(ValueError,'five'):bind_item(self.cal,self.meth,ledger,'NEW',observations[:4],'gpqa','knowledge','ind',['https://example.test/source'])
        linked=bind_item(self.cal,self.meth,ledger,'NEW',observations,'gpqa','knowledge','ind',['https://example.test/source'])
        self.assertEqual(ledger['entries'],[]);validate_ledger(linked,self.cal)
        changed=copy.deepcopy(linked);changed['entries'][0]['a']+=0.1
        with self.assertRaises(ValueError):validate_ledger(changed,self.cal)
        merged=merged_calibration(self.cal,linked);self.assertEqual(merged['q_basket'],self.cal['q_basket'])
        with self.assertRaises(ValueError):bind_item(self.cal,self.meth,linked,'NEW',observations,'gpqa','knowledge','ind',['https://example.test/source'])

class RatingPresentationTests(SimpleTestCase):
    def test_threshold_zone_reruns_with_same_procedure_and_has_no_badge(self):
        from catalog.rating.monte_carlo import resolve_threshold,badge_passes,mcse
        calls=[]
        def run(draws):
            calls.append(draws)
            return None,None,None,[0.501],1
        result,draws=resolve_threshold(run,6000)
        self.assertEqual(calls,[6000,12000]);self.assertEqual(draws,12000)
        self.assertFalse(badge_passes(0.501,mcse(0.501,draws)))
        self.assertTrue(badge_passes(0.55,mcse(0.55,draws)))
        self.assertFalse(badge_passes(0.49,0.001))
        self.assertFalse(badge_passes(0.9,0.001,False))
    def test_all_22_locales_have_complete_labels_and_placeholders(self):
        import re
        from catalog.context import t,TEXT
        from catalog.i18n import SUPPORTED_CODES
        from catalog.rating.content import source_labels
        from catalog.rating.translations import PATH
        overlay=R.load_json(PATH);labels=source_labels(CONFIG)
        for lang in SUPPORTED_CODES:
            for key,(_,en) in labels.items():
                value=t(key,lang);self.assertNotEqual(value,key)
                self.assertEqual(set(re.findall(r'\{\w+\}',value)),set(re.findall(r'\{\w+\}',en)),(lang,key))
                if lang not in ('en','ru'):self.assertIn(key,overlay['translations'][lang])
    def test_tooltips_localize_without_raw_reason_codes(self):
        from catalog.rating.presentation import snapshot,model_rating
        from catalog.i18n import SUPPORTED_CODES
        for lang in SUPPORTED_CODES:
            for record in snapshot()['models']:
                value=model_rating(record['model_id'],lang)
                text=' '.join(value['audit_text'])
                self.assertNotIn('unconfirmed_',text)
                self.assertNotIn('rating_tpl_',text)
    def test_price_audit_uses_values_and_rtl_ranges_are_isolated(self):
        from catalog.rating.presentation import model_rating,template_text
        result=model_rating('gpt-6-astra-d05a172f','en')
        price=next(x['text'] for x in result['audit'] if 'API price' in x['text'])
        self.assertIn('$10.0 / $50.0',price)
        self.assertIn('2026-09-19',price)
        text=template_text('text_bounded','ar',dict(min=58.1,max=62.4,range='14–19',missing=['resource']))
        self.assertIn('\u206658.1–62.4\u2069',text)
        self.assertIn('\u206614–19\u2069',text)

    def test_runtime_has_no_offline_imports(self):
        import subprocess,sys
        result=subprocess.run([sys.executable,'-c',"from catalog.rating.presentation import snapshot; import sys; snapshot(); assert not {'numpy','pandas','openpyxl','scipy'} & set(sys.modules)"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_corrupt_snapshot_fails_validation(self):
        from catalog.rating.presentation import snapshot
        value=copy.deepcopy(snapshot());value['models'][0]['status']='Rated'
        self.assertTrue(check_snapshot(value))

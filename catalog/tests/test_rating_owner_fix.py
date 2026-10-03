"""Owner #023 invariants: complete numeric coverage and frozen-scale extension."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase
from catalog.rating import evidence as R
from catalog.rating.builder import build_snapshot
from catalog.rating.checks import CONFIG,check_snapshot,content_hash
from catalog.rating.primary_context import primary_context
from catalog.rating.pipeline import coverage_errors
from catalog import catalog_master as cm

class OwnerRatingTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.master=cm.WORKBOOK_PATH
        cls.snapshot,*_=build_snapshot(cls.master)
        cls.rows={r['model_id']:r for r in cls.snapshot['models']}
        cls.reference=R.load_json(Path(__file__).parent/'fixtures/rating_v1/LLM.OVERALL@BALANCED.snapshot.json')

    def test_all_published_models_are_numeric_and_tools_are_absent(self):
        ms=R.read_master(self.master)
        ids=set(ms['Models'].loc[ms['Models'].Status=='PUBLISHED','Record ID'])
        tools={r['Record ID'] for r in cm.read_workbook(self.master)[0]['Tools']}
        self.assertEqual(len(ids),343)
        self.assertEqual(set(self.rows),ids)
        self.assertFalse(set(self.rows)&tools)
        self.assertEqual(check_snapshot(self.snapshot),[])
        self.assertTrue(all(0<=r['aipediya_rating']<=100 for r in self.rows.values()))
        for _,r in ms['Models'][ms['Models'].Status=='PUBLISHED'].iterrows():
            self.assertEqual(self.rows[r['Record ID']]['primary_rating_context'],primary_context(r))

    def test_reference_59_capabilities_and_27_exact_scores_preserved(self):
        count=0
        for old in self.reference['models']:
            if old['status']!='Rated':continue
            count+=1;new=self.rows[old['model_id']]
            for field in ('theta','Q_central','Q_cons','sd_stat','sd_total','P_no1','P_no1_mcse'):
                self.assertAlmostEqual(new[field],old[field],places=10)
            if old['score_type']=='exact':self.assertAlmostEqual(new['aipediya_rating'],old['overall_cons'],places=10)
            else:self.assertTrue(old['overall_min']<=new['aipediya_rating']<=old['overall_max'])
        self.assertEqual(count,59)

    def test_gaps_never_become_zero_facts_or_verified(self):
        for row in self.rows.values():
            if row['missing_estimate_inputs']:self.assertEqual(row['rating_state'],'estimated')
            for field in ('price','resource'):
                if field in row['missing_estimate_inputs']:
                    self.assertIsNone(row['component_facts'][field])
                    self.assertTrue(0<row['component_estimates'][field]<1)
            if row['primary_rating_context']!='LLM.OVERALL':self.assertIsNone(row['public_context_rank'])

    def test_bad_coverage_state_and_snapshot_id_block_qa(self):
        for field,value in [('aipediya_rating',None),('primary_rating_context',''),('rating_state','NR'),('rating_snapshot_id','wrong')]:
            bad=copy.deepcopy(self.snapshot);bad['models'][0][field]=value
            bad['snapshot']['content_sha256']=content_hash(bad)
            self.assertTrue(check_snapshot(bad),field)
        self.assertTrue(coverage_errors(self.master,set(self.rows)-{next(iter(self.rows))},set()))
        with self.assertRaisesRegex(ValueError,'No primary'):primary_context({'Name':'unknown','Tasks':'unmapped-kind'})
        self.assertEqual(primary_context({'Name':'video with sound','Tasks':'video_generation','Output Modalities':'video | audio'}),'VID.GEN')

    def test_new_zero_evidence_model_rebuilds_all_profiles_automatically(self):
        rows,meta,extra=cm.read_workbook(self.master)
        parent=next(r for r in rows['Models'] if r['Record ID']=='gpt-6-astra-d05a172f')
        model=dict(parent,**{'Record ID':'owner-fix-zero-evidence','Name':'Owner QA zero evidence','Family':'Owner QA isolated family','Context':'','Last Verified':''})
        rows['Models'].append(model)
        prior_before=hashlib.sha256((CONFIG/'owner_estimation_priors.json').read_bytes()).hexdigest()
        from catalog.rating.pipeline import rebuild
        with tempfile.TemporaryDirectory() as directory:
            master=Path(directory)/'master.xlsx';out=Path(directory)/'snapshots'
            with patch.object(cm,'WORKBOOK_PATH',master),patch('catalog.rating.pipeline.rebuild',side_effect=lambda p:rebuild(p,out)) as auto:
                cm.write_workbook(rows,meta,master,extra)
            self.assertEqual(auto.call_count,1)
            index=R.load_json(out/'current.json')
            self.assertEqual(set(index['profiles']),{'BALANCED','QUALITY_FIRST','ECONOMY'})
            for name in index['profiles'].values():
                snapshot=R.load_json(out/name);new=next(r for r in snapshot['models'] if r['model_id']==model['Record ID'])
                self.assertEqual(len(snapshot['models']),344)
                self.assertEqual(new['rating_state'],'estimated')
                self.assertEqual(new['numeric_evidence'],dict(independent=0,developer=0,aipediya=0))
                self.assertIsNone(new['component_facts']['price']);self.assertIsNone(new['component_facts']['resource'])
                self.assertTrue(0<new['aipediya_rating']<100)
                self.assertEqual(check_snapshot(snapshot),[])
                if snapshot['snapshot']['profile']=='BALANCED':
                    for old in self.snapshot['models']:
                        same=next(r for r in snapshot['models'] if r['model_id']==old['model_id'])
                        self.assertEqual(old['aipediya_rating'],same['aipediya_rating'])
            self.assertEqual(coverage_errors(master,set(self.rows)|{model['Record ID']},set(),out),[])
        self.assertEqual(prior_before,hashlib.sha256((CONFIG/'owner_estimation_priors.json').read_bytes()).hexdigest())

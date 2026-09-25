import csv
from datetime import date, timedelta
import json
import tempfile
from io import StringIO
from pathlib import Path
from django.core.management import call_command
from django.test import TestCase
from catalog.models import ModelVersion, Evaluation, Benchmark, Offer, Revision
from catalog.management.commands.import_epoch_snapshot import OWN_FILES
from catalog.views import INITIAL_PAGE_SIZE, CHUNK_SIZE


class ComparisonReleaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_catalog', verbosity=0)
        ModelVersion.objects.update(released=date(2020, 1, 1))
        from catalog.chronology import renumber_chronologically
        renumber_chronologically()
        source = ModelVersion.objects.first()
        for i in range(34):
            ModelVersion.objects.create(family=source.family, name=('z' if i % 2 else 'A') + str(i),
                slug=f'comparison-{i}', version=str(i), category='text', tasks=['reasoning', 'coding'] if i % 2 else ['documents'],
                source=source.source, checked=source.checked, released=date(2021, 1, 1) + timedelta(days=i))

    def all_models(self, **params):
        result = []
        first = self.client.get('/', params, follow=True)
        for page in range(1, first.context['page'].paginator.num_pages + 1):
            response = self.client.get('/', {**params, 'page': page}, follow=True)
            result.extend(response.context['page'])
        self.assertEqual(len(result), len({m.public_number for m in result}))
        return result

    def test_every_text_sort_all_pages_both_languages_and_directions(self):
        for lang in ('ru', 'en'):
            for field in ('number', 'name', 'purpose', 'access'):
                for direction in ('asc', 'desc'):
                    models = self.all_models(lang=lang, sort=f'{field}_{direction}')
                    self.assertEqual(len(models), 41)
                    from catalog.comparison import alphabet
                    values = [(m.public_number if field == 'number' else alphabet(m.name) if field == 'name' else getattr(m, field + '_key'), m.public_number) for m in models]
                    known = [(v, n) for v, n in values if v != '']
                    self.assertEqual([v for v,n in known], sorted([v for v,n in known], reverse=direction == 'desc'))
                    self.assertTrue(all(v == '' for v,n in values[len(known):]))
                    for key in {v for v,n in known}:
                        ties = [n for v,n in known if v == key]
                        self.assertEqual(ties, sorted(ties))

    def test_price_default_basis_and_no_substitute_prices(self):
        for direction in ('asc', 'desc'):
            response = self.client.get('/', {'sort': 'price_' + direction, 'lang': 'ru'}, follow=True)
            self.assertEqual(response.context['price_unit'], 'input')
            models = self.all_models(sort='price_' + direction)
            known = [m.comparison_offer.amount for m in models if m.comparison_offer]
            self.assertEqual(known, sorted(known, reverse=direction == 'desc'))
            self.assertTrue(all(m.comparison_offer is None for m in models[len(known):]))
            self.assertContains(response, 'Нет цены в выбранных условиях')

    def test_direct_later_page_shows_actual_loaded_row_count(self):
        source = ModelVersion.objects.filter(published=True).first()
        need = INITIAL_PAGE_SIZE + CHUNK_SIZE + 5 - ModelVersion.objects.filter(published=True).count()
        for i in range(max(0, need)):
            ModelVersion.objects.create(
                family=source.family, name=f'chunk-{i}', slug=f'chunk-{i}', version=str(i),
                category='text', tasks=['reasoning'], source=source.source, checked=source.checked,
                published=True,
            )
        response = self.client.get('/', {'page': 2})
        page = response.context['page']
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page), CHUNK_SIZE)
        self.assertEqual(response.context['shown_count'], len(page))
        self.assertEqual(response.context['shown_count'], page.end_index() - page.start_index() + 1)
        partial = self.client.get('/', {'page': 2, 'partial': 'rows'})
        self.assertEqual(partial.status_code, 200)
        self.assertTrue(partial.has_header('X-Aipedia-Next'))
        self.assertIn('partial=rows', partial['X-Aipedia-Next'])
        self.assertIn('page=3', partial['X-Aipedia-Next'])

    def test_explicit_modes_composite_missing_and_filters(self):
        model = ModelVersion.objects.first()
        bench = Benchmark.objects.create(name='ECI', protocol='test snapshot', category='text', unit='')
        for mode, score in [('high', 140), ('low', 120)]:
            Evaluation.objects.create(model=model, benchmark=bench, score=score, configuration=mode,
                snapshot='2026-09-20', source=model.source, evaluator='Epoch AI', result_kind='composite',
                independent=False, public=True, checked=model.checked, observation_key=mode)
        for direction in ('best', 'worst'):
            response = self.client.get('/', {'sort':'check_' + direction, 'configuration':'low'})
            self.assertEqual(response.context['benchmark'], bench)
            self.assertEqual(response.context['page'][0].comparison_evaluation.score, 120)
            self.assertEqual(response.context['found_count'], 41)
            self.assertTrue(all(m.comparison_evaluation is None for m in list(response.context['page'])[1:]))
            self.assertContains(response, 'Epoch AI · ECI')
        response = self.client.get('/', {'benchmark':bench.pk,'configuration':'high','evaluated_only':'1'})
        self.assertEqual(response.context['found_count'], 1)
        self.assertEqual(response.context['page'][0].comparison_evaluation.score, 140)
        self.assertEqual(Evaluation.objects.filter(benchmark=bench).count(), 2)
        response = self.client.get('/', {'category':'image','sort':'purpose_desc'})
        self.assertTrue(all(m.category == 'image' for m in response.context['page']))

    def test_snapshot_import_is_additive_dry_run_and_idempotent(self):
        model = ModelVersion.objects.first()
        before = (Evaluation.objects.count(), Revision.objects.count(), Offer.objects.count())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'epoch-export').mkdir()
            metadata = []
            for filename in sorted(OWN_FILES):
                metadata.append({'source_file':filename,'benchmark':filename,'score_column':'Best score (across scorers)'})
                with (root/'epoch-export'/filename).open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['id','Model version','Best score (across scorers)','Started at']);writer.writeheader()
                    for mode,score in [('high','0.8'),('low','0.6')]: writer.writerow({'id':mode,'Model version':'exact-'+mode,'Best score (across scorers)':score,'Started at':'2026-09-19T00:00:00Z'})
            with (root/'epoch-export'/'benchmark_metadata.csv').open('w', newline='', encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=metadata[0]);writer.writeheader();writer.writerows(metadata)
            (root/'eci_scores.csv').write_text('Model,eci,eci_ci_low,eci_ci_high\nExact,150,148,152\n',encoding='utf-8')
            alias = {'catalog_slug':model.slug,'catalog_version':model.version,'status':'verified'}
            (root/'verified-alias-registry.json').write_text(json.dumps({'checked':'2026-09-20',
                'own_runs':[{**alias,'source_model':'exact-'+mode,'configuration':mode} for mode in ('high','low')],
                'eci':[{**alias,'source_model':'Exact'}]}),encoding='utf-8')
            call_command('import_epoch_snapshot',str(root),dry_run=True,stdout=StringIO())
            self.assertEqual(before, (Evaluation.objects.count(),Revision.objects.count(),Offer.objects.count()))
            call_command('import_epoch_snapshot',str(root),stdout=StringIO())
            self.assertEqual(Evaluation.objects.count(),before[0]+29)
            self.assertEqual(Evaluation.objects.filter(observation_key__isnull=False,configuration='high').count(),14)
            history = Revision.objects.count()
            call_command('import_epoch_snapshot',str(root),stdout=StringIO())
            self.assertEqual(Evaluation.objects.count(),before[0]+29)
            self.assertEqual(Revision.objects.count(),history)
            self.assertEqual(Offer.objects.count(),before[2])

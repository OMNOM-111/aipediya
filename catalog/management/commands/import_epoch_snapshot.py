"""Reviewed, additive Epoch observations. No external benchmark scores imported."""
import csv
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import (Access, Benchmark, Evaluation, ModelFamily, ModelVersion,
    Organization, PublicationRevision, ResearchRecord, ResearchRevision, Service, Source)
from .import_epoch_runs import RUNS

OWN_FILES = {
    'gpqa_diamond.csv', 'otis_mock_aime_2024_2025.csv', 'frontiermath.csv',
    'frontiermath_tier_4.csv', 'frontiermath_tiers_1_3_v2.csv', 'frontiermath_tier_4_v2.csv',
    'frontiermath_erdos.csv', 'swe_bench_verified.csv', 'math_level_5.csv',
    'simpleqa_verified.csv', 'chess_puzzles.csv', 'ebr_bench.csv',
    'mystery_game_puzzles.csv', 'mirrorcode.csv',
}


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Command(BaseCommand):
    help = 'Import reviewed Epoch own runs and official ECI, preserving configurations and history.'

    def add_arguments(self, parser):
        parser.add_argument('directory', help='Reviewed package with epoch-export and verified-alias-registry.json')
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(options['directory'])
        registry = json.loads((root / 'verified-alias-registry.json').read_text(encoding='utf-8-sig'))
        checked = date.fromisoformat(registry['checked'])
        snapshot = checked.isoformat()
        self.stats = dict(created_models=0, observations=0, created=0, enriched=0, unchanged=0, review=0, accepted=0, external_csvs_read=0)
        own_source, _ = Source.objects.get_or_create(url='https://epoch.ai/benchmarks', defaults={'title': 'Epoch AI · own benchmark runs', 'publisher': 'Epoch AI'})
        eci_source, _ = Source.objects.get_or_create(url='https://epoch.ai/eci', defaults={'title': 'Epoch AI · Epoch Capabilities Index', 'publisher': 'Epoch AI'})
        self.new_models(root, checked)
        models = {m.slug: m for m in ModelVersion.objects.filter(published=True)}
        self.correct_legacy_mapping(models)
        metadata = {r['source_file']: r for r in rows(root / 'epoch-export' / 'benchmark_metadata.csv') if r['source_file'] in OWN_FILES}
        metadata['frontiermath_erdos.csv'] = {'benchmark': 'FrontierMath Open Problems (Erdős)', 'score_column': 'Best score (across scorers)', 'release_date': ''}
        aliases = {r['source_model']: r for r in registry['own_runs']}
        for filename in sorted(OWN_FILES):
            path = root / 'epoch-export' / filename
            file_hash = digest(path)
            meta = metadata[filename]
            name, protocol = RUNS.get(filename, (meta['benchmark'], meta['benchmark'] + '; Epoch AI own run; best score across scorers'))
            benchmark, _ = Benchmark.objects.get_or_create(name=name, protocol=protocol, defaults={'category': 'text', 'unit': '%'})
            for row in rows(path):
                identity = aliases.get(row['Model version'])
                score = Decimal(row[meta['score_column']]) * 100
                if not score.is_finite() or not 0 <= score <= 100 or not row['id']:
                    raise CommandError(f'Invalid own-run score or ID: {filename}')
                model = self.resolve(identity, models)
                mode = identity['configuration'] if identity else 'unresolved'
                source_id = filename + ':' + row['id']
                observation_key = hashlib.sha256(f'epoch-own:{source_id}:{file_hash}'.encode()).hexdigest()
                if not model:
                    self.stage(observation_key, row, filename, identity, snapshot)
                    continue
                measured = date.fromisoformat(row['Started at'][:10]) if row.get('Started at') else None
                source = own_source
                details = {'ru': f"Собственный прогон Epoch AI; {meta['benchmark']}; версия: {row['Model version']}; режим: {mode}; исходный id: {row['id']}; файл: {filename}. CC BY 4.0, Epoch AI. Снимок {snapshot}. Показана колонка источника Best score (across scorers), не выбор лучшего режима AIpedia.",
                           'en': f"Epoch AI own run; {meta['benchmark']}; version: {row['Model version']}; mode: {mode}; source id: {row['id']}; file: {filename}. CC BY 4.0, Epoch AI. Snapshot {snapshot}. Source column Best score (across scorers), not AIpedia's selection of the best effort."}
                defaults = dict(model=model, benchmark=benchmark, score=score.quantize(Decimal('.001')), evaluator='Epoch AI', independent=True, public=True,
                    measured=measured, source=source, checked=checked, configuration=mode, source_model=row['Model version'],
                    source_record_id=source_id, snapshot=snapshot, source_sha256=file_hash, result_kind='independent', conditions=details)
                # Enrich the 45 historical observations in place only after an
                # exact source row ID + score match. Their IDs/values stay intact.
                legacy = Evaluation.objects.filter(model=model, benchmark=benchmark, observation_key__isnull=True, public=True, source=source)
                legacy = [e for e in legacy if e.score == defaults['score'] and row['id'] in json.dumps(e.conditions)]
                evaluation = self.publish(observation_key, defaults, legacy[0] if len(legacy) == 1 else None)
                old = ResearchRecord.objects.filter(external_id='epoch-own-run:' + source_id).first()
                if old and old.state != 'accepted':
                    before = {'state': old.state, 'review_reason': old.review_reason}
                    old.state = 'accepted'
                    old.review_reason = f'Published exact reviewed source version; configuration {mode}; evaluation {evaluation.pk}'[:300]
                    old.save(update_fields=['state', 'review_reason'])
                    ResearchRevision.objects.create(record=old, batch=f'Epoch {snapshot}', action='resolve_epoch_modes', before=before,
                        after={'state': old.state, 'review_reason': old.review_reason, 'evaluation': evaluation.pk, 'alias_evidence': identity})
                self.stats['accepted'] += 1
        aliases = {r['source_model']: r for r in registry['eci']}
        path = root / 'eci_scores.csv'
        file_hash = digest(path)
        benchmark, _ = Benchmark.objects.get_or_create(name='ECI', protocol='Epoch Capabilities Index; official model-group estimates', defaults={'category': 'text', 'unit': ''})
        for row in rows(path):
            identity = aliases.get(row['Model'])
            model = self.resolve(identity, models)
            key = hashlib.sha256(f'epoch-eci:{row["Model"]}:{file_hash}'.encode()).hexdigest()
            if not model:
                self.stage(key, row, 'eci_scores.csv', identity, snapshot)
                continue
            self.publish(key, dict(model=model, benchmark=benchmark, score=Decimal(row['eci']), evaluator='Epoch AI', independent=False, public=True,
                measured=None, source=eci_source, checked=checked, configuration='published model-group index', source_model=row['Model'],
                source_record_id=row['Model'], snapshot=snapshot, source_sha256=file_hash, result_kind='composite',
                confidence_low=Decimal(row['eci_ci_low']) if row['eci_ci_low'] else None,
                confidence_high=Decimal(row['eci_ci_high']) if row['eci_ci_high'] else None,
                conditions={'ru': 'Официальный ECI model scores, Epoch AI, CC BY 4.0. Составной индекс по собственным, сторонним и заявленным разработчиками результатам. 90% bootstrap-интервал. Не отдельный режим reasoning effort; date в выгрузке — дата выпуска модели, не измерения. Методика: https://epoch.ai/eci#documentation',
                            'en': 'Official ECI model scores, Epoch AI, CC BY 4.0. Composite of own, third-party and developer-reported results. 90% bootstrap interval. Not a per-effort score; export date is the model release date, not measurement date. Methodology: https://epoch.ai/eci#documentation'}))
            self.stats['accepted'] += 1
        if options['dry_run']:
            transaction.set_rollback(True)
        self.stdout.write(json.dumps({**self.stats, 'dry_run': options['dry_run'], 'snapshot': snapshot}, sort_keys=True))

    def resolve(self, identity, models):
        if not identity or identity['status'] != 'verified':
            return None
        model = models.get(identity['catalog_slug'])
        if not model or model.version != identity['catalog_version']:
            raise CommandError('Reviewed alias no longer matches catalog: ' + identity['source_model'])
        if model.entry_type != 'model':
            raise CommandError('Cannot attach model benchmark to a product')
        return model

    def stage(self, key, row, filename, identity, snapshot):
        self.stats['observations'] += 1
        self.stats['review'] += 1
        source_model = row.get('Model version') or row.get('Model')
        if identity:
            reason = f"{identity['status']}: {source_model}; " + (identity.get('identity_reason') or identity.get('reason') or '')
        else:
            reason = f'No exact catalog identity for {source_model} in reviewed aliases ({snapshot}); source row retained; verify version before publication'
        payload = {'source_file': filename, 'snapshot': snapshot, 'row': row, 'alias': identity}
        record, created = ResearchRecord.objects.get_or_create(external_id='epoch-snapshot:' + key,
            defaults={'batch': 'Epoch ' + snapshot, 'payload': payload, 'review_reason': reason[:300]})
        if created:
            ResearchRevision.objects.create(record=record, batch=record.batch, action='epoch_stage', before={}, after=payload)
        if not created and record.review_reason != reason[:300]:
            before = {'review_reason': record.review_reason}
            record.review_reason = reason[:300]
            record.save(update_fields=['review_reason'])
            ResearchRevision.objects.create(record=record, batch=record.batch, action='clarify_review', before=before, after={'review_reason': record.review_reason})
        if row.get('id'):
            old = ResearchRecord.objects.filter(external_id='epoch-own-run:' + filename + ':' + row['id'], state='review_required').first()
            if old and old.review_reason != reason[:300]:
                before = {'review_reason': old.review_reason}
                old.review_reason = reason[:300]
                old.save(update_fields=['review_reason'])
                ResearchRevision.objects.create(record=old, batch='Epoch '+snapshot, action='clarify_review', before=before, after={'review_reason': old.review_reason})

    def publish(self, key, defaults, legacy=None):
        self.stats['observations'] += 1
        existing = Evaluation.objects.filter(observation_key=key).first()
        if existing:
            for field in ('score', 'model', 'benchmark', 'configuration', 'source_model', 'source_sha256', 'public'):
                if getattr(existing, field) != defaults[field]:
                    raise CommandError('Immutable observation conflict: ' + key)
            self.stats['unchanged'] += 1
            return existing
        before = {}
        if legacy:
            before = {'evaluation': legacy.pk, 'score': str(legacy.score), 'conditions': legacy.conditions}
            for field in ('configuration', 'source_model', 'source_record_id', 'snapshot', 'source_sha256', 'result_kind'):
                setattr(legacy, field, defaults[field])
            legacy.observation_key = key
            legacy.save(update_fields=['configuration', 'source_model', 'source_record_id', 'snapshot',
                'source_sha256', 'result_kind', 'observation_key'])
            evaluation = legacy
            self.stats['enriched'] += 1
        else:
            evaluation = Evaluation.objects.create(observation_key=key, **defaults)
            self.stats['created'] += 1
        PublicationRevision.objects.create(entity_id=evaluation.model.research_entity_id or f'model:{evaluation.model_id}', model=evaluation.model,
            action='epoch_observation', source_record_ids=[evaluation.source_record_id], before=before,
            after={'evaluation': evaluation.pk, 'observation_key': key, 'score': str(evaluation.score), 'mode': evaluation.configuration, 'snapshot': evaluation.snapshot})
        staged = ResearchRecord.objects.filter(external_id='epoch-snapshot:' + key).first()
        if staged and staged.state != 'accepted':
            before = {'state': staged.state, 'review_reason': staged.review_reason}
            staged.state = 'accepted'
            staged.review_reason = f'Exact reviewed alias resolved; evaluation {evaluation.pk}'
            staged.save(update_fields=['state', 'review_reason'])
            ResearchRevision.objects.create(record=staged, batch=staged.batch, action='resolve_alias', before=before,
                after={'state': staged.state, 'review_reason': staged.review_reason})
        return evaluation

    def correct_legacy_mapping(self, models):
        target = models.get('deepseek-v4-pro-2026-04-24')
        if not target: return
        for evaluation in Evaluation.objects.filter(observation_key__isnull=True, evaluator='Epoch AI', public=True):
            if 'WUk3f44JhxtAJaSxi6gFZR' not in json.dumps(evaluation.conditions): continue
            if evaluation.model_id == target.pk: continue
            if evaluation.model.name != 'DeepSeek V4 Pro 0813':
                raise CommandError('Unexpected target of historical DeepSeek observation')
            previous = evaluation.model
            evidence = {'evaluation': evaluation.pk, 'score': str(evaluation.score), 'old_model': previous.slug,
                'new_model': target.slug, 'source_run_id': 'WUk3f44JhxtAJaSxi6gFZR',
                'reason': 'April 24 base model run predates August 13 version; pricing alias was not version identity',
                'evidence': ['https://epoch.ai/models/deepseek-v4-pro', 'https://epoch.ai/models/deepseek-v4-pro-0813']}
            evaluation.model = target
            evaluation.save(update_fields=['model'])
            for model in (previous, target):
                PublicationRevision.objects.create(entity_id=model.research_entity_id or f'model:{model.pk}', model=model,
                    action='correct_eval_identity', source_record_ids=['WUk3f44JhxtAJaSxi6gFZR'], before={'model': previous.slug}, after=evidence)

    def new_models(self, root, checked):
        path = root / 'verified-new-models.json'
        if not path.exists(): return
        for item in json.loads(path.read_text(encoding='utf-8-sig'))['models']:
            existing = ModelVersion.objects.filter(slug=item['slug']).first()
            if existing:
                if existing.version != item['version']: raise CommandError('Conflicting existing model version')
                continue
            source, _ = Source.objects.get_or_create(url=item['source_url'], defaults={'title': item['name'] + ' · official model documentation', 'publisher': item['developer']})
            developer = Organization.objects.get(name=item['developer'])
            family, _ = ModelFamily.objects.get_or_create(name=item['family'], developer=developer)
            model = ModelVersion.objects.create(family=family, name=item['name'], version=item['version'], slug=item['slug'],
                category=item['category'], tasks=item['tasks'], input_modalities=item['input_modalities'], output_modalities=item['output_modalities'],
                context=item.get('context'), released=item.get('released'), source=source, checked=checked, catalog_status=item.get('catalog_status', 'active'),
                description={'ru': f"{item['name']} — модель {item['developer']}. Точная версия: {item['version']}. Возможности и ограничения приведены в источнике.",
                             'en': f"{item['name']} is a model from {item['developer']}. Exact version: {item['version']}. See the source for capabilities and limitations."})
            if item.get('catalog_status') != 'archived':
                service, _ = Service.objects.get_or_create(name=item['name'] + ' API', provider=developer, kind='api', url=item['source_url'], defaults={'compute_location': 'cloud'})
                Access.objects.create(model=model, service=service, source=source, checked=checked)
            PublicationRevision.objects.create(entity_id=f'model:{model.pk}', model=model, action='verified_model', source_record_ids=[item['source_url']], before={}, after=item)
            self.stats['created_models'] += 1

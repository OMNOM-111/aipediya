import json
from datetime import date
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import ModelVersion, PublicationRevision
from catalog.chronology import renumber_chronologically


class Command(BaseCommand):
    help = 'Apply exact-version release evidence and rebuild chronological numbers atomically.'

    def add_arguments(self, parser):
        parser.add_argument('manifest')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, manifest, dry_run=False, **options):
        document = json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
        rows = document['models']
        slugs = [r['slug'] for r in rows]
        published = set(ModelVersion.objects.filter(published=True).values_list('slug', flat=True))
        if len(slugs) != len(set(slugs)) or set(slugs) != published:
            raise CommandError('Manifest must cover every current published slug exactly once; regenerate after data drift.')
        changed = 0
        with transaction.atomic():
            for row in rows:
                released = date.fromisoformat(row['released']) if row.get('released') else None
                if released and (released > date.today() or not row.get('source_url', '').startswith('https://') or not row.get('evidence')):
                    raise CommandError('Unverified or future release date: ' + row['slug'])
                if not released and not row.get('reason'):
                    raise CommandError('Missing reason for unknown release: ' + row['slug'])
                model = ModelVersion.objects.select_for_update().get(slug=row['slug'])
                evidence = {k: v for k, v in row.items() if k not in {'slug', 'released'}}
                if model.released == released and model.release_evidence == evidence:
                    continue
                before = {'released': str(model.released) if model.released else None, 'release_evidence': model.release_evidence}
                ModelVersion.objects.filter(pk=model.pk).update(released=released, release_evidence=evidence)
                PublicationRevision.objects.create(model=model, entity_id=model.research_entity_id or model.slug,
                    action='verify_release_date', before=before,
                    after={'released': str(released) if released else None, 'release_evidence': evidence})
                changed += 1
            result = renumber_chronologically()
            result.update({'dates_changed': changed, 'dry_run': dry_run})
            if dry_run:
                transaction.set_rollback(True)
        self.stdout.write(json.dumps(result))

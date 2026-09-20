import json
import tempfile
from datetime import date
from io import StringIO
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from catalog.models import ModelVersion, Organization, ModelFamily, Source, PublicationRevision


class ChronologyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = Source.objects.create(title='Fixture', publisher='Fixture', url='https://example.com/releases')
        developer = Organization.objects.create(name='Fixture', source=cls.source, checked=date(2026, 1, 1))
        cls.family = ModelFamily.objects.create(name='Fixture', developer=developer)

    def model(self, name, released=None):
        return ModelVersion.objects.create(name=name, slug=name.lower(), family=self.family, version='1',
            released=released, source=self.source, checked=date(2026, 1, 1))

    def test_backfilled_older_model_renumbers_without_changing_identity(self):
        newer = self.model('Astra', date(2026, 9, 1))
        newer_pk, newer_slug = newer.pk, newer.slug
        older = self.model('Older', date(2024, 1, 1))
        # Save the stale object: its old number now belongs to Older.
        newer.description = {'en': 'Updated description'}
        newer.save()
        newer.refresh_from_db()
        self.assertEqual((older.public_number, newer.public_number), (1, 2))
        self.assertEqual((newer.pk, newer.slug), (newer_pk, newer_slug))
        self.assertTrue(PublicationRevision.objects.filter(model=newer, action='renumber_chronology',
            before__public_number=1, after__public_number=2).exists())
        response = self.client.get('/')
        self.assertEqual(response.context['sort'], 'number_asc')
        self.assertEqual([m.slug for m in response.context['page']], ['older', 'astra'])
        self.assertContains(response, '2024-01-01')
        self.assertEqual(self.client.get('/models/' + newer_slug).status_code, 200)

    def test_same_day_uses_name_and_unknown_stays_last_both_directions(self):
        self.model('Zulu', date(2024, 1, 1))
        self.model('Alpha', date(2024, 1, 1))
        unknown = self.model('Undated')
        self.assertIsNone(unknown.public_number)
        for direction, expected in [('asc', ['alpha', 'zulu', 'undated']), ('desc', ['zulu', 'alpha', 'undated'])]:
            response = self.client.get('/', {'sort': 'number_' + direction})
            self.assertEqual([m.slug for m in response.context['page']], expected)
            self.assertContains(response, 'Дата выпуска не подтверждена')
        unknown.released = date(2023, 1, 1)
        unknown.save(update_fields=['released'])
        self.assertEqual(unknown.public_number, 1)

    def test_manifest_dry_run_idempotency_coverage_and_rollback(self):
        first = self.model('First')
        second = self.model('Second')
        document = {'models': [
            {'slug': 'first', 'released': '2020-01-01', 'source_url': 'https://example.com/releases', 'evidence': 'Exact release'},
            {'slug': 'second', 'released': None, 'reason': 'No dated announcement for exact version'}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dates.json'
            path.write_text(json.dumps(document))
            before = PublicationRevision.objects.count()
            call_command('apply_release_chronology', str(path), dry_run=True, stdout=StringIO())
            first.refresh_from_db()
            self.assertIsNone(first.released)
            self.assertEqual(PublicationRevision.objects.count(), before)
            call_command('apply_release_chronology', str(path), stdout=StringIO())
            first.refresh_from_db(); second.refresh_from_db()
            self.assertEqual(first.public_number, 1)
            self.assertIsNone(second.public_number)
            count = PublicationRevision.objects.count()
            call_command('apply_release_chronology', str(path), stdout=StringIO())
            self.assertEqual(PublicationRevision.objects.count(), count)
            document['models'][0]['released'] = '2019-01-01'
            document['models'][1] = {'slug': 'second', 'released': '2099-01-01'}
            path.write_text(json.dumps(document))
            with self.assertRaises(CommandError):
                call_command('apply_release_chronology', str(path), stdout=StringIO())
            first.refresh_from_db()
            self.assertEqual(first.released, date(2020, 1, 1))
            document['models'].pop()
            path.write_text(json.dumps(document))
            with self.assertRaises(CommandError):
                call_command('apply_release_chronology', str(path), stdout=StringIO())

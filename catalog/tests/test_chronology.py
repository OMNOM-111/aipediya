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
        older.refresh_from_db(); newer.refresh_from_db()
        # Numbers follow assignment order (each new entry takes the next free
        # number), never the release date, and are never recomputed.
        self.assertEqual((newer.public_number, older.public_number), (1, 2))
        # Refining data on an existing entry never changes its permanent number.
        newer.description = {'en': 'Updated description'}
        newer.save()
        newer.refresh_from_db()
        self.assertEqual(newer.public_number, 1)
        self.assertEqual((newer.pk, newer.slug), (newer_pk, newer_slug))
        self.assertTrue(PublicationRevision.objects.filter(model=newer, action='assign_catalog_number',
            after__public_number=1).exists())
        # The clean catalogue opens newest-first by release date, independent of
        # the permanent numbers.
        response = self.client.get('/')
        self.assertEqual(response.context['sort'], 'release_desc')
        self.assertEqual([m.slug for m in response.context['page']], ['astra', 'older'])
        self.assertContains(response, '2024-01-01')
        self.assertEqual(self.client.get('/models/' + newer_slug).status_code, 200)

    def test_same_day_uses_name_and_unknown_stays_last_both_directions(self):
        self.model('Zulu', date(2024, 1, 1))
        self.model('Alpha', date(2025, 1, 1))
        undated = self.model('Undated')
        # Every published entry now carries a permanent number, dated or not.
        undated.refresh_from_db()
        self.assertIsNotNone(undated.public_number)
        number_before = undated.public_number
        for direction, expected in [('desc', ['alpha', 'zulu', 'undated']), ('asc', ['zulu', 'alpha', 'undated'])]:
            response = self.client.get('/', {'sort': 'release_' + direction, 'lang': 'ru'})
            self.assertEqual([m.slug for m in response.context['page']], expected)
            self.assertContains(response, 'Дата выпуска не подтверждена')
        # An approximate date sorts the entry by that date but keeps its number.
        undated.approx_released = date(2023, 6, 1)
        undated.approx_precision = 'month'
        undated.save(update_fields=['approx_released', 'approx_precision'])
        undated.refresh_from_db()
        self.assertEqual(undated.public_number, number_before)
        response = self.client.get('/', {'sort': 'release_asc', 'lang': 'ru'})
        self.assertEqual([m.slug for m in response.context['page']], ['undated', 'zulu', 'alpha'])

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
            self.assertEqual(second.public_number, 2)
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

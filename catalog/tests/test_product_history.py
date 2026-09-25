from django.test import SimpleTestCase, override_settings


class ProductHistoryTests(SimpleTestCase):
    def test_local_history_and_sources(self):
        page = self.client.get("/ru/history/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "История развития сайта")
        self.assertContains(page, "GSD-1.0")
        self.assertContains(page, "Каноническая база каталога")
        self.assertContains(page, "ed103a3ff163")
        self.assertContains(page, 'aria-haspopup="dialog"', count=4)
        self.assertContains(page, 'class="ph-environment ph-local"', count=1)
        self.assertContains(page, 'class="ph-environment ph-production"', count=1)
        self.assertNotContains(page, 'class="ph-environment ph-git"')
        self.assertContains(page, 'class="ph-git-detail"', count=1)
        self.assertEqual(page["Cache-Control"], "private, no-store")
        self.assertEqual(self.client.get("/ru/history/source/release").status_code, 200)
        self.assertEqual(self.client.get("/ru/history/source/secret").status_code, 404)

    def test_english_and_rtl_routes(self):
        self.assertContains(self.client.get("/history/"), "Site development")
        arabic = self.client.get("/ar/history/")
        self.assertEqual(arabic.status_code, 200)
        self.assertContains(arabic, 'dir="rtl"')
        self.assertContains(arabic, 'lang="en"')

    @override_settings(AIPEDIA_ENV="production", SECURE_SSL_REDIRECT=False)
    def test_history_is_private_in_production(self):
        for url in ("/history/", "/ru/history/", "/history/source/release"):
            self.assertEqual(self.client.get(url, secure=True).status_code, 404)

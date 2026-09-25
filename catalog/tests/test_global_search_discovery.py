"""GSD-1.0: locale URLs, readiness, sitemap graph, facets, structured data,
datasets, hubs and the discovery outbox."""
import csv
import io
import json
import re
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog import datasets, readiness
from catalog.i18n import SUPPORTED_CODES
from catalog.locale_urls import URL_CODE, localize, split
from catalog.models import ContentTranslation, DiscoveryEvent, ModelVersion, Offer, Tool
from catalog.seo import json_ld_script, sitemap_urlsets
from catalog.translation_pipeline import source_hash


def public_model():
    return ModelVersion.objects.filter(published=True, entry_type="model").order_by("pk").first()


def ensure_tool():
    tool = Tool.objects.filter(published=True).first()
    if tool:
        return tool
    model = public_model()
    return Tool.objects.create(
        name="Fixture Coding Tool", slug="fixture-coding-tool", version="Fixture Coding Tool",
        developer=model.family.developer, category="coding_agent", purposes=["code"],
        description={"en": "A coding agent fixture.", "ru": "Тестовый агент для кода."},
        local_execution="hybrid", source=model.source, checked=model.checked,
    )


def make_hidden(template, slug="hidden-candidate"):
    hidden = ModelVersion.objects.create(
        family=template.family, name="Secret Candidate", slug=slug, version="Secret Candidate",
        category=template.category, tasks=["code"], description={"en": "Hidden research text", "ru": "Скрыто"},
        source=template.source, checked=template.checked, published=False, open_weights=True,
        context=2_000_000,
    )
    return hidden


@override_settings(AIPEDIA_INDEXING_ALLOWED=True,
                   NAVER_SITE_VERIFICATION="9c99ee04834598097c2ba9b6a809819418e5d74d")
class NaverVerificationMetaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_naver_token_is_in_server_rendered_head_without_changing_seo_signals(self):
        response = self.client.get("/")
        html = response.content.decode()
        head = html.split("</head>", 1)[0]

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<meta name="naver-site-verification" content="9c99ee04834598097c2ba9b6a809819418e5d74d">',
            head,
        )
        self.assertEqual(html.count('name="naver-site-verification"'), 1)
        self.assertIn("<title>", head)
        self.assertIn('name="description"', head)
        self.assertIn('rel="canonical" href="https://aipediya.com/"', head)
        self.assertIn('hreflang="x-default" href="https://aipediya.com/"', head)


class LocaleUrlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_builder_and_split_are_inverse_for_every_locale(self):
        for code in SUPPORTED_CODES:
            for neutral in ("/", "/tools/", "/models/x", "/methodology", "/collections/coding-models"):
                path = localize(neutral, code)
                lang, back, redirect = split(path)
                self.assertEqual(back, neutral)
                self.assertIsNone(redirect)
                self.assertEqual(lang, None if code == "en" else code)
        self.assertEqual(localize("/", "zh-Hans"), "/zh-hans/")
        self.assertEqual(localize("/tools/", "pt-BR"), "/pt-br/tools/")

    def test_every_route_type_legacy_redirect_is_single_hop(self):
        model = public_model()
        tool = ensure_tool()
        cases = {
            "/?lang=ru": "/ru/",
            "/?lang=en": "/",
            "/?lang=zh-CN&kind=tool&sort=name_asc": "/zh-hans/tools/?sort=name_asc",
            "/?kind=model&page=1": "/",
            f"/models/{model.slug}?lang=de&kind=model&page=1&tab=pricing": f"/de/models/{model.slug}?tab=pricing",
            f"/tools/{tool.slug}?lang=ar&kind=tool": f"/ar/tools/{tool.slug}",
            "/privacy?lang=uk": "/uk/privacy",
            "/ru/?lang=de": "/ru/",
            "/zh-Hans/": "/zh-hans/",
            "/pt_BR/tools/": "/pt-br/tools/",
            "/zh-cn/": "/zh-hans/",
            "/en/": "/",
            f"/en/models/{model.slug}": f"/models/{model.slug}",
            "/ru": "/ru/",
        }
        for source, target in cases.items():
            response = self.client.get(source)
            self.assertEqual(response.status_code, 301, source)
            self.assertEqual(response["Location"], target, source)
            final = self.client.get(target)
            self.assertIn(final.status_code, (200,), f"{source} -> {target} is not a final 200")

    def test_unknown_and_hidden_are_404_never_redirected_home(self):
        hidden = make_hidden(public_model())
        for path in ("/xx/", "/ru/admin/", "/ru/robots.txt", f"/models/{hidden.slug}",
                     f"/models/{hidden.slug}?lang=ru", f"/ru/models/{hidden.slug}", "/models/not-real?lang=ru",
                     "/collections/not-a-hub", "/be/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)

    def test_explicit_url_ignores_cookie_accept_language_country_and_user_agent(self):
        self.client.cookies["aipedia_lang"] = "fa"
        response = self.client.get("/ko/tools/", HTTP_ACCEPT_LANGUAGE="de", HTTP_CF_IPCOUNTRY="RU",
                                   HTTP_USER_AGENT="Googlebot/2.1")
        self.assertEqual(response.context["lang"], "ko")
        self.assertContains(response, '<html lang="ko" dir="ltr">')
        self.assertNotIn("Cookie", response.get("Vary", ""))

    def test_switcher_keeps_ux_params_and_drops_fragments(self):
        model = public_model()
        response = self.client.get(f"/models/{model.slug}?tab=pricing")
        self.assertContains(response, f'href="/ja/models/{model.slug}?tab=pricing"')
        rows = self.client.get("/", {"partial": "rows", "page": 1}).content.decode()
        self.assertNotIn("partial=rows", rows)


@override_settings(AIPEDIA_INDEXING_ALLOWED=True)
class ReadinessAndSignalsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_registry_reasons_missing_outdated_and_manual(self):
        model = public_model()
        model.description = {**model.description, "en": "Fresh English", "ru": "Свежий", "de": "Veraltet"}
        model.save()
        ContentTranslation.objects.update_or_create(
            entity_type="model", object_id=model.pk, field="description", language="de",
            defaults={"source_hash": source_hash("Old English"), "text": "Veraltet", "state": "outdated"},
        )
        model.refresh_from_db()
        result = readiness.entity_readiness(model)
        self.assertEqual(result["en"].status, readiness.INDEXABLE)
        self.assertEqual(result["ru"].status, readiness.INDEXABLE)
        self.assertEqual(result["de"].status, readiness.NOT_READY)
        self.assertIn(result["de"].reason, ("outdated-translation-description", "missing-translation-description"))
        self.assertEqual(result["ja"].reason, "missing-translation-description")
        hidden = make_hidden(model)
        self.assertEqual(readiness.entity_readiness(hidden)["en"].status, readiness.NOT_PUBLIC)

    def test_not_ready_locale_is_noindex_and_absent_from_alternates_and_sitemap(self):
        model = public_model()
        model.description = {"en": "Only English", "ru": "Только русский"}
        model.save()
        page = self.client.get(f"/ja/models/{model.slug}")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="robots" content="noindex,follow"')
        self.assertContains(page, 'lang="en">Only English')  # fallback is marked, not passed off as Japanese
        english = self.client.get(f"/models/{model.slug}")
        self.assertNotContains(english, f'hreflang="ja" href="https://aipediya.com/ja/models/{model.slug}"')
        self.assertContains(english, f'hreflang="ru" href="https://aipediya.com/ru/models/{model.slug}"')
        locs = {entry["loc"] for entry in sitemap_urlsets()["ja"]}
        self.assertNotIn(f"https://aipediya.com/ja/models/{model.slug}", locs)

    def test_hidden_records_never_leak_into_any_channel(self):
        hidden = make_hidden(public_model())
        tool = ensure_tool()
        tool.model_links.create(model=hidden, source=tool.source, checked=tool.checked)
        everything = json.dumps(sitemap_urlsets(), default=str)
        self.assertNotIn(hidden.slug, everything)
        for kind in ("models", "tools"):
            for fmt in ("json", "csv"):
                self.assertNotIn(hidden.slug, datasets.build(kind, fmt).decode())
                self.assertNotIn("Secret Candidate", datasets.build(kind, fmt).decode())
        for path in ("/", "/tools/", f"/tools/{tool.slug}", "/collections/open-weight-models",
                     "/collections/long-context-models", "/collections/coding-models", "/?q=Secret"):
            self.assertNotContains(self.client.get(path), "Secret Candidate", msg_prefix=path)
        self.assertFalse(DiscoveryEvent.objects.filter(record_id=hidden.slug).exists())

    def test_single_h1_lang_dir_title_and_description_for_rtl_and_cjk(self):
        model = public_model()
        for code in ("ar", "fa", "zh-Hans", "en", "ru"):
            html = self.client.get(localize(f"/models/{model.slug}", code)).content.decode()
            self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1, code)
            want = "rtl" if code in ("ar", "fa") else "ltr"
            self.assertIn(f'<html lang="{code}" dir="{want}">', html)
            self.assertRegex(html, r'<meta name="description" content="[^"]+">')

    def test_listing_signals_filters_pagination_and_partials(self):
        filtered = self.client.get("/tools/?platform=cli&sort=name_asc")
        self.assertContains(filtered, 'name="robots" content="noindex,follow"')
        self.assertNotContains(filtered, 'rel="canonical"')
        entity = public_model()
        with_params = self.client.get(f"/models/{entity.slug}?q=x&sort=name_asc&tab=pricing")
        self.assertContains(with_params, f'rel="canonical" href="https://aipediya.com/models/{entity.slug}"')
        partial = self.client.get("/", {"partial": "rows"})
        self.assertEqual(partial["X-Robots-Tag"], "noindex")
        self.assertNotIn("partial=", re.sub(r'data-next-url="[^"]*"', "", partial.content.decode()))
        self.assertEqual(self.client.get("/", {"page": "999"}).status_code, 404)

    def test_robots_production_blocks_only_facets(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /*?q=", body)
        self.assertIn("Disallow: /*&sort=", body)
        self.assertIn("Disallow: /*?partial=", body)
        self.assertNotIn("lang=", body)
        from catalog.views import robots_allows
        allowed = ("/", "/ru/", "/?page=2", "/ru/tools/?page=2", "/tools/?page=3", "/models/x", "/ja/tools/y",
                   "/collections/coding-models?page=2", "/methodology", "/sitemap.xml")
        allowed += ("/ru/models/x?page=2", "/tools/x?page=4")
        blocked = ("/?sort=name_asc", "/ru/?q=gpt", "/models/x?tab=pricing", "/ru/models/x?page=2&tab=checks",
                   "/tools/?page=2&sort=name_asc", "/ru/tools/?page=2&platform=cli", "/?partial=rows", "/admin/")
        for path in allowed:
            self.assertTrue(robots_allows(path), path)
        for path in blocked:
            self.assertFalse(robots_allows(path), path)
        self.assertNotIn("Disallow: /*?\n", body)

    def test_canonical_never_uses_request_host(self):
        response = self.client.get("/", HTTP_HOST="evil.example")
        if response.status_code == 200:
            self.assertNotContains(response, "evil.example")

    def test_sitemap_graph_is_reciprocal_unique_and_within_limits(self):
        sets = sitemap_urlsets()
        seen = set()
        for lang, entries in sets.items():
            for entry in entries:
                self.assertNotIn(entry["loc"], seen)
                seen.add(entry["loc"])
                urls = [url for _code, url in entry["alternates"]]
                self.assertIn(entry["loc"], urls)
                for url in urls:
                    self.assertTrue(url.startswith("https://aipediya.com/"))
        # Reciprocity: every alternate of a page lists the same alternate set.
        by_loc = {entry["loc"]: entry for entries in sets.values() for entry in entries}
        for entry in by_loc.values():
            for _code, url in entry["alternates"]:
                self.assertEqual(by_loc[url]["alternates"], entry["alternates"])
        index = self.client.get("/sitemap.xml").content.decode()
        for code in SUPPORTED_CODES:
            if sets[code]:
                self.assertIn(f"/sitemaps/{URL_CODE[code]}.xml", index)
                body = self.client.get(f"/sitemaps/{URL_CODE[code]}.xml").content
                self.assertLess(len(body), 50 * 1024 * 1024)
                self.assertNotIn(b"localhost", body)
                self.assertNotIn(b"127.0.0.1", body)
        self.assertEqual(self.client.get("/sitemaps/xx.xml").status_code, 404)

    def test_sitemap_lastmod_does_not_change_on_page_view(self):
        before = self.client.get("/sitemaps/en.xml").content
        self.client.get("/")
        self.client.get(f"/models/{public_model().slug}")
        self.assertEqual(before, self.client.get("/sitemaps/en.xml").content)

    def test_json_ld_escaping_and_types(self):
        payload = json_ld_script({"name": "</script><script>alert(1)</script>&"})
        self.assertNotIn("</script>", payload)
        self.assertNotIn("<", payload)
        self.assertEqual(json.loads(payload)["name"], "</script><script>alert(1)</script>&")
        html = self.client.get(f"/models/{public_model().slug}").content.decode()
        blocks = [json.loads(block) for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html)]
        types = {block["@type"] for block in blocks}
        self.assertEqual(types, {"Organization", "BreadcrumbList"})
        self.assertNotIn("aggregateRating", html)
        self.assertNotIn('"Review"', html)
        dataset = self.client.get("/datasets/models").content.decode()
        blocks = [json.loads(block) for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', dataset)]
        ds = next(block for block in blocks if block["@type"] == "Dataset")
        self.assertNotIn("license", ds)
        self.assertEqual({item["@type"] for item in ds["distribution"]}, {"DataDownload"})
        self.assertEqual(ds["includedInDataCatalog"]["@type"], "DataCatalog")

    def test_local_is_never_indexable(self):
        with self.settings(AIPEDIA_INDEXING_ALLOWED=False):
            self.assertEqual(self.client.get("/robots.txt").content.decode(), "User-agent: *\nDisallow: /\n")
            self.assertEqual(self.client.get("/")["X-Robots-Tag"], "noindex, nofollow")

    def test_methodology_is_linked_and_localized_everywhere(self):
        home = self.client.get("/uk/")
        self.assertContains(home, 'href="/uk/methodology"')
        for code in SUPPORTED_CODES:
            response = self.client.get(localize("/methodology", code))
            self.assertEqual(response.status_code, 200)
            if code != "en":
                self.assertNotRegex(response.content.decode(), r'<(p|h2) lang="en">', msg=code)
            self.assertContains(response, 'rel="canonical"', msg_prefix=code)
        body = self.client.get("/methodology").content.decode()
        self.assertIn("does not calculate its own rating", body)
        self.assertIn("no automatic daily monitoring", body)


class DatasetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_counts_allowlist_and_relations(self):
        models = datasets.records("models")
        tools = datasets.records("tools")
        self.assertEqual(len(models), readiness.public_models().count())
        self.assertEqual(len(tools), readiness.public_tools().count())
        allowed = {name for name, _t, _m in datasets.MODEL_FIELDS}
        for row in models:
            self.assertEqual(set(row), allowed)
            self.assertNotIn("description", row)
        public_slugs = set(readiness.public_models().values_list("slug", flat=True))
        for row in tools:
            self.assertTrue(set(row["supported_models"]) <= public_slugs)

    def test_deterministic_and_checksums_match_downloads(self):
        self.assertEqual(datasets.manifest(), datasets.manifest())
        manifest = self.client.get("/datasets/manifest.json").json()
        for kind, info in datasets.DATASETS.items():
            for fmt in ("json", "csv"):
                response = self.client.get(f"/datasets/{info['slug']}.{fmt}")
                self.assertEqual(response.status_code, 200)
                import hashlib
                self.assertEqual(hashlib.sha256(response.content).hexdigest(),
                                 manifest["files"][f"{info['slug']}.{fmt}"]["sha256"])

    def test_csv_formula_injection_is_neutralized(self):
        model = public_model()
        offer = Offer.objects.filter(model=model).first() or Offer.objects.first()
        ModelVersion.objects.filter(pk=model.pk)  # no bulk updates: use save()
        model.name = "=HYPERLINK(\"http://x\")"
        model.save()
        rows = list(csv.DictReader(io.StringIO(datasets.as_csv("models").decode())))
        row = next(item for item in rows if item["record_id"] == model.slug)
        self.assertTrue(row["name"].startswith("'="))
        self.assertEqual(json.loads(datasets.as_json("models"))["records"][0].keys(),
                         json.loads(datasets.as_json("models"))["records"][0].keys())
        self.assertIsNotNone(offer)

    def test_unknown_is_null_not_zero(self):
        for row in datasets.records("models"):
            if row["context_window_tokens"] is None:
                return
        self.skipTest("seed has no model with unknown context")

    @override_settings(AIPEDIA_DATASETS_PUBLIC=False)
    def test_publication_gate(self):
        self.assertEqual(self.client.get("/datasets/models").status_code, 404)
        self.assertEqual(self.client.get("/datasets/aipediya-ai-tools.csv").status_code, 404)
        self.assertEqual(self.client.get("/datasets/manifest.json").status_code, 404)


@override_settings(AIPEDIA_INDEXING_ALLOWED=True)
class HubTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def test_registry_is_finite_and_thin_hubs_are_noindex(self):
        from catalog.hubs import HUBS, MIN_ENTRIES, members, status
        self.assertLessEqual(len(HUBS), 10)
        for hub in HUBS.values():
            count = len(members(hub))
            state, reason = status(hub, "en", count)
            response = self.client.get(f"/collections/{hub.slug}")
            self.assertEqual(response.status_code, 200)
            if count < MIN_ENTRIES:
                self.assertEqual(state, readiness.NOT_READY)
                self.assertContains(response, 'name="robots" content="noindex,follow"')
            else:
                self.assertContains(response, f'rel="canonical" href="https://aipediya.com/collections/{hub.slug}"')

    def test_membership_uses_published_records_only(self):
        from catalog.hubs import HUBS, members
        hidden = make_hidden(public_model())
        for hub in HUBS.values():
            self.assertNotIn(hidden.pk, members(hub))


class DiscoveryOutboxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def setUp(self):
        DiscoveryEvent.objects.all().delete()

    def test_get_requests_never_enqueue(self):
        model = public_model()
        for path in ("/", f"/models/{model.slug}", "/sitemap.xml", "/sitemaps/en.xml", "/datasets/models"):
            self.client.get(path)
        self.assertEqual(DiscoveryEvent.objects.count(), 0)

    def test_update_enqueues_ready_locales_once_dedup(self):
        model = public_model()
        model.context = (model.context or 0) + 1
        model.save()
        model.context += 1
        model.save()
        urls = list(DiscoveryEvent.objects.filter(state="pending").values_list("url", flat=True))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn(f"https://aipediya.com/models/{model.slug}", urls)
        self.assertEqual(len(urls), len(readiness.ready_locales(model)))

    def test_unpublish_keeps_previously_public_urls_as_removals(self):
        model = public_model()
        before = readiness.ready_locales(model)
        model.published = False
        model.save()
        removals = DiscoveryEvent.objects.filter(action="remove", record_id=model.slug)
        self.assertEqual(removals.count(), len(before))
        self.assertTrue(all(event.reason == "unpublished" for event in removals))

    def test_translation_change_notifies_only_that_locale(self):
        model = public_model()
        english = model.description["en"]
        model.description = {**model.description, "it": "Descrizione"}
        model._aipedia_translation_write = True
        model.save()
        DiscoveryEvent.objects.all().delete()
        ContentTranslation.objects.update_or_create(
            entity_type="model", object_id=model.pk, field="description", language="it",
            defaults={"source_hash": source_hash(english), "text": "Descrizione", "state": "current"},
        )
        events = list(DiscoveryEvent.objects.all())
        self.assertTrue(all(event.lang == "it" for event in events))
        self.assertLessEqual(len(events), 1)

    def test_price_change_is_significant(self):
        offer = Offer.objects.filter(model__published=True, model__entry_type="model").first()
        offer.amount = (offer.amount or 0) + 1
        offer.save()
        self.assertTrue(DiscoveryEvent.objects.filter(record_id=offer.model.slug, reason="offer-changed").exists())


class DispatcherTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)

    def setUp(self):
        DiscoveryEvent.objects.all().delete()
        from catalog.discovery import enqueue
        enqueue("/models/a", "en", "upsert", "created", "model", "a")
        enqueue("/models/b", "ru", "remove", "unpublished", "model", "b")
        DiscoveryEvent.objects.create(url="https://evil.example/x", action="upsert", reason="manual")

    def run_dispatch(self, status, probe=None, **extra):
        from catalog.management.commands import indexnow_dispatch as module
        calls = []

        def fake_post(url, payload, timeout=20):
            calls.append(json.loads(payload))
            return status, None

        with override_settings(AIPEDIA_ENV="production", AIPEDIA_INDEXNOW_ENABLED=True,
                               AIPEDIA_INDEXNOW_KEY="0123456789abcdef"), \
                mock.patch.object(module.Command, "post", staticmethod(fake_post)), \
                mock.patch.object(module.Command, "probe", staticmethod(probe or (lambda url, timeout=15: 200 if url.endswith("/a") else 404))):
            call_command("indexnow_dispatch", "--send", **extra)
        return calls

    def test_local_never_sends(self):
        from catalog.management.commands import indexnow_dispatch as module
        with mock.patch.object(module.Command, "post") as post:
            call_command("indexnow_dispatch", "--send")
        post.assert_not_called()
        self.assertEqual(DiscoveryEvent.objects.filter(state="pending").count(), 3)

    def test_accepted_marks_sent_and_host_allowlist(self):
        calls = self.run_dispatch(202)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sorted(calls[0]["urlList"]),
                         ["https://aipediya.com/models/a", "https://aipediya.com/ru/models/b"])
        self.assertEqual(calls[0]["host"], "aipediya.com")
        # The key file must sit at the host root so it authorises every URL.
        self.assertEqual(calls[0]["keyLocation"], "https://aipediya.com/0123456789abcdef.txt")
        self.assertEqual(DiscoveryEvent.objects.get(url="https://evil.example/x").state, "skipped")
        self.assertEqual(DiscoveryEvent.objects.filter(state="sent").count(), 2)
        # Idempotent: a second run sends nothing.
        self.assertEqual(self.run_dispatch(200), [])

    def test_live_gate_defers_until_production_matches(self):
        self.run_dispatch(200, probe=lambda url, timeout=15: 404)
        self.assertEqual(DiscoveryEvent.objects.get(url="https://aipediya.com/models/a").state, "pending")
        self.assertEqual(DiscoveryEvent.objects.get(url="https://aipediya.com/ru/models/b").state, "sent")

    def test_retry_and_failure_codes(self):
        self.run_dispatch(429)
        event = DiscoveryEvent.objects.get(url="https://aipediya.com/models/a")
        self.assertEqual((event.state, event.attempts, event.last_status), ("pending", 1, 429))
        DiscoveryEvent.objects.filter(state="pending").update(next_attempt=None)
        self.run_dispatch(503)
        DiscoveryEvent.objects.filter(state="pending").update(next_attempt=None)
        self.run_dispatch(422)
        self.assertEqual(DiscoveryEvent.objects.get(url="https://aipediya.com/models/a").state, "failed")

    def test_forbidden_aborts_and_keeps_pending(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.run_dispatch(403)
        self.assertEqual(DiscoveryEvent.objects.get(url="https://aipediya.com/models/a").state, "pending")

    def test_bounded_retries(self):
        for _ in range(3):
            DiscoveryEvent.objects.filter(state="pending").update(next_attempt=None)
            self.run_dispatch(500, **{"max_attempts": 3})
        self.assertEqual(DiscoveryEvent.objects.get(url="https://aipediya.com/models/a").state, "failed")


class BrowserContractRegressionTests(TestCase):
    """Defects found in GSD-1.0 browser QA."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        template = public_model()
        ModelVersion.objects.bulk_create([
            ModelVersion(family=template.family, name=f"Paging {n}", slug=f"paging-{n}", version=f"Paging {n}",
                         category=template.category, tasks=template.tasks, description=template.description,
                         source=template.source, checked=template.checked)
            for n in range(210)
        ])

    def test_prev_next_links_are_well_formed(self):
        html = self.client.get("/pl/?page=2").content.decode()
        self.assertIn('<link rel="prev" href="/pl/">', html)
        self.assertIn('<link rel="next" href="/pl/?page=3">', html)
        self.assertNotIn("/pl//pl/", html)

    def test_panel_title_header_is_ascii_safe(self):
        from urllib.parse import unquote
        response = self.client.get(f"/ru/models/{public_model().slug}", {"partial": "panel"})
        header = response["X-Aipedia-Title"]
        header.encode("ascii")
        self.assertIn("AI-модель", unquote(header))

    def test_head_requests_are_allowed(self):
        self.assertEqual(self.client.head("/ru/").status_code, 200)


def ld_blocks(html):
    return [json.loads(block) for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]


@override_settings(AIPEDIA_INDEXING_ALLOWED=True)
class StructuredDataAndSitemapReconciliationTests(TestCase):
    """GSD-1.0 reconciliation: every schema type where required, valid and
    visible; every indexable page in the sitemap and vice versa."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        cls.tool = ensure_tool()

    def assert_breadcrumb(self, html, blocks, canonical):
        crumbs = [block for block in blocks if block["@type"] == "BreadcrumbList"]
        self.assertEqual(len(crumbs), 1)
        items = crumbs[0]["itemListElement"]
        self.assertEqual([item["position"] for item in items], list(range(1, len(items) + 1)))
        self.assertEqual(items[-1]["item"], canonical)
        visible = re.search(r'<nav class="breadcrumbs"[^>]*>(.*?)</nav>', html, re.S)
        self.assertIsNotNone(visible, "BreadcrumbList without a visible breadcrumb")
        for item in items:
            self.assertTrue(item["name"])
            self.assertIn(escape_html(item["name"]), visible.group(1))

    def test_structured_data_matrix(self):
        model = public_model()
        pages = {
            "/": {"Organization"},
            "/tools/": {"Organization"},
            f"/models/{model.slug}": {"Organization", "BreadcrumbList"},
            f"/ru/tools/{self.tool.slug}": {"Organization", "BreadcrumbList"},
            "/methodology": {"Organization", "BreadcrumbList"},
            "/collections/": {"Organization", "BreadcrumbList"},
            "/ar/collections/open-weight-models": {"Organization", "BreadcrumbList"},
            "/datasets/": {"Organization", "BreadcrumbList", "DataCatalog"},
            "/datasets/models": {"Organization", "BreadcrumbList", "Dataset"},
            "/datasets/tools": {"Organization", "BreadcrumbList", "Dataset"},
        }
        for path, expected in pages.items():
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            html = response.content.decode()
            blocks = ld_blocks(html)
            self.assertEqual({block["@type"] for block in blocks}, expected, path)
            for block in blocks:
                self.assertEqual(block["@context"], "https://schema.org")
                self.assertNotIn("aggregateRating", json.dumps(block))
                self.assertNotIn("review", json.dumps(block).lower())
            org = next(block for block in blocks if block["@type"] == "Organization")
            self.assertEqual(org["name"], "AIpediya")
            self.assertEqual(org["url"], "https://aipediya.com/")
            self.assertTrue(org["logo"].endswith("/static/brand-512.png"))
            if "BreadcrumbList" in expected:
                self.assert_breadcrumb(html, blocks, "https://aipediya.com" + path)
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find("brand-512.png"))
        self.assertIsNotNone(finders.find("share-card.png"))

    def test_dataset_datacatalog_and_datadownload_are_valid(self):
        manifest = self.client.get("/datasets/manifest.json").json()
        catalog = next(b for b in ld_blocks(self.client.get("/datasets/").content.decode()) if b["@type"] == "DataCatalog")
        self.assertEqual(catalog["url"], "https://aipediya.com/datasets/")
        self.assertEqual({item["@type"] for item in catalog["dataset"]}, {"Dataset"})
        self.assertEqual(len(catalog["dataset"]), 2)
        for kind, info in datasets.DATASETS.items():
            html = self.client.get(f"/datasets/{kind}").content.decode()
            ds = next(b for b in ld_blocks(html) if b["@type"] == "Dataset")
            self.assertEqual(ds["name"], info["name"])
            self.assertIn(info["name"], html)  # visible
            self.assertGreaterEqual(len(ds["description"]), 50)
            self.assertLessEqual(len(ds["description"]), 5000)
            self.assertEqual(ds["url"], f"https://aipediya.com/datasets/{kind}")
            self.assertEqual(ds["creator"]["@type"], "Organization")
            self.assertEqual(ds["includedInDataCatalog"]["@type"], "DataCatalog")
            self.assertNotIn("license", ds)  # owner has not granted one
            self.assertEqual(ds["version"], manifest["files"][f"{info['slug']}.json"]["dataset_version"])
            formats = {}
            for dist in ds["distribution"]:
                self.assertEqual(dist["@type"], "DataDownload")
                path = dist["contentUrl"].replace("https://aipediya.com", "")
                self.assertIn(f'href="{path}"', html)  # visible download link
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response["Content-Type"].startswith(dist["encodingFormat"]))
                formats[dist["encodingFormat"]] = path
            self.assertEqual(set(formats), {"application/json", "text/csv"})

    def test_every_indexable_page_is_in_the_sitemap_and_back(self):
        sets = sitemap_urlsets()
        locs = {entry["loc"] for entries in sets.values() for entry in entries}
        model = public_model()
        neutral_pages = ["/", "/tools/", "/methodology", "/privacy", "/collections/", "/datasets/",
                         "/datasets/models", "/datasets/tools", f"/models/{model.slug}",
                         f"/tools/{self.tool.slug}"]
        from catalog.hubs import HUBS
        neutral_pages += [f"/collections/{slug}" for slug in HUBS]
        checked = 0
        for code in SUPPORTED_CODES:
            for neutral in neutral_pages:
                path = localize(neutral, code)
                html = self.client.get(path).content.decode()
                indexable = 'name="robots" content="noindex' not in html
                url = "https://aipediya.com" + path
                self.assertEqual(indexable, url in locs, f"{path}: indexable={indexable}, in sitemap={url in locs}")
                checked += 1
        self.assertEqual(checked, len(SUPPORTED_CODES) * len(neutral_pages))


def escape_html(text):
    from django.utils.html import escape
    return escape(text)


class IndexNowKeyFileTests(TestCase):
    @override_settings(AIPEDIA_INDEXNOW_KEY="0123456789abcdef")
    def test_root_key_file_is_served_and_only_for_the_configured_key(self):
        root = self.client.get("/0123456789abcdef.txt")
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.content.decode().strip(), "0123456789abcdef")
        self.assertEqual(self.client.get("/indexnow/0123456789abcdef.txt").status_code, 200)
        self.assertEqual(self.client.get("/fedcba9876543210.txt").status_code, 404)
        self.assertEqual(self.client.get("/robots.txt").status_code, 200)
        self.assertEqual(self.client.get("/ru/0123456789abcdef.txt").status_code, 404)

    def test_root_key_file_is_404_when_unconfigured(self):
        self.assertEqual(self.client.get("/0123456789abcdef.txt").status_code, 404)

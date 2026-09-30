"""Adaptive Interface / Mobile & Tablet UX regression guards.

Pixel layout is verified in a real browser (artifacts/adaptive-ui/); these
tests pin the server markup and the CSS/JS contracts the responsive layout
depends on, so a later edit cannot silently bring back the desktop table on
phones, the page-wide sideways scroll or the stuck infinite loading.
"""
import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from catalog.chronology import renumber_chronologically
from catalog.models import ModelVersion


class ResponsiveCatalogMarkupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        ModelVersion.objects.update(released=date(2020, 1, 1))
        renumber_chronologically()

    def _sort_links(self, response):
        sheet = re.search(r'<dialog class="sheet" id="sort-sheet".*?</dialog>', response.content.decode(), re.S)
        self.assertIsNotNone(sheet)
        return re.findall(r'<a href="([^"]+)"(?: aria-current="true")?><span>(.*?)</span>', sheet.group(0))

    def test_models_catalog_has_filter_and_sort_sheets(self):
        response = self.client.get("/")
        self.assertContains(response, 'data-sheet-open="filters"', count=1)
        self.assertContains(response, 'data-sheet-open="sort"', count=1)
        self.assertContains(response, 'aria-controls="filter-sheet"')
        self.assertContains(response, 'aria-controls="sort-sheet"')
        self.assertContains(response, '<dialog class="sheet" id="filter-sheet" data-sheet="filters"')
        self.assertContains(response, '<dialog class="sheet" id="sort-sheet" data-sheet="sort"')
        # The filter sheet reuses the header controls (moved in by site.js),
        # so it ships an empty slot and one Apply bound to the real form.
        self.assertContains(response, "data-filter-slot")
        self.assertContains(response, 'type="submit" form="catalog-filters" class="mint-button sheet-apply"')
        # Column-header filters stay in the table for the desktop layout.
        self.assertContains(response, 'details class="col-filter"')

    def test_sort_sheet_lists_every_order_once_with_current_marked(self):
        response = self.client.get("/")
        options = response.context["sort_options"]
        links = self._sort_links(response)
        self.assertEqual(len(links), len(options))
        hrefs = [href for href, _ in links]
        for option in options:
            self.assertIn(f"sort={option}", " ".join(hrefs))
        labels = [re.sub(r"<[^>]+>", "", label) for _, label in links]
        self.assertEqual(len(labels), len(set(labels)), "sort labels must be distinguishable")
        self.assertIn("№ 1 → 9", labels)
        self.assertEqual(response.content.decode().count('aria-current="true"><span>'), 1)

    def test_tools_catalog_has_its_own_sort_options(self):
        response = self.client.get("/tools/")
        self.assertContains(response, 'data-sheet-open="filters"')
        links = self._sort_links(response)
        hrefs = " ".join(href for href, _ in links)
        for key in ("category", "ecosystem", "platform", "local"):
            self.assertIn(f"sort={key}_asc", hrefs)
        self.assertNotIn("sort=check_best", hrefs)

    def test_sheet_labels_are_localized_and_rtl_keeps_direction(self):
        ru = self.client.get("/ru/")
        self.assertContains(ru, "Фильтр")
        self.assertContains(ru, "Порядок")
        self.assertContains(ru, "Применить")
        ar = self.client.get("/ar/")
        self.assertContains(ar, 'dir="rtl"')
        self.assertContains(ar, 'data-sheet-open="sort"')
        self.assertContains(ar, '<bdi dir="ltr">№ 1 → 9</bdi>', html=True)

    def test_active_filter_count_badge(self):
        developer = ModelVersion.objects.filter(public_number__isnull=False).first().family.developer_id
        response = self.client.get("/", {"developer": developer})
        self.assertContains(response, '<span class="toolbar-badge">1</span>', html=True)
        self.assertNotContains(self.client.get("/"), 'class="toolbar-badge"')

    def test_rows_keep_cells_needed_by_mobile_cards(self):
        response = self.client.get("/")
        body = response.content.decode()
        row = re.search(r'<tr data-slug="[^"]+" data-kind="model".*?</tr>', body, re.S).group(0)
        for cell in ("number-col", "model-col", "developer-col", "purpose-col", "price-col", "access-col", "release-col"):
            self.assertIn(f'class="{cell}"', row)
        self.assertIn('class="model-name"', row)

    def test_direct_detail_url_still_opens_panel(self):
        model = ModelVersion.objects.filter(public_number__isnull=False).first()
        response = self.client.get(f"/models/{model.slug}")
        self.assertContains(response, 'class="model-panel is-open"')
        self.assertContains(response, "is-panel-open")
        self.assertContains(response, 'data-sheet-open="filters"')


class ResponsiveAssetContractTests(SimpleTestCase):
    def _asset(self, name):
        return (Path(settings.BASE_DIR) / "static" / name).read_text(encoding="utf-8-sig")

    def test_catalog_area_is_a_size_container(self):
        css = self._asset("site.css")
        self.assertIn("container: catalog / inline-size", css)
        self.assertIn("container: panel / inline-size", css)
        self.assertIn("@container catalog (max-width: 1299px)", css)
        # Hidden absolutely positioned helpers must stay inside the table
        # scroller, or they stretch the app-shell document below the screen.
        self.assertRegex(css, r"\.table-scroll \{[^}]*position: relative")

    def test_table_no_longer_forces_a_desktop_width(self):
        css = self._asset("table-layout.css")
        # The old 1110px/1120px minimums made phones a sideways-scrolling desktop table.
        self.assertNotRegex(css, r"min-width:\s*11[0-9]{2}px")
        self.assertIn("@container catalog (max-width: 719px)", css)
        self.assertIn("grid-template-areas", css)
        for column in ("rating-col", "status-col", "context-col", "checks-col", "access-col",
                       "local-col", "ecosystem-col", "platform-col", "category-col"):
            self.assertIn(column, css)

    def test_shell_and_panel_modes(self):
        css = self._asset("site.css")
        self.assertIn("--shell-max:", css)
        self.assertIn("@media (min-width: 1280px)", css)
        self.assertIn("@media (max-width: 1279px)", css)
        self.assertIn("@media (max-width: 720px) and (min-height: 540px)", css)
        self.assertIn("100dvh", css)
        self.assertIn("env(safe-area-inset-bottom)", css)
        self.assertIn("@media (hover: none)", css)
        self.assertIn("--touch: 44px", css)
        self.assertIn("--z-sheet", css)
        # Drawer starts below the header, so language/search stay above it.
        self.assertIn("inset-block: var(--aip-header-h, 0) 0", css)

    def test_site_js_sheet_and_panel_behaviour(self):
        js = self._asset("site.js")
        self.assertIn("showModal()", js)
        self.assertIn("fillFilterSheet", js)
        self.assertIn("emptyFilterSheet", js)
        # Touch taps must stay open; pointer leave is hover-only.
        self.assertGreaterEqual(js.count('event.pointerType === "mouse"'), 2)
        # Closing the sheet applies pending choices instead of losing them.
        self.assertIn("filterSheetDirty", js)
        # Clicks inside a dialog never close the detail panel; Escape is left
        # to an open sheet.
        self.assertIn('target.closest("dialog")', js)
        self.assertIn('document.querySelector("dialog.sheet[open]")', js)
        # Language links follow the panel's address changes.
        self.assertIn("function syncLanguageLinks", js)
        self.assertGreaterEqual(js.count("syncLanguageLinks()"), 4)
        self.assertIn("openPanelFromLink(link, false, location.href)", js)

    def test_infinite_loading_watches_viewport_and_table_scroller(self):
        js = self._asset("site.js")
        # A viewport observer (phones scroll the page) plus the table scroller
        # (app shell), re-checked after every loaded chunk.
        self.assertIn('new IntersectionObserver(onIntersect, { rootMargin: "240px 0px" })', js)
        self.assertIn("root: tableScroll", js)
        self.assertIn("recheck", js)
        self.assertIn("return true;", js)

import hashlib
import json
import secrets
from urllib.parse import quote
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import (
    FileResponse, HttpResponse, HttpResponseNotFound, HttpResponsePermanentRedirect, JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe
from .models import (
    Benchmark, Category, Evaluation, ModelVersion, Offer, Platform, Service, Tool,
)
from . import readiness
from .i18n import SUPPORTED_CODES
from .locale_urls import URL_CODE, FROM_URL_CODE, absolute, localize
from .seo import json_ld_script, page_signals, render_index, render_urlset, sitemap_urlsets
from .static_pages import label_text, labels_ready


def _ready_for_labels(keys):
    return [code for code in SUPPORTED_CODES if labels_ready(keys, code)]


def _catalog_seo(request, page, kind="model", hub=None):
    """Listing signals: only the clean listing and its plain ?page=N pages are
    indexable; any filter, search or sort makes the page ``noindex,follow``
    without pointing a canonical at a different (unfiltered) page."""
    lang = request.aipedia_lang
    neutral = request.aipedia_neutral_path
    only_pagination = not any(key != "page" for key in request.GET)
    page_number = page.number if page.number > 1 else None
    if hub is not None:
        from .static_pages import localized_blocks
        blocks = {tag: text for tag, text, _fb in localized_blocks(hub.page, lang)}
        title = blocks.get("title", "")
        description = blocks.get("intro", "")
        from .hubs import ready_locales
        ready = ready_locales(hub, page.paginator.count)
        crumbs = [("AIpediya", "/"), (label_text("collections", lang), "/collections/"), (title, neutral)]
    else:
        key = "tools_catalog" if kind == "tool" else "models_catalog"
        title = label_text(f"{key}_title", lang)
        description = label_text(f"{key}_description", lang)
        ready = _ready_for_labels([f"{key}_title", f"{key}_description", "page_n"])
        crumbs = None
    if page_number:
        word = label_text("page_n", lang)
        # Chinese orders the page number inside the phrase (第 2 页).
        page_label = f"第{page_number}{word}" if lang in ("zh-Hans", "zh-Hant") else f"{word} {page_number}"
        title = f"{title} — {page_label}"
    signals = page_signals(
        neutral, lang, title=f"{title} | AIpediya", description=description, ready_langs=ready,
        indexable=only_pagination, page=page_number,
        breadcrumbs=crumbs,
    )
    signals["h1"] = title
    return signals


def _entity_seo(request, entity, kind):
    lang = request.aipedia_lang
    from .comparison import localized
    suffix_key = "tool_title_suffix" if kind == "tool" else "model_title_suffix"
    developer = entity.developer.name if kind == "tool" else entity.family.developer.name
    version = "" if not entity.version or entity.version.casefold() == entity.name.casefold() else f" {entity.version}"
    name = f"{entity.name}{version}"
    title = f"{name} — {label_text(suffix_key, lang)} ({developer}) | AIpediya"
    description = localized(entity.description, lang) if entity.description else name
    # Some imported cards have only the generic "model from X / exact version"
    # sentence. Give their EN/RU search snippets the verified facts already on
    # the card, without changing the master text or inventing a price/score.
    if kind == "model" and lang in ("en", "ru") and (
        "Exact version:" in description or "Точная версия:" in description
    ):
        if lang == "ru":
            facts = [f"{name} — модель {developer}."]
            if entity.context:
                facts.append(f"Контекст: {entity.context:,} токенов.")
            if any(access.service.kind == "api" for access in entity.accesses.all()):
                facts.append("Доступ через API подтверждён.")
            if not any(offer.active and offer.amount is not None for offer in entity.offers.all()):
                facts.append("Проверенной цены в AIpediya нет.")
        else:
            facts = [f"{name} by {developer}."]
            if entity.context:
                facts.append(f"Context: {entity.context:,} tokens.")
            if any(access.service.kind == "api" for access in entity.accesses.all()):
                facts.append("Documented API access.")
            if not any(offer.active and offer.amount is not None for offer in entity.offers.all()):
                facts.append("No verified price in AIpediya.")
        description = " ".join(facts)
    ready = [code for code in readiness.ready_locales(entity) if labels_ready([suffix_key], code)]
    from .context import t
    listing = ("/tools/", t("tools_tab", lang)) if kind == "tool" else ("/", t("models_tab", lang))
    neutral = f"/{'tools' if kind == 'tool' else 'models'}/{entity.slug}"
    return page_signals(
        neutral, lang, title=title, description=description, ready_langs=ready, og_type="article",
        breadcrumbs=[("AIpediya", "/"), (listing[1], listing[0]), (name, neutral)],
    )


def versions():
    return ModelVersion.objects.filter(published=True, entry_type="model").select_related(
        "family__developer__source", "source"
    ).prefetch_related(
        "offers__service__provider", "offers__source", "evaluations__benchmark",
        "evaluations__source", "accesses__service__provider", "accesses__source",
        "facts__source", "audits__source", "origin_country_links__country",
    )


def tools():
    return Tool.objects.filter(published=True).select_related(
        "developer__source", "source", "legacy_version"
    ).prefetch_related(
        "platform_links__platform", "model_links__model",
        "legacy_version__offers__service__provider", "legacy_version__offers__source",
        "legacy_version__accesses__service__provider", "legacy_version__accesses__source",
    )


from .comparison import (
    decorate, decorate_tool, sort_models, sort_tools, price_matches, condition_key, localized,
)
from .context import TEXT, t, category_label


ENTRY_TYPES = [code for code, _ in ModelVersion._meta.get_field("entry_type").choices]
# First paint shows a full window; further chunks load as the table scrolls.
INITIAL_PAGE_SIZE = 150
CHUNK_SIZE = 50
DEFAULT_PER_PAGE = INITIAL_PAGE_SIZE  # kept for tests / older imports
PANEL_TABS = ("overview", "pricing", "checks")
TEXT_SORTS = (
    "number", "name", "developer", "purpose", "price", "access", "context", "status", "release",
)
TOOL_SORTS = (
    "number", "name", "category", "developer", "purpose", "ecosystem", "platform",
    "price", "local", "release",
)


class CatalogPaginator:
    """Paginator with a larger first page, then fixed scroll chunks."""

    def __init__(self, object_list):
        self.object_list = object_list
        self.count = len(object_list)
        self.per_page = INITIAL_PAGE_SIZE
        if self.count <= INITIAL_PAGE_SIZE:
            self.num_pages = 1
        else:
            remaining = self.count - INITIAL_PAGE_SIZE
            self.num_pages = 1 + (remaining + CHUNK_SIZE - 1) // CHUNK_SIZE

    @classmethod
    def page_from_slice(cls, object_list, count, number):
        """Build a page from an already sliced queryset."""
        paginator = cls([])
        paginator.count = count
        if count <= INITIAL_PAGE_SIZE:
            paginator.num_pages = 1
        else:
            remaining = count - INITIAL_PAGE_SIZE
            paginator.num_pages = 1 + (remaining + CHUNK_SIZE - 1) // CHUNK_SIZE
        number, start, end = paginator.bounds(number)
        return CatalogPage(paginator, number, object_list, start, end)

    def bounds(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError):
            number = 1
        number = max(1, min(number, self.num_pages))
        if number == 1:
            return number, 0, min(INITIAL_PAGE_SIZE, self.count)
        start = INITIAL_PAGE_SIZE + (number - 2) * CHUNK_SIZE
        return number, start, min(start + CHUNK_SIZE, self.count)

    def get_page(self, number):
        number, start, end = self.bounds(number)
        return CatalogPage(self, number, self.object_list[start:end], start, end)


class CatalogPage:
    def __init__(self, paginator, number, object_list, start, end):
        self.paginator = paginator
        self.number = number
        self.object_list = object_list
        self._start = start
        self._end = end

    def __iter__(self):
        return iter(self.object_list)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    @property
    def has_previous(self):
        return self.number > 1

    @property
    def has_next(self):
        return self.number < self.paginator.num_pages

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1

    def start_index(self):
        return 0 if self.paginator.count == 0 else self._start + 1

    def end_index(self):
        return self._end


def _catalog_counts():
    return {
        "models": ModelVersion.objects.filter(published=True, entry_type="model").count(),
        "tools": Tool.objects.filter(published=True).count(),
    }


def _number_page(qs, number, descending=False):
    """Return one chronological page without hydrating the whole catalogue."""
    count = qs.count()
    paginator = CatalogPaginator([])
    paginator.count = count
    if count <= INITIAL_PAGE_SIZE:
        paginator.num_pages = 1
    else:
        remaining = count - INITIAL_PAGE_SIZE
        paginator.num_pages = 1 + (remaining + CHUNK_SIZE - 1) // CHUNK_SIZE
    page_number, start, end = paginator.bounds(number)
    order = F("public_number").desc(nulls_last=True) if descending else F("public_number").asc(nulls_last=True)
    object_list = list(qs.order_by(order, "pk")[start:end])
    return CatalogPaginator.page_from_slice(object_list, count, page_number)


def _tool_catalog_context(request, selected_slug=None, hub=None):
    qs = tools()
    if hub is not None:
        from .hubs import members
        qs = qs.filter(pk__in=members(hub))
    categories = list(Category.objects.all())
    taxonomy_labels = {item.code: item.labels for item in categories}
    lang = request.aipedia_lang
    q = request.GET.get("q", "").strip()[:200]
    if q.startswith("#") and q[1:].isdigit():
        qs = qs.filter(public_number=int(q[1:]))
    elif q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(aliases__icontains=q)
            | Q(version__icontains=q)
            | Q(developer__name__icontains=q)
            | Q(description__icontains=q)
            | Q(ecosystem__icontains=q)
        )

    category = request.GET.get("category", "")
    tool_categories = [code for code, _ in Tool.CATEGORIES]
    if category in tool_categories:
        qs = qs.filter(category=category)
    else:
        category = ""

    task = request.GET.get("task", "")
    if task in {item.code for item in categories}:
        qs = qs.filter(purposes__icontains='"' + task + '"')

    developer = request.GET.get("developer", "")
    if developer.isdigit():
        qs = qs.filter(developer_id=int(developer))
    else:
        developer = ""

    platform = request.GET.get("platform", "")
    platform_codes = list(Platform.objects.order_by("position").values_list("code", flat=True))
    if platform in platform_codes:
        qs = qs.filter(platforms__code=platform)
    else:
        platform = ""

    local_execution = request.GET.get("local", "")
    local_values = [code for code, _ in Tool.LOCAL_EXECUTION]
    if local_execution in local_values:
        qs = qs.filter(local_execution=local_execution)
    else:
        local_execution = ""

    ecosystem = request.GET.get("ecosystem", "").strip()[:120]
    if ecosystem:
        qs = qs.filter(ecosystem__icontains=ecosystem)

    default_sort = hub.sort if hub is not None else "release_desc"
    sort = request.GET.get("sort", default_sort)
    orders = [f"{key}_{direction}" for key in TOOL_SORTS for direction in ("asc", "desc")]
    if sort not in orders:
        sort = default_sort

    price_scope = request.GET.get("price_scope", "standard")
    if price_scope not in {"standard", "batch", "offpeak", "peak", "flex", "fast", "priority", "free", "annual", "all"}:
        price_scope = "standard"
    price_variant = request.GET.get("price_variant", "base")
    if price_variant not in {"base", "long", "all"}:
        price_variant = "base"
    price_modality = request.GET.get("price_modality", "text")
    if price_modality not in {"text", "audio", "image"}:
        price_modality = "text"
    price_units = list(
        Offer.objects.filter(
            active=True,
            amount__isnull=False,
            billing_unit="",
            model__tool_record__published=True,
        )
        .exclude(unit="other")
        .order_by("unit")
        .values_list("unit", flat=True)
        .distinct()
    )
    price_unit = request.GET.get("price_unit", "")
    if sort.startswith("price_") and not price_unit:
        price_unit = "input"
    if price_unit not in price_units:
        price_unit = "input" if sort.startswith("price_") and "input" in price_units else ""

    qs = qs.distinct()
    fast_number_page = sort in {"number_asc", "number_desc"} and not price_unit
    if fast_number_page:
        page = _number_page(qs, request.GET.get("page"), descending=sort == "number_desc")
        items = list(page.object_list)
    else:
        items = list(qs)
    price_conditions = {}
    for tool in items:
        if not tool.legacy_version:
            continue
        for offer in tool.legacy_version.offers.all():
            if price_matches(offer, price_unit, price_scope, price_variant, modality=price_modality):
                from .price_text import full_conditions

                price_conditions[condition_key(offer)] = full_conditions(offer.conditions, lang)
    price_condition = request.GET.get("price_condition", "")
    if price_condition not in price_conditions:
        price_condition = ""
    if price_unit and price_unit not in {"input", "output", "cache_read", "cache_write"} and not price_condition and price_conditions:
        price_condition = sorted(price_conditions)[0]

    for tool in items:
        decorate_tool(
            tool,
            taxonomy_labels,
            price_unit,
            price_scope,
            lang,
            price_variant,
            price_condition,
            price_modality,
        )
    comparison_count = sum(bool(item.comparison_offer) for item in items)
    if not fast_number_page:
        items = sort_tools(items, sort)
        page = CatalogPaginator(items).get_page(request.GET.get("page"))

    selected_tool = None
    slug = selected_slug or request.GET.get("tool", "").strip()
    if slug:
        selected_tool = next((item for item in page.object_list if item.slug == slug), None)
        if selected_tool is None:
            selected_tool = tools().filter(slug=slug).first()
            if selected_tool:
                decorate_tool(
                    selected_tool,
                    taxonomy_labels,
                    price_unit,
                    price_scope,
                    lang,
                    price_variant,
                    price_condition,
                    price_modality,
                )
    panel_tab = request.GET.get("tab", "overview")
    if panel_tab not in {"overview", "pricing"}:
        panel_tab = "overview"

    developers = Tool.objects.filter(published=True).values(
        "developer_id", "developer__name"
    ).distinct().order_by("developer__name")
    chips = _tool_filter_chips(
        request,
        lang,
        q=q,
        category=category,
        developer=developer,
        platform=platform,
        local_execution=local_execution,
        ecosystem=ecosystem,
        sort=sort,
        developers=developers,
    )
    return {
        "page": page,
        "q": q,
        "kind": "tool",
        "entity_kind": "tool",
        "selected_entity": selected_tool,
        "selected_model": None,
        "selected_tool": selected_tool,
        "model": None,
        "tool": selected_tool,
        "public_number": getattr(selected_tool, "public_number", None),
        "catalog_status": getattr(selected_tool, "catalog_status", ""),
        "panel_tab": panel_tab,
        "counts": _catalog_counts(),
        "found_count": page.paginator.count,
        "shown_count": len(page.object_list),
        "categories": categories,
        "category": category,
        "tool_categories": tool_categories,
        "developers": developers,
        "developer": developer,
        "platforms": Platform.objects.order_by("position", "code"),
        "platform": platform,
        "local_values": local_values,
        "local_execution": local_execution,
        "ecosystem": ecosystem,
        "sort": sort,
        "sort_options": orders,
        "price_units": price_units,
        "price_unit": price_unit,
        "price_scope": price_scope,
        "price_variant": price_variant,
        "price_modality": price_modality,
        "price_conditions": sorted(price_conditions.items(), key=lambda pair: pair[1]),
        "price_condition": price_condition,
        "comparison_count": comparison_count,
        "filter_chips": chips,
        "hub": hub,
        "seo": _catalog_seo(request, page, kind="tool", hub=hub),
    }


def _tool_filter_chips(request, lang, **values):
    chips = []

    def add(param, text):
        params = request.GET.copy()
        params.pop(param, None)
        params.pop("page", None)
        chips.append({"label": text, "href": "?" + params.urlencode() if params else request.path})

    developers = {
        str(item["developer_id"]): item["developer__name"] for item in values["developers"]
    }
    for param in ("q", "ecosystem"):
        if values.get(param):
            add(param, values[param])
    if values.get("category"):
        add("category", t(values["category"], lang))
    if values.get("developer"):
        add("developer", developers.get(values["developer"], values["developer"]))
    if values.get("platform"):
        add("platform", values["platform"])
    if values.get("local_execution"):
        add("local", t(values["local_execution"], lang))
    if values.get("sort") and values["sort"] != "release_desc":
        add("sort", t(values["sort"], lang))
    return chips


def _catalog_context(request, selected_slug=None, hub=None):
    qs = versions()
    if hub is not None:
        from .hubs import members
        qs = qs.filter(pk__in=members(hub))
    categories = list(Category.objects.all())
    taxonomy_labels = {item.code: item.labels for item in categories}
    q = request.GET.get("q", "").strip()[:200]
    if q.startswith("#") and q[1:].isdigit():
        qs = qs.filter(public_number=int(q[1:]))
    elif q:
        match = (Q(name__icontains=q) | Q(aliases__icontains=q) | Q(version__icontains=q)
                 | Q(family__developer__name__icontains=q) | Q(description__icontains=q))
        for category in categories:
            if any(q.casefold() in label.casefold() for label in category.labels.values()):
                match |= Q(tasks__icontains='"' + category.code + '"')
        for key in ("coding", "documents", "reasoning", "images", "video", "audio", "translation"):
            if any(q.casefold() in label.casefold() for label in TEXT[key]):
                match |= Q(tasks__icontains='"' + key + '"')
        qs = qs.filter(match)

    category_code = request.GET.get("category", "")
    aliases = {"code": ["coding"], "image_generation": ["images"],
               "video_generation": ["video"], "speech": ["audio"]}
    if category_code in {"image", "video", "audio"}:
        qs = qs.filter(category=category_code)
    elif category_code in {item.code for item in categories}:
        category_match = Q(tasks__icontains='"' + category_code + '"')
        for alias in aliases.get(category_code, []):
            category_match |= Q(tasks__icontains='"' + alias + '"')
        if category_code in {"image", "video", "audio"}:
            category_match |= Q(category=category_code)
        qs = qs.filter(category_match)
    else:
        category_code = ""

    task = request.GET.get("task", "")
    if task in {item.code for item in categories}:
        qs = qs.filter(tasks__icontains='"' + task + '"')

    developer = request.GET.get("developer", "")
    if developer.isdigit():
        qs = qs.filter(family__developer_id=int(developer))
    else:
        developer = ""

    access = request.GET.get("access", "")
    access_kinds = [code for code, _ in Service._meta.get_field("kind").choices]
    if access in access_kinds:
        qs = qs.filter(accesses__service__kind=access)
    else:
        access = ""

    status = request.GET.get("status", "all")
    if status not in {"active", "deprecated", "retired", "archived", "all"}:
        status = "all"
    if status != "all":
        qs = qs.filter(catalog_status=status)

    kind = "model"
    entry_type = ""

    lang = request.aipedia_lang
    default_sort = hub.sort if hub is not None else "release_desc"
    sort = request.GET.get("sort", default_sort)
    sort = {"score": "check_best", "check_desc": "check_best", "check_asc": "check_worst"}.get(sort, sort)
    orders = [f"{key}_{direction}" for key in TEXT_SORTS for direction in ("asc", "desc")] + ["check_best", "check_worst"]
    if sort not in orders:
        sort = default_sort
    price_scope = request.GET.get("price_scope", "standard")
    if price_scope not in {"standard", "batch", "offpeak", "peak", "flex", "fast", "priority", "free", "annual", "all"}:
        price_scope = "standard"
    price_variant = request.GET.get("price_variant", "base")
    if price_variant not in {"base", "long", "all"}:
        price_variant = "base"
    price_modality = request.GET.get("price_modality", "text")
    if price_modality not in {"text", "audio", "image"}:
        price_modality = "text"
    price_units = list(Offer.objects.filter(active=True, amount__isnull=False, billing_unit="").exclude(unit="other").order_by("unit").values_list("unit", flat=True).distinct())
    price_unit = request.GET.get("price_unit", "")
    if sort.startswith("price_") and not price_unit:
        price_unit = "input"
    if price_unit not in price_units:
        price_unit = "input" if sort.startswith("price_") else ""
    benchmarks = list(Benchmark.objects.filter(evaluation__public=True).distinct().order_by("name", "protocol", "pk"))
    try:
        benchmark_id = int(request.GET.get("benchmark", ""))
    except (TypeError, ValueError):
        benchmark_id = None
    benchmark = next((item for item in benchmarks if item.pk == benchmark_id), None)
    if not benchmark and sort.startswith("check_"):
        benchmark = next((item for item in benchmarks if item.name == "ECI"), benchmarks[0] if benchmarks else None)
    configurations = sorted(set(Evaluation.objects.filter(public=True, benchmark=benchmark).values_list("configuration", flat=True))) if benchmark else []
    configuration = request.GET.get("configuration", "")
    if configuration not in configurations:
        configuration = configurations[0] if configurations else ""
    snapshots = sorted(set(Evaluation.objects.filter(public=True, benchmark=benchmark, configuration=configuration).values_list("snapshot", flat=True)), reverse=True) if benchmark else []
    snapshot = request.GET.get("snapshot", "")
    if snapshot not in snapshots:
        snapshot = snapshots[0] if snapshots else ""
    qs = qs.distinct()
    fast_number_page = (
        sort in {"number_asc", "number_desc"}
        and not price_unit
        and benchmark is None
        and request.GET.get("evaluated_only") != "1"
    )
    if fast_number_page:
        page = _number_page(qs, request.GET.get("page"), descending=sort == "number_desc")
        models = list(page.object_list)
    else:
        models = list(qs)
    price_conditions = {}
    for model in models:
        for offer in model.offers.all():
            if price_matches(offer, price_unit, price_scope, price_variant, modality=price_modality):
                from .price_text import full_conditions
                price_conditions[condition_key(offer)] = full_conditions(offer.conditions, lang)
    price_condition = request.GET.get("price_condition", "")
    if price_condition not in price_conditions:
        price_condition = ""
    # Media and subscription offers can use incompatible resolutions/tiers even
    # within one unit. Require one displayed condition for their comparison.
    if price_unit and price_unit not in {"input", "output", "cache_read", "cache_write"} and not price_condition and price_conditions:
        price_condition = sorted(price_conditions)[0]
    for model in models:
        decorate(model, taxonomy_labels, price_unit, benchmark, price_scope, lang, configuration, snapshot, price_variant, price_condition, price_modality)
    if request.GET.get("evaluated_only") == "1" and benchmark:
        models = [item for item in models if item.comparison_evaluation]
    comparison_count = sum(bool(item.comparison_offer) for item in models)
    if not fast_number_page:
        models = sort_models(models, sort, benchmark)
        page = CatalogPaginator(models).get_page(request.GET.get("page"))
    counts = _catalog_counts()
    panel_tab = request.GET.get("tab", "overview")
    if panel_tab not in PANEL_TABS:
        panel_tab = "overview"
    selected_model = None
    slug = selected_slug or request.GET.get("model", "").strip()
    if slug:
        selected_model = next((item for item in page.object_list if item.slug == slug), None)
        if selected_model is None:
            selected_model = versions().filter(slug=slug).first()
            if selected_model:
                selected_model = decorate(
                    selected_model, taxonomy_labels, price_unit, benchmark, price_scope, lang,
                    configuration, snapshot, price_variant, price_condition, price_modality,
                )
    context = {
        "page": page, "q": q, "category": category_code, "sort": sort, "status": status,
        "categories": categories, "access_kinds": access_kinds, "sort_options": list(orders),
        "price_units": price_units, "price_unit": price_unit, "price_scope": price_scope,
        "benchmarks": benchmarks, "benchmark": benchmark, "counts": counts,
        "configurations": configurations, "configuration": configuration,
        "snapshots": snapshots, "snapshot": snapshot, "price_variant": price_variant,
        "price_modality": price_modality,
        "price_conditions": sorted(price_conditions.items(), key=lambda pair: pair[1]), "price_condition": price_condition,
        "comparison_count": comparison_count,
        "developers": ModelVersion.objects.filter(published=True, entry_type="model").values("family__developer_id", "family__developer__name").distinct().order_by("family__developer__name"),
        "found_count": page.paginator.count, "shown_count": len(page.object_list),
        "kind": kind, "entry_type": entry_type, "entry_types": ENTRY_TYPES,
        "access": access, "developer": developer,
        "entity_kind": "model", "selected_entity": selected_model,
        "selected_model": selected_model, "selected_tool": None, "panel_tab": panel_tab,
        "model": selected_model, "tool": None,
        "public_number": getattr(selected_model, "public_number", None),
        "catalog_status": getattr(selected_model, "catalog_status", ""),
        "facts": getattr(selected_model, "facts_by_key", {}),
        "hub": hub,
        "seo": _catalog_seo(request, page, kind="model", hub=hub),
        "filter_chips": _filter_chips(request, {
            "q": q, "kind": kind, "entry_type": entry_type, "category": category_code,
            "developer": developer, "access": access, "status": status,
            "price_unit": price_unit, "benchmark": benchmark, "sort": sort,
        }, lang, categories, access_kinds),
    }
    return context


def _filter_chips(request, values, lang, categories, access_kinds):
    chips = []
    labels = {item.code: category_label(item.code, item.labels, lang) for item in categories}
    developers = {
        str(item["family__developer_id"]): item["family__developer__name"]
        for item in ModelVersion.objects.filter(published=True, entry_type="model").values("family__developer_id", "family__developer__name")
    }

    def add(param, label):
        params = request.GET.copy()
        params.pop(param, None)
        if param == "benchmark":
            params.pop("configuration", None)
            params.pop("snapshot", None)
            params.pop("evaluated_only", None)
        if param == "price_unit":
            params.pop("price_scope", None)
            params.pop("price_modality", None)
            params.pop("price_variant", None)
            params.pop("price_condition", None)
        params.pop("page", None)
        chips.append({"label": label, "href": "?" + params.urlencode() if params else request.path})

    if values["q"]:
        add("q", values["q"])
    if values["entry_type"]:
        add("entry_type", t(values["entry_type"], lang))
    if values["category"]:
        add("category", labels.get(values["category"], values["category"]))
    if values["developer"]:
        add("developer", developers.get(values["developer"], values["developer"]))
    if values["access"] in access_kinds:
        add("access", t(values["access"], lang))
    if values["status"] and values["status"] != "all":
        add("status", t(values["status"], lang))
    if values["price_unit"]:
        unit_key = "unit_image" if values["price_unit"] == "image" else values["price_unit"]
        add("price_unit", t(unit_key, lang))
    if values["benchmark"]:
        add("benchmark", values["benchmark"].name)
    if values["sort"] and values["sort"] != "release_desc":
        add("sort", t(values["sort"], lang))
    return chips


def _page_guard(request, context):
    """Pagination is finite: ``page`` must be an integer inside the range.

    ``?page=1`` alone is a duplicate of the clean listing and redirects there;
    anything invalid or out of range is a 404 instead of a silently clamped
    page with different content.
    """
    raw = request.GET.get("page")
    if raw is None:
        return None
    if not raw.isdigit() or int(raw) < 1 or int(raw) > context["page"].paginator.num_pages:
        return _not_found(request)
    if raw == "1":
        params = request.GET.copy()
        params.pop("page")
        query = params.urlencode()
        return HttpResponsePermanentRedirect(request.path + ("?" + query if query else ""))
    return None


def _render_catalog(request, context, listing=False):
    partial = request.GET.get("partial")
    if listing:
        guard = _page_guard(request, context)
        if guard is not None:
            return guard
    if partial == "rows":
        response = render(request, "catalog_rows.html", context)
        if context["page"].has_next:
            params = request.GET.copy()
            params["page"] = context["page"].next_page_number()
            params["partial"] = "rows"
            response["X-Aipedia-Next"] = "?" + params.urlencode()
        return response
    if partial == "panel":
        if not context.get("selected_entity"):
            return HttpResponseNotFound()
        response = render(request, "panel.html", context)
        response["Cache-Control"] = "no-store"
        # Percent-encoded: HTTP headers are Latin-1, localized titles are not.
        response["X-Aipedia-Title"] = quote(context["seo"]["title"], safe="")
        response["X-Aipedia-Slug"] = context["selected_entity"].slug
        response["X-Aipedia-Kind"] = context["entity_kind"]
        return response
    return render(request, "catalog.html", context)


def _not_found(request):
    from .context import t
    lang = request.aipedia_lang
    return render(request, "404.html", {
        "seo": page_signals("/", lang, title=f"{t('not_found', lang)} | AIpediya", description="",
                            ready_langs=[], indexable=False),
    }, status=404)


@require_safe
def catalog(request):
    return _render_catalog(request, _catalog_context(request), listing=True)


@require_safe
def tool_catalog(request):
    return _render_catalog(request, _tool_catalog_context(request), listing=True)


def _canonical_redirect(request, manager, hidden, slug, prefix, other=None, other_prefix=""):
    """301 from a hidden duplicate/alias card to its published canonical card.

    ``other`` covers a record classified on the wrong catalog (e.g. a model
    listed as a tool): its canonical card lives in the other catalog."""
    from django.http import HttpResponsePermanentRedirect
    from .locale_urls import localize
    target = hidden.filter(slug=slug).exclude(redirect_to="").values_list("redirect_to", flat=True).first()
    if target and manager.filter(slug=target).exists():
        return HttpResponsePermanentRedirect(localize("/%s/%s" % (prefix, target), request.aipedia_lang))
    if target and other is not None and other.filter(slug=target).exists():
        return HttpResponsePermanentRedirect(localize("/%s/%s" % (other_prefix, target), request.aipedia_lang))
    return None


@require_safe
def detail(request, slug):
    if not readiness.public_models().filter(slug=slug).exists():
        return _canonical_redirect(request, readiness.public_models(),
                                   ModelVersion.objects.filter(entry_type="model", published=False),
                                   slug, "models", readiness.public_tools(), "tools") or _not_found(request)
    context = _catalog_context(request, selected_slug=slug)
    model = context["selected_model"]
    context["listing_title"] = context["seo"]["title"]
    context["seo"] = _entity_seo(request, model, "model")
    context["facts"] = model.facts_by_key
    return _render_catalog(request, context)


@require_safe
def tool_detail(request, slug):
    if not readiness.public_tools().filter(slug=slug).exists():
        return _canonical_redirect(request, readiness.public_tools(), Tool.objects.filter(published=False),
                                   slug, "tools", readiness.public_models(), "models") or _not_found(request)
    context = _tool_catalog_context(request, selected_slug=slug)
    context["listing_title"] = context["seo"]["title"]
    context["seo"] = _entity_seo(request, context["selected_tool"], "tool")
    return _render_catalog(request, context)


@require_safe
def collection(request, slug):
    from .hubs import HUBS, status
    from .static_pages import localized_blocks
    hub = HUBS.get(slug)
    if hub is None:
        return _not_found(request)
    builder = _tool_catalog_context if hub.kind == "tool" else _catalog_context
    context = builder(request, hub=hub)
    lang = request.aipedia_lang
    context["hub_blocks"] = {tag: (text, fallback) for tag, text, fallback in localized_blocks(hub.page, lang)}
    context["hub_state"] = status(hub, lang)
    return _render_catalog(request, context, listing=True)


@require_safe
def collections_index(request):
    from .hubs import HUB_LABELS, listed_hubs
    from .static_pages import localized_blocks
    lang = request.aipedia_lang
    items = []
    for hub, count in listed_hubs(lang):
        blocks = {tag: text for tag, text, _fb in localized_blocks(hub.page, lang)}
        items.append({"hub": hub, "count": count, "title": blocks.get("title"), "intro": blocks.get("intro"),
                      "url": localize(f"/collections/{hub.slug}", lang)})
    ready = [code for code in SUPPORTED_CODES
             if labels_ready(HUB_LABELS + ("collections_intro",), code) and listed_hubs(code)]
    title = label_text("collections", lang)
    seo = page_signals("/collections/", lang, title=f"{title} | AIpediya",
                       description=label_text("collections_intro", lang), ready_langs=ready,
                       breadcrumbs=[("AIpediya", "/"), (title, "/collections/")])
    from .search_pages import COPY
    return render(request, "collections.html", {"seo": seo, "items": items, "title": title,
                                                "intro": label_text("collections_intro", lang),
                                                "search_copy": COPY.get(lang),
                                                "context_url": localize("/compare/model-context", lang),
                                                "pricing_url": localize("/api-pricing", lang)})


@require_safe
def search_reference(request, topic):
    """Authored EN/RU reference pages; no filter or locale parameter variants."""
    from .search_pages import COPY, context_rows, pricing_rows

    lang = request.aipedia_lang
    if lang not in COPY:
        return _not_found(request)
    is_context = topic == "context"
    neutral = "/compare/model-context" if is_context else "/api-pricing"
    if request.META.get("QUERY_STRING"):
        return HttpResponsePermanentRedirect(localize(neutral, lang))
    copy = COPY[lang]
    rows = context_rows() if is_context else pricing_rows()
    if not is_context:
        from .price_text import full_conditions
        for row in rows:
            row["condition_in"] = full_conditions(row["input"].conditions, lang)
            row["condition_out"] = full_conditions(row["output"].conditions, lang)
    # A data-driven page without enough verified entries would be thin.
    if len(rows) < 5:
        return _not_found(request)
    key = "context" if is_context else "pricing"
    title = copy[f"{key}_title"]
    seo = page_signals(neutral, lang, title=f"{title} | AIpediya",
                       description=copy[f"{key}_description"], ready_langs=("en", "ru"),
                       breadcrumbs=[("AIpediya", "/"),
                                    (label_text("collections", lang), "/collections/"),
                                    (title, neutral)])
    return render(request, "search_reference.html", {
        "seo": seo, "title": title, "copy": copy, "rows": rows,
        "is_context": is_context, "intro": copy[f"{key}_intro"],
        "method": copy[f"{key}_method"],
        "context_url": localize("/compare/model-context", lang),
        "pricing_url": localize("/api-pricing", lang),
        "coding_url": localize("/collections/coding-models", lang),
        "api_url": localize("/collections/api-models", lang),
        "long_url": localize("/collections/long-context-models", lang),
        "methodology_url": localize("/methodology", lang),
    })


@require_safe
def methodology(request):
    from .context import t
    from .static_pages import localized_blocks, page_ready
    lang = request.aipedia_lang
    title = t("methodology", lang)
    ready = [code for code in SUPPORTED_CODES
             if page_ready("methodology", code) and labels_ready(["methodology_description"], code)]
    seo = page_signals("/methodology", lang, title=f"{title} | AIpediya",
                       description=label_text("methodology_description", lang), ready_langs=ready,
                       breadcrumbs=[("AIpediya", "/"), (title, "/methodology")])
    return render(request, "methodology.html", {
        "seo": seo, "title": title, "blocks": localized_blocks("methodology", lang),
        "counts": _catalog_counts(),
    })


DATASET_DESCRIPTIONS = {
    None: "Two open datasets of the published AIpediya catalog, AI models and AI tools, in JSON and CSV with documented schema, provenance and checksums.",
    "models": "Published AI models in the AIpediya catalog: developer, origin, category, modalities, context window, release dates with precision, status, open weights, license, access routes and list prices, each with its source and check date.",
    "tools": "Published AI tools in the AIpediya catalog: developer, origin, category, platforms, local execution, supported models, release dates with precision, status, access routes and list prices, each with its source and check date.",
}
DATASET_DESCRIPTIONS_RU = {
    None: "Два открытых набора данных опубликованного каталога AIpediya — AI-модели и AI-инструменты — в JSON и CSV с описанной схемой, происхождением данных и контрольными суммами.",
    "models": "Опубликованные AI-модели каталога AIpediya: разработчик, происхождение, категория, модальности, контекстное окно, даты выпуска с точностью, статус, открытые веса, лицензия, способы доступа и цены — с источником и датой проверки.",
    "tools": "Опубликованные AI-инструменты каталога AIpediya: разработчик, происхождение, категория, платформы, локальный запуск, поддерживаемые модели, даты выпуска с точностью, статус, способы доступа и цены — с источником и датой проверки.",
}


@require_safe
def datasets_index(request):
    return _dataset_page(request, None)


@require_safe
def dataset_page(request, kind):
    return _dataset_page(request, kind)


def _dataset_page(request, kind):
    from . import datasets
    if not datasets.datasets_enabled():
        return _not_found(request)
    lang = request.aipedia_lang
    docs_lang = "ru" if lang == "ru" else "en"
    neutral = request.aipedia_neutral_path
    catalog_url = absolute("/datasets/", "en")
    entries = []
    for key in (list(datasets.DATASETS) if kind is None else [kind]):
        rows = datasets.records(key)
        meta = datasets.metadata(key, rows)
        slug = datasets.DATASETS[key]["slug"]
        files = {}
        for fmt in ("json", "csv"):
            payload = datasets.build(key, fmt)
            files[fmt] = {"url": f"/datasets/{slug}.{fmt}",
                          "abs": f"{settings.AIPEDIA_PUBLIC_ORIGIN}/datasets/{slug}.{fmt}",
                          "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        entries.append({"kind": key, "slug": slug, "meta": meta, "files": files,
                        "page": localize(f"/datasets/{key}", lang),
                        "description": (DATASET_DESCRIPTIONS_RU if docs_lang == "ru" else DATASET_DESCRIPTIONS)[key]})
    title = label_text("datasets", lang) if kind is None else datasets.DATASETS[kind]["name"]
    if kind is None:
        json_ld = [{
            "@context": "https://schema.org", "@type": "DataCatalog", "name": "AIpediya open data",
            "url": catalog_url, "publisher": {"@type": "Organization", "name": "AIpediya", "url": absolute("/", "en")},
            "dataset": [
                {"@type": "Dataset", "name": entry["meta"]["name"], "url": absolute(f"/datasets/{entry['kind']}", "en"),
                 "description": DATASET_DESCRIPTIONS[entry["kind"]]}
                for entry in entries
            ],
        }]
    else:
        entry = entries[0]
        meta = entry["meta"]
        json_ld = [{
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": meta["name"],
            "description": DATASET_DESCRIPTIONS[kind],
            "url": absolute(f"/datasets/{kind}", "en"),
            "identifier": entry["slug"],
            "version": meta["dataset_version"],
            "dateModified": meta["data_as_of"],
            "creator": {"@type": "Organization", "name": "AIpediya", "url": absolute("/", "en")},
            "isAccessibleForFree": True,
            "includedInDataCatalog": {"@type": "DataCatalog", "name": "AIpediya open data", "url": catalog_url},
            "variableMeasured": [field["name"] for field in meta["fields"]],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/json" if fmt == "json" else "text/csv",
                 "contentUrl": entry["files"][fmt]["abs"]}
                for fmt in ("json", "csv")
            ],
        }]
    crumbs = [("AIpediya", "/"), (label_text("datasets", lang), "/datasets/")]
    if kind is not None:
        crumbs.append((title, neutral))

    description = (DATASET_DESCRIPTIONS_RU if docs_lang == "ru" else DATASET_DESCRIPTIONS)[kind]
    seo = page_signals(neutral, lang, title=f"{title} | AIpediya", description=description,
                       ready_langs=datasets.dataset_page_langs(), json_ld=json_ld, breadcrumbs=crumbs)
    return render(request, "datasets.html", {
        "seo": seo, "title": title, "entries": entries, "kind": kind, "docs_lang": docs_lang,
        "docs_fallback": lang not in datasets.DOCS_LANGS, "license_status": datasets.LICENSE_STATUS,
        "schema_version": datasets.SCHEMA_VERSION,
    })


@require_safe
def dataset_download(request, slug, fmt):
    from . import datasets
    if not datasets.datasets_enabled():
        return HttpResponseNotFound()
    kind = next((key for key, value in datasets.DATASETS.items() if value["slug"] == slug), None)
    if kind is None or fmt not in ("json", "csv"):
        return HttpResponseNotFound()
    payload = datasets.build(kind, fmt)
    content_type = "application/json; charset=utf-8" if fmt == "json" else "text/csv; charset=utf-8"
    response = HttpResponse(payload, content_type=content_type)
    response["ETag"] = '"' + hashlib.sha256(payload).hexdigest() + '"'
    response["Content-Disposition"] = f'inline; filename="{slug}.{fmt}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_safe
def dataset_manifest(request):
    from . import datasets
    if not datasets.datasets_enabled():
        return HttpResponseNotFound()
    return JsonResponse(datasets.manifest(), json_dumps_params={"indent": 1})


@require_safe
def health(request):
    ModelVersion.objects.exists()
    path = Path(settings.BASE_DIR) / 'BUILD.json'
    build = json.loads(path.read_text()) if path.exists() else {}
    return JsonResponse({
        "service": "aipedia",
        "status": "ok",
        "release": build.get("commit", "local"),
        "environment": settings.AIPEDIA_ENV,
    })


@require_safe
def release_acceptance(request):
    path = Path(settings.BASE_DIR) / 'public-release' / 'aipedia-acceptance-20260920.zip'
    if not path.is_file(): return HttpResponseNotFound()
    return FileResponse(path.open('rb'), as_attachment=True, filename=path.name, content_type='application/zip')


# Facet, search and fragment parameters are excluded from crawling; locale
# paths, entity pages and plain listing ?page=N pagination stay crawlable. Exact
# previously discovered card URLs are allowed separately so crawlers can see
# their 301, 404 or fragment noindex without opening a query-space wildcard.
ROBOTS_BLOCKED_PARAMS = (
    "q", "sort", "category", "task", "developer", "access", "status", "benchmark", "configuration",
    "snapshot", "evaluated_only", "price_unit", "price_scope", "price_variant", "price_modality",
    "price_condition", "platform", "local", "ecosystem", "partial", "model", "tool",
)


def robots_rules():
    """(Allow|Disallow, pattern) for Production robots.txt, most general first.

    Card URLs with any query (``?tab=``, ``?page=``, filters) are canonical
    duplicates of the clean card and are not crawled. Listing pagination stays
    allowed, while only the exact observed GSC legacy card URLs are excepted.
    """
    rules = [("Allow", "/"), ("Disallow", "/admin/"), ("Disallow", "/healthz")]
    for param in ROBOTS_BLOCKED_PARAMS:
        rules.append(("Disallow", f"/*?{param}="))
        rules.append(("Disallow", f"/*&{param}="))
    for kind in ("models", "tools"):
        for prefix in ("", "/*"):
            rules.append(("Disallow", f"{prefix}/{kind}/*?"))
    # The tools listing shares its path prefix with tool cards. Permit only
    # plain listing pagination; facet combinations remain blocked.
    for prefix in ("", "/*"):
        rules.append(("Allow", f"{prefix}/tools/?page="))
        rules.append(("Disallow", f"{prefix}/tools/?page=*&"))
    from .legacy_search_urls import GSC_LEGACY_CARD_URLS

    # `$` anchors each exception to one observed URL, including parameter
    # order and values. Any added facet, page or partial combination stays
    # blocked by the card query rules above.
    rules.extend(("Allow", path + "$") for path in GSC_LEGACY_CARD_URLS)
    return rules


def robots_allows(path_and_query, rules=None):
    """Longest-match evaluation (Google/Bing/Yandex semantics, ``*`` and ``$``)."""
    import re as _re
    best = ("Allow", -1)
    for kind, pattern in rules or robots_rules():
        regex = "^" + _re.escape(pattern).replace(r"\*", ".*").replace(r"\$", "$")
        if _re.match(regex, path_and_query) and len(pattern) >= best[1]:
            if len(pattern) > best[1] or kind == "Allow":
                best = (kind, len(pattern))
    return best[0] == "Allow"


@require_safe
def robots(request):
    if not getattr(settings, "AIPEDIA_INDEXING_ALLOWED", False):
        # Local / non-production: never indexable.
        return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain; charset=utf-8")
    lines = ["User-agent: *"] + [f"{kind}: {path}" for kind, path in robots_rules()]
    lines += ["", f"Sitemap: {settings.AIPEDIA_PUBLIC_ORIGIN}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_safe
def sitemap(request):
    return HttpResponse(render_index(sitemap_urlsets()), content_type="application/xml; charset=utf-8")


@require_safe
def sitemap_locale(request, code):
    lang = FROM_URL_CODE.get(code)
    if lang is None:
        return HttpResponseNotFound()
    entries = sitemap_urlsets()[lang]
    if not entries:
        return HttpResponseNotFound()
    return HttpResponse(render_urlset(entries), content_type="application/xml; charset=utf-8")


@require_safe
def ads_txt(request):
    body = settings.AIPEDIA_ADS_TXT.strip() or "# AIpediya: ads.txt is not configured."
    return HttpResponse(body + "\n", content_type="text/plain; charset=utf-8")


@require_safe
def indexnow_key(request, key):
    configured = settings.AIPEDIA_INDEXNOW_KEY
    if not configured or not secrets.compare_digest(key, configured):
        return HttpResponseNotFound()
    return HttpResponse(configured + "\n", content_type="text/plain; charset=utf-8")


@require_safe
def privacy(request):
    from .context import t
    from .static_pages import page_blocks, page_label, page_ready
    lang = request.aipedia_lang
    title = t("privacy", lang)
    description = (
        "Как AIpediya обрабатывает технические данные, согласие и будущую рекламу."
        if lang == "ru"
        else "How AIpediya processes technical data, consent choices, and future advertising."
    )
    # Reachable in every locale; indexable only where the page is fully localized.
    ready = [code for code in SUPPORTED_CODES if code in ("en", "ru") or page_ready("privacy", code)]
    return render(request, "privacy.html", {
        "seo": page_signals("/privacy", lang, title=f"{title} | AIpediya", description=description,
                            ready_langs=ready),
        "blocks": page_blocks("privacy", lang),
        "contact_label": page_label("privacy_contact", lang),
    })


def handler404(request, exception=None):
    if not hasattr(request, "aipedia_lang"):
        from .i18n import DEFAULT_LANG
        request.aipedia_lang = DEFAULT_LANG
    return _not_found(request)

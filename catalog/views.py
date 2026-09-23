import secrets
import json
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from .models import (
    Benchmark, Category, Evaluation, ModelVersion, Offer, Platform, Service, Tool,
)
from .seo import alternate_links, public_url, sitemap_entries


def _seo(request, title, description):
    lang = request.aipedia_lang
    page_raw = request.GET.get("page", "")
    page = int(page_raw) if page_raw.isdigit() else None
    indexable_page = page if page and page > 1 else None
    duplicate_page = bool(page_raw) and indexable_page is None
    alternates, x_default = alternate_links(request.path, page=indexable_page)
    return {
        "title": title,
        "description": description[:160],
        "canonical": public_url(request.path, lang, page=indexable_page),
        "alternates": alternates,
        "x_default": x_default,
        "noindex": duplicate_page or any(key not in {"lang", "page"} for key in request.GET),
    }


def _catalog_seo(request, page):
    lang = request.aipedia_lang
    is_tools = request.GET.get("kind") == "tool"
    page_raw = request.GET.get("page", "")
    requested_page = int(page_raw) if page_raw.isdigit() else None
    only_pagination = not any(key not in {"lang", "page"} for key in request.GET)
    indexable_page = requested_page if (
        only_pagination and requested_page and requested_page > 1 and page.number == requested_page
    ) else None
    if lang == "ru":
        title = "AIpediya - " + ("каталог AI-инструментов" if is_tools else "каталог AI-моделей")
        description = (
            "Проверенный каталог AI-инструментов: категории, экосистемы моделей, платформы, доступ и цены."
            if is_tools
            else "Проверенный каталог AI-моделей: назначение, доступ, цены и независимые оценки."
        )
    else:
        title = "AIpediya - " + ("AI tools catalog" if is_tools else "AI model catalog")
        description = (
            "Verified AI tools catalog: categories, model ecosystems, platforms, access, and pricing."
            if is_tools
            else "Verified AI model catalog: capabilities, access methods, prices, and independent evaluations."
        )
    alternates, x_default = alternate_links(request.path, page=indexable_page)
    return {
        "title": title,
        "description": description,
        "canonical": public_url(request.path, lang, page=indexable_page),
        "alternates": alternates,
        "x_default": x_default,
        "noindex": not only_pagination or bool(page_raw) and indexable_page is None,
    }


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


def _tool_catalog_context(request, selected_slug=None):
    qs = tools()
    categories = list(Category.objects.all())
    taxonomy_labels = {item.code: item.labels for item in categories}
    lang = request.aipedia_lang
    q = request.GET.get("q", "").strip()[:200]
    if q.startswith("#") and q[1:].isdigit():
        qs = qs.filter(public_number=int(q[1:]))
    elif q:
        qs = qs.filter(
            Q(name__icontains=q)
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

    sort = request.GET.get("sort", "number_asc")
    orders = [f"{key}_{direction}" for key in TOOL_SORTS for direction in ("asc", "desc")]
    if sort not in orders:
        sort = "number_asc"

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
        "seo": _catalog_seo(request, page),
    }


def _tool_filter_chips(request, lang, **values):
    chips = []

    def add(param, text):
        params = request.GET.copy()
        params.pop(param, None)
        params.pop("page", None)
        chips.append({"label": text, "href": "?" + params.urlencode()})

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
    if values.get("sort") and values["sort"] != "number_asc":
        add("sort", t(values["sort"], lang))
    return chips


def _catalog_context(request, selected_slug=None):
    if request.GET.get("kind") == "tool":
        return _tool_catalog_context(request, selected_slug=selected_slug)
    qs = versions()
    categories = list(Category.objects.all())
    taxonomy_labels = {item.code: item.labels for item in categories}
    q = request.GET.get("q", "").strip()[:200]
    if q.startswith("#") and q[1:].isdigit():
        qs = qs.filter(public_number=int(q[1:]))
    elif q:
        match = (Q(name__icontains=q) | Q(version__icontains=q)
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
    sort = request.GET.get("sort", "number_asc")
    sort = {"score": "check_best", "check_desc": "check_best", "check_asc": "check_worst"}.get(sort, sort)
    orders = [f"{key}_{direction}" for key in TEXT_SORTS for direction in ("asc", "desc")] + ["check_best", "check_worst"]
    if sort not in orders:
        sort = "number_asc"
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
        "seo": _catalog_seo(request, page),
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
        chips.append({"label": label, "href": "?" + params.urlencode() if params else f"?lang={lang}"})

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
    if values["sort"] and values["sort"] != "number_asc":
        add("sort", t(values["sort"], lang))
    return chips


def _render_catalog(request, context):
    if request.GET.get("partial") == "rows":
        response = render(request, "catalog_rows.html", context)
        if context["page"].has_next:
            params = request.GET.copy()
            params["page"] = context["page"].next_page_number()
            params["partial"] = "rows"
            response["X-Aipedia-Next"] = "?" + params.urlencode()
        return response
    if request.GET.get("partial") == "panel":
        if not context.get("selected_entity"):
            return HttpResponseNotFound()
        response = render(request, "panel.html", context)
        response["Cache-Control"] = "no-store"
        response["X-Aipedia-Title"] = context["seo"]["title"]
        response["X-Aipedia-Slug"] = context["selected_entity"].slug
        response["X-Aipedia-Kind"] = context["entity_kind"]
        return response
    return render(request, "catalog.html", context)


@require_GET
def catalog(request):
    return _render_catalog(request, _catalog_context(request))


@require_GET
def detail(request, slug):
    context = _catalog_context(request, selected_slug=slug)
    model = context["selected_model"]
    if not model:
        get_object_or_404(versions(), slug=slug)
    lang = request.aipedia_lang
    description = model.description.get(lang) or model.description.get("en") or model.description.get("ru") or model.name
    version = "" if model.version.casefold() == model.name.casefold() else f" {model.version}"
    context["seo"] = _seo(request, f"{model.name}{version} | AIpediya", description)
    context["facts"] = model.facts_by_key
    return _render_catalog(request, context)


@require_GET
def tool_detail(request, slug):
    params = request.GET.copy()
    params["kind"] = "tool"
    request.GET = params
    context = _tool_catalog_context(request, selected_slug=slug)
    tool = context["selected_tool"]
    if not tool:
        get_object_or_404(tools(), slug=slug)
    description = (
        tool.description.get(request.aipedia_lang)
        or tool.description.get("en")
        or tool.description.get("ru")
        or tool.name
    )
    context["seo"] = _seo(request, f"{tool.name} | AIpediya", description)
    return _render_catalog(request, context)


@require_GET
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


@require_GET
def release_acceptance(request):
    path = Path(settings.BASE_DIR) / 'public-release' / 'aipedia-acceptance-20260920.zip'
    if not path.is_file(): return HttpResponseNotFound()
    return FileResponse(path.open('rb'), as_attachment=True, filename=path.name, content_type='application/zip')


@require_GET
def robots(request):
    body = "\n".join((
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /healthz",
        f"Sitemap: {settings.AIPEDIA_PUBLIC_ORIGIN}/sitemap.xml",
        "",
    ))
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_GET
def sitemap(request):
    rows = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for entry in sitemap_entries():
        lastmod = f"<lastmod>{entry['lastmod'].isoformat()}</lastmod>" if entry["lastmod"] else ""
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{escape(code)}" href="{escape(url)}"/>'
            for code, url in entry["alternates"]
        )
        links += f'<xhtml:link rel="alternate" hreflang="x-default" href="{escape(entry["x_default"])}"/>'
        rows.append(f"<url><loc>{escape(entry['loc'])}</loc>{lastmod}{links}</url>")
    rows.append("</urlset>")
    return HttpResponse("".join(rows), content_type="application/xml; charset=utf-8")


@require_GET
def ads_txt(request):
    body = settings.AIPEDIA_ADS_TXT.strip() or "# AIpediya: ads.txt is not configured."
    return HttpResponse(body + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def indexnow_key(request, key):
    configured = settings.AIPEDIA_INDEXNOW_KEY
    if not configured or not secrets.compare_digest(key, configured):
        return HttpResponseNotFound()
    return HttpResponse(configured + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def privacy(request):
    lang = request.aipedia_lang
    title = "Конфиденциальность | AIpediya" if lang == "ru" else "Privacy | AIpediya"
    description = (
        "Как AIpediya обрабатывает технические данные, согласие и будущую рекламу."
        if lang == "ru"
        else "How AIpediya processes technical data, consent choices, and future advertising."
    )
    from .static_pages import page_blocks, page_label
    return render(request, "privacy.html", {
        "seo": _seo(request, title, description),
        "blocks": page_blocks("privacy", lang),
        "contact_label": page_label("privacy_contact", lang),
    })

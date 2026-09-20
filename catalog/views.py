import secrets
import json
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from .models import Benchmark, Category, Evaluation, ModelVersion, Offer, Service
from .seo import public_url, sitemap_entries


def _seo(request, title, description):
    lang = "en" if request.GET.get("lang") == "en" else "ru"
    page_raw = request.GET.get("page", "")
    page = int(page_raw) if page_raw.isdigit() else None
    indexable_page = page if page and page > 1 else None
    duplicate_page = bool(page_raw) and indexable_page is None
    return {
        "title": title,
        "description": description[:160],
        "canonical": public_url(request.path, lang, page=indexable_page),
        "alternate_ru": public_url(request.path, "ru", page=indexable_page),
        "alternate_en": public_url(request.path, "en", page=indexable_page),
        "noindex": duplicate_page or any(key not in {"lang", "page"} for key in request.GET),
    }


def _catalog_seo(request, page):
    lang = "en" if request.GET.get("lang") == "en" else "ru"
    page_raw = request.GET.get("page", "")
    requested_page = int(page_raw) if page_raw.isdigit() else None
    only_pagination = not any(key not in {"lang", "page"} for key in request.GET)
    indexable_page = requested_page if (
        only_pagination and requested_page and requested_page > 1 and page.number == requested_page
    ) else None
    return {
        "title": "AIpedia - " + ("AI model catalog" if lang == "en" else "каталог нейросетей"),
        "description": (
            "Verified AI model catalog: capabilities, access methods, prices, and independent evaluations."
            if lang == "en"
            else "Проверенный каталог нейросетей: назначение, доступ, цены и независимые оценки."
        ),
        "canonical": public_url(request.path, lang, page=indexable_page),
        "alternate_ru": public_url(request.path, "ru", page=indexable_page),
        "alternate_en": public_url(request.path, "en", page=indexable_page),
        "noindex": not only_pagination or bool(page_raw) and indexable_page is None,
    }


def versions():
    return ModelVersion.objects.filter(published=True).select_related(
        "family__developer__source", "source"
    ).prefetch_related(
        "offers__service__provider", "offers__source", "evaluations__benchmark",
        "evaluations__source", "accesses__service__provider", "accesses__source",
        "facts__source", "audits__source",
    )


from .comparison import decorate, sort_models, price_matches, condition_key, localized


@require_GET
def catalog(request):
    qs = versions()
    categories = list(Category.objects.all())
    taxonomy_labels = {item.code: item.labels for item in categories}
    q = request.GET.get("q", "").strip()[:200]
    if q.startswith("#") and q[1:].isdigit():
        qs = qs.filter(public_number=int(q[1:]))
    elif q:
        from .context import TEXT
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

    access = request.GET.get("access", "")
    access_kinds = [code for code, _ in Service._meta.get_field("kind").choices]
    if access in access_kinds:
        qs = qs.filter(accesses__service__kind=access)

    status = request.GET.get("status", "active")
    if status not in {"active", "archived", "all"}:
        status = "active"
    if status != "all":
        qs = qs.filter(catalog_status=status)

    lang = "en" if request.GET.get("lang") == "en" else "ru"
    sort = request.GET.get("sort", "number_asc")
    sort = {"score": "check_best", "check_desc": "check_best", "check_asc": "check_worst"}.get(sort, sort)
    orders = [f"{key}_{direction}" for key in ("number", "name", "purpose", "price", "access") for direction in ("asc", "desc")] + ["check_best", "check_worst"]
    if sort not in orders: sort = "number_asc"
    price_scope = request.GET.get("price_scope", "standard")
    if price_scope not in {"standard", "batch", "offpeak", "peak", "flex", "fast", "priority", "free", "annual", "all"}: price_scope = "standard"
    price_variant = request.GET.get("price_variant", "base")
    if price_variant not in {"base", "long", "all"}: price_variant = "base"
    price_modality = request.GET.get('price_modality', 'text')
    if price_modality not in {'text', 'audio', 'image'}: price_modality = 'text'
    price_units = list(Offer.objects.filter(active=True, amount__isnull=False, billing_unit="").exclude(unit="other").order_by("unit").values_list("unit", flat=True).distinct())
    price_unit = request.GET.get("price_unit", "")
    if sort.startswith("price_") and not price_unit: price_unit = "input"
    if price_unit not in price_units: price_unit = "input" if sort.startswith("price_") else ""
    benchmarks = list(Benchmark.objects.filter(evaluation__public=True).distinct().order_by("name", "protocol", "pk"))
    try: benchmark_id = int(request.GET.get("benchmark", ""))
    except (TypeError, ValueError): benchmark_id = None
    benchmark = next((b for b in benchmarks if b.pk == benchmark_id), None)
    if not benchmark and sort.startswith("check_"):
        benchmark = next((b for b in benchmarks if b.name == "ECI"), benchmarks[0] if benchmarks else None)
    configurations = sorted(set(Evaluation.objects.filter(public=True, benchmark=benchmark).values_list("configuration", flat=True))) if benchmark else []
    configuration = request.GET.get("configuration", "")
    if configuration not in configurations: configuration = configurations[0] if configurations else ""
    snapshots = sorted(set(Evaluation.objects.filter(public=True, benchmark=benchmark, configuration=configuration).values_list("snapshot", flat=True)), reverse=True) if benchmark else []
    snapshot = request.GET.get("snapshot", "")
    if snapshot not in snapshots: snapshot = snapshots[0] if snapshots else ""
    models = list(qs.distinct())
    price_conditions = {}
    for model in models:
        for offer in model.offers.all():
            if price_matches(offer, price_unit, price_scope, price_variant, modality=price_modality):
                from .price_text import full_conditions
                price_conditions[condition_key(offer)] = full_conditions(offer.conditions, lang)
    price_condition = request.GET.get("price_condition", "")
    if price_condition not in price_conditions: price_condition = ""
    # Media and subscription offers can use incompatible resolutions/tiers even
    # within one unit. Require one displayed condition for their comparison.
    if price_unit and price_unit not in {"input", "output", "cache_read", "cache_write"} and not price_condition and price_conditions:
        price_condition = sorted(price_conditions)[0]
    for model in models:
        decorate(model, taxonomy_labels, price_unit, benchmark, price_scope, lang, configuration, snapshot, price_variant, price_condition, price_modality)
    if request.GET.get("evaluated_only") == "1" and benchmark:
        models = [m for m in models if m.comparison_evaluation]
    models = sort_models(models, sort, benchmark)
    page = Paginator(models, 25).get_page(request.GET.get("page"))
    counts = versions().aggregate(
        models=Count("pk", filter=Q(entry_type="model")),
        products=Count("pk", filter=~Q(entry_type="model")),
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
        "comparison_count": sum(bool(m.comparison_offer) for m in models),
        "developers": ModelVersion.objects.filter(published=True).values("family__developer_id", "family__developer__name").distinct().order_by("family__developer__name"),
        "found_count": page.paginator.count, "shown_count": len(page.object_list),
        "seo": _catalog_seo(request, page),
    }
    if request.GET.get("partial") == "rows":
        response = render(request, "catalog_rows.html", context)
        if page.has_next():
            params = request.GET.copy()
            params["page"] = page.next_page_number()
            response["X-Aipedia-Next"] = "?" + params.urlencode()
        return response
    return render(request, "catalog.html", context)


@require_GET
def detail(request, slug):
    taxonomy_labels = {item.code: item.labels for item in Category.objects.all()}
    model = decorate(get_object_or_404(versions(), slug=slug), taxonomy_labels, lang="en" if request.GET.get("lang") == "en" else "ru")
    lang = "en" if request.GET.get("lang") == "en" else "ru"
    description = model.description.get(lang) or model.description.get("en") or model.name
    version = "" if model.version.casefold() == model.name.casefold() else f" {model.version}"
    context = {
        "model": model,
        "public_number": model.public_number,
        "catalog_status": model.catalog_status,
        "facts": {item.key: item for item in model.facts.all()},
        "seo": _seo(request, f"{model.name}{version} | AIpedia", description),
    }
    return render(request, "detail.html", context)


@require_GET
def health(request):
    ModelVersion.objects.exists()
    path = Path(settings.BASE_DIR) / 'BUILD.json'
    build = json.loads(path.read_text()) if path.exists() else {}
    return JsonResponse({"service": "aipedia", "status": "ok", "release": build.get('commit', 'local')})


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
    rows = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, checked in sitemap_entries():
        lastmod = f"<lastmod>{checked.isoformat()}</lastmod>" if checked else ""
        rows.append(f"<url><loc>{escape(url)}</loc>{lastmod}</url>")
    rows.append("</urlset>")
    return HttpResponse("".join(rows), content_type="application/xml; charset=utf-8")


@require_GET
def ads_txt(request):
    body = settings.AIPEDIA_ADS_TXT.strip() or "# AIpedia: ads.txt is not configured."
    return HttpResponse(body + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def indexnow_key(request, key):
    configured = settings.AIPEDIA_INDEXNOW_KEY
    if not configured or not secrets.compare_digest(key, configured):
        return HttpResponseNotFound()
    return HttpResponse(configured + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def privacy(request):
    lang = "en" if request.GET.get("lang") == "en" else "ru"
    title = "Privacy | AIpedia" if lang == "en" else "Конфиденциальность | AIpedia"
    description = (
        "How AIpedia processes technical data, consent choices, and future advertising."
        if lang == "en"
        else "Как AIpedia обрабатывает технические данные, согласие и будущую рекламу."
    )
    return render(request, "privacy.html", {"seo": _seo(request, title, description)})

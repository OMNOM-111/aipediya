"""Page-level search signals and the sitemap graph (GSD-04).

All absolute URLs come from :mod:`catalog.locale_urls` (settings origin, never
the request Host). Alternates are limited to locales that are indexable for
the page according to :mod:`catalog.readiness`, so HTML hreflang, sitemap
alternates and the readiness registry always describe the same URL set.
"""
import json
from datetime import date, datetime

from django.utils.html import escape

from .i18n import DEFAULT_LANG, SUPPORTED_CODES
from .locale_urls import absolute, localize

# hreflang values are BCP-47 language(-script/-region) tags.
HREFLANG = {code: code for code in SUPPORTED_CODES}


def page_signals(neutral_path, lang, *, title, description, ready_langs, indexable=True, page=None,
                 og_type="website", json_ld=None, breadcrumbs=None):
    """Return the ``seo`` dict consumed by ``base.html``.

    ``indexable`` False (filtered listing, not-ready locale, 404) yields
    ``noindex,follow`` with no canonical and no alternates, so a noindex page
    never advertises itself or claims reciprocity.
    """
    ready = [code for code in SUPPORTED_CODES if code in set(ready_langs)]
    indexable = indexable and lang in ready
    signals = {
        "title": title,
        "description": _clip(description),
        "noindex": not indexable,
        "canonical": "",
        "alternates": [],
        "x_default": "",
        "og_type": og_type,
        "og_locale": lang.replace("-", "_"),
        "json_ld": [item for item in (json_ld or []) if item],
        # One trail feeds both the visible breadcrumb and BreadcrumbList, so the
        # structured data never describes navigation that readers cannot see.
        "breadcrumbs": [(name, localize(path, lang)) for name, path in (breadcrumbs or [])],
    }
    if breadcrumbs:
        signals["json_ld"].append({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": index, "name": name, "item": absolute(path, lang)}
                for index, (name, path) in enumerate(breadcrumbs, start=1)
            ],
        })
    if indexable:
        signals["canonical"] = absolute(neutral_path, lang, page=page)
        signals["alternates"] = [(HREFLANG[code], absolute(neutral_path, code, page=page)) for code in ready]
        if DEFAULT_LANG in ready:
            signals["x_default"] = absolute(neutral_path, DEFAULT_LANG, page=page)
    signals["og_url"] = signals["canonical"] or absolute(neutral_path, lang)
    return signals


def _clip(text, limit=158):
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def json_ld_script(data):
    """Serialize JSON-LD safely for embedding inside <script>."""
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=_default)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(type(value))


# ---------------------------------------------------------------- sitemap graph

def site_pages():
    """Yield sitemap entries ``{"path", "langs", "lastmod"}`` from the registry.

    Language-neutral paths; one entry per page, listing its indexable locales.
    """
    from django.db.models import Max

    from . import readiness
    from .hubs import HUBS, ready_locales as hub_locales, members
    from .models import ContentTranslation, PublicationRevision, ToolPublicationRevision
    from .static_pages import page_ready
    from .datasets import datasets_enabled, dataset_page_langs

    models = list(readiness.public_models().only("pk", "slug", "checked", "description", "suitable",
                                                 "limitations", "published", "entry_type"))
    tools = list(readiness.public_tools().only("pk", "slug", "checked", "description", "published"))
    latest_model = max((m.checked for m in models), default=None)
    latest_tool = max((t.checked for t in tools), default=None)

    from .static_pages import labels_ready
    # Every rule below is the same one the corresponding view applies.
    def labelled(keys):
        return [c for c in SUPPORTED_CODES if labels_ready(keys, c)]

    yield {"path": "/", "langs": labelled(["models_catalog_title", "models_catalog_description", "page_n"]),
           "lastmod": latest_model}
    yield {"path": "/tools/", "langs": labelled(["tools_catalog_title", "tools_catalog_description", "page_n"]),
           "lastmod": latest_tool}
    yield {"path": "/methodology", "langs": [c for c in SUPPORTED_CODES if page_ready("methodology", c)
                                             and labels_ready(["methodology_description"], c)],
           "lastmod": None}
    # Same readiness rule as views.privacy (indexable only where fully localized).
    yield {"path": "/privacy", "langs": [c for c in SUPPORTED_CODES if page_ready("privacy", c)],
           "lastmod": None}
    hub_langs_any = set()
    from .hubs import HUB_LABELS
    for hub in HUBS.values():
        count = len(members(hub))
        langs = hub_locales(hub, count)
        if langs:
            hub_langs_any.update(langs)
            yield {"path": f"/collections/{hub.slug}", "langs": langs,
                   "lastmod": latest_tool if hub.kind == "tool" else latest_model}
    if hub_langs_any:
        yield {"path": "/collections/", "langs": [c for c in SUPPORTED_CODES if c in hub_langs_any
                                                  and labels_ready(HUB_LABELS + ("collections_intro",), c)],
               "lastmod": None}
    if datasets_enabled():
        langs = dataset_page_langs()
        yield {"path": "/datasets/", "langs": langs, "lastmod": None}
        yield {"path": "/datasets/models", "langs": langs, "lastmod": latest_model}
        yield {"path": "/datasets/tools", "langs": langs, "lastmod": latest_tool}

    # Entity pages: lastmod = the newest of the editorial check date, the last
    # publication change and (per locale) the last translation update. Viewing a
    # page never changes any of these.
    pub_model = dict(PublicationRevision.objects.order_by().values_list("model_id").annotate(last=Max("created")))
    pub_tool = dict(ToolPublicationRevision.objects.order_by().values_list("tool_id").annotate(last=Max("created")))
    for kind, objects, pub, entity_type in (
        ("models", models, pub_model, "model"), ("tools", tools, pub_tool, "tool"),
    ):
        rows = readiness._rows_for(entity_type, [obj.pk for obj in objects])
        updated = {}
        for object_id, language, stamp in ContentTranslation.objects.filter(
            entity_type=entity_type, object_id__in=[obj.pk for obj in objects]
        ).order_by().values_list("object_id", "language").annotate(last=Max("updated")):
            updated[(object_id, language)] = stamp
        for obj in objects:
            langs = [lang for lang in SUPPORTED_CODES
                     if readiness.evaluate(obj, lang, rows.get(obj.pk, {})).indexable]
            if not langs:
                continue
            base = _latest(obj.checked, pub.get(obj.pk))
            lastmod = {lang: _latest(base, updated.get((obj.pk, lang))) for lang in langs}
            yield {"path": f"/{kind}/{obj.slug}", "langs": langs, "lastmod": lastmod}


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def _latest(*values):
    dates = [_as_date(value) for value in values if value is not None]
    return max(dates) if dates else None


def sitemap_urlsets():
    """``{lang: [url entries]}``: every indexable address grouped by its locale."""
    sets = {code: [] for code in SUPPORTED_CODES}
    for page in site_pages():
        langs = page["langs"]
        alternates = [(HREFLANG[code], absolute(page["path"], code)) for code in langs]
        x_default = absolute(page["path"], DEFAULT_LANG) if DEFAULT_LANG in langs else ""
        for lang in langs:
            lastmod = page["lastmod"].get(lang) if isinstance(page["lastmod"], dict) else page["lastmod"]
            sets[lang].append({
                "loc": absolute(page["path"], lang),
                "lastmod": lastmod,
                "alternates": alternates,
                "x_default": x_default,
            })
    return sets


def render_urlset(entries):
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for entry in entries:
        lastmod = f"<lastmod>{entry['lastmod'].isoformat()}</lastmod>" if entry["lastmod"] else ""
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{escape(code)}" href="{escape(url)}"/>'
            for code, url in entry["alternates"]
        )
        if entry["x_default"]:
            links += f'<xhtml:link rel="alternate" hreflang="x-default" href="{escape(entry["x_default"])}"/>'
        rows.append(f"<url><loc>{escape(entry['loc'])}</loc>{lastmod}{links}</url>")
    rows.append("</urlset>")
    return "\n".join(rows)


def render_index(sets):
    from .locale_urls import URL_CODE
    from django.conf import settings

    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for lang, entries in sets.items():
        if not entries:
            continue
        stamps = [entry["lastmod"] for entry in entries if entry["lastmod"]]
        lastmod = f"<lastmod>{max(stamps).isoformat()}</lastmod>" if stamps else ""
        rows.append(f"<sitemap><loc>{escape(settings.AIPEDIA_PUBLIC_ORIGIN)}/sitemaps/{URL_CODE[lang]}.xml</loc>{lastmod}</sitemap>")
    rows.append("</sitemapindex>")
    return "\n".join(rows)

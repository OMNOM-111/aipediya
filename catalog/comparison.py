"""Server-side comparison keys, shared by sorting and displayed cells."""
import re
import unicodedata
import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from .context import TEXT
from .marks import mark_for
from .public_text import public_text

SCOPE_GROUPS = {
    "free": ("free", "бесплат"),
    "batch": ("batch",),
    "offpeak": ("off-peak", "off peak", "непиков"),
    "annual": ("annual", "annually", "годов"),
    "flex": ("flex",),
    "fast": ("fast", "high-speed"),
    "priority": ("priority",),
    "peak": ("peak",),
}

TOOL_COUNTRY_ALIASES = {
    "australia": "AU", "canada": "CA", "china": "CN",
    "czech republic": "CZ", "france": "FR", "germany": "DE",
    "india": "IN", "israel": "IL", "netherlands": "NL",
    "russia": "RU", "south korea": "KR", "sweden": "SE",
    "uk": "GB", "usa": "US",
}
COUNTRY_LABELS = {
    "AU": ("Австралия", "Australia"), "CA": ("Канада", "Canada"),
    "CN": ("Китай", "China"), "CZ": ("Чехия", "Czech Republic"),
    "FR": ("Франция", "France"), "DE": ("Германия", "Germany"),
    "IN": ("Индия", "India"), "IL": ("Израиль", "Israel"),
    "NL": ("Нидерланды", "Netherlands"), "RU": ("Россия", "Russia"),
    "KR": ("Южная Корея", "South Korea"), "SE": ("Швеция", "Sweden"),
    "GB": ("Великобритания", "United Kingdom"), "US": ("США", "United States"),
}


def developer_countries(value):
    """Convert verified Organization.country text to display-only badges."""
    codes = []
    for part in re.split(r"[/,;]", value or ""):
        code = TOOL_COUNTRY_ALIASES.get(part.strip().casefold())
        if code and code not in codes:
            codes.append(code)
    return [
        SimpleNamespace(code=code, name_ru=COUNTRY_LABELS[code][0], name_en=COUNTRY_LABELS[code][1])
        for code in codes
    ]


def localized(value, lang):
    if isinstance(value, dict):
        text = value.get(lang) or value.get('en') or value.get('ru') or next((item for item in value.values() if item), '')
    else:
        text = str(value)
    # Some imported source prose was JSON-escaped twice. Decode only Unicode
    # escapes, leaving ordinary backslashes and non-ASCII characters intact.
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), text)
    return public_text(text, lang)


def alphabet(value):
    return unicodedata.normalize('NFKC', value).casefold().replace('ё', 'е')


def label(code, lang):
    from .context import t
    return t(code, lang)


def task_label(task, taxonomy_labels, lang):
    """Localized use-case label: category taxonomy first, then the UI table."""
    from .context import category_label
    labels = taxonomy_labels.get(task)
    if labels is not None:
        return category_label(task, labels, lang)
    return label(task, lang)


@lru_cache(maxsize=1)
def gap_notes():
    path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation_gap_notes.json'
    return json.loads(path.read_text(encoding='utf-8-sig')).get('by_slug', {}) if path.exists() else {}


def offer_condition_text(offer):
    return ' '.join(localized(offer.conditions, lang) for lang in ('ru', 'en')).casefold()


def offer_scope_tags(offer):
    text = offer_condition_text(offer)
    found = {key for key, terms in SCOPE_GROUPS.items() if any(
        re.search(r'(?:^| · )' + re.escape(term) + r'(?:\b| tier)', text) for term in terms)}
    if 'offpeak' in found:
        found.discard('peak')
    return frozenset(found)


def price_matches(offer, unit, scope='standard', variant='base', condition='', modality='text'):
    if not offer.active or offer.amount is None or offer.billing_unit or offer.unit != unit:
        return False
    if offer.service.kind not in ({'web', 'app', 'cli', 'ide'} if unit in {'month', 'year'} else {'api'}):
        return False
    text = offer_condition_text(offer)
    found = offer_scope_tags(offer)
    if scope == 'standard' and found or scope not in {'standard', 'all'} and scope not in found:
        return False
    long_context = any(term in text for term in ('long context', '>200', '> 200', 'over 200', 'свыше 200', '>512', '> 512'))
    if unit in {'input', 'output', 'cache_read', 'cache_write'}:
        # This basis is explicitly text tokens. Audio/image token offers must
        # never silently enter the text-token comparison.
        offer_modality = 'image' if any(term in text for term in (' · image', 'image tokens')) else 'audio' if any(term in text for term in (' · audio', 'audio tokens', 'только аудиотокены', 'по входным и выходным аудиотокенам')) else 'text'
        if offer_modality != modality:
            return False
        if variant == 'base' and long_context or variant == 'long' and not long_context:
            return False
    if condition and condition != condition_key(offer):
        return False
    return True


def condition_key(offer):
    import hashlib
    return hashlib.sha256(localized(offer.conditions, 'en').encode()).hexdigest()[:16]


def decorate(model, taxonomy_labels=None, price_unit='', benchmark=None, price_scope='standard',
             lang='ru', configuration=None, snapshot=None, price_variant='base', price_condition='', price_modality='text'):
    taxonomy_labels = taxonomy_labels or {}
    model.current_offers = [o for o in model.offers.all() if o.active]
    from .price_text import full_conditions
    for offer in model.current_offers:
        offer.display_conditions = full_conditions(offer.conditions, lang)
    model.display_offers = [o for o in model.current_offers if o.primary]
    model.public_evaluations = sorted([e for e in model.evaluations.all() if e.public],
        key=lambda e: (e.result_kind != 'composite', e.benchmark.name, e.configuration, e.pk))
    model.task_labels = sorted(set(task_label(task, taxonomy_labels, lang)
                                   for task in model.tasks), key=alphabet)
    model.purpose_key = alphabet(' · '.join(model.task_labels))
    model.sorted_accesses = sorted(model.accesses.all(),
        key=lambda a: (alphabet(label(a.service.kind, lang)), alphabet(localized(a.service.provider.name, lang)), a.pk))
    model.access_labels = sorted(set(label(a.service.kind, lang) for a in model.sorted_accesses), key=alphabet)
    model.access_key = alphabet(' · '.join(model.access_labels))
    model.local_execution = any(a.service.compute_location == 'local' for a in model.sorted_accesses)
    candidates = [o for o in model.current_offers if price_matches(o, price_unit, price_scope, price_variant, price_condition, price_modality)]
    model.comparison_offer = min(candidates, key=lambda o: (o.amount, o.pk)) if candidates else None
    candidates = [e for e in model.public_evaluations if benchmark and e.benchmark_id == benchmark.pk
                  and (configuration is None or e.configuration == configuration)
                  and (snapshot is None or e.snapshot == snapshot)]
    # Never silently pick the best run. Most recent measurement, then stable ID.
    candidates.sort(key=lambda e: (str(e.measured or e.checked), e.pk), reverse=True)
    model.comparison_evaluation = candidates[0] if candidates else None
    model.more_evaluations = max(0, len(model.public_evaluations) - 2)
    model.evaluation_gap = gap_notes().get(model.slug) if not model.public_evaluations else None
    model.type_key = alphabet(label(model.entry_type, lang))
    model.status_key = alphabet(label(model.catalog_status, lang))
    model.developer_name = localized(model.family.developer.name, lang)
    model.developer_key = alphabet(model.developer_name)
    model.display_version = "" if model.version.casefold() == model.name.casefold() else model.version
    model.initials = initials_for(model.developer_name or model.name)
    model.mark = mark_for(model.family.developer.name)
    model.table_evaluations = [
        item for item in model.public_evaluations
        if item.independent or item.result_kind == "composite"
    ]
    model.table_offers = paired_primary_offers(model)
    model.resource_links = resource_links(model, lang)
    model.facts_by_key = {item.key: item for item in model.facts.all()}
    model.origin_countries = [link.country for link in model.origin_country_links.all()]
    return model


def sort_models(models, sort, benchmark=None):
    # Stable secondary key is the chronological number, then database identity.
    models.sort(key=lambda m: (m.public_number is None, m.public_number or m.pk))
    descending = sort.endswith('_desc') or sort == 'check_best' and (not benchmark or benchmark.higher_is_better) or sort == 'check_worst' and benchmark and not benchmark.higher_is_better
    def key(m):
        if sort.startswith('number_'): return m.public_number
        if sort.startswith('name_'): return alphabet(m.name)
        if sort.startswith('purpose_'): return m.purpose_key or None
        if sort.startswith('access_'): return m.access_key or None
        if sort.startswith('type_'): return m.type_key or None
        if sort.startswith('developer_'): return m.developer_key or None
        if sort.startswith('status_'): return m.status_key or None
        if sort.startswith('context_'): return m.context
        if sort.startswith('release_'): return m.released or m.approx_released
        if sort.startswith('price_'): return m.comparison_offer.amount if m.comparison_offer else None
        return m.comparison_evaluation.score if m.comparison_evaluation else None
    known = [m for m in models if key(m) is not None]
    missing = [m for m in models if key(m) is None]
    return sorted(known, key=key, reverse=bool(descending)) + missing


def decorate_tool(tool, taxonomy_labels=None, price_unit='', price_scope='standard',
                  lang='ru', price_variant='base', price_condition='', price_modality='text'):
    """Build the Tools view model without model-only evaluation/context data."""
    taxonomy_labels = taxonomy_labels or {}
    tool.task_labels = sorted(
        set(
            task_label(task, taxonomy_labels, lang)
            for task in tool.purposes
        ),
        key=alphabet,
    )
    tool.purpose_key = alphabet(' · '.join(tool.task_labels))
    tool.developer_name = localized(tool.developer.name, lang)
    tool.developer_key = alphabet(tool.developer_name)
    tool.category_label = label(tool.category, lang)
    tool.category_key = alphabet(tool.category_label)
    tool.ecosystem_text = localized(tool.ecosystem, lang)
    tool.ecosystem_key = alphabet(tool.ecosystem_text)
    tool.sorted_platforms = [link.platform for link in tool.platform_links.all()]
    tool.platform_labels = [localized(platform.labels, lang) for platform in tool.sorted_platforms]
    tool.platform_key = alphabet(' · '.join(tool.platform_labels))
    tool.local_label = label(tool.local_execution, lang) if tool.local_execution else ''
    tool.local_key = alphabet(tool.local_label)
    tool.status_key = alphabet(label(tool.catalog_status, lang))
    tool.initials = initials_for(tool.developer_name or tool.name)
    tool.mark = mark_for(tool.developer.name)
    tool.display_version = "" if tool.version.casefold() == tool.name.casefold() else tool.version
    tool.origin_countries = developer_countries(tool.developer.country)

    legacy = tool.legacy_version
    tool.current_offers = []
    tool.sorted_accesses = []
    tool.access_labels = []
    tool.table_offers = []
    tool.comparison_offer = None
    if legacy:
        tool.current_offers = [offer for offer in legacy.offers.all() if offer.active]
        from .price_text import full_conditions

        for offer in tool.current_offers:
            offer.display_conditions = full_conditions(offer.conditions, lang)
        tool.table_offers = paired_primary_offers(tool)
        candidates = [
            offer
            for offer in tool.current_offers
            if price_matches(
                offer, price_unit, price_scope, price_variant, price_condition, price_modality
            )
        ]
        tool.comparison_offer = min(candidates, key=lambda offer: (offer.amount, offer.pk)) if candidates else None
        tool.sorted_accesses = sorted(
            legacy.accesses.all(),
            key=lambda access: (
                alphabet(label(access.service.kind, lang)),
                alphabet(localized(access.service.provider.name, lang)),
                access.pk,
            ),
        )
        tool.access_labels = sorted(
            set(label(access.service.kind, lang) for access in tool.sorted_accesses), key=alphabet
        )
    tool.resource_links = []
    if tool.official_url:
        tool.resource_links.append(
            {"kind": "provider", "url": tool.official_url, "label": label("official_link", lang)}
        )
    # Only published catalog models may be linked; hidden records never leak.
    tool.linked_models = [
        link.model for link in tool.model_links.all()
        if link.model.published and link.model.entry_type == "model"
    ]
    return tool


def sort_tools(tools, sort):
    tools.sort(key=lambda tool: (tool.public_number is None, tool.public_number or tool.pk))
    descending = sort.endswith('_desc')

    def key(tool):
        if sort.startswith('number_'):
            return tool.public_number
        if sort.startswith('name_'):
            return alphabet(tool.name)
        if sort.startswith('category_'):
            return tool.category_key or None
        if sort.startswith('developer_'):
            return tool.developer_key or None
        if sort.startswith('purpose_'):
            return tool.purpose_key or None
        if sort.startswith('ecosystem_'):
            return tool.ecosystem_key or None
        if sort.startswith('platform_'):
            return tool.platform_key or None
        if sort.startswith('price_'):
            return tool.comparison_offer.amount if tool.comparison_offer else None
        if sort.startswith('local_'):
            return tool.local_key or None
        if sort.startswith('release_'):
            return tool.released or tool.approx_released
        return tool.public_number

    known = [tool for tool in tools if key(tool) is not None]
    missing = [tool for tool in tools if key(tool) is None]
    return sorted(known, key=key, reverse=descending) + missing


def initials_for(name):
    parts = [part for part in re.split(r"\s+", (name or "").strip()) if part]
    if not parts:
        return "?"
    first = parts[0][:1]
    second = parts[1][:1] if len(parts) > 1 else ""
    return (first + second).upper()


def paired_primary_offers(model):
    primaries = [offer for offer in model.current_offers if offer.primary and offer.amount is not None]
    selected = list(primaries)
    have_units = {(offer.service_id, offer.unit) for offer in selected}
    complements = {"input": "output", "output": "input"}
    for offer in primaries:
        want = complements.get(offer.unit)
        if not want or (offer.service_id, want) in have_units:
            continue
        tags = offer_scope_tags(offer)
        match = next(
            (
                other for other in model.current_offers
                if other.service_id == offer.service_id
                and other.unit == want
                and other.amount is not None
                and offer_scope_tags(other) == tags
            ),
            None,
        )
        if match:
            selected.append(match)
            have_units.add((match.service_id, match.unit))
    order = {"input": 0, "output": 1, "cache_read": 2, "cache_write": 3}
    selected.sort(key=lambda offer: (order.get(offer.unit, 9), offer.pk))
    return selected


def _is_github_repo(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "github.com" not in host:
        return False
    parts = [part for part in parsed.path.split("/") if part]
    blocked = {"features", "topics", "orgs", "settings", "marketplace", "pricing", "login", "about", "collections"}
    return len(parts) >= 2 and parts[0].casefold() not in blocked


def _is_docs_url(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    return "docs" in host or "/docs" in path or "documentation" in path or "ai.google.dev" in host


def resource_links(model, lang):
    items = []
    seen = set()

    def add(kind, url, label_key):
        url = (url or "").strip()
        if not url or url in seen:
            return
        seen.add(url)
        items.append({"kind": kind, "url": url, "label": label(label_key, lang)})

    provider = None
    docs = None
    github = None
    for access in model.sorted_accesses:
        url = access.service.url
        if _is_github_repo(url):
            github = github or url
        elif _is_docs_url(url):
            docs = docs or url
        elif access.service.kind in {"web", "app", "api"} and not provider:
            provider = url
    source_url = model.source.url if model.source_id else ""
    if source_url:
        if _is_github_repo(source_url):
            github = github or source_url
        elif _is_docs_url(source_url):
            docs = docs or source_url
    if provider:
        add("provider", provider, "go_to_provider")
    if docs:
        add("docs", docs, "documentation")
    if github:
        add("github", github, "github")
    return items


def format_context(value):
    if value in (None, ""):
        return ""
    number = int(value)
    if number % 1_000_000 == 0:
        return f"{number // 1_000_000}M"
    if number % 1000 == 0:
        return f"{number // 1000}K"
    return f"{number:,}".replace(",", " ")


def page_window(page, radius=2):
    total = page.paginator.num_pages
    current = page.number
    chosen = {1, total} if total else set()
    for number in range(current - radius, current + radius + 1):
        if 1 <= number <= total:
            chosen.add(number)
    result = []
    previous = 0
    for number in sorted(chosen):
        if previous and number > previous + 1:
            result.append(None)
        result.append(number)
        previous = number
    return result

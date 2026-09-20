"""Server-side comparison keys, shared by sorting and displayed cells."""
import re
import unicodedata
import json
from functools import lru_cache
from pathlib import Path
from .context import TEXT
from .public_text import public_text


def localized(value, lang):
    text = value.get(lang) or value.get('ru') or value.get('en') or '' if isinstance(value, dict) else str(value)
    # Some imported source prose was JSON-escaped twice. Decode only Unicode
    # escapes, leaving ordinary backslashes and non-ASCII characters intact.
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), text)
    return public_text(text, lang)


def alphabet(value):
    return unicodedata.normalize('NFKC', value).casefold().replace('ё', 'е')


def label(code, lang):
    return TEXT.get(code, (code, code))[lang == 'en']


@lru_cache(maxsize=1)
def gap_notes():
    path = Path(__file__).resolve().parent.parent / 'data' / 'evaluation_gap_notes.json'
    return json.loads(path.read_text(encoding='utf-8-sig')).get('by_slug', {}) if path.exists() else {}


def price_matches(offer, unit, scope='standard', variant='base', condition='', modality='text'):
    if not offer.active or offer.amount is None or offer.billing_unit or offer.unit != unit:
        return False
    if offer.service.kind not in ({'web', 'app', 'cli', 'ide'} if unit in {'month', 'year'} else {'api'}):
        return False
    text = ' '.join(localized(offer.conditions, lang) for lang in ('ru', 'en')).casefold()
    groups = {
        'free': ('free', 'бесплат'), 'batch': ('batch',),
        'offpeak': ('off-peak', 'off peak', 'непиков'),
        'annual': ('annual', 'annually', 'годов'),
        'flex': ('flex',), 'fast': ('fast', 'high-speed'), 'priority': ('priority',), 'peak': ('peak',),
    }
    # Match the plan label, not phrases such as "no free tier" in a paid plan's notes.
    found = {key for key, terms in groups.items() if any(
        re.search(r'(?:^| · )' + re.escape(term) + r'(?:\b| tier)', text) for term in terms)}
    if 'offpeak' in found: found.discard('peak')
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
    model.task_labels = sorted(set(localized(taxonomy_labels.get(task, label(task, lang)), lang)
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
        if sort.startswith('price_'): return m.comparison_offer.amount if m.comparison_offer else None
        return m.comparison_evaluation.score if m.comparison_evaluation else None
    known = [m for m in models if key(m) is not None]
    missing = [m for m in models if key(m) is None]
    return sorted(known, key=key, reverse=bool(descending)) + missing

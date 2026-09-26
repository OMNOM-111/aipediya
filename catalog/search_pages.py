"""Two finite, source-backed search reference pages over published records.

These are not faceted URL generators. Unknown values stay absent and prices
are paired only within one provider and the standard base text-token tier.
"""
from . import readiness
from .comparison import offer_scope_tags, price_matches
from .models import Offer
from urllib.parse import urlparse


# Deliberately finite. A newly imported provider is reviewed before its price
# can be described here as the developer's own standard API list price.
OFFICIAL_PRICE_HOSTS = {
    "OpenAI": ("openai.com",),
    "Anthropic": ("anthropic.com",),
    "Alibaba Cloud / Qwen Team": ("alibabacloud.com",),
    "Google": ("ai.google.dev", "cloud.google.com"),
    "Mistral AI": ("mistral.ai",),
    "Z.ai / Zhipu AI": ("z.ai", "bigmodel.cn"),
    "MiniMax": ("minimax.io", "minimaxi.com"),
    "Moonshot AI / Kimi": ("moonshot.ai", "moonshot.cn"),
}


def _official_standard(offer):
    hosts = OFFICIAL_PRICE_HOSTS.get(offer.service.provider.name, ())
    host = (urlparse(offer.source.url).hostname or "").lower()
    if not any(host == domain or host.endswith("." + domain) for domain in hosts):
        return False
    conditions = " ".join(str(value) for value in offer.conditions.values()).casefold()
    return "не нормализован" not in conditions and "not normalized" not in conditions


COPY = {
    "en": {
        "context_title": "Compare AI model context windows",
        "context_description": "Compare documented context-window sizes across published AI models, with model cards, source links and check dates.",
        "context_intro": "A context window is the maximum token span recorded for a model, not a measure of answer quality. Limits can depend on provider, tier and configuration. Check the linked model and provider source before using a limit in production.",
        "context_method": "The table includes published models with a recorded context window, ordered by token count. Missing limits are omitted, not treated as zero. Equal or larger windows do not imply better coding or reasoning results.",
        "pricing_title": "AI model API prices: input and output tokens",
        "pricing_description": "Compare verified standard API list prices per 1 million text input and output tokens, with provider sources, conditions and check dates.",
        "pricing_intro": "Input and output tokens are billed separately. This table shows only active, primary, standard base-text API offers with both prices from the same service. Batch, cache, long-context and audio/image-token rates are excluded.",
        "pricing_method": "These are provider list prices in USD per 1 million tokens, not a total-cost or quality ranking. Taxes, minimum charges, region, quotas and changes after the check date can affect a real bill. Missing prices are not zero; see each card for other tiers.",
        "model": "Model", "developer": "Developer", "context": "Context (tokens)",
        "input": "Input / 1M", "output": "Output / 1M", "provider": "API provider",
        "source": "Source", "checked": "Checked", "conditions": "Conditions",
        "related": "Related catalog pages", "pricing_link": "API pricing", "context_link": "Context comparison",
        "coding_link": "Models for programming", "api_link": "Models with API access",
        "long_link": "Long-context models", "methodology_link": "Sources and methodology",
    },
    "ru": {
        "context_title": "Сравнение контекстных окон AI-моделей",
        "context_description": "Сравнение документированных размеров контекста опубликованных AI-моделей со ссылками на карточки, источники и даты проверки.",
        "context_intro": "Контекстное окно — записанный предел токенов модели, а не оценка качества ответа. Ограничение зависит от поставщика, тарифа и конфигурации. Перед применением проверьте карточку и источник разработчика.",
        "context_method": "В таблицу входят опубликованные модели с указанным размером контекста; порядок — по числу токенов. Неизвестные пределы пропущены, а не приравнены к нулю. Больший контекст не означает лучшего результата в коде или рассуждении.",
        "pricing_title": "Цены API AI-моделей: входные и выходные токены",
        "pricing_description": "Сравнение проверенных базовых цен API за 1 млн текстовых входных и выходных токенов: источники поставщика, условия и даты проверки.",
        "pricing_intro": "Входные и выходные токены оплачиваются отдельно. Здесь только действующие основные предложения API с парой цен одного сервиса для стандартных текстовых токенов. Пакетные, кэшированные, длинноконтекстные и аудио/изображения исключены.",
        "pricing_method": "Это опубликованные цены поставщиков в USD за 1 млн токенов, а не рейтинг стоимости или качества. Налоги, минимальные платежи, регион, лимиты и изменения после проверки влияют на счёт. Отсутствующая цена не равна нулю; другие тарифы показаны в карточке.",
        "model": "Модель", "developer": "Разработчик", "context": "Контекст (токенов)",
        "input": "Вход / 1 млн", "output": "Выход / 1 млн", "provider": "Поставщик API",
        "source": "Источник", "checked": "Проверено", "conditions": "Условия",
        "related": "Связанные страницы каталога", "pricing_link": "Цены API", "context_link": "Сравнение контекста",
        "coding_link": "Модели для программирования", "api_link": "Модели с API",
        "long_link": "Модели с длинным контекстом", "methodology_link": "Источники и методика",
    },
}


def context_rows(limit=None):
    rows = readiness.public_models().filter(context__isnull=False, context__gt=0).select_related(
        "family__developer", "source"
    ).order_by("-context", "name", "slug")
    return list(rows[:limit] if limit else rows)


def pricing_rows():
    offers = Offer.objects.filter(
        model__in=readiness.public_models(), active=True, primary=True,
        service__kind="api", unit__in=("input", "output"),
    ).select_related("model", "model__family__developer", "service__provider", "source")
    pairs = {}
    for offer in offers:
        if price_matches(offer, offer.unit) and _official_standard(offer):
            pairs.setdefault((offer.model_id, offer.service_id), {})[offer.unit] = offer
    rows = []
    for pair in pairs.values():
        incoming, outgoing = pair.get("input"), pair.get("output")
        if not incoming or not outgoing or offer_scope_tags(incoming) != offer_scope_tags(outgoing):
            continue
        rows.append({"model": incoming.model, "service": incoming.service,
                     "input": incoming, "output": outgoing})
    return sorted(rows, key=lambda row: (row["input"].amount, row["output"].amount,
                                         row["model"].name, row["model"].slug))

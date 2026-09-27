"""Master v015 final (2026-09-27): countries, prices, independent evaluations, QA gaps.

Owner task 2026-09-27: finish v015 in the master first (single source of truth):

* origin countries of the new v015 models (+ one older public model without
  one) and developer countries of public tools, each with a source;
* official prices of active API models/services that had none (currency, unit,
  context tier, scope, effective date and source in every row);
* independent Epoch AI own runs (CC BY 4.0, snapshot 2026-09-27) mapped only to
  the exact catalog version;
* ``*_status`` facts (master-only) for verified gaps: no official price, no
  establishable country, no publishable independent evaluation. They feed the
  data-quality queue of ``catalog_master qa`` instead of silently empty fields.

Every change goes to the Changelog; Record IDs, existing rows and history stay.
Re-running writes nothing new (rows are keyed by stable content keys).

  .venv\\Scripts\\python.exe tools\\master_v015_final_2026_09_27.py --book AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx --epoch artifacts\\epoch-ai-2026-09-27\\data
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402

RUN = "v015-final-2026-09-27"
CHECKED = "2026-09-27"
EPOCH_SNAPSHOT = "2026-09-27"

# ---------------------------------------------------------------- countries
ORIGINS = {  # model Record ID -> (country, source)
    "claude-opus-5-5": ("US", "https://www.anthropic.com/company"),
    "gpt-6-sol": ("US", "https://openai.com/about/"),
    "gpt-6-luna": ("US", "https://openai.com/about/"),
    "gemini-3-8-flash-tts": ("US", "https://about.google/company-info/"),
    "gemini-3-8-flash-lite-tts": ("US", "https://about.google/company-info/"),
    "nemotron-3-diarization": ("US", "https://www.nvidia.com/en-us/about-nvidia/"),
    "gliner-2-5-decide": ("US", "https://www.prnewswire.com/news-releases/fastino-launches-pioneer-the-first-agent-for-fine-tuning-and-inference-of-llms-302748105.html"),
    "yandex-speech-tts-live": ("RU", "https://yandex.com/company/"),
    "flux-3-action-droid": ("DE", "https://blackforestlabs.ai/about-us/"),
    "flux-3-action-so101": ("DE", "https://blackforestlabs.ai/about-us/"),
    "gigachat-35-432b-a28b-reasoning-02085d96": ("RU", "https://habr.com/ru/companies/sberbank/articles/1080596/"),
}
TOOL_COUNTRIES = {  # tool Record ID -> (Developer Country text used by the site, source, evidence)
    "cursor-02a2dc32": ("USA", "https://cursor.com/terms-of-service", "Anysphere, Inc., 2261 Market Street, San Francisco, CA"),
    "ollama-1e62e6c9": ("USA", "https://ollama.com/terms", "Ollama Inc.; laws of the State of California"),
    "lm-studio-bionic-3ac51e8d": ("USA", "https://lmstudio.ai/app-terms", "Element Labs, Inc., Delaware; laws of New York"),
    "midjourney-6047a08d": ("USA", "https://docs.midjourney.com/hc/en-us/articles/32083055291277-Terms-of-Service", "Midjourney, Inc.; laws of the State of California, USA"),
    "suno-4e930621": ("USA", "https://suno.com/terms", "Suno Inc., Cambridge, MA"),
    "comfyui-4aec921a": ("USA", "https://www.comfy.org/terms-of-service", "Comfy Organization, Inc., Delaware; San Francisco, CA"),
    "github-copilot-179ab1d0": ("USA", "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service", "GitHub, Inc.; laws of the USA and California"),
    "grok-speech-to-text-cfab200f": ("USA", "https://x.ai/company", "xAI, United States (same source as xAI model origins)"),
    "cline-e0d25424": ("USA", "https://cline.bot/tos", "Cline Bot Inc.; State of Delaware"),
    "qwen-intelligence": ("China", "https://www.alibabagroup.com/en-US/about-alibaba", "Alibaba Group, Hangzhou, China"),
    "alice-ai-pro-business": ("Russia", "https://yandex.com/company/", "Yandex, Moscow, Russia"),
}
ORIGIN_GAPS = {  # tool Record ID -> reason (country is not established; not invented)
    "aider-67a11cba": "Open-source project of an individual maintainer; no legal entity or country is stated in the official repository or site.",
    "llamacpp-bd626fa5": "Community project (ggml-org); ggml.ai states no location and was acquired by Hugging Face in 2026; project country not established.",
    "roo-code-c6a1ecaa": "roocode.com now redirects to roomote.dev; no legal entity or location is stated.",
}

# ------------------------------------------------------------------ prices
OPENAI = ("OpenAI · API", "api", "https://platform.openai.com/", "OpenAI", "cloud", "https://developers.openai.com/api/docs/pricing")
GOOGLE = ("Google · Gemini API", "api", "https://ai.google.dev/", "Google", "cloud", "https://ai.google.dev/gemini-api/docs/pricing")
QWEN = ("Alibaba Cloud Model Studio · API", "api", "https://modelstudio.console.alibabacloud.com/", "Alibaba Cloud", "cloud",
        "https://www.alibabacloud.com/help/en/model-studio/model-pricing")
QWEN_LT = QWEN[:5] + ("https://www.alibabacloud.com/help/en/model-studio/qwen3-8-livetranslate-flash-realtime",)
KIMI = ("Kimi API · API", "api", "https://platform.kimi.ai/docs/pricing/chat", "Moonshot AI", "cloud", "https://platform.kimi.ai/docs/pricing/chat")
UPSTAGE = ("Upstage · API", "api", "https://console.upstage.ai/", "Upstage", "cloud", "https://www.upstage.ai/pricing")
SARVAM_D = ("Sarvam Digitize API", "api", "https://docs.sarvam.ai/api-reference/doc-ai/job/digitise", "Sarvam AI", "cloud", "https://www.sarvam.ai/api-pricing")
SARVAM_E = ("Sarvam Extract API", "api", "https://docs.sarvam.ai/api-reference/doc-ai/job/extract", "Sarvam AI", "cloud", "https://www.sarvam.ai/api-pricing")
YANDEX_TTS = ("Yandex Realtime API", "api", "https://aistudio.yandex.ru/ru/docs/speechkit/tts/api/tts-realtime", "Yandex", "cloud",
              "https://aistudio.yandex.ru/docs/ru/speechkit/pricing")
SOURCECRAFT = ("SourceCraft subscription", "web", "https://sourcecraft.dev/", "Yandex B2B Tech", "cloud",
               "https://sourcecraft.dev/portal/docs/en/sourcecraft/pricing")

SHORT = ("Standard; USD per 1M tokens; input context <272K", "Standard; USD за 1M токенов; входной контекст <272K")
SHORT_ONLY = ("Standard; USD per 1M tokens; short context only", "Standard; USD за 1M токенов; только короткий контекст")


def gpt(record, inp, out, cached=None, cond=SHORT):
    rows = [(record, OPENAI, "input", inp, "", cond, True, True), (record, OPENAI, "output", out, "", cond, True, True)]
    if cached is not None:
        rows.append((record, OPENAI, "cache_read", cached, "", cond, True, True))
    return rows


OFFERS = [  # (record, service, unit, amount, billing unit, (EN, RU), primary, active[, extra, record type])
    *gpt("gpt-5-pro", "15", "120", cond=SHORT_ONLY),
    *gpt("gpt-5-1", "1.25", "10", "0.125", SHORT_ONLY),
    *gpt("gpt-5-2", "1.75", "14", "0.175", SHORT_ONLY),
    *gpt("gpt-5-2-pro", "21", "168", cond=SHORT_ONLY),
    *gpt("gpt-5-3-codex", "1.75", "14", "0.175", SHORT_ONLY),
    *gpt("gpt-5-4", "2.5", "15", "0.25"),
    *gpt("gpt-5-4-pro", "30", "180"),
    *gpt("gpt-5-4-mini", "0.75", "4.5", "0.075", SHORT_ONLY),
    *gpt("gpt-5-4-nano", "0.2", "1.25", "0.02", SHORT_ONLY),
    *gpt("gpt-5-5-pro", "30", "180"),
    ("gemini-31-flash-lite-image-7d4267da", GOOGLE, "input", "0.25", "", ("Standard · text/image/video input; USD per 1M tokens", "Standard · вход text/image/video; USD за 1M токенов"), True, True),
    ("gemini-31-flash-lite-image-7d4267da", GOOGLE, "output", "1.5", "", ("Standard · text and thinking output; USD per 1M tokens", "Standard · вывод текста и рассуждений; USD за 1M токенов"), True, True),
    ("gemini-31-flash-lite-image-7d4267da", GOOGLE, "output", "30", "", ("Standard · image tokens output; USD per 1M tokens (1K image = 1,120 tokens)", "Standard · image tokens на выходе; USD за 1M токенов (изображение 1K = 1 120 токенов)"), False, True),
    ("gemini-31-flash-lite-image-7d4267da", GOOGLE, "image", "0.0336", "", ("Standard · per 1K (1024×1024) output image", "Standard · за выходное изображение 1K (1024×1024)"), True, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "input", "1.5", "", ("International (Singapore); input 0–32K tokens; USD per 1M tokens", "International (Singapore); вход 0–32K токенов; USD за 1M токенов"), True, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "output", "7.5", "", ("International (Singapore); input 0–32K tokens; USD per 1M tokens", "International (Singapore); вход 0–32K токенов; USD за 1M токенов"), True, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "input", "2.7", "", ("International (Singapore); long context: input 32K–128K tokens; USD per 1M tokens", "International (Singapore); long context: вход 32K–128K токенов; USD за 1M токенов"), False, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "output", "13.5", "", ("International (Singapore); long context: input 32K–128K tokens; USD per 1M tokens", "International (Singapore); long context: вход 32K–128K токенов; USD за 1M токенов"), False, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "input", "4.5", "", ("International (Singapore); long context: input 128K–200K tokens; USD per 1M tokens", "International (Singapore); long context: вход 128K–200K токенов; USD за 1M токенов"), False, True),
    ("qwen3-coder-480b-a35b-instruct-1fa8b593", QWEN, "output", "22.5", "", ("International (Singapore); long context: input 128K–200K tokens; USD per 1M tokens", "International (Singapore); long context: вход 128K–200K токенов; USD за 1M токенов"), False, True),
    ("qwen38-livetranslate-c09db33d", QWEN_LT, "input", "7.5", "", ("International (Singapore) · audio tokens input; USD per 1M tokens", "International (Singapore) · только аудиотокены на входе; USD за 1M токенов"), True, True),
    ("qwen38-livetranslate-c09db33d", QWEN_LT, "input", "0.55", "", ("International (Singapore) · image tokens input; USD per 1M tokens", "International (Singapore) · image tokens на входе; USD за 1M токенов"), False, True),
    ("qwen38-livetranslate-c09db33d", QWEN_LT, "output", "20", "", ("International (Singapore) · text output; USD per 1M tokens", "International (Singapore) · текст на выходе; USD за 1M токенов"), True, True),
    ("qwen38-livetranslate-c09db33d", QWEN_LT, "output", "30", "", ("International (Singapore) · audio tokens output; USD per 1M tokens", "International (Singapore) · аудиотокены на выходе; USD за 1M токенов"), False, True),
    ("kimi-k26-03b6a51b", KIMI, "input", "0.95", "", ("Cache miss input; USD per 1M tokens; context 262,144", "Вход без кэша; USD за 1M токенов; контекст 262 144"), True, True),
    ("kimi-k26-03b6a51b", KIMI, "cache_read", "0.16", "", ("Cache hit input; USD per 1M tokens", "Вход из кэша; USD за 1M токенов"), True, True),
    ("kimi-k26-03b6a51b", KIMI, "output", "4", "", ("Output; USD per 1M tokens", "Выход; USD за 1M токенов"), True, True),
    ("kimi-k27-code-b770ac42", KIMI, "input", "0.95", "", ("Cache miss input; USD per 1M tokens; context 262,144", "Вход без кэша; USD за 1M токенов; контекст 262 144"), True, True),
    ("kimi-k27-code-b770ac42", KIMI, "cache_read", "0.19", "", ("Cache hit input; USD per 1M tokens", "Вход из кэша; USD за 1M токенов"), True, True),
    ("kimi-k27-code-b770ac42", KIMI, "output", "4", "", ("Output; USD per 1M tokens", "Выход; USD за 1M токенов"), True, True),
    ("kimi-k3-40b65aea", KIMI, "input", "3", "", ("Non-cached input; USD per 1M tokens; context 1,048,576", "Вход без кэша; USD за 1M токенов; контекст 1 048 576"), True, True),
    ("kimi-k3-40b65aea", KIMI, "cache_read", "0.3", "", ("Cached input; USD per 1M tokens", "Вход из кэша; USD за 1M токенов"), True, True),
    ("kimi-k3-40b65aea", KIMI, "output", "15", "", ("Output; USD per 1M tokens", "Выход; USD за 1M токенов"), True, True),
    ("kimi-k3-40b65aea", KIMI, "cache_write", "3", "", ("Cache write, 5-minute TTL; USD per 1M tokens", "Запись в кэш, TTL 5 минут; USD за 1M токенов"), False, True),
    ("kimi-k3-40b65aea", KIMI, "cache_write", "6", "", ("Cache write, 1-hour TTL; USD per 1M tokens", "Запись в кэш, TTL 1 час; USD за 1M токенов"), False, True),
    ("solar-pro-2-31b-b20a98f3", UPSTAGE, "input", "0.15", "", ("Solar Pro 2; USD per 1M tokens", "Solar Pro 2; USD за 1M токенов"), True, True),
    ("solar-pro-2-31b-b20a98f3", UPSTAGE, "cache_read", "0.015", "", ("Solar Pro 2 cached input; USD per 1M tokens", "Solar Pro 2, вход из кэша; USD за 1M токенов"), True, True),
    ("solar-pro-2-31b-b20a98f3", UPSTAGE, "output", "0.6", "", ("Solar Pro 2; USD per 1M tokens", "Solar Pro 2; USD за 1M токенов"), True, True),
    ("sarvam-vision-2-1", SARVAM_D, "other", "0.5", "страница", ("Digitisation API (Document AI), pay-as-you-go; INR per page", "Digitisation API (Document AI), pay-as-you-go; INR за страницу"), True, True, {"currency": "INR"}),
    ("sarvam-vision-2-1", SARVAM_E, "other", "1", "страница", ("Extraction API (Document AI), pay-as-you-go; INR per page", "Extraction API (Document AI), pay-as-you-go; INR за страницу"), False, True, {"currency": "INR"}),
    ("yandex-speech-tts-live", YANDEX_TTS, "other", "0.00205", "начатый блок из 250 символов", ("Realtime API (Speech TTS Live); USD without VAT per started 250-character block; text input only", "Realtime API (Speech TTS Live); USD без НДС за каждый начатый блок 250 символов; тарифицируется только текст"), True, True, {"currency": "USD", "vat": "excluded"}),
    ("yandex-speech-tts-live", YANDEX_TTS, "other", "0.25", "начатый блок из 250 символов", ("Realtime API (Speech TTS Live); RUB incl. VAT per started 250-character block", "Realtime API (Speech TTS Live); ₽ с НДС за каждый начатый блок 250 символов"), False, True, {"currency": "RUB", "vat": "included"}),
    *[("sourcecraft", SOURCECRAFT, "month", amount, "", ("%s plan; USD per active license per month, excl. VAT; effective from 2026-10-01" % plan,
                                                           "Тариф %s; USD за активную лицензию в месяц, без НДС; действует с 2026-10-01" % plan),
       plan == "Start", False, {"currency": "USD", "vat": "excluded", "effective_from": "2026-10-01"}, "tool")
      for plan, amount in (("Start", "9.75"), ("Go", "20.41"), ("Go X5", "45"), ("Go X15", "94.18"))],
]
# Existing master rows (researched earlier) that only lacked a Research Key.
KEYLESS = {  # Key -> Conditions RU (the rows had EN only)
    "offer-v001-amazon-q-developer-pro-usd-user-month": (
        "Прейскурантная цена за пользователя в месяц для действующих подписок Pro. Новые подписки закрыты с "
        "2026-05-15; к действующим можно добавлять пользователей. Поддержка IDE и платных подписок заканчивается "
        "2027-04-30. Возможны доплаты за дополнительное использование."),
    "offer-v002-speech-engine-burst": (
        "Burst-тариф, не стандартная ставка. Включённые минуты и параллельность зависят от плана. Без налогов."),
}
# Researched earlier but the currency is explicitly unconfirmed in the master: not published, queued.
PENDING = {"offer-batch-007-minimax-speech-recognition-paygo": "minimax-speech-recognition-b5f156c4"}

# Existing $0 rows that are real free tiers but did not say so (found by catalog_master qa).
FREE_TIER_CONDITIONS = {  # Research Key -> (EN, RU, source checked 2026-09-27)
    "AI-0087:unit": ("Free (listed as Free on the official pricing page)", "Бесплатно (на официальной странице цен указано Free)"),
    "AI-0086:unit": ("Free (listed as Free on the official pricing page)", "Бесплатно (на официальной странице цен указано Free)"),
    "AI-0181:unit": ("Hobby — free plan", "Hobby — бесплатный тариф · Подписка и квоты продукта; не равна неограниченному API. Набор доступных моделей зависит от тарифа."),
    "AI-0193:unit": ("Free plan: 50 credits per day; no commercial rights; download limits.", "Бесплатный тариф: 50 кредитов в день; без коммерческих прав; ограничения выгрузок."),
}
PRICING_GAPS = {  # Record ID -> (sheet, status, reason EN, source)
    "qwen-image-21-a858263a": ("Models", "no_official_hosted_price", "Official Model Studio pricing (checked 2026-09-27) lists no qwen-image-2.1; weights are published on Hugging Face.", "https://www.alibabacloud.com/help/en/model-studio/model-pricing"),
    "command-a-05-2026-fa756fc5": ("Models", "custom_enterprise_pricing", "Cohere's public pricing lists no Command A+ rate; deployment is covered by commercial agreements; weights under Apache 2.0.", "https://cohere.com/pricing"),
    "north-mini-code-10-2abc4e72": ("Models", "custom_enterprise_pricing", "Cohere pricing states custom enterprise pricing for North; no per-token rate is published.", "https://cohere.com/pricing"),
    "north-small-translate-10-edfeef02": ("Models", "custom_enterprise_pricing", "Cohere pricing states custom enterprise pricing for North; no per-token rate is published.", "https://cohere.com/pricing"),
    "jamba-15-large-f86c9085": ("Models", "superseded_in_api", "AI21 lists only 'Jamba Large', whose API alias now points to jamba-large-1.7; the 1.5 version is not separately priced.", "https://www.ai21.com/pricing/"),
    "jamba-15-mini-d6559504": ("Models", "superseded_in_api", "AI21 lists only 'Jamba Mini', whose API alias points to the 1.7 generation; the 1.5 version is not separately priced.", "https://www.ai21.com/pricing/"),
    "plamo-20-prime-31b-cd7f441e": ("Models", "superseded_in_api", "PLaMo API now sells only PLaMo 3.0 Prime (JPY 60 / 250 per 1M tokens); 2.x versions have no current price.", "https://plamo.preferredai.jp/api"),
    "plamo-21-prime-cee1a175": ("Models", "superseded_in_api", "PLaMo API now sells only PLaMo 3.0 Prime; 2.1 Prime has no current price.", "https://plamo.preferredai.jp/api"),
    "plamo-22-prime-af56bfb2": ("Models", "superseded_in_api", "PLaMo API now sells only PLaMo 3.0 Prime; 2.2 Prime has no current price.", "https://plamo.preferredai.jp/api"),
    "plamo-translate-aba1ee70": ("Models", "no_official_hosted_price", "The PLaMo API pricing page (checked 2026-09-27) lists no PLaMo Translate rate.", "https://plamo.preferredai.jp/api"),
    "exaone-40-9d0b00ae": ("Models", "no_official_hosted_price", "Open weights; the launch API partner (FriendliAI) no longer lists EXAONE 4.0 on its pricing page (checked 2026-09-27).", "https://friendli.ai/pricing"),
    "gliner-2-5-decide": ("Models", "no_official_hosted_price", "Open weights (Apache 2.0); Fastino's hosted API publishes no per-unit price.", "https://fastino.ai/blog/gliner-2-5-decide-open-weight-decision-model"),
    "nemotron-3-diarization": ("Models", "open_weights_no_hosted_api", "Open weights on Hugging Face; no hosted commercial API is documented.", "https://huggingface.co/nvidia/Nemotron-3-Diarization"),
    "flux-3-action-droid": ("Models", "open_weights_no_hosted_api", "Robot policy weights on Hugging Face; no hosted commercial API.", "https://huggingface.co/black-forest-labs/flux-3-action-droid"),
    "flux-3-action-so101": ("Models", "open_weights_no_hosted_api", "Robot policy weights on Hugging Face; no hosted commercial API.", "https://huggingface.co/black-forest-labs/flux-3-action-so101"),
    "alice-ai-pro-business": ("Tools", "subscription_price_not_published", "Available by subscription to Yandex Cloud clients; the launch announcement states no price.", "https://www.yandex.ru/company/news/24-09-2026-05"),
    "qwen-intelligence": ("Tools", "custom_enterprise_pricing", "B2B platform for phone makers; no public price.", "https://www.alibabacloud.com/blog/alibaba-launches-qwen-intelligence-to-power-next-generation-agentic-smartphones_603597"),
    "yandex-ai-studio": ("Tools", "usage_based_per_model", "Platform billed per model and service used; prices are listed per model, not for the platform as a whole.", "https://aistudio.yandex.ru/docs/ru/speechkit/pricing"),
    "sourcecraft": ("Tools", "scheduled_price", "Published plans take effect on 2026-10-01; stored as scheduled (inactive) prices until then.", "https://sourcecraft.dev/portal/docs/en/sourcecraft/pricing"),
}

# -------------------------------------------------------------- evaluations
OWN_FILES = {
    "gpqa_diamond.csv", "otis_mock_aime_2024_2025.csv", "frontiermath.csv", "frontiermath_tier_4.csv",
    "frontiermath_tiers_1_3_v2.csv", "frontiermath_tier_4_v2.csv", "frontiermath_erdos.csv", "swe_bench_verified.csv",
    "math_level_5.csv", "simpleqa_verified.csv", "chess_puzzles.csv", "ebr_bench.csv", "mystery_game_puzzles.csv",
    "mirrorcode.csv", "furniture_assembly.csv",
}
EXACT = {  # Epoch model version -> (Record ID, mode, Epoch model_group == catalog name)
    "claude-opus-5-5_max": ("claude-opus-5-5", "max", "Claude Opus 5.5"),
    "gpt-6-sol_max": ("gpt-6-sol", "max", "GPT-6 Sol"),
    "qwen3.8-max_xhigh": ("qwen38-max-0b915bf5", "xhigh", "Qwen 3.8 Max"),
    "qwen3.8-max-0902_xhigh": ("qwen38-max-0902-32381f5b", "xhigh", "Qwen3.8 Max (0902)"),
    "deepseek-v4-flash-0731_max": ("deepseek-v4-flash-0731-e8dc06e5", "max", "DeepSeek V4 Flash 0731"),
}
PROTOCOLS = {"gpqa_diamond.csv": ("GPQA Diamond", "GPQA Diamond; Epoch AI own run; best score across scorers"),
             "otis_mock_aime_2024_2025.csv": ("Mock AIME 2024/2025", "Mock AIME 2024/2025; Epoch AI own run; best score across scorers"),
             "frontiermath.csv": ("FrontierMath", "FrontierMath; Epoch AI own run; best score across scorers"),
             "swe_bench_verified.csv": ("SWE-bench Verified", "SWE-bench Verified; Epoch AI own run; best score across scorers"),
             "frontiermath_erdos.csv": ("FrontierMath Open Problems (Erdős)", None)}
EVAL_GAPS = {  # Record ID -> reason (EN, RU)
    "gpt-6-luna": ("No Epoch AI own run of GPT-6 Luna in the 2026-09-27 snapshot; leaderboards whose terms block republication (Artificial Analysis, Arena, LiveBench, SWE-bench) are not used.",
                   "В снимке Epoch AI от 27.09.2026 нет собственного прогона GPT-6 Luna; лидерборды, условия которых запрещают републикацию (Artificial Analysis, Arena, LiveBench, SWE-bench), не используются."),
    "gemini-3-8-flash-tts": ("Text-to-speech model: the licensed independent source (Epoch AI own runs) covers no TTS benchmarks; no publishable independent TTS evaluation found.",
                             "Модель синтеза речи: лицензированный независимый источник (прогоны Epoch AI) не содержит TTS-бенчмарков; публикуемой независимой TTS-оценки не найдено."),
    "gemini-3-8-flash-lite-tts": ("Text-to-speech model: the licensed independent source (Epoch AI own runs) covers no TTS benchmarks; no publishable independent TTS evaluation found.",
                                  "Модель синтеза речи: лицензированный независимый источник (прогоны Epoch AI) не содержит TTS-бенчмарков; публикуемой независимой TTS-оценки не найдено."),
    "yandex-speech-tts-live": ("Text-to-speech model: no publishable independent TTS evaluation of this exact version found.",
                               "Модель синтеза речи: публикуемой независимой оценки этой версии не найдено."),
    "nemotron-3-diarization": ("Speaker-diarization model: no independent diarization result for this exact version with republication rights found; vendor figures are not independent.",
                               "Модель диаризации: независимого результата этой версии с правом републикации не найдено; данные разработчика не считаются независимыми."),
    "sarvam-vision-2-1": ("Document OCR model: only developer-reported results exist; no independent evaluation of the exact version found.",
                          "OCR-модель документов: есть только результаты разработчика; независимой оценки точной версии не найдено."),
    "gliner-2-5-decide": ("Encoder for extraction/decisions: only developer-reported results exist; no independent evaluation found.",
                          "Энкодер для извлечения и решений: есть только результаты разработчика; независимой оценки не найдено."),
    "flux-3-action-droid": ("Robot policy: only developer-reported evaluations exist; no independent robotics benchmark of the exact version found.",
                            "Политика робота: есть только оценки разработчика; независимого робототехнического бенчмарка точной версии не найдено."),
    "flux-3-action-so101": ("Robot policy: only developer-reported evaluations exist; no independent robotics benchmark of the exact version found.",
                            "Политика робота: есть только оценки разработчика; независимого робототехнического бенчмарка точной версии не найдено."),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--epoch", required=True, help="Unpacked Epoch AI benchmark_data.zip (snapshot 2026-09-27)")
    args = parser.parse_args()
    book, epoch = Path(args.book), Path(args.epoch)
    before_sha = hashlib.sha256(book.read_bytes()).hexdigest()
    rows, meta, extra = cm.read_workbook(book)
    stamp = cm.now_utc()
    log = rows["Changelog"]
    stats = {k: 0 for k in ("origins", "tool_countries", "offers", "research_keys", "evaluations", "facts")}

    def note(sheet, rid, field, before, after, reason):
        log.append({"Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": rid, "Field": field,
                    "Before": before, "After": after, "Reason": "%s: %s" % (RUN, reason)})

    def add_row(sheet, row, reason):
        existing = next((r for r in rows[sheet] if r.get("Key") == row["Key"]), None)
        if existing is not None:
            # a row of this run: keep it in line with the script (logged), never touch other rows
            if RUN in row["Key"]:
                for field, value in row.items():
                    if field not in ("Research Key",) and existing.get(field, "") != value:
                        note(sheet, row.get("Record ID", ""), "%s (%s)" % (field, row["Key"]), existing.get(field, ""), value, "correction of this run's row")
                        existing[field] = value
            return False
        rows[sheet].append({**{c: "" for c in rows[sheet][0]}, **row})
        note(sheet, row.get("Record ID", ""), "row added (%s)" % row["Key"], "", json.dumps(row, ensure_ascii=False)[:2000], reason)
        return True

    def fact(record_type, rid, name, value, source):
        key = "fact-%s-%s-%s" % (RUN, name, rid)
        if add_row("Facts", {"Key": key[:120], "Record Type": record_type, "Record ID": rid, "Fact": name,
                             "Value (JSON)": json.dumps(value, ensure_ascii=False, sort_keys=True),
                             "Source URL": source, "Checked": CHECKED}, "verified status for the data-quality queue"):
            stats["facts"] += 1

    models = {r["Record ID"]: r for r in rows["Models"]}
    tools = {r["Record ID"]: r for r in rows["Tools"]}

    # countries
    for rid, (country, source) in ORIGINS.items():
        assert models[rid]["Status"] == "PUBLISHED", rid
        if any(r["Record ID"] == rid and r["Country"] == country for r in rows["Origins"]):
            continue
        if add_row("Origins", {"Key": "origin-%s-%s" % (RUN, rid), "Record Type": "model", "Record ID": rid,
                               "Country": country, "Position": "0", "Source URL": source, "Checked": CHECKED},
                   "developer country of origin (official company page)"):
            stats["origins"] += 1
        old = models[rid].get("Origin Countries", "")
        if country not in cm_split(old):
            models[rid]["Origin Countries"] = "; ".join(cm_split(old) + [country])
            note("Models", rid, "Origin Countries", old, models[rid]["Origin Countries"], "origin country added with source")
    for rid, (country, source, evidence) in TOOL_COUNTRIES.items():
        row = tools[rid]
        if row.get("Developer Country") != country:
            note("Tools", rid, "Developer Country", row.get("Developer Country", ""), country, "developer country: " + evidence)
            row["Developer Country"] = country
            stats["tool_countries"] += 1
        fact("tool", rid, "origin_status", {"status": "confirmed", "country": country, "evidence": evidence}, source)
    # xAI developer of the four Grok voice tools is one organization; one fact per tool
    for rid in ("grok-speech-to-text-streaming-1109f624", "grok-text-to-speech-ade3260f", "grok-voice-agent-64dc28d2"):
        if tools[rid].get("Developer Country") != "USA":
            note("Tools", rid, "Developer Country", tools[rid].get("Developer Country", ""), "USA", "same developer organization as xAI models")
            tools[rid]["Developer Country"] = "USA"
            stats["tool_countries"] += 1
    for rid in ("sourcecraft",):
        if tools[rid].get("Developer Country") != "Russia":
            note("Tools", rid, "Developer Country", tools[rid].get("Developer Country", ""), "Russia", "Yandex B2B Tech (Yandex), Russia")
            tools[rid]["Developer Country"] = "Russia"
            stats["tool_countries"] += 1
    if models["sarvam-vision-2-1"].get("Developer Country") == "IN":
        note("Models", "sarvam-vision-2-1", "Developer Country", "IN", "India", "same notation as the Local organization (flag unchanged: IN)")
        models["sarvam-vision-2-1"]["Developer Country"] = "India"
    for rid, reason in ORIGIN_GAPS.items():
        fact("tool", rid, "origin_status", {"status": "not_established", "reason": reason},
             tools[rid].get("Official URL") or tools[rid].get("Official Source") or "")

    # prices
    for index, spec in enumerate(OFFERS):
        record, service, unit, amount, billing, (en, ru), primary, active = spec[:8]
        extra_json = spec[8] if len(spec) > 8 else {}
        record_type = spec[9] if len(spec) > 9 else "model"
        owner = (models if record_type == "model" else tools)[record]
        assert owner["Status"] == "PUBLISHED", record
        name, kind, url, provider, compute, source = service
        research_key = "%s:%s:%s:%s:%s" % (RUN, record, unit, amount, hashlib.sha1((en + name).encode()).hexdigest()[:8])
        conditions_extra = {"currency": "USD", "scope": "Standard", "audit_run": RUN, "checked": CHECKED,
                            "effective_from": None, **extra_json}
        if add_row("Offers", {"Key": "offer-%s-%03d" % (RUN, index), "Record Type": record_type, "Record ID": record,
                              "Service": name, "Service Kind": kind, "Service URL": url, "Provider": provider,
                              "Compute Location": compute, "Amount": str(Decimal(amount)), "Unit": unit,
                              "Billing Unit": billing, "Conditions EN": en, "Conditions RU": ru,
                              "Conditions Extra (JSON)": json.dumps(conditions_extra, ensure_ascii=False, sort_keys=True),
                              "Primary": "YES" if primary else "NO", "Active": "YES" if active else "NO",
                              "Source URL": source, "Checked": CHECKED, "Research Key": research_key[:120]},
                   "official price (%s)" % source):
            stats["offers"] += 1
    for row in rows["Offers"]:
        if row["Key"] in KEYLESS:
            if not row.get("Research Key"):
                row["Research Key"] = "master:%s" % row["Key"]
                note("Offers", row["Record ID"], "Research Key (%s)" % row["Key"], "", row["Research Key"],
                     "stable identity so sync-local can create this researched price row")
                stats["research_keys"] += 1
            if not row.get("Conditions RU"):
                row["Conditions RU"] = KEYLESS[row["Key"]]
                note("Offers", row["Record ID"], "Conditions RU (%s)" % row["Key"], "", row["Conditions RU"],
                     "Russian conditions required for a public price row (translation of Conditions EN)")
        if row["Key"] in PENDING and row.get("Research Key") == "master:%s" % row["Key"]:
            note("Offers", row["Record ID"], "Research Key (%s)" % row["Key"], row["Research Key"], "",
                 "currency not confirmed in the master: price stays unpublished (data-quality queue)")
            row["Research Key"] = ""
    for row in rows["Offers"]:
        fix = FREE_TIER_CONDITIONS.get(row.get("Research Key"))
        if fix and (row.get("Conditions EN"), row.get("Conditions RU")) != fix:
            for field, value in zip(("Conditions EN", "Conditions RU"), fix):
                note("Offers", row["Record ID"], "%s (%s)" % (field, row["Key"]), row.get(field, ""), value,
                     "free tier stated explicitly (official pricing page lists it as free)")
                row[field] = value
    for key, rid in PENDING.items():
        fact("tool", rid, "pricing_status", {"status": "verification_pending", "reason": "Official page shows $0.38 per hour "
             "without an ISO currency code; the row stays unpublished until the currency is confirmed.", "offer_key": key},
             "https://platform.minimax.io/docs/guides/pricing-paygo")
    for rid, (sheet, status, reason, source) in PRICING_GAPS.items():
        fact("model" if sheet == "Models" else "tool", rid, "pricing_status", {"status": status, "reason": reason}, source)

    # independent evaluations: Epoch AI own runs, exact versions only
    metadata = {r["model_version"]: r for r in read_csv(epoch / "model_metadata.csv")}
    bench_meta = {r["source_file"]: r for r in read_csv(epoch / "benchmark_metadata.csv")}
    for version, (rid, mode, group) in EXACT.items():
        assert metadata[version]["model_group"] == group, (version, metadata[version]["model_group"])
        assert models[rid]["Status"] == "PUBLISHED", rid
    known = {r.get("Source Record ID") for r in rows["Evaluations"]}
    for filename in sorted(OWN_FILES):
        path = epoch / filename
        if not path.exists():
            continue
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        meta_row = bench_meta.get(filename, {})
        name, protocol = PROTOCOLS.get(filename, (None, None))
        name = name or meta_row["benchmark"]
        protocol = protocol or name + "; Epoch AI own run; best score across scorers"
        column = meta_row.get("score_column") or "Best score (across scorers)"
        for row in read_csv(path):
            if row["Model version"] not in EXACT:
                continue
            rid, mode, _group = EXACT[row["Model version"]]
            source_id = "%s:%s" % (filename, row["id"])
            if source_id in known:
                continue
            score = (Decimal(row[column]) * 100).quantize(Decimal(".001"))
            assert 0 <= score <= 100, (filename, row)
            observation_key = hashlib.sha256(("epoch-own:%s:%s" % (source_id, file_hash)).encode()).hexdigest()
            en = ("Epoch AI own run; %s; version: %s; mode: %s; source id: %s; file: %s. CC BY 4.0, Epoch AI. Snapshot %s. "
                  "Source column %s, not AIpedia's selection of the best effort." % (name, row["Model version"], mode, row["id"], filename, EPOCH_SNAPSHOT, column))
            ru = ("Собственный прогон Epoch AI; %s; версия: %s; режим: %s; исходный id: %s; файл: %s. CC BY 4.0, Epoch AI. Снимок %s. "
                  "Показана колонка источника %s, не выбор лучшего режима AIpedia." % (name, row["Model version"], mode, row["id"], filename, EPOCH_SNAPSHOT, column))
            if add_row("Evaluations", {
                    "Key": "evaluation-%s-%s" % (RUN, observation_key[:16]), "Record Type": "model", "Record ID": rid,
                    "Benchmark": name, "Protocol": protocol, "Benchmark Category": "text", "Unit": "%", "Higher Is Better": "YES",
                    "Score": format(score.normalize(), "f"), "Evaluator": "Epoch AI", "Result Kind": "independent",
                    "Independent": "YES", "Public": "YES", "Measured": (row.get("Started at") or "")[:10], "Configuration": mode,
                    "Conditions EN": en, "Conditions RU": ru, "Source URL": "https://epoch.ai/benchmarks", "Checked": CHECKED,
                    "Observation Key": observation_key, "Source Model": row["Model version"], "Source Record ID": source_id,
                    "Snapshot": EPOCH_SNAPSHOT, "Source SHA256": file_hash},
                    "independent Epoch AI own run, exact version (CC BY 4.0)"):
                stats["evaluations"] += 1
                known.add(source_id)
    for rid, (en, ru) in EVAL_GAPS.items():
        fact("model", rid, "independent_evaluation_status", {"status": "gap", "reason_en": en, "reason_ru": ru,
                                                              "checked_sources": ["https://epoch.ai/benchmarks/use-this-data"]},
             "https://epoch.ai/benchmarks/use-this-data")
    for rid in ("claude-opus-5-5", "gpt-6-sol"):
        fact("model", rid, "independent_evaluation_status", {"status": "available", "source": "Epoch AI own runs, snapshot 2026-09-27"},
             "https://epoch.ai/benchmarks")

    renumbered = cm.refresh_derived(rows, log, "%s: chronology recomputed" % RUN, stamp)
    meta = dict(meta)
    meta.update({"Verification run": "%s — countries, prices, independent evaluations, QA gaps" % RUN})
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, book, extra)
    print(json.dumps({"book": str(book), "before_sha256": before_sha,
                      "after_sha256": hashlib.sha256(book.read_bytes()).hexdigest(), "renumbered": renumbered, **stats},
                     ensure_ascii=False, indent=1))


def cm_split(value):
    return [part.strip() for part in (value or "").replace(",", ";").split(";") if part.strip()]


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()

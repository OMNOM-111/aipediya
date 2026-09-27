"""Apply the owner-requested 25–27 September catalog packet to canonical master.

Run once before catalog_master refresh. This script edits the workbook only.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from catalog import catalog_master as cm


STAMP = cm.now_utc()
DAY = "2026-09-27"
rows, meta, extra = cm.read_workbook(cm.WORKBOOK_PATH)


def j(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def log(sheet, record_id, field, before, after, reason):
    rows["Changelog"].append({"Timestamp (UTC)": STAMP, "Sheet": sheet,
        "Record ID": record_id, "Field": field, "Before": str(before or ""),
        "After": str(after or ""), "Reason": reason})


def add(sheet, values):
    record_id = values["Record ID"]
    if any(r["Record ID"] == record_id for r in rows[sheet]):
        raise ValueError(f"Existing Record ID: {record_id}")
    row = {key: "" for key in cm.MAIN[sheet]}
    row.update({"Status": "PUBLISHED", "Publication Decision": "PUBLIC",
                "Decision Code": "CURRENT_RELEASE", "Decision Date": DAY,
                "Last Verified": DAY, "On Local": "NO", "On Production": "NO",
                "Catalog Status": "active"})
    row.update(values)
    rows[sheet].append(row)
    log(sheet, record_id, "Record ID", "", record_id, "Owner catalog packet 2026-09-25 to 2026-09-27")
    return row


def change(sheet, record_id, field, value, reason):
    row = next(r for r in rows[sheet] if r["Record ID"] == record_id)
    old = row.get(field, "")
    if old != value:
        row[field] = value
        log(sheet, record_id, field, old, value, reason)


def aux(sheet, record_type, record_id, key, values):
    if any(r["Key"] == key for r in rows[sheet]):
        raise ValueError(f"Existing aux key: {key}")
    row = {col: "" for col in cm.AUX[sheet]}
    row.update({"Key": key, "Record Type": record_type, "Record ID": record_id})
    row.update(values)
    rows[sheet].append(row)
    log(sheet, record_id, key, "", j(values), "Verified 25–27 September catalog packet")


def fact(record_type, record_id, key, value, source):
    aux("Facts", record_type, record_id, f"fact-20260927-{record_id}-{key}",
        {"Fact": key, "Value (JSON)": j(value), "Source URL": source, "Checked": DAY})


def model(record_id, name, developer, release, source, **values):
    base = {"Record ID": record_id, "Name": name, "Developer": developer,
            "Official Source": source, "Decision Sources": source,
            "Source URL": source, "Source Title": name, "Source Publisher": developer,
            "Release Stage": "released", "Category": "text", "Open Weights": "NO"}
    base["Approx Date" if release.startswith("≈") else "Exact Release Date"] = release
    base["Release Evidence (JSON)" if not release.startswith("≈") else "Approx Evidence (JSON)"] = j({
        "date_text": release.lstrip("≈"), "date_kind": "official release" if not release.startswith("≈") else "first documented public existence",
        "precision": "day", "source_url": source, "checked": DAY})
    base.update(values)
    return add("Models", base)


def tool(record_id, name, developer, release, source, **values):
    base = {"Record ID": record_id, "Name": name, "Developer": developer,
            "Official Source": source, "Decision Sources": source,
            "Source URL": source, "Source Title": name, "Source Publisher": developer,
            "Official URL": source, "Catalog Status": "active"}
    base["Approx Date" if release.startswith("≈") else "Exact Release Date"] = release
    base["Release Evidence (JSON)" if not release.startswith("≈") else "Approx Evidence (JSON)"] = j({
        "date_text": release.lstrip("≈"), "date_kind": "official release" if not release.startswith("≈") else "first documented public existence",
        "precision": "day", "source_url": source, "checked": DAY})
    base.update(values)
    return add("Tools", base)


LONGCAT = "https://longcat.chat/platform/docs/ChangeLog.html"
LONGCAT_PRICE = "https://vercel.com/ai-gateway/models/longcat-2.5-preview"
model("longcat-2-5-preview", "LongCat-2.5-Preview", "Meituan", "2026-09-25", LONGCAT,
      **{"Release Stage": "preview", "Family": "LongCat", "Version": "LongCat-2.5-Preview",
         "Tasks": "coding; agents; vision; image understanding", "Input Modalities": "text; image",
         "Output Modalities": "text", "Context": "1000000", "Origin Countries": "CN",
         "Description EN": "Preview model for coding, agent tasks and image understanding; up to 1M input tokens and 131,072 output tokens.",
         "Description RU": "Предварительная модель для программирования, агентных задач и анализа изображений; контекст до 1 млн токенов и вывод до 131 072 токенов.",
         "Suitable EN": "Coding, agent workflows and visual reasoning.",
         "Suitable RU": "Программирование, агентные сценарии и визуальный анализ.",
         "Limitations EN": "Preview; promotional API prices may change.",
         "Limitations RU": "Предварительная версия; акционные цены API могут измениться.",
         "Secondary Source": LONGCAT_PRICE,
         "Notes": "The requested promotional price is corroborated for 2.5 by Vercel AI Gateway; the LongCat public pricing page found during this check labels the same rates as LongCat-2.0. Verify model-specific direct-platform billing before release."})
aux("Origins", "model", "longcat-2-5-preview", "origin-20260927-longcat-cn",
    {"Country": "CN", "Position": "1", "Source URL": LONGCAT, "Checked": DAY})
aux("Access", "model", "longcat-2-5-preview", "access-20260927-longcat-api",
    {"Service": "LongCat API", "Service Kind": "api", "Service URL": "https://api.longcat.chat/openai/v1",
     "Provider": "Meituan", "Compute Location": "cloud", "Source URL": "https://longcat.chat/platform/docs/APIDocs.html", "Checked": DAY})
for unit, amount, label in (("input", "0.30", "uncached input"),
                             ("cache_read", "0.006", "cached input"),
                             ("output", "1.20", "output")):
    aux("Offers", "model", "longcat-2-5-preview", f"offer-20260927-longcat-{unit}",
        {"Service": "Meituan LongCat via Vercel AI Gateway", "Service Kind": "api",
         "Service URL": LONGCAT_PRICE, "Provider": "Vercel AI Gateway", "Compute Location": "cloud",
         "Amount": amount, "Unit": unit, "Conditions EN": f"Limited-time promotional price per 1M {label} tokens via Vercel AI Gateway; not a permanent direct-platform rate.",
         "Conditions RU": f"Временная акционная цена за 1 млн токенов ({label}) через Vercel AI Gateway; не постоянный тариф прямой платформы.",
         "Primary": "YES" if unit == "input" else "NO", "Active": "YES",
         "Source URL": LONGCAT_PRICE, "Checked": DAY,
         "Research Key": f"20260927-longcat-2-5-preview-vercel-{unit}"})
fact("model", "longcat-2-5-preview", "capabilities", {"max_output_tokens": 131072, "checked": DAY}, "https://longcat.chat/platform/docs/FAQ.html")

QWEN_BLOG = "https://qwenlm.github.io/blog/qwen3guard/"
for size, slug in (("0.6B", "0-6b"), ("4B", "4b"), ("8B", "8b")):
    rid = f"qwen3guard-stream-{slug}"
    hf = f"https://huggingface.co/Qwen/Qwen3Guard-Stream-{size}"
    model(rid, f"Qwen3Guard-Stream {size}", "Qwen / Alibaba", "2025-09-23", QWEN_BLOG,
          **{"Family": "Qwen3Guard", "Version": f"Qwen3Guard-Stream-{size}",
             "Tasks": "streaming moderation; safety classification", "Input Modalities": "text",
             "Output Modalities": "text", "License": "Apache-2.0", "Open Weights": "YES",
             "Origin Countries": "CN", "Secondary Source": hf,
             "Description EN": f"{size} open-weight streaming moderation model. Classifies text as Safe, Controversial or Unsafe; supports 119 languages and dialects.",
             "Description RU": f"Открытая модель потоковой модерации на {size} параметров. Классы Safe, Controversial и Unsafe; поддержка 119 языков и диалектов.",
             "Suitable EN": "Real-time safety checks on generated text.",
             "Suitable RU": "Проверка безопасности текста при потоковой генерации.",
             "Limitations EN": "Requires incremental token input; hosted API price not established.",
             "Limitations RU": "Для потокового анализа нужны токены по мере генерации; коммерческая цена API не установлена.",
             "Notes": "2026 KV-cache fix applies only to 0.6B and 4B unless separately verified." if size != "8B" else "Do not infer the 2026 0.6B/4B KV-cache fix for 8B."})
    aux("Origins", "model", rid, f"origin-20260927-{rid}-cn",
        {"Country": "CN", "Position": "1", "Source URL": QWEN_BLOG, "Checked": DAY})
    fact("model", rid, "pricing_status", {"status": "open_weights_no_hosted_api", "reason": "No model-specific commercial hosted API price established."}, hf)
    fact("model", rid, "capabilities", {"parameters": size, "languages": 119, "severity": ["Safe", "Controversial", "Unsafe"]}, hf)

GPT_RESEARCHER = "https://github.com/assafelovic/gpt-researcher/releases/tag/v3.7.0"
tool("gpt-researcher", "GPT Researcher", "GPT Researcher contributors", "≈2023-10-21",
     "https://github.com/assafelovic/gpt-researcher",
     **{"Version": "v3.7.0", "Category": "agent_platform", "Purposes": "research; agents",
        "Local Execution": "yes", "Platforms": "windows; macos; linux; cli", "Developer Country": "",
        "Secondary Source": GPT_RESEARCHER,
        "Description EN": "Open-source deep-research agent. GitHub v3.7.0 adds Jev context filtering, BM25 fallback and pluggable retrievers; requires Python 3.12+.",
        "Description RU": "Открытый агент для глубокого исследования. GitHub v3.7.0 добавляет отбор контекста Jev, резервный BM25 и подключаемые поисковые модули; требуется Python 3.12+.",
        "Notes": "Apache-2.0. GitHub release v3.7.0 and PyPI package 0.16.0 are separate version lines; first public existence is approximate."})
fact("tool", "gpt-researcher", "origin_status", {"status": "not_established", "reason": "Contributor geography is not an established product origin."}, "https://github.com/assafelovic/gpt-researcher")
fact("tool", "gpt-researcher", "version_history", {"github_release": "v3.7.0", "github_date": "2026-09-26", "pypi_package": "0.16.0", "license": "Apache-2.0"}, GPT_RESEARCHER)

KOBOLD = "https://github.com/LostRuins/koboldcpp/releases/tag/v1.122.1"
tool("koboldcpp", "KoboldCpp", "LostRuins / KoboldCpp contributors", "≈2023-05-17",
     "https://github.com/LostRuins/koboldcpp",
     **{"Version": "v1.122.1", "Category": "runtime", "Purposes": "local inference; model serving",
        "Local Execution": "yes", "Platforms": "windows; linux; macos; cli", "Developer Country": "",
        "Secondary Source": KOBOLD,
        "Description EN": "Self-hosted GGUF inference server. v1.122.1 fixes combined --agent and --cli use and reduces excess terminal logging.",
        "Description RU": "Локальный сервер для запуска GGUF-моделей. v1.122.1 исправляет совместную работу --agent и --cli и сокращает лишние сообщения в терминале.",
        "Notes": "AGPL-3.0. Self-hosted software; no commercial API price is implied. First public existence is approximate."})
fact("tool", "koboldcpp", "origin_status", {"status": "not_established", "reason": "Contributor geography not established."}, "https://github.com/LostRuins/koboldcpp")
fact("tool", "koboldcpp", "pricing_status", {"status": "open_weights_no_hosted_api", "reason": "Self-hosted runtime, no official commercial hosted API price."}, KOBOLD)

DARK = "https://github.com/Layr-Labs/d-inference"
tool("darkbloom", "Darkbloom", "Eigen Labs / Layr Labs", "≈2026-04-17", DARK,
     **{"Version": "provider v0.9.10", "Category": "runtime", "Purposes": "private inference; model serving",
        "Local Execution": "yes", "Platforms": "macos", "Developer Country": "USA",
        "Description EN": "Public Alpha decentralized private inference provider for Apple Silicon, with OpenAI- and Anthropic-compatible APIs.",
        "Description RU": "Публичная альфа децентрализованного приватного запуска моделей на Apple Silicon с API, совместимыми с OpenAI и Anthropic.",
        "Notes": "Proprietary / all rights reserved. A public repository does not imply an open-source license. Provider v0.9.10 on 2026-09-27: model-cache location, model switching without restart/reconnect, preload changes. First public existence approximate."})
fact("tool", "darkbloom", "version_history", {"provider": "0.9.10", "date": DAY, "license": "proprietary / all rights reserved"}, DARK)
fact("tool", "darkbloom", "pricing_status", {"status": "no_official_hosted_price", "reason": "No official hosted API price established for self-hosted provider."}, DARK)

VMLX = "https://pypi.org/project/vmlx/1.6.68/"
tool("vmlx", "vMLX", "JANGQ AI / Jinho Jang", "2026-03-16", "https://pypi.org/project/vmlx/1.0.0/",
     **{"Version": "v1.6.68", "Category": "runtime", "Purposes": "local inference; model serving",
        "Local Execution": "yes", "Platforms": "macos; cli", "Developer Country": "",
        "Secondary Source": VMLX, "Official URL": "https://github.com/jjang-ai/vmlx",
        "Description EN": "Apache-2.0 Apple Silicon inference server for LLM, VLM and image models, with OpenAI-, Anthropic- and Ollama-compatible APIs.",
        "Description RU": "Сервер Apache-2.0 для локального запуска LLM, VLM и моделей изображений на Apple Silicon; API совместимы с OpenAI, Anthropic и Ollama.",
        "Notes": "First PyPI release v1.0.0 on 2026-03-16. v1.6.68 on 2026-09-27 includes JANG/JANGH compatibility, prefix cache, state recovery and MTP-token fail-safe changes."})
fact("tool", "vmlx", "origin_status", {"status": "not_established", "reason": "Developer country not confirmed from source."}, "https://github.com/jjang-ai/vmlx")
fact("tool", "vmlx", "pricing_status", {"status": "open_weights_no_hosted_api", "reason": "Self-hosted server; no official commercial hosted API price."}, VMLX)

UPDATES = [
    ("Tools", "codex-59301cf4", "pre_release", {"version": "0.159.0-alpha.9", "date": DAY, "stable_version_retained": "0.157.1"}, "https://github.com/openai/codex/releases/tag/rust-v0.159.0-alpha.9"),
    ("Tools", "llamacpp-bd626fa5", "build_updates", {"pre_release_builds": ["b11216", "b11205", "b11203"], "period": "2026-09-26/27", "area": "SYCL/CUDA inference engine"}, "https://github.com/ggml-org/llama.cpp/releases"),
    ("Models", "gpt-6-sol", "code_update", {"date": "2026-09-25", "fix": "image encoding", "scope": "API and Codex image understanding, visual/computer-use tasks"}, "https://developers.openai.com/api/docs/changelog"),
    ("Models", "gpt-6-luna", "code_update", {"date": "2026-09-25", "fix": "image encoding", "scope": "API and Codex image understanding, visual/computer-use tasks"}, "https://developers.openai.com/api/docs/changelog"),
    ("Tools", "replit-agent-e4e5c5fc", "product_update", {"date": "2026-09-25", "features": ["Muse", "apps for Meta devices", "Atta charts", "Airwallex MCP", "GPT-6 Sol / GPT-6 Luna Fast / Claude Opus 5.5 model choices"], "caveat": "tier and workspace restrictions apply; Luna Fast is not a separate catalog model"}, "https://replit.com/blog"),
    ("Tools", "qwen-code-984fcfb7", "product_update", {"version": "0.24.6", "features": ["Managed Runtime v2", "qwen sessions ps", "advisor tool"]}, "https://github.com/QwenLM/qwen-code/releases/tag/v0.24.6"),
    ("Tools", "cline-e0d25424", "desktop_update", {"version": "0.0.37", "date": "2026-09-26", "features": ["About page", "What's New", "macOS diagnostics"], "scope": "desktop only; IDE and CLI versions separate"}, "https://github.com/cline/cline/releases"),
]
for sheet, rid, key, payload, url in UPDATES:
    fact("model" if sheet == "Models" else "tool", rid, key,
         {**payload, "checked": DAY}, url)
    change(sheet, rid, "Last Verified", DAY, "25–27 September update verified")

change("Tools", "qwen-code-984fcfb7", "Version", "0.24.6", "Owner-requested version correction; GitHub v0.24.6")
change("Tools", "qwen-code-984fcfb7", "Secondary Source", "https://github.com/QwenLM/qwen-code/releases/tag/v0.24.6", "Version source")

cm.write_workbook(rows, meta, cm.WORKBOOK_PATH, extra)
print("master packet rows written", {s: len(rows[s]) for s in ("Models", "Tools")})

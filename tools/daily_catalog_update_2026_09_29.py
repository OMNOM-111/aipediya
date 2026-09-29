"""Apply Daily Catalog Update #016 to the Catalog Master workbook.

Idempotent: rerunning updates the same records/aux rows by name, alias, Record ID
or stable row keys, and does not create duplicates.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog import catalog_master as cm


TODAY = "2026-09-29"
RELEASE_DATE = "2026-09-28"
CLAUDE_SOURCE = "https://www.anthropic.com/claude-sonnet-5-5"
ELEVEN_SOURCE = "https://elevenlabs.io/fr/blog/eleven-v4"
HOLO_SOURCE = "https://huggingface.co/blog/Hcompany/holo4"
MANUS_SOURCE = "https://www.manus.im/blog/introducing-manus-2-0"
OPENAI_DEPRECATIONS = "https://developers.openai.com/api/docs/deprecations"
META_ENTERPRISE_SOURCE = "https://about.fb.com/news/2026/09/launching-meta-enterprise-platform/"


def slug_key(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").casefold()).strip()


def json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def split_list(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def row_template(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


class MasterUpdate:
    def __init__(self) -> None:
        self.rows, self.meta, self.extra = cm.read_workbook(cm.WORKBOOK_PATH)
        self.changelog = self.rows.setdefault("Changelog", [])
        self.created: list[str] = []
        self.updated: list[str] = []
        self.missing_shutdown: list[str] = []

    def log(self, sheet: str, rid: str, field: str, before: str, after: str, reason: str) -> None:
        self.changelog.append({
            "Timestamp (UTC)": TODAY + "T00:00:00Z",
            "Sheet": sheet,
            "Record ID": rid,
            "Field": field,
            "Before": before,
            "After": after,
            "Reason": reason,
        })

    def find_main(self, sheet: str, names: list[str], sources: list[str] | None = None) -> dict[str, str] | None:
        wanted = {slug_key(name) for name in names if name}
        source_set = set(sources or [])
        found = []
        for row in self.rows[sheet]:
            values = [row.get("Record ID", ""), row.get("Name", ""), *cm.split_aliases(row.get("Aliases"))]
            if wanted.intersection(slug_key(value) for value in values if value):
                found.append(row)
                continue
            if source_set and row.get("Official Source") in source_set and slug_key(row.get("Name", "")) in wanted:
                found.append(row)
        unique = {row["Record ID"]: row for row in found}
        if len(unique) > 1:
            raise SystemExit("duplicate candidates for %s %s: %s" % (sheet, names, sorted(unique)))
        return next(iter(unique.values()), None)

    def ensure_main(self, sheet: str, names: list[str], spec: dict[str, str], aliases: list[str] | None = None) -> str:
        row = self.find_main(sheet, names + [spec.get("Record ID", "")], [spec.get("Official Source", "")])
        if row is None:
            taken = {item.get("Record ID") for item in self.rows[sheet] if item.get("Record ID")}
            rid = spec.get("Record ID") or cm.new_record_id(sheet, spec["Name"], taken)
            row = row_template(cm.MAIN[sheet])
            row["Record ID"] = rid
            self.rows[sheet].append(row)
            self.created.append("%s:%s" % (sheet, rid))
            self.log(sheet, rid, "Record", "", spec["Name"], "daily catalog update #016: create record")
        rid = row["Record ID"]
        merged_aliases = list(cm.split_aliases(row.get("Aliases")))
        for alias in aliases or []:
            if alias and slug_key(alias) not in {slug_key(item) for item in merged_aliases} and slug_key(alias) != slug_key(row.get("Name", "")):
                merged_aliases.append(alias)
        if merged_aliases:
            spec = {**spec, "Aliases": cm.ALIAS_SEPARATOR.join(merged_aliases)}
        for field, value in spec.items():
            if field not in row or value is None:
                continue
            old = row.get(field, "")
            if old != value:
                row[field] = value
                self.updated.append("%s:%s:%s" % (sheet, rid, field))
                self.log(sheet, rid, field, old, value, "daily catalog update #016")
        return rid

    def ensure_aux(self, sheet: str, key: str, spec: dict[str, str]) -> None:
        row = next((item for item in self.rows[sheet] if item.get("Key") == key), None)
        if row is None:
            row = row_template(cm.AUX[sheet])
            row["Key"] = key
            self.rows[sheet].append(row)
            self.created.append("%s:%s" % (sheet, key))
            self.log(sheet, spec.get("Record ID", key), "Aux row", "", key, "daily catalog update #016: create %s" % sheet)
        for field, value in spec.items():
            old = row.get(field, "")
            if old != value:
                row[field] = value
                self.updated.append("%s:%s:%s" % (sheet, key, field))
                self.log(sheet, spec.get("Record ID", key), "%s (%s)" % (field, key), old, value, "daily catalog update #016")

    def access(self, rid: str, service: str, kind: str, url: str, provider: str, source: str, record_type: str = "model", compute: str = "cloud") -> None:
        key = "access-20260929-%s-%s" % (rid, re.sub(r"[^a-z0-9]+", "-", service.lower()).strip("-")[:28])
        self.ensure_aux("Access", key, {
            "Key": key, "Record Type": record_type, "Record ID": rid,
            "Service": service, "Service Kind": kind, "Service URL": url,
            "Provider": provider, "Compute Location": compute,
            "Source URL": source, "Checked": TODAY,
        })

    def offer(self, rid: str, unit: str, amount: str, service: str, url: str, provider: str, source: str, conditions_en: str, conditions_ru: str, primary: str = "NO", record_type: str = "model") -> None:
        key = "offer-20260929-%s-%s" % (rid, unit)
        self.ensure_aux("Offers", key, {
            "Key": key, "Record Type": record_type, "Record ID": rid,
            "Service": service, "Service Kind": "api" if unit not in {"month", "year"} else "web",
            "Service URL": url, "Provider": provider, "Compute Location": "cloud",
            "Amount": amount, "Unit": unit, "Billing Unit": "",
            "Conditions EN": conditions_en, "Conditions RU": conditions_ru,
            "Primary": primary, "Active": "YES", "Source URL": source, "Checked": TODAY,
            "Research Key": "20260929-%s-%s" % (rid, unit),
        })

    def origin(self, rid: str, code: str, position: int, source: str, record_type: str = "model") -> None:
        key = "origin-20260929-%s-%s" % (rid, code.lower())
        self.ensure_aux("Origins", key, {
            "Key": key, "Record Type": record_type, "Record ID": rid,
            "Country": code, "Position": str(position), "Source URL": source, "Checked": TODAY,
        })

    def fact(self, rid: str, fact: str, value: dict, source: str, record_type: str = "model") -> None:
        key = "fact-20260929-%s-%s" % (rid, fact)
        self.ensure_aux("Facts", key, {
            "Key": key, "Record Type": record_type, "Record ID": rid,
            "Fact": fact, "Value (JSON)": json_text(value), "Source URL": source, "Checked": TODAY,
        })

    def base_model(self, name: str, developer: str, source: str, source_title: str, category: str, tasks: str, inputs: str, outputs: str, description_en: str, description_ru: str, suitable_en: str, suitable_ru: str, limitations_en: str, limitations_ru: str, **extra: str) -> dict[str, str]:
        normalized_extra = {key.replace("_", " "): value for key, value in extra.items()}
        return {
            "Status": "PUBLISHED",
            "Publication Decision": "PUBLIC",
            "Name": name,
            "Developer": developer,
            "Exact Release Date": RELEASE_DATE,
            "Decision Code": "CURRENT_RELEASE",
            "Decision Date": TODAY,
            "Decision Sources": source,
            "Reason": "Самостоятельная новая модель, объявленная официальным источником 2026-09-28.",
            "Official Source": source,
            "Last Verified": TODAY,
            "Release Stage": "released",
            "Category": category,
            "Tasks": tasks,
            "Input Modalities": inputs,
            "Output Modalities": outputs,
            "License": "proprietary",
            "Open Weights": "NO",
            "Catalog Status": "active",
            "Description EN": description_en,
            "Description RU": description_ru,
            "Suitable EN": suitable_en,
            "Suitable RU": suitable_ru,
            "Limitations EN": limitations_en,
            "Limitations RU": limitations_ru,
            "Source Title": source_title,
            "Source URL": source,
            "Source Publisher": developer,
            "Checked (DB)": TODAY,
            "Release Evidence (JSON)": json_text({
                "checked": TODAY,
                "date_kind": "official announcement",
                "date_text": RELEASE_DATE,
                "precision": "day",
                "source_url": source,
            }),
            **normalized_extra,
        }

    def apply(self) -> None:
        claude = self.ensure_main("Models", ["Claude Sonnet 5.5", "claude-sonnet-5-5"], self.base_model(
            "Claude Sonnet 5.5", "Anthropic", CLAUDE_SOURCE, "Claude Sonnet 5.5", "text",
            "coding; agents; reasoning; text; vision; computer use", "text; image", "text",
            "Claude Sonnet 5.5 is Anthropic's lower-cost Claude 5.5 Sonnet model for coding, everyday agent tasks, knowledge work, vision and computer use.",
            "Claude Sonnet 5.5 — модель Anthropic семейства Claude 5.5 для кода, повседневных агентных задач, работы со знаниями, зрения и computer use.",
            "Coding, agentic workflows, document work, image understanding and computer-use tasks on Claude Platform or partner clouds.",
            "Код, агентные сценарии, документы, понимание изображений и computer use через Claude Platform или партнёрские облака.",
            "Closed weights; self-hosted deployment is not offered. Claude Haiku 5.5 is announced only as forthcoming and is not a separate public card in this update.",
            "Закрытые веса; self-hosted развёртывание не заявлено. Claude Haiku 5.5 объявлена как будущая модель и в этом обновлении не публикуется отдельной карточкой.",
            Family="Claude Sonnet 5.5", Version="claude-sonnet-5-5", Context="", Developer_Country="USA", Origin_Countries="US",
        ), aliases=["claude-sonnet-5-5"])
        row = next(r for r in self.rows["Models"] if r["Record ID"] == claude)
        if row.get("Developer Country") != "USA":
            old = row.get("Developer Country", "")
            row["Developer Country"] = "USA"
            self.log("Models", claude, "Developer Country", old, "USA", "daily catalog update #016")
        self.origin(claude, "US", 0, CLAUDE_SOURCE)
        for service, url in (
            ("Claude Platform", "https://platform.claude.com/"),
            ("Claude on AWS", "https://claude.com/partners/claude-on-aws"),
            ("Claude on Google Cloud", "https://claude.com/partners/google-cloud-vertex-ai"),
            ("Claude on Microsoft Azure", "https://claude.com/partners/microsoft-foundry"),
        ):
            self.access(claude, service, "api", url, "Anthropic", CLAUDE_SOURCE)
        conditions_en = "Claude Sonnet 5.5 API price per 1M tokens; cache reads and writes are separate rates."
        conditions_ru = "Цена Claude Sonnet 5.5 API за 1 млн токенов; чтение и запись кэша тарифицируются отдельно."
        for unit, amount, primary in (("input", "2", "YES"), ("output", "10", "NO"), ("cache_read", "0.20", "NO"), ("cache_write", "2.50", "NO")):
            self.offer(claude, unit, amount, "Claude Platform", "https://platform.claude.com/", "Anthropic", CLAUDE_SOURCE, conditions_en, conditions_ru, primary)

        eleven_common = {
            "Developer": "ElevenLabs",
            "source": ELEVEN_SOURCE,
            "source_title": "Eleven v4: our most expressive text to speech model",
            "category": "audio",
            "inputs": "text",
            "outputs": "audio",
            "extra": {"Developer_Country": "USA/UK"},
        }
        eleven_v4 = self.ensure_main("Models", ["Eleven v4", "eleven_v4"], self.base_model(
            "Eleven v4", eleven_common["Developer"], eleven_common["source"], eleven_common["source_title"], eleven_common["category"],
            "text-to-speech; dialogue; voice cloning; localization", eleven_common["inputs"], eleven_common["outputs"],
            "Eleven v4 is ElevenLabs' expressive text-to-speech model for natural dialogue, 90+ languages, multi-speaker speech and professional voice cloning.",
            "Eleven v4 — выразительная TTS-модель ElevenLabs для естественных диалогов, 90+ языков, многоголосной речи и Professional Voice Cloning.",
            "Expressive TTS, multi-speaker dialogue, dubbing/localization and Professional Voice Cloning through ElevenAgents, ElevenCreative and ElevenAPI.",
            "Выразительная TTS, многоголосные диалоги, дубляж/локализация и Professional Voice Cloning через ElevenAgents, ElevenCreative и ElevenAPI.",
            "Closed weights. Official post states up to 10,000 characters per generation; current per-model API price was not separately published in this source.",
            "Закрытые веса. Официальный пост указывает до 10 000 символов на генерацию; отдельный текущий API-тариф для модели в этом источнике не опубликован.",
            Family="Eleven v4", Version="eleven_v4", Origin_Countries="US; GB", **eleven_common["extra"],
        ), aliases=["eleven_v4"])
        eleven_v4_turbo = self.ensure_main("Models", ["Eleven v4 Turbo", "eleven_v4_turbo"], self.base_model(
            "Eleven v4 Turbo", eleven_common["Developer"], eleven_common["source"], eleven_common["source_title"], eleven_common["category"],
            "realtime voice agents; text-to-speech; voice cloning; streaming", eleven_common["inputs"], eleven_common["outputs"],
            "Eleven v4 Turbo is a separate low-latency ElevenLabs speech model for realtime voice agents, voice cloning and bidirectional streaming.",
            "Eleven v4 Turbo — отдельная низколатентная речевая модель ElevenLabs для realtime voice agents, voice cloning и bidirectional streaming.",
            "Realtime voice agents and low-latency expressive TTS in 90+ languages, including WebSocket streaming scenarios.",
            "Realtime voice agents и низколатентная выразительная TTS на 90+ языках, включая WebSocket streaming.",
            "Closed weights. Official post reports about 100 ms median inference latency and about 150 ms median time to first audible speech in the cited setup; exact deployment latency varies.",
            "Закрытые веса. Официальный пост указывает около 100 мс median inference latency и около 150 мс median time to first audible speech в описанном тесте; фактическая задержка зависит от развёртывания.",
            Family="Eleven v4", Version="eleven_v4_turbo", Origin_Countries="US; GB", **eleven_common["extra"],
        ), aliases=["eleven_v4_turbo"])
        for rid in (eleven_v4, eleven_v4_turbo):
            row = next(r for r in self.rows["Models"] if r["Record ID"] == rid)
            if row.get("Developer Country") != "USA/UK":
                old = row.get("Developer Country", "")
                row["Developer Country"] = "USA/UK"
                self.log("Models", rid, "Developer Country", old, "USA/UK", "daily catalog update #016")
            self.origin(rid, "US", 0, ELEVEN_SOURCE)
            self.origin(rid, "GB", 1, ELEVEN_SOURCE)
            self.access(rid, "ElevenAPI", "api", "https://elevenlabs.io/docs", "ElevenLabs", ELEVEN_SOURCE)
            self.access(rid, "ElevenAgents", "web", "https://elevenlabs.io/", "ElevenLabs", ELEVEN_SOURCE)
            self.access(rid, "ElevenCreative", "web", "https://elevenlabs.io/", "ElevenLabs", ELEVEN_SOURCE)
            self.fact(rid, "pricing_status", {
                "status": "no_official_hosted_price",
                "reason": "The Eleven v4 launch post confirms API availability but does not publish a separate per-model current API price.",
            }, ELEVEN_SOURCE)

        holo27 = self.ensure_main("Models", ["Holo4-27B", "Hcompany/Holo4-27B"], self.base_model(
            "Holo4-27B", "H Company", HOLO_SOURCE, "Holo4: powering generalist computer-use agents", "text",
            "computer use; agents; vision; coding; tool use", "text; image", "text; actions",
            "Holo4-27B is a 27B dense agentic VLM by H Company for GUI, code and tool-call workflows across web, desktop and mobile environments.",
            "Holo4-27B — 27B dense agentic VLM от H Company для GUI, кода и tool calls в web, desktop и mobile средах.",
            "Computer-use agents that combine GUI control, code execution and API/MCP tool calls with a 262,144-token context.",
            "Computer-use агенты, объединяющие GUI, выполнение кода и API/MCP tool calls с контекстом 262 144 токена.",
            "Non-commercial license (CC BY-NC 4.0). Quantized BF16/FP8/NVFP4/Q4 GGUF variants are treated as formats of this same model, not separate cards.",
            "Некоммерческая лицензия CC BY-NC 4.0. Quantization-варианты BF16/FP8/NVFP4/Q4 GGUF считаются форматами этой модели, а не отдельными карточками.",
            Family="Holo4", Version="Holo4-27B", Context="262144", License="CC BY-NC 4.0", Open_Weights="YES", Developer_Country="France", Origin_Countries="FR",
        ), aliases=["Hcompany/Holo4-27B"])
        holo35 = self.ensure_main("Models", ["Holo4-35B-A3B", "Hcompany/Holo4-35B-A3B"], self.base_model(
            "Holo4-35B-A3B", "H Company", HOLO_SOURCE, "Holo4: powering generalist computer-use agents", "text",
            "computer use; agents; vision; coding; tool use", "text; image", "text; actions",
            "Holo4-35B-A3B is H Company's 35B-A3B mixture-of-experts Holo4 model for agentic computer-use workflows.",
            "Holo4-35B-A3B — MoE-модель Holo4 от H Company для агентных computer-use сценариев.",
            "Agentic workflows on the H Models API and released BF16, FP8, NVFP4 and Q4 GGUF weights.",
            "Агентные сценарии через H Models API и опубликованные веса BF16, FP8, NVFP4 и Q4 GGUF.",
            "Non-commercial license status follows the Holo4 release; architecture is Qwen3.5-based. Do not infer Holo4-27B-only details unless explicitly stated.",
            "Некоммерческий статус лицензии следует релизу Holo4; архитектура основана на Qwen3.5. Характеристики Holo4-27B не копируются автоматически.",
            Family="Holo4", Version="Holo4-35B-A3B", License="CC BY-NC 4.0", Open_Weights="YES", Developer_Country="France", Origin_Countries="FR",
        ), aliases=["Hcompany/Holo4-35B-A3B"])
        holotron = self.ensure_main("Models", ["Holotron4-30B-A3B", "Hcompany/Holotron4-30B-A3B", "Holotron4 Nano"], self.base_model(
            "Holotron4-30B-A3B", "H Company", HOLO_SOURCE, "Holo4: powering generalist computer-use agents", "text",
            "computer use; agents; vision; coding; tool use", "text; image", "text; actions",
            "Holotron4-30B-A3B is the Holotron4 Nano model from H Company, built from NVIDIA Nemotron 3 Nano Omni for generalist agentic workflows.",
            "Holotron4-30B-A3B — модель Holotron4 Nano от H Company на базе NVIDIA Nemotron 3 Nano Omni для generalist agentic workflows.",
            "Computer-use and tool/API/coding workflows with a 262,144-token context and BF16/FP8 weights.",
            "Computer-use, tool/API/coding сценарии с контекстом 262 144 токена и весами BF16/FP8.",
            "The article uses Holotron4 Nano as the product name for HF ID Hcompany/Holotron4-30B-A3B; no separate Nano card is created.",
            "В статье Holotron4 Nano является названием HF ID Hcompany/Holotron4-30B-A3B; отдельная карточка Nano не создаётся.",
            Family="Holotron4", Version="Hcompany/Holotron4-30B-A3B", Context="262144", License="", Open_Weights="YES", Developer_Country="France", Origin_Countries="FR",
        ), aliases=["Hcompany/Holotron4-30B-A3B", "Holotron4 Nano"])
        for rid, has_api in ((holo27, True), (holo35, True), (holotron, False)):
            row = next(r for r in self.rows["Models"] if r["Record ID"] == rid)
            for field, value in (("Developer Country", "France"), ("Open Weights", "YES")):
                if row.get(field) != value:
                    old = row.get(field, "")
                    row[field] = value
                    self.log("Models", rid, field, old, value, "daily catalog update #016")
            self.origin(rid, "FR", 0, HOLO_SOURCE)
            self.access(rid, "Hugging Face model repository", "download", "https://huggingface.co/%s" % next(r for r in cm.split_aliases(row.get("Aliases")) if r.startswith("Hcompany/")), "H Company", HOLO_SOURCE, compute="local")
            if has_api:
                self.access(rid, "H Models API", "api", "https://hub.hcompany.ai/models-api/introduction", "H Company", HOLO_SOURCE)
                self.fact(rid, "pricing_status", {
                    "status": "no_official_hosted_price",
                    "reason": "The Holo4 announcement confirms H Models API availability but does not publish current per-model hosted pricing.",
                }, HOLO_SOURCE)

        cue = self.ensure_main("Tools", ["Cue"], {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Name": "Cue", "Developer": "Manus",
            "Exact Release Date": RELEASE_DATE, "Decision Code": "CURRENT_RELEASE", "Decision Date": TODAY,
            "Decision Sources": MANUS_SOURCE, "Reason": "Самостоятельное приложение для персональных AI agents, объявленное Manus 2.0.",
            "Official Source": MANUS_SOURCE, "Last Verified": TODAY, "Version": "Cue early access",
            "Category": "agent_platform", "Purposes": "personal agents; multi-agent collaboration; automation",
            "Local Execution": "hybrid", "Official URL": "https://cue.im/", "Platforms": "web; desktop; mobile",
            "Catalog Status": "active", "Developer Country": "", "Description EN": "Cue is a standalone Manus app for personal AI agents with separate agent email, phone, wallet and computer, plus multi-agent group collaboration.",
            "Description RU": "Cue — самостоятельное приложение Manus для персональных AI agents: у агентов есть отдельные email, phone, wallet и computer, а также multi-agent group collaboration.",
            "Ecosystem EN": "", "Ecosystem RU": "",
            "Source Title": "Introducing Manus 2.0", "Source URL": MANUS_SOURCE, "Source Publisher": "Manus",
            "Checked (DB)": TODAY, "Release Evidence (JSON)": json_text({"checked": TODAY, "date_text": RELEASE_DATE, "precision": "day", "source_url": MANUS_SOURCE}),
        })
        self.access(cue, "Cue", "web", "https://cue.im/", "Manus", MANUS_SOURCE, record_type="tool")
        self.offer(cue, "month", "0", "Cue", "https://cue.im/", "Manus", MANUS_SOURCE, "Free early access with invite code at launch.", "Бесплатный ранний доступ по invite code на момент запуска.", "YES", record_type="tool")
        self.fact(cue, "origin_status", {"status": "not_established", "reason": "The launch post identifies Manus but does not establish a legal entity country for Cue."}, MANUS_SOURCE, record_type="tool")

        manus = self.ensure_main("Tools", ["Manus"], {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Name": "Manus", "Developer": "Manus",
            "Exact Release Date": RELEASE_DATE, "Decision Code": "CURRENT_RELEASE", "Decision Date": TODAY,
            "Decision Sources": MANUS_SOURCE, "Reason": "Manus 2.0 is an updated standalone agent platform with new architecture and capabilities.",
            "Official Source": MANUS_SOURCE, "Last Verified": TODAY, "Version": "Manus 2.0", "Category": "agent_platform",
            "Purposes": "general agents; automations; cloud computer; video editing; game development; computer use",
            "Local Execution": "hybrid", "Official URL": "https://manus.im/", "Platforms": "web; desktop; mobile; windows; macos; android; ios",
            "Catalog Status": "active", "Developer Country": "", "Description EN": "Manus 2.0 is Manus's agent platform with the Cascade harness, Cloud Computer, event-triggered Automations, Manus Studio, Video Editor, Game Dev and Remote Control / Computer Use.",
            "Description RU": "Manus 2.0 — агентная платформа Manus с Cascade harness, Cloud Computer, event-triggered Automations, Manus Studio, Video Editor, Game Dev и Remote Control / Computer Use.",
            "Ecosystem EN": "", "Ecosystem RU": "",
            "Source Title": "Introducing Manus 2.0", "Source URL": MANUS_SOURCE, "Source Publisher": "Manus",
            "Checked (DB)": TODAY, "Release Evidence (JSON)": json_text({"checked": TODAY, "date_text": RELEASE_DATE, "precision": "day", "source_url": MANUS_SOURCE}),
        })
        self.access(manus, "Manus", "web", "https://manus.im/", "Manus", MANUS_SOURCE, record_type="tool")
        self.fact(manus, "origin_status", {"status": "not_established", "reason": "The launch post identifies Manus but does not establish a legal entity country."}, MANUS_SOURCE, record_type="tool")
        self.fact(manus, "pricing_status", {"status": "subscription_price_not_published", "reason": "The Manus 2.0 launch post links to pricing but does not state a current plan price."}, MANUS_SOURCE, record_type="tool")

        for model_id in ("gpt-3.5-turbo-instruct", "babbage-002", "davinci-002", "gpt-3.5-turbo-1106"):
            found = self.find_main("Models", [model_id])
            if found is None:
                self.missing_shutdown.append(model_id)
                continue
            spec = {
                "Catalog Status": "retired",
                "Last Verified": TODAY,
                "Secondary Source": OPENAI_DEPRECATIONS,
                "Limitations EN": "Historical/retired API model. OpenAI deprecations page lists final API shutdown on 2026-09-28.",
                "Limitations RU": "Историческая/retired API-модель. Страница deprecations OpenAI указывает окончательный shutdown API 2026-09-28.",
                "Notes": (found.get("Notes", "") + "\n[DAILY-CATALOG-UPDATE-2026-09-29] OpenAI deprecations page lists API shutdown 2026-09-28; exact lifecycle checked without deleting the historical record.").strip(),
            }
            self.ensure_main("Models", [model_id], {**found, **spec})

    def save(self) -> None:
        stamp = TODAY + "T00:00:00Z"
        self.meta = dict(self.meta)
        self.meta["Schema"] = cm.SCHEMA
        self.meta = cm.refresh_meta(self.meta, self.rows, stamp)
        cm.write_workbook(self.rows, self.meta, cm.WORKBOOK_PATH, self.extra)
        print(json.dumps({
            "created": self.created,
            "updated_count": len(set(self.updated)),
            "missing_shutdown_records": self.missing_shutdown,
        }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    update = MasterUpdate()
    update.apply()
    update.save()
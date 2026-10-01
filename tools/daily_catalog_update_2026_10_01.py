"""Apply Daily Catalog Update Release #021 (2026-10-01) to the master workbook.

The update is intentionally idempotent.  It publishes only the two confirmed
model records and Cloudflare OS, updates already-published records in place,
and preserves unresolved report items as master-only NEEDS_REVIEW candidates.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog import catalog_master as cm


DAY = "2026-10-01"
BATCH = "release-021-daily-catalog-2026-10-01"
REASON = "daily catalog update #021"

ARGON = "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/"
FAIRWIND = "https://blog.google/innovation-and-ai/technology/safety-security/fairwind-program/"
PPLX_BLOG = "https://perplexity.ai/pl/hub/blog/contextual-embedding-beyond-the-gold-passage"
PPLX_HF = "https://huggingface.co/perplexity-ai/pplx-embed-v2-context-9b-preview"
CLOUDFLARE_OS = "https://blog.cloudflare.com/cloudflare-os/"
CLOUDFLARE_OS_MANAGED = "https://blog.cloudflare.com/managed-cloudflare-os/"
CLOUDFLARE_OS_GITHUB = "https://github.com/cloudflare/cloudflare-os"
GLM = "https://autoclaw.z.ai/blog/model/glm-5.3-flash/"
GLM_HF = "https://huggingface.co/zai-org/GLM-5.3-Flash"
GEMINI_SKILLS = "https://blog.google/products-and-platforms/products/gemini/automate-tasks-with-skills/"
GEMINI_WORKSPACE = "https://workspaceupdates.googleblog.com/2026/09/skills-gemini-app-workspace.html"
HYDRAFUSION = "https://github.blog/changelog/2026-09-30-hydrafusion-in-vs-code-and-the-github-copilot-app/"
CODEX_1593 = "https://github.com/openai/codex/releases/tag/rust-v0.159.3"
PERPLEXITY_AUTOMATIONS = "https://www.perplexity.ai/en-GB/hub/blog/computer-adds-automations-for-ongoing-work"
SOURCECRAFT_PRICING = "https://sourcecraft.dev/portal/docs/en/sourcecraft/pricing"
LING_SECONDARY = "https://technode.com/2026/09/30/ant-group-launches-ling-3-1-flash-with-560-billion-parameters/"
AI_SEARCH_GA = "https://developers.cloudflare.com/changelog/post/2026-10-01-ai-search-generally-available/"
MONETIZATION_FIRST = "https://blog.cloudflare.com/monetization-gateway/"
MONETIZATION_BETA = "https://developers.cloudflare.com/changelog/post/2026-09-30-closed-beta/"
ROBINHOOD = "https://robinhood.com/us/en/newsroom/hood-summit-2026/"


def json_text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def blank(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


class Update:
    def __init__(self, path: Path = cm.WORKBOOK_PATH) -> None:
        self.path = path
        self.rows, self.meta, self.extra = cm.read_workbook(path)
        self.changelog = self.rows.setdefault("Changelog", [])
        self.created: list[str] = []
        self.updated: list[str] = []
        self.stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def log(self, sheet: str, record_id: str, field: str, before: str, after: str, reason: str = REASON) -> None:
        self.changelog.append({
            "Timestamp (UTC)": self.stamp,
            "Sheet": sheet,
            "Record ID": record_id,
            "Field": field,
            "Before": before,
            "After": after,
            "Reason": reason,
        })

    def main(self, sheet: str, record_id: str, spec: dict[str, str]) -> dict[str, str]:
        row = next((item for item in self.rows[sheet] if item.get("Record ID") == record_id), None)
        if row is None:
            row = blank(cm.MAIN[sheet])
            row["Record ID"] = record_id
            self.rows[sheet].append(row)
            self.created.append(f"{sheet}:{record_id}")
            self.log(sheet, record_id, "Record", "", spec.get("Name", record_id), REASON + ": create record")
        for field, value in spec.items():
            if field not in row or value is None:
                continue
            before = row.get(field, "")
            if before != value:
                row[field] = value
                self.updated.append(f"{sheet}:{record_id}:{field}")
                self.log(sheet, record_id, field, before, value)
        return row

    def aux(self, sheet: str, key: str, spec: dict[str, str]) -> dict[str, str]:
        row = next((item for item in self.rows[sheet] if item.get("Key") == key), None)
        if row is None:
            row = blank(cm.AUX[sheet])
            row["Key"] = key
            self.rows[sheet].append(row)
            self.created.append(f"{sheet}:{key}")
            self.log(sheet, spec.get("Record ID", key), "Aux row", "", key, REASON + f": create {sheet}")
        for field, value in spec.items():
            before = row.get(field, "")
            if before != value:
                row[field] = value
                self.updated.append(f"{sheet}:{key}:{field}")
                self.log(sheet, spec.get("Record ID", key), f"{field} ({key})", before, value)
        return row

    def note(self, row: dict[str, str], marker: str, text: str) -> str:
        notes = row.get("Notes", "")
        if marker in notes:
            return notes
        return (notes.rstrip() + "\n" + text).strip()

    def fact(self, key: str, record_type: str, record_id: str, name: str, value: dict, source: str) -> None:
        self.aux("Facts", key, {
            "Key": key,
            "Record Type": record_type,
            "Record ID": record_id,
            "Fact": name,
            "Value (JSON)": json_text(value),
            "Source URL": source,
            "Checked": DAY,
        })

    def origin(self, key: str, record_id: str, source: str, record_type: str = "model", code: str = "US", position: str = "0") -> None:
        self.aux("Origins", key, {
            "Key": key,
            "Record Type": record_type,
            "Record ID": record_id,
            "Country": code,
            "Position": position,
            "Source URL": source,
            "Checked": DAY,
        })

    def apply_new_models(self) -> None:
        argon_id = "gemini-4-argon-bcdaec0e"
        self.main("Models", argon_id, {
            "Status": "PUBLISHED",
            "Publication Decision": "PUBLIC",
            "Name": "Gemini 4 Argon",
            "Developer": "Google DeepMind",
            "Exact Release Date": "2026-09-30",
            "Reason": "Отдельная frontier-модель Google с подтверждённым ограниченным доступом через Fairwind; широкий API/GA ещё не открыт.",
            "Decision Code": "CURRENT_RELEASE",
            "Decision Date": DAY,
            "Decision Sources": ARGON,
            "Official Source": ARGON,
            "Last Verified": DAY,
            "On Local": "NO",
            "On Production": "NO",
            "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Доступ ограничен доверенными cyber-defenders через Fairwind. Объявленные API-цены относятся к будущему запуску; они не записаны как активные Offers.",
            "Release Stage": "preview",
            "Family": "Gemini 4",
            "Version": "Gemini 4 Argon",
            "Category": "text",
            "Tasks": "reasoning; code; agents; cybersecurity; knowledge work; vision; video understanding",
            "Input Modalities": "text; image; video; files",
            "Output Modalities": "text",
            "License": "Proprietary",
            "Open Weights": "NO",
            "Catalog Status": "active",
            "Developer Country": "UK/USA",
            "Origin Countries": "US; GB",
            "Description EN": "Gemini 4 Argon is Google DeepMind's frontier reasoning model for long-horizon coding, enterprise knowledge work, visual analysis, and defensive cybersecurity.",
            "Description RU": "Gemini 4 Argon — frontier-модель Google DeepMind для длительных цепочек рассуждений, программирования, корпоративной работы с знаниями, визуального анализа и защитной кибербезопасности.",
            "Suitable EN": "Complex long-running coding and professional workflows, visual document and video analysis, and authorized defensive cybersecurity work.",
            "Suitable RU": "Сложные длительные задачи программирования и профессиональной работы, анализ документов и видео, а также разрешённые защитные задачи кибербезопасности.",
            "Limitations EN": "Limited Fairwind access only; broad developer, enterprise, and consumer availability, API identifier, input context window, and active pricing are not yet published.",
            "Limitations RU": "Доступ пока только через ограниченную программу Fairwind; широкий доступ, API ID, входное контекстное окно и действующие цены ещё не опубликованы.",
            "Source Title": "Gemini 4 Argon: our next era of frontier intelligence",
            "Source URL": ARGON,
            "Source Publisher": "Google",
            "Checked (DB)": DAY,
            "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-09-30", "precision": "day", "stage": "limited Fairwind rollout", "source_url": ARGON}),
            "Research Date Hint": "2026-09-30 (day)",
            "Import Sources (unverified)": ARGON,
            "Import Batch": BATCH,
        })
        self.origin("origin-021-gemini-4-argon-us", argon_id, ARGON)
        self.origin("origin-021-gemini-4-argon-gb", argon_id, ARGON, code="GB", position="1")
        self.aux("Access", "access-021-gemini-4-argon-fairwind", {
            "Key": "access-021-gemini-4-argon-fairwind", "Record Type": "model", "Record ID": argon_id,
            "Service": "Google Fairwind Program", "Service Kind": "web", "Service URL": FAIRWIND,
            "Provider": "Google", "Compute Location": "cloud", "Source URL": ARGON, "Checked": DAY,
        })
        self.fact("fact-021-gemini-4-argon-availability", "model", argon_id, "availability_status", {
            "checked": DAY, "status": "limited_trusted_defenders", "program": "Fairwind",
            "broad_availability": "announced, not yet available", "api_model_id": None,
        }, ARGON)
        self.fact("fact-021-gemini-4-argon-pricing", "model", argon_id, "announced_future_pricing", {
            "checked": DAY, "active": False, "introductory_usd_per_million_tokens": {"input": 2, "output": 10},
            "cached_input_discount_percent": 95, "later_usd_per_million_tokens": {"input": 4, "output": 20},
        }, ARGON)
        self.fact("fact-021-gemini-4-argon-evaluation", "model", argon_id, "independent_evaluation_status", {
            "checked": DAY, "status": "developer_reported", "reason_en": "The launch post contains developer-reported results; no independently republishable exact-version result was added in this update.",
        }, ARGON)

        pplx_id = "pplx-embed-v2-context-9b-preview-88e13515"
        self.main("Models", pplx_id, {
            "Status": "PUBLISHED",
            "Publication Decision": "PUBLIC",
            "Name": "pplx-embed-v2-context-9b-preview",
            "Developer": "Perplexity AI",
            "Exact Release Date": "2026-09-30",
            "Reason": "Отдельная официально опубликованная preview embedding-модель с загружаемыми весами и собственной model card.",
            "Decision Code": "CURRENT_RELEASE",
            "Decision Date": DAY,
            "Decision Sources": PPLX_BLOG + " | " + PPLX_HF,
            "Official Source": PPLX_BLOG,
            "Secondary Source": PPLX_HF,
            "Last Verified": DAY,
            "On Local": "NO",
            "On Production": "NO",
            "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Preview без обратной совместимости. Число параметров не переносилось из имени: Hugging Face показывает 8B, а официальный model ID содержит 9b; точная архитектурная трактовка требует отдельного подтверждения. Hosted API пока не заявлен.",
            "Release Stage": "preview",
            "Family": "pplx-embed v2",
            "Version": "pplx-embed-v2-context-9b-preview",
            "Category": "text",
            "Tasks": "embeddings; retrieval; RAG; contextual document encoding",
            "Input Modalities": "text",
            "Output Modalities": "embedding",
            "License": "MIT",
            "Open Weights": "YES",
            "Catalog Status": "active",
            "Developer Country": "USA",
            "Origin Countries": "US",
            "Description EN": "A Perplexity contextual embedding preview that encodes document chunks jointly so each chunk embedding reflects the surrounding document context.",
            "Description RU": "Предварительная contextual embedding-модель Perplexity, которая кодирует фрагменты документа совместно, чтобы embedding каждого фрагмента учитывал контекст всего документа.",
            "Suitable EN": "Context-aware retrieval and RAG over chunked documents, with native INT8 output and 1024/2048 Matryoshka dimensions.",
            "Suitable RU": "Контекстный поиск и RAG по документам, разбитым на фрагменты, с нативным INT8 и Matryoshka-размерностями 1024/2048.",
            "Limitations EN": "Preview interface and embeddings may change without backward compatibility; query and document encoders must be called separately; no hosted Perplexity API was confirmed.",
            "Limitations RU": "Preview-интерфейс и embeddings могут измениться без обратной совместимости; запросы и документы кодируются разными методами; hosted API Perplexity не подтверждён.",
            "Source Title": "Contextual embedding beyond the gold passage",
            "Source URL": PPLX_BLOG,
            "Source Publisher": "Perplexity AI",
            "Checked (DB)": DAY,
            "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-09-30", "precision": "day", "source_url": PPLX_BLOG, "model_card": PPLX_HF}),
            "Research Date Hint": "2026-09-30 (day)",
            "Import Sources (unverified)": PPLX_BLOG + " | " + PPLX_HF,
            "Import Batch": BATCH,
        })
        self.origin("origin-021-pplx-embed-us", pplx_id, PPLX_BLOG)
        self.aux("Access", "access-021-pplx-embed-hf", {
            "Key": "access-021-pplx-embed-hf", "Record Type": "model", "Record ID": pplx_id,
            "Service": "Hugging Face model repository", "Service Kind": "download", "Service URL": PPLX_HF,
            "Provider": "Perplexity AI", "Compute Location": "local", "Source URL": PPLX_HF, "Checked": DAY,
        })
        self.fact("fact-021-pplx-embed-config", "model", pplx_id, "embedding_configuration", {
            "checked": DAY, "dimensions": 2048, "matryoshka_dimensions": [1024, 2048], "quantization": "native unnormalized INT8",
            "query_method": "encode_queries", "document_method": "encode", "minimum_transformers": "5.4.0",
        }, PPLX_HF)
        self.fact("fact-021-pplx-embed-evaluation", "model", pplx_id, "independent_evaluation_status", {
            "checked": DAY, "status": "developer_reported", "reason_en": "Only developer/model-card results were reviewed for this daily update.",
        }, PPLX_HF)

    def apply_cloudflare_os(self) -> None:
        record_id = "cloudflare-os-038daad4"
        self.main("Tools", record_id, {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Name": "Cloudflare OS", "Developer": "Cloudflare",
            "Exact Release Date": "2026-08-05", "Reason": "Самостоятельная open-source agent workspace, доступная для развёртывания в аккаунте Cloudflare; managed-версия остаётся в waitlist.",
            "Decision Code": "CURRENT_RELEASE", "Decision Date": DAY, "Decision Sources": CLOUDFLARE_OS + " | " + CLOUDFLARE_OS_MANAGED,
            "Official Source": CLOUDFLARE_OS, "Secondary Source": CLOUDFLARE_OS_MANAGED, "Last Verified": DAY,
            "On Local": "NO", "On Production": "NO",
            "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Первый публичный open-source выпуск — 2026-08-05. С 2026-10-01 открыт waitlist на fully managed deployment; это обновление доступа, а не новая дата выпуска.",
            "Version": "open source; managed waitlist", "Category": "agent_platform", "Purposes": "agents; automation; knowledge work; app building; coding",
            "Local Execution": "no", "Official URL": CLOUDFLARE_OS_GITHUB, "Platforms": "web; github", "Catalog Status": "active",
            "Developer Country": "USA",
            "Description EN": "Cloudflare OS is an open-source organizational agent workspace for building tools, working with company context, documents, repositories, and connected systems on Cloudflare.",
            "Description RU": "Cloudflare OS — open-source рабочее пространство агентов для создания инструментов и работы с контекстом компании, документами, репозиториями и подключёнными системами на Cloudflare.",
            "Ecosystem EN": "Cloudflare Workers, Access, AI Gateway, GitHub, Google Workspace, Gatekeepers and MCP",
            "Ecosystem RU": "Cloudflare Workers, Access, AI Gateway, GitHub, Google Workspace, Gatekeepers и MCP",
            "Source Title": "Cloudflare OS: an open platform for agents, apps, and work", "Source URL": CLOUDFLARE_OS,
            "Source Publisher": "Cloudflare", "Checked (DB)": DAY,
            "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-08-05", "precision": "day", "source_url": CLOUDFLARE_OS, "managed_update": "2026-10-01 waitlist"}),
            "Research Date Hint": "2026-08-05 (day)", "Import Sources (unverified)": CLOUDFLARE_OS + " | " + CLOUDFLARE_OS_MANAGED,
            "Import Batch": BATCH,
        })
        self.aux("Access", "access-021-cloudflare-os-github", {
            "Key": "access-021-cloudflare-os-github", "Record Type": "tool", "Record ID": record_id,
            "Service": "Cloudflare OS source", "Service Kind": "download", "Service URL": CLOUDFLARE_OS_GITHUB,
            "Provider": "Cloudflare", "Compute Location": "cloud", "Source URL": CLOUDFLARE_OS, "Checked": DAY,
        })
        self.aux("Access", "access-021-cloudflare-os-managed", {
            "Key": "access-021-cloudflare-os-managed", "Record Type": "tool", "Record ID": record_id,
            "Service": "Managed Cloudflare OS waitlist", "Service Kind": "web", "Service URL": CLOUDFLARE_OS_MANAGED,
            "Provider": "Cloudflare", "Compute Location": "cloud", "Source URL": CLOUDFLARE_OS_MANAGED, "Checked": DAY,
        })
        self.fact("fact-021-cloudflare-os-access", "tool", record_id, "release_update", {
            "checked": DAY, "first_release": "2026-08-05 open source", "update": "2026-10-01 managed deployment waitlist",
            "open_source_available": True, "managed_general_availability": False,
        }, CLOUDFLARE_OS_MANAGED)

    def apply_existing_updates(self) -> None:
        glm = next(row for row in self.rows["Models"] if row.get("Record ID") == "glm-53-flash-bdc83193")
        self.main("Models", "glm-53-flash-bdc83193", {
            "Secondary Source": GLM,
            "Last Verified": DAY,
            "Notes": self.note(glm, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] Сохранена первая подтверждённая дата 2026-08-26. Новая официальная статья фактически доступна 01.10, но датирована 02.10; она подтверждает новую multimodal base/weights и не используется для переписывания первоначальной даты."),
            "Tasks": "code; reasoning; text; agents; vision; video understanding; file processing",
            "Input Modalities": "text; image; video; files",
            "Output Modalities": "text",
            "Context": "1000000",
            "License": "MIT",
            "Description EN": "GLM-5.3-Flash is Z.ai's native multimodal GLM-5 model with 320B total and 18B active parameters for coding, agents, visual understanding, files, and long-context professional work.",
            "Description RU": "GLM-5.3-Flash — нативно мультимодальная модель Z.ai семейства GLM-5 с 320 млрд общих и 18 млрд активных параметров для кода, агентов, визуального анализа, файлов и длинного контекста.",
            "Suitable EN": "Coding, tool use, automation, text/image/video/file understanding, and workflows up to a one-million-token context.",
            "Suitable RU": "Программирование, инструменты, автоматизация, понимание текста, изображений, видео и файлов, а также задачи с контекстом до одного миллиона токенов.",
            "Limitations EN": "The Oct 2-dated official article was already accessible on Oct 1; it is treated as a capability/weights update and does not replace the earlier verified release date.",
            "Limitations RU": "Официальная статья с датой 2 октября уже была доступна 1 октября; она учтена как обновление возможностей и весов и не заменяет ранее подтверждённую дату выпуска.",
        })
        self.aux("Access", "access-021-glm53-hf", {
            "Key": "access-021-glm53-hf", "Record Type": "model", "Record ID": "glm-53-flash-bdc83193",
            "Service": "Hugging Face model repository", "Service Kind": "download", "Service URL": GLM_HF,
            "Provider": "Z.ai", "Compute Location": "local", "Source URL": GLM, "Checked": DAY,
        })
        self.fact("fact-021-glm53-multimodal", "model", "glm-53-flash-bdc83193", "release_update", {
            "checked": DAY, "source_date": "2026-10-02", "observed_before_source_date": True, "not_release_date": True,
            "architecture": {"total_parameters_billion": 320, "active_parameters_billion": 18},
            "input_modalities": ["text", "image", "video", "files"], "context_tokens": 1000000,
            "weights": "Hugging Face", "license": "MIT",
        }, GLM)

        gemini = next(row for row in self.rows["Tools"] if row.get("Record ID") == "gemini-90ef8dfa")
        self.main("Tools", "gemini-90ef8dfa", {
            "Last Verified": DAY,
            "Notes": self.note(gemini, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] Skills заменят Gems по поэтапному графику. Будущие даты rollout/deprecation сохранены в Facts; карточка Gemini остаётся active и не архивируется."),
        })
        self.fact("fact-021-gemini-skills", "tool", "gemini-90ef8dfa", "release_update", {
            "checked": DAY, "announcement_date": "2026-09-30", "feature": "Skills", "replaces": "Gems",
            "capabilities": ["reusable instructions", "composable skills", "reference files"],
            "rollout": {"workspace_starts": "2026-10-05", "gemini_app_starts": "2026-10-13", "gems_move_to_settings": "2026-11-17"},
            "gems_end_no_sooner_than": {"business_enterprise": "2027-03-01", "education": "2027-06-01"},
            "future_dates_not_current_availability": True,
        }, GEMINI_WORKSPACE)

        copilot = next(row for row in self.rows["Tools"] if row.get("Record ID") == "github-copilot-179ab1d0")
        self.main("Tools", "github-copilot-179ab1d0", {
            "Last Verified": DAY,
            "Notes": self.note(copilot, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] HydraFusion research preview расширен из CLI в VS Code и Copilot app. Это multi-model orchestration внутри Copilot, не отдельная модель/карточка."),
        })
        self.fact("fact-021-copilot-hydrafusion", "tool", "github-copilot-179ab1d0", "release_update", {
            "checked": DAY, "effective_date": "2026-09-30", "feature": "HydraFusion research preview",
            "surfaces": ["Copilot CLI", "VS Code 1.140+", "GitHub Copilot app"], "workflows": ["Single", "Cascade", "Critique"],
            "plans": ["Pro", "Pro+", "Business", "Enterprise"], "business_enterprise_admin_preview_required": True,
            "not_a_standalone_model": True,
        }, HYDRAFUSION)

        codex = next(row for row in self.rows["Tools"] if row.get("Record ID") == "codex-59301cf4")
        self.main("Tools", "codex-59301cf4", {
            "Version": "0.159.3",
            "Last Verified": DAY,
            "Notes": self.note(codex, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] Официальный stable release channel подтверждает 0.159.3 (30.09 22:57 UTC); prerelease=false. Последовательность stable 0.159.0–0.159.3 сохранена в Facts."),
            "Description EN": "Codex is OpenAI's coding agent across CLI, IDE, desktop, and cloud workflows. The latest verified stable CLI release is 0.159.3.",
            "Description RU": "Codex — агент OpenAI для программирования в CLI, IDE, настольных и облачных сценариях. Последняя подтверждённая стабильная версия CLI — 0.159.3.",
        })
        self.fact("fact-021-codex-stable", "tool", "codex-59301cf4", "release_update", {
            "checked": DAY, "stable_version": "0.159.3", "prerelease": False, "released_utc": "2026-09-30T22:57:00Z",
            "stable_history": ["0.159.0", "0.159.1", "0.159.2", "0.159.3"],
        }, CODEX_1593)

        perplexity = next(row for row in self.rows["Tools"] if row.get("Record ID") == "perplexity-7a1d922e")
        self.main("Tools", "perplexity-7a1d922e", {
            "Last Verified": DAY,
            "Notes": self.note(perplexity, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] Computer Automations учтены как функция существующего Perplexity Computer/Perplexity, не как отдельная карточка."),
            "Purposes": "retrieval; research; agents; automation",
            "Description EN": "Perplexity is an AI search and research assistant that also offers Computer workflows and Automations triggered by schedules or connected-app events.",
            "Description RU": "Perplexity — AI-ассистент для поиска и исследований, который также поддерживает Computer-сценарии и Automations по расписанию или событиям подключённых приложений.",
        })
        self.fact("fact-021-perplexity-automations", "tool", "perplexity-7a1d922e", "release_update", {
            "checked": DAY, "feature": "Computer Automations", "triggers": ["schedule", "conditional event"],
            "integrations": ["Slack", "Gmail", "Outlook", "Linear", "GitHub"], "includes_history_and_review_controls": True,
            "not_a_separate_tool_card": True,
        }, PERPLEXITY_AUTOMATIONS)

    def apply_sourcecraft_prices(self) -> None:
        exact = {
            "offer-v015-final-2026-09-27-058": "9.754098",
            "offer-v015-final-2026-09-27-059": "20.409836",
            "offer-v015-final-2026-09-27-060": "45.000000",
            "offer-v015-final-2026-09-27-061": "94.180328",
        }
        for key, amount in exact.items():
            row = next(item for item in self.rows["Offers"] if item.get("Key") == key)
            self.aux("Offers", key, {**row, "Amount": amount, "Active": "YES", "Checked": DAY})
        self.fact("fact-v015-final-2026-09-27-pricing_status-sourcecraft", "tool", "sourcecraft", "pricing_status", {
            "status": "current_official_price", "effective_from": "2026-10-01", "checked": DAY,
            "plans": ["Start", "Go", "Go X5", "Go X15"], "currency": "USD", "vat": "excluded",
        }, SOURCECRAFT_PRICING)
        sourcecraft = next(row for row in self.rows["Tools"] if row.get("Record ID") == "sourcecraft")
        self.main("Tools", "sourcecraft", {
            "Last Verified": DAY,
            "Notes": self.note(sourcecraft, "[DAILY-CATALOG-UPDATE-2026-10-01]", "[DAILY-CATALOG-UPDATE-2026-10-01] Четыре ранее сохранённых USD-тарифа Start/Go/Go X5/Go X15 вступили в силу и активированы по официальной pricing policy."),
        })

    def apply_candidates(self) -> None:
        candidates = [
            ("Models", "ling-3-1-flash-ed6a8f2c", {
                "Status": "NEEDS_REVIEW", "Publication Decision": "NEEDS_REVIEW", "Name": "Ling-3.1-Flash", "Developer": "InclusionAI / Ant Group",
                "Reason": "Не найден первичный официальный model card/repository/release post точной версии; параметры 560B/25B/1M пока подтверждены только вторичным источником.",
                "Decision Code": "SOURCE", "Decision Date": DAY, "Decision Sources": LING_SECONDARY, "Secondary Source": LING_SECONDARY,
                "Last Verified": DAY, "On Local": "NO", "On Production": "NO", "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Candidate only. Не переносить вторичные claims в публичные поля до официального источника.",
                "Category": "text", "Catalog Status": "active", "Source Title": "Ant Group launches Ling-3.1-Flash with 560 billion parameters",
                "Source URL": LING_SECONDARY, "Source Publisher": "TechNode", "Import Sources (unverified)": LING_SECONDARY, "Import Batch": BATCH,
            }),
            ("Tools", "cloudflare-ai-search-e8e99bba", {
                "Status": "NEEDS_REVIEW", "Publication Decision": "NEEDS_REVIEW", "Name": "Cloudflare AI Search", "Developer": "Cloudflare",
                "Reason": "GA-обновление подтверждено, но перед публикацией отдельной карточки нужно закрепить первую дату/границу сущности AI Search относительно прежнего AutoRAG.",
                "Decision Code": "SCOPE", "Decision Date": DAY, "Decision Sources": AI_SEARCH_GA, "Official Source": AI_SEARCH_GA,
                "Last Verified": DAY, "On Local": "NO", "On Production": "NO", "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] GA 01.10.2026: multimodal embeddings, PDF OCR, larger files; billing starts 01.11.2026. Candidate only.",
                "Version": "GA", "Category": "api_service", "Purposes": "search; retrieval; RAG", "Local Execution": "no",
                "Official URL": AI_SEARCH_GA, "Platforms": "web; api", "Catalog Status": "active", "Developer Country": "USA",
                "Source Title": "AI Search is generally available", "Source URL": AI_SEARCH_GA, "Source Publisher": "Cloudflare",
                "Import Sources (unverified)": AI_SEARCH_GA, "Import Batch": BATCH,
            }),
            ("Tools", "cloudflare-monetization-gateway-df9e00bf", {
                "Status": "NEEDS_REVIEW", "Publication Decision": "NEEDS_REVIEW", "Name": "Cloudflare Monetization Gateway", "Developer": "Cloudflare",
                "Exact Release Date": "2026-07-01", "Reason": "Продукт и closed beta подтверждены, но требуется редакционное решение: самостоятельная Tool-карточка или инфраструктурная функция Cloudflare.",
                "Decision Code": "SCOPE", "Decision Date": DAY, "Decision Sources": MONETIZATION_FIRST + " | " + MONETIZATION_BETA,
                "Official Source": MONETIZATION_FIRST, "Secondary Source": MONETIZATION_BETA, "Last Verified": DAY,
                "On Local": "NO", "On Production": "NO", "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Closed beta с 30.09; x402-платежи за API, MCP tools, сайты и datasets. Candidate only.",
                "Version": "closed beta", "Category": "api_service", "Purposes": "payments; agents; API monetization; MCP", "Local Execution": "no",
                "Official URL": MONETIZATION_BETA, "Platforms": "web; api", "Catalog Status": "active", "Developer Country": "USA",
                "Source Title": "Introducing Monetization Gateway", "Source URL": MONETIZATION_FIRST, "Source Publisher": "Cloudflare",
                "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-07-01", "precision": "day", "source_url": MONETIZATION_FIRST, "closed_beta": "2026-09-30"}),
                "Research Date Hint": "2026-07-01 (day)", "Import Sources (unverified)": MONETIZATION_FIRST + " | " + MONETIZATION_BETA, "Import Batch": BATCH,
            }),
            ("Tools", "robinhood-agents-503b1a9f", {
                "Status": "NEEDS_REVIEW", "Publication Decision": "NEEDS_REVIEW", "Name": "Robinhood Agents", "Developer": "Robinhood",
                "Exact Release Date": "2026-09-29", "Reason": "Официальный анонс находится вне окна ежедневного отчёта и требует проверки фактической доступности, цен, моделей и границы с Robinhood Agentic Trading.",
                "Decision Code": "SCOPE", "Decision Date": DAY, "Decision Sources": ROBINHOOD, "Official Source": ROBINHOOD,
                "Last Verified": DAY, "On Local": "NO", "On Production": "NO", "Notes": "[DAILY-CATALOG-UPDATE-2026-10-01] Candidate only; не публиковать до проверки rollout и продуктовой границы.",
                "Version": "announced rollout", "Category": "agent_platform", "Purposes": "market research; holdings analysis; trading agents", "Local Execution": "no",
                "Official URL": ROBINHOOD, "Platforms": "web; ios; android", "Catalog Status": "active", "Developer Country": "USA",
                "Source Title": "HOOD Summit 2026", "Source URL": ROBINHOOD, "Source Publisher": "Robinhood",
                "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-09-29", "precision": "day", "source_url": ROBINHOOD, "availability": "coming soon / rolling rollout requires reconciliation"}),
                "Research Date Hint": "2026-09-29 (day)", "Import Sources (unverified)": ROBINHOOD, "Import Batch": BATCH,
            }),
        ]
        for sheet, record_id, spec in candidates:
            self.main(sheet, record_id, spec)

    def apply(self) -> None:
        self.apply_new_models()
        self.apply_cloudflare_os()
        self.apply_existing_updates()
        self.apply_sourcecraft_prices()
        self.apply_candidates()

    def save(self) -> None:
        self.meta = cm.refresh_meta(dict(self.meta), self.rows, self.stamp)
        cm.write_workbook(self.rows, self.meta, self.path, self.extra)
        print(json.dumps({
            "created": self.created,
            "updated_fields": len(self.updated),
            "updated_records": sorted({item.rsplit(":", 1)[0] for item in self.updated}),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=cm.WORKBOOK_PATH)
    args = parser.parse_args()
    update = Update(args.path)
    update.apply()
    update.save()

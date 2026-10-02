"""Apply Daily Catalog Update Release #022 (2026-10-02) to the master workbook.

Idempotent.  Adds the current-window decision models Clef, Clef-flash and
Strands Decider 2B, the historical catch-ups for the four Kev 1.0 models and
the AnythingLLM Tool, and updates the existing GitHub Copilot record in place.
Vendor / self-reported benchmark numbers are recorded only as developer-reported
facts; no Evaluation rows are created.  Unknown values stay empty.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog import catalog_master as cm
from tools import daily_catalog_update_2026_10_01 as base
from tools.daily_catalog_update_2026_10_01 import Update as BaseUpdate, json_text


DAY = "2026-10-02"
BATCH = "release-022-daily-catalog-2026-10-02"
REASON = "daily catalog update #022"
# The shared row helpers read these module globals for Changelog reasons.
base.DAY, base.BATCH, base.REASON = DAY, BATCH, REASON
MARK = "[DAILY-CATALOG-UPDATE-2026-10-02]"

CLEF_BLOG = "https://blog.cloudflare.com/clef-decision-models/"
CLEF_CHANGELOG = "https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/"
CLEF_WAI = "https://developers.cloudflare.com/workers-ai/models/clef/"
CLEF_HF = "https://huggingface.co/cloudflare/clef"
FLASH_WAI = "https://developers.cloudflare.com/workers-ai/models/clef-flash/"
FLASH_HF = "https://huggingface.co/cloudflare/clef-flash"
CLEF_RL = "https://www.cloudflare.com/resource/clef-rl-interest/"

STRANDS_BLOG = "https://strandsagents.com/blog/introducing-strands-decider/"
STRANDS_GH = "https://github.com/strands-labs/strands-decider"
STRANDS_HF = "https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19"

KEV_RELEASE = "https://github.com/jaredpalmer/kev/releases/tag/kev-1.0"
KEV_REPO = "https://github.com/jaredpalmer/kev"
KEV_PROFILE = "https://github.com/jaredpalmer"
KEV_HF = {size: "https://huggingface.co/jaredpalmer/kev-%s" % size for size in ("0.8b", "4b", "9b", "27b")}

ALLM_SITE = "https://anythingllm.com/"
ALLM_PRICING = "https://anythingllm.com/pricing"
ALLM_REPO = "https://github.com/Mintplex-Labs/anything-llm"
ALLM_RELEASE = "https://github.com/Mintplex-Labs/anything-llm/releases/tag/v1.17.0"
ALLM_DOCKER = "https://hub.docker.com/r/mintplexlabs/anythingllm"
ALLM_ANNOUNCE = "https://medium.com/rampp/anythingllm-the-easiest-way-to-chat-with-documents-in-seconds-337ea08d4b7e"
ALLM_ORG = "https://github.com/Mintplex-Labs"

COPILOT_ID = "github-copilot-179ab1d0"
COPILOT_COMPUTER_USE = "https://github.blog/changelog/2026-10-01-github-copilot-can-now-interact-with-desktop-apps"
COPILOT_WORKFLOWS = "https://github.blog/changelog/2026-10-01-dynamic-workflows-in-copilot-cli-and-the-copilot-app"
COPILOT_RETIRED = "https://github.blog/changelog/2026-10-02-selected-models-in-github-copilot-deprecated"
COPILOT_RETIRE_NOTICE = "https://github.blog/changelog/2026-09-16-upcoming-deprecation-of-selected-github-copilot-models"

WEB_SEARCH_CHANGELOG = "https://developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/"
WEB_SEARCH_DOCS = "https://developers.cloudflare.com/web-search/"
WEB_SEARCH_PROVIDERS = "https://developers.cloudflare.com/web-search/providers/"
WEB_SEARCH_HOWTO = "https://developers.cloudflare.com/web-search/how-to-use/"
XAI_RELEASE_NOTES = "https://docs.x.ai/developers/release-notes"
XAI_STT_DOCS = "https://docs.x.ai/developers/model-capabilities/audio/speech-to-text"

WEB_SEARCH_ID = "cloudflare-web-search-api-0bb0f08e"
XAI_STT_IDS = ("grok-speech-to-text-cfab200f", "grok-speech-to-text-streaming-1109f624")
CLEF_ID = "clef-bdc7df20"
FLASH_ID = "clef-flash-4eaa2224"
STRANDS_ID = "strands-decider-2b-81831af4"
KEV_IDS = {"0.8b": "kev-0-8b-46011d0e", "4b": "kev-4b-2ab542cc", "9b": "kev-9b-v2-7e1fcef1", "27b": "kev-27b-v2-59a82a0e"}
ALLM_ID = "anythingllm-90d04ca3"


class Update(BaseUpdate):
    def log(self, sheet, record_id, field, before, after, reason=REASON):
        super().log(sheet, record_id, field, before, after, reason)

    def fact(self, key, record_type, record_id, name, value, source):
        self.aux("Facts", key, {
            "Key": key, "Record Type": record_type, "Record ID": record_id, "Fact": name,
            "Value (JSON)": json_text(value), "Source URL": source, "Checked": DAY,
        })

    def origin(self, key, record_id, source, record_type="model", code="US", position="0"):
        self.aux("Origins", key, {
            "Key": key, "Record Type": record_type, "Record ID": record_id, "Country": code,
            "Position": position, "Source URL": source, "Checked": DAY,
        })

    def access(self, key, record_type, record_id, service, kind, url, provider, location, source):
        self.aux("Access", key, {
            "Key": key, "Record Type": record_type, "Record ID": record_id, "Service": service,
            "Service Kind": kind, "Service URL": url, "Provider": provider, "Compute Location": location,
            "Source URL": source, "Checked": DAY,
        })

    def model(self, record_id, spec):
        base = {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Decision Date": DAY,
            "Last Verified": DAY, "On Local": "NO", "On Production": "NO", "Release Stage": "released",
            "Category": "text", "Output Modalities": "other", "License": "Apache-2.0", "Open Weights": "YES",
            "Catalog Status": "active", "Developer Country": "USA", "Origin Countries": "US",
            "Checked (DB)": DAY, "Import Batch": BATCH,
        }
        self.main("Models", record_id, {**base, **spec})

    def evaluation_status(self, key, record_id, developer, sources, reason_en, reason_ru):
        self.fact(key, "model", record_id, "independent_evaluation_status", {
            "checked": DAY, "final_class": "developer_reported", "status": "developer_reported",
            "developer_evaluators": [developer], "developer_sources": sources,
            "independent_public_evaluators": [], "counts": {"developer": 1, "independent_public": 0},
            "reason_en": reason_en, "reason_ru": reason_ru,
            "next_step": "Look for a third-party exact-version decision-model evaluation with a stated results licence.",
        }, sources[0])

    # ------------------------------------------------------------ Cloudflare
    def apply_clef(self):
        common_limits = {
            "max_images": 4, "image_formats": ["PNG", "JPEG", "WebP"], "max_image_mib": 4,
            "max_image_megapixels": 16, "max_decoded_images_mib": 8, "max_request_body_mib": 13,
            "remote_image_urls": False,
        }
        for record_id, name, size, base, price, wai, hf, latency, limits_source in (
                (CLEF_ID, "Clef", 27, "Qwen/Qwen3.8-27B", "0.24", CLEF_WAI, CLEF_HF, 209.3, CLEF_WAI),
                (FLASH_ID, "Clef-flash", 9, "Qwen/Qwen3.5-9B", "0.09", FLASH_WAI, FLASH_HF, 38.8, FLASH_WAI)):
            slug = "clef" if record_id == CLEF_ID else "clef-flash"
            fast = record_id == FLASH_ID
            self.model(record_id, {
                "Name": name, "Developer": "Cloudflare", "Exact Release Date": "2026-10-01",
                "Reason": "Отдельная open-weight decision-модель Cloudflare с собственным Workers AI ID, model card и ценой; не alias и не режим другой модели.",
                "Decision Code": "CURRENT_RELEASE", "Decision Sources": " | ".join((CLEF_BLOG, CLEF_CHANGELOG, wai, hf)),
                "Aliases": "@cf/cloudflare/%s | Cloudflare/%s" % (slug, slug),
                "Official Source": CLEF_BLOG, "Secondary Source": wai,
                "Notes": "%s Decision model: возвращает вероятности по типизированным вопросам (noul/choice/score), не генерирует текст; Max Output намеренно пуст. "
                         "Context 65,536 — окно Workers AI; model card указывает default max_length 16,384 для локального encode_record (Facts). "
                         "Benchmarks Cloudflare (Decision Index, latency) — developer-reported, Evaluation rows не созданы." % MARK,
                "Family": "Clef", "Version": name, "Tasks": "text; vision",
                "Input Modalities": "text; image; video", "Context": "65536",
                "Description EN": ("Clef-flash is Cloudflare's fast %dB open-weight multimodal decision model: it reads a text, JSON, image or video state with a schema of typed questions and returns calibrated probabilities instead of generated text." % size) if fast else
                                  ("Clef is Cloudflare's %dB open-weight multimodal decision model: it reads a text, JSON, image or video state with a schema of typed questions and returns calibrated probabilities instead of generated text." % size),
                "Description RU": ("Clef-flash — быстрая open-weight мультимодальная decision-модель Cloudflare на %d млрд параметров: принимает состояние (текст, JSON, изображения, видео) и схему типизированных вопросов и возвращает откалиброванные вероятности, а не сгенерированный текст." % size) if fast else
                                  ("Clef — open-weight мультимодальная decision-модель Cloudflare на %d млрд параметров: принимает состояние (текст, JSON, изображения, видео) и схему типизированных вопросов и возвращает откалиброванные вероятности, а не сгенерированный текст." % size),
                "Suitable EN": "Routing, moderation, triage, scoring and other agent or workflow decisions with up to 64 yes/no, multiple-choice or ordinal questions per request on Workers AI or self-hosted weights.",
                "Suitable RU": "Маршрутизация, модерация, триаж, оценка и другие решения агентов и рабочих процессов — до 64 вопросов типа да/нет, выбор варианта или шкала за запрос в Workers AI или на собственных весах.",
                "Limitations EN": "Not a text generator: answers are bounded to the supplied options and probabilities. Workers AI accepts at most 4 PNG/JPEG/WebP images (4 MiB and 16 MP each, 8 MiB decoded total, 13 MiB request body) and no remote image URLs. Published benchmarks are Cloudflare's own.",
                "Limitations RU": "Не генерирует текст: ответы ограничены заданными вариантами и вероятностями. Workers AI принимает не более 4 изображений PNG/JPEG/WebP (до 4 MiB и 16 Мп каждое, 8 MiB суммарно после декодирования, тело запроса до 13 MiB), удалённые URL изображений не принимаются. Опубликованные бенчмарки — собственные данные Cloudflare.",
                "Source Title": "Introducing Clef: our open-source decision models, and new RL fine-tuning platform",
                "Source URL": CLEF_BLOG, "Source Publisher": "Cloudflare",
                "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-10-01", "precision": "day", "date_kind": "release",
                                                      "source_url": CLEF_BLOG, "changelog": CLEF_CHANGELOG, "model_card": hf}),
                "Research Date Hint": "2026-10-01 (day)",
                "Import Sources (unverified)": " | ".join((CLEF_BLOG, CLEF_CHANGELOG, wai, hf)),
            })
            self.origin("origin-022-%s-us" % slug, record_id, CLEF_BLOG)
            self.access("access-022-%s-workers-ai" % slug, "model", record_id, "Cloudflare Workers AI", "api", wai,
                        "Cloudflare", "cloud", wai)
            self.access("access-022-%s-hf" % slug, "model", record_id, "Hugging Face model repository", "download", hf,
                        "Cloudflare", "local", hf)
            self.aux("Offers", "offer-022-%s-input" % slug, {
                "Key": "offer-022-%s-input" % slug, "Record Type": "model", "Record ID": record_id,
                "Service": "Cloudflare Workers AI", "Service Kind": "api", "Service URL": wai, "Provider": "Cloudflare",
                "Compute Location": "cloud", "Amount": price, "Unit": "input", "Billing Unit": "",
                "Conditions EN": "Workers AI, per 1M input tokens (@cf/cloudflare/%s)." % slug,
                "Conditions RU": "Workers AI, за 1 млн входных токенов (@cf/cloudflare/%s)." % slug,
                "Conditions Extra (JSON)": "", "Primary": "YES", "Active": "YES", "Source URL": wai, "Checked": DAY,
                "Research Key": "release022:%s:workers-ai:input" % slug,
            })
            self.fact("fact-022-%s-decision" % slug, "model", record_id, "structured_decision_capabilities", {
                "checked": DAY, "parameters_billion": size, "base_model": base,
                "architecture": "Qwen backbone with retained vision encoder, LoRA adapters and a joint schema head; one forward pass scores every option",
                "inputs": ["text", "structured JSON state", "image", "video"],
                "outputs": ["typed decisions", "probability per option", "probability-weighted score"],
                "question_types": ["noul", "choice", "score"], "max_questions_per_request": 64,
                "free_form_generation": False, "max_output_tokens": None,
                "workers_ai_model_id": "@cf/cloudflare/%s" % slug,
                "access": ["Workers AI binding env.AI.run()", "REST /ai/run", "AI Gateway compatible"],
                "context_tokens_workers_ai": 65536, "model_card_default_max_length": 16384,
                "workers_ai_image_limits": common_limits, "license": "Apache-2.0", "weights": hf,
                "tested_hardware_not_minimum": "single NVIDIA H200 (model card test environment)",
                "developer_reported_median_latency_ms": latency,
                "developer_benchmark_not_independent": True,
            }, limits_source)
            self.evaluation_status("fact-022-%s-evaluation" % slug, record_id, "Cloudflare", [CLEF_BLOG, hf],
                                   "Only Cloudflare's own Decision Index, workflow and latency results were found for the exact version.",
                                   "Для точной версии найдены только собственные результаты Cloudflare (Decision Index, workflow evals, latency).")
        self.fact("fact-022-clef-rl-fine-tuning", "model", CLEF_ID, "fine_tuning_service", {
            "checked": DAY, "launched": "2026-10-01", "service": "Cloudflare reinforcement-learning fine-tuning",
            "method": "reinforcement learning (RLCD) for calibrated decisions", "tunes": ["Clef", "Clef-flash"],
            "availability": "design partners, hands-on with Cloudflare forward-deployed engineers", "self_serve": False,
            "signup": CLEF_RL, "standalone_product_id": None, "not_a_standalone_tool": True,
        }, CLEF_BLOG)

    # ------------------------------------------------------------ Strands
    def apply_strands(self):
        self.model(STRANDS_ID, {
            "Name": "Strands Decider 2B", "Developer": "Strands Agents / AWS", "Exact Release Date": "2026-10-01",
            "Reason": "Отдельная open-weight decision-модель Strands Labs (AWS) с опубликованным checkpoint, лицензией и пакетом запуска.",
            "Decision Code": "CURRENT_RELEASE", "Decision Sources": " | ".join((STRANDS_BLOG, STRANDS_GH, STRANDS_HF)),
            "Aliases": "strands-decider-2b | StrandsAgents/strands-decider-2B-hobson-v19",
            "Official Source": STRANDS_BLOG, "Secondary Source": STRANDS_HF,
            "Notes": "%s Exact checkpoint StrandsAgents/strands-decider-2B-hobson-v19 (reference v19; v20 — эксперимент, не заменил). Marketed 2B, checkpoint ≈1.9B. "
                     "Hosted inference provider на Hugging Face не развёрнут — коммерческий API и цена не созданы. JevBench и прочие результаты — self-reported." % MARK,
            "Family": "Strands Decider", "Version": "strands-decider-2B-hobson-v19", "Tasks": "text; agents",
            "Input Modalities": "text", "Context": "4096",
            "Description EN": "Strands Decider 2B is an open-weight decision model from Strands Labs (AWS) that reads a text state and typed questions and returns calibrated probabilities over the allowed answers instead of generating text.",
            "Description RU": "Strands Decider 2B — open-weight decision-модель Strands Labs (AWS): читает текстовое состояние и типизированные вопросы и возвращает откалиброванные вероятности по допустимым ответам вместо генерации текста.",
            "Suitable EN": "Fast local next-step, routing and classification decisions for agents with yes/no, choice and score questions on CPU, CUDA or Apple MPS.",
            "Suitable RU": "Быстрые локальные решения агентов о следующем шаге, маршрутизации и классификации с вопросами да/нет, выбор и шкала на CPU, CUDA или Apple MPS.",
            "Limitations EN": "No text generation; validated for a 4,096-token reference window. The bundled HTTP server binds to 127.0.0.1 without authentication and is meant for local experiments. No hosted API or price; published scores are self-reported.",
            "Limitations RU": "Не генерирует текст; проверенное reference-окно — 4 096 токенов. Встроенный HTTP-сервер слушает 127.0.0.1 без аутентификации и предназначен для локальных экспериментов. Hosted API и цены нет; опубликованные результаты — self-reported.",
            "Source Title": "Introducing Strands Decider", "Source URL": STRANDS_BLOG, "Source Publisher": "Strands Agents / AWS",
            "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-10-01", "precision": "day", "date_kind": "release",
                                                  "source_url": STRANDS_BLOG, "model_card": STRANDS_HF,
                                                  "hf_repo_created_utc": "2026-09-30T15:48:31Z", "repo_creation_not_release": True}),
            "Research Date Hint": "2026-10-01 (day)",
            "Import Sources (unverified)": " | ".join((STRANDS_BLOG, STRANDS_GH, STRANDS_HF)),
        })
        self.origin("origin-022-strands-decider-us", STRANDS_ID, STRANDS_BLOG)
        self.access("access-022-strands-decider-hf", "model", STRANDS_ID, "Hugging Face model repository", "download",
                    STRANDS_HF, "Strands Agents / AWS", "local", STRANDS_HF)
        self.access("access-022-strands-decider-package", "model", STRANDS_ID, "strands-decider package and CLI", "download",
                    STRANDS_GH, "Strands Agents / AWS", "local", STRANDS_GH)
        self.fact("fact-022-strands-decider-decision", "model", STRANDS_ID, "structured_decision_capabilities", {
            "checked": DAY, "checkpoint": "StrandsAgents/strands-decider-2B-hobson-v19", "marketed_parameters_billion": 2,
            "checkpoint_parameters_billion_approx": 1.9, "base_model": "Qwen/Qwen3.5-2B-Base",
            "architecture": "base torso + rank-16 LoRA + pointer/readout head (~1M parameters); LM head removed",
            "inputs": ["text state", "typed questions"], "outputs": ["probability / confidence over typed answers"],
            "question_types": ["noul", "choice", "score"], "free_form_generation": False, "max_output_tokens": None,
            "context_tokens_reference": 4096, "context_tokens_preregistered_eval": 3072,
            "local_devices": ["CPU", "CUDA", "Apple MPS"],
            "package": "strands-decider (pip)", "cli": ["strands-decider ask", "strands-decider serve"],
            "local_http_endpoint": "/v1/systemone", "local_server_bind": "127.0.0.1", "local_server_auth": False,
            "local_server_scope": "local experiments", "hosted_inference_provider": None,
            "training_hardware_not_inference_minimum": {"single_rtx_3090_hours_approx": 11, "8x_h100_approx": "1h10m"},
            "license": "Apache-2.0", "developer_benchmark_not_independent": True,
        }, STRANDS_GH)
        self.fact("fact-022-strands-decider-pricing", "model", STRANDS_ID, "pricing_status", {
            "checked": DAY, "status": "open_weights_no_hosted_api",
            "reason": "Apache-2.0 weights and local package; no hosted inference provider or official price.",
        }, STRANDS_HF)
        self.evaluation_status("fact-022-strands-decider-evaluation", STRANDS_ID, "Strands Agents / AWS", [STRANDS_HF, STRANDS_BLOG],
                               "JevBench and other published results for the exact checkpoint are marked self-reported by the developer.",
                               "JevBench и другие результаты точного checkpoint помечены разработчиком как self-reported.")

    # ------------------------------------------------------------ Kev
    def apply_kev(self):
        kev = (
            ("0.8b", "Kev-0.8B", "2026-09-24", "v1.0", "Qwen/Qwen3.5-0.8B-Base", "LoRA adapter + pointer head", 8192, 2.35,
             "9a45d25e", "2026-09-24T14:37:02Z", "2026-09-20T23:46:29Z", "", 0.8),
            ("4b", "Kev-4B", "2026-09-24", "v1.0", "Qwen/Qwen3.5-4B-Base", "LoRA adapter + pointer head", 8192, 2.41,
             "139fdd94", "2026-09-24T14:36:57Z", "2026-09-20T22:46:04Z", "", 4),
            ("9b", "Kev-9B v2", "2026-09-30", "v2 (Kev 1.0)", "Qwen/Qwen3.5-9B-Base", "LoRA adapter + pointer head", 8192, 2.19,
             "b5d8c18e", "2026-09-30T20:31:09Z", "2026-09-20T22:46:00Z", "jaredpalmer/kev-9b@v1", 9),
            ("27b", "Kev-27B v2", "2026-09-30", "v2 (Kev 1.0)", "Qwen/Qwen3.8-27B (post-trained)", "full bf16 weights (51 GB) + pointer head", 65536, 1.32,
             "28be62e9", "2026-09-30T17:50:39Z", "2026-09-24T02:58:44Z", "jaredpalmer/kev-27b@v1-lora", 27),
        )
        for size, name, released, version, base, form, context, temperature, revision, revision_date, first_name_date, previous, params in kev:
            record_id, hf = KEV_IDS[size], KEV_HF[size]
            v2 = size in ("9b", "27b")
            aliases = "jaredpalmer/kev-%s" % size + (" | Kev-%s" % size.upper() if v2 else "")
            self.model(record_id, {
                "Name": name, "Developer": "Jared Palmer", "Exact Release Date": released,
                "Reason": "Отдельная модель семейства Kev с собственным Hub-репозиторием и точной ревизией весов; historical catch-up, не релиз 1 октября.",
                "Decision Code": "HISTORICAL_RELEASE", "Decision Sources": " | ".join((KEV_RELEASE, hf)),
                "Aliases": aliases, "Official Source": KEV_RELEASE, "Secondary Source": hf,
                "Notes": ("%s Historical catch-up. Kev 1.0 (2026-10-01) — family release: ничего нового не обучалось, он закрепил тег v1.0. "
                          "Дата %s — коммит закреплённых весов %s на Hugging Face. Расхождение: модель с тем же именем и предыдущими весами была на Hub с %s; "
                          "ранние checkpoints — Facts.version_history. %s"
                          "Developer benchmark tables Kev 1.0 не являются независимой проверкой; community quantized variants не переносятся на BF16/official checkpoint." %
                          (MARK, released, revision, first_name_date[:10],
                           "Предыдущая версия: %s (не отдельная карточка). " % previous if previous else "")),
                "Family": "Kev", "Version": version, "Tasks": "text",
                "Input Modalities": "text", "Context": str(context),
                "Description EN": "%s is an open-weight Kev decision model by Jared Palmer: it reads one document or state with typed questions and returns a probability distribution per question instead of generating text." % name,
                "Description RU": "%s — open-weight decision-модель семейства Kev (Jared Palmer): читает один документ или состояние с типизированными вопросами и возвращает распределение вероятностей по каждому вопросу вместо генерации текста." % name,
                "Suitable EN": "Self-hosted document and state decisions with choice, score and yes/no questions behind a System One-compatible API.",
                "Suitable RU": "Самостоятельно развёрнутые решения по документам и состояниям с вопросами выбор, шкала и да/нет через API, совместимый с System One.",
                "Limitations EN": ("No free-form text generation. Validated context is %s tokens; the server accepts states up to 65,536 tokens. Serving the 51 GB bf16 weights is documented on one B200, H200 or H100 80 GB GPU (not a universal minimum). Published results are the developer's own." % format(context, ",")) if size == "27b" else
                                  ("No free-form text generation. Validated context is %s tokens, although the serving system accepts states up to 65,536 tokens. Published results are the developer's own." % format(context, ",")),
                "Limitations RU": ("Не генерирует свободный текст. Проверенный контекст — %s токенов; сервер принимает состояния до 65 536 токенов. Для 51 GB bf16-весов документирован запуск на одной B200, H200 или H100 80 GB (не универсальный минимум). Опубликованные результаты — данные разработчика." % format(context, ",").replace(",", " ")) if size == "27b" else
                                  ("Не генерирует свободный текст. Проверенный контекст — %s токенов, хотя сервер принимает состояния до 65 536 токенов. Опубликованные результаты — данные разработчика." % format(context, ",").replace(",", " ")),
                "Source Title": "Release Kev 1.0 · jaredpalmer/kev", "Source URL": KEV_RELEASE, "Source Publisher": "Jared Palmer (GitHub)",
                "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": released, "precision": "day", "date_kind": "pinned_weights_commit",
                                                      "source_url": hf, "weights_revision": revision, "weights_commit_utc": revision_date,
                                                      "family_release": {"name": "Kev 1.0", "date": "2026-10-01", "newly_trained": False, "url": KEV_RELEASE},
                                                      "same_name_first_on_hub_utc": first_name_date, "not_import_date": True}),
                "Research Date Hint": "%s (day)" % released,
                "Import Sources (unverified)": " | ".join((KEV_RELEASE, hf)),
            })
            self.origin("origin-022-kev-%s-us" % size, record_id, KEV_RELEASE)
            self.fact("fact-022-kev-%s-origin" % size, "model", record_id, "entity_verification", {
                "checked": DAY, "developer": "Jared Palmer", "country": "USA",
                "evidence": "GitHub profile of the repository owner lists New York, NY",
            }, KEV_PROFILE)
            self.access("access-022-kev-%s-hf" % size, "model", record_id, "Hugging Face model repository", "download", hf,
                        "Jared Palmer", "local", hf)
            self.fact("fact-022-kev-%s-decision" % size, "model", record_id, "structured_decision_capabilities", {
                "checked": DAY, "parameters_billion": params, "base_model": base, "form": form,
                "inputs": ["one document / state", "typed questions"], "outputs": ["probability distribution per question"],
                "question_types": ["choice", "score", "noul"], "free_form_generation": False, "max_output_tokens": None,
                "validated_context_tokens": context, "service_max_state_tokens": 65536,
                "temperature": temperature, "weights_revision": revision, "pinned_tag": "v1.0",
                "license": "Apache-2.0", "serving_hardware_documented": ["B200", "H200", "H100 80 GB"] if size == "27b" else None,
                "serving_hardware_is_not_universal_minimum": True,
                "community_quantized_variants_not_applicable": True, "developer_benchmark_not_independent": True,
            }, KEV_RELEASE)
            self.fact("fact-022-kev-%s-versions" % size, "model", record_id, "version_history", {
                "checked": DAY, "record_checkpoint": {"revision": revision, "committed_utc": revision_date},
                "same_name_first_on_hub_utc": first_name_date, "previous_version_tag": previous or None,
                "family_release": "Kev 1.0 2026-10-01 (card-only commits, weights unchanged)",
                "earlier_family_release": "GitHub release kev-family, first published 2026-09-20, current family assembled 2026-09-24",
            }, hf)
            self.fact("fact-022-kev-%s-pricing" % size, "model", record_id, "pricing_status", {
                "checked": DAY, "status": "open_weights_no_hosted_api",
                "reason": "Apache-2.0 open weights; no official hosted API or price.",
            }, KEV_RELEASE)
            self.evaluation_status("fact-022-kev-%s-evaluation" % size, record_id, "Jared Palmer", [KEV_RELEASE, hf],
                                   "Kev 1.0 benchmark tables are the developer's own; no third-party exact-version result was found.",
                                   "Таблицы Kev 1.0 — собственные результаты разработчика; независимого результата точной версии не найдено.")

    # ------------------------------------------------------------ AnythingLLM
    def apply_anythingllm(self):
        self.main("Tools", ALLM_ID, {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Name": "AnythingLLM", "Developer": "Mintplex Labs Inc",
            "Approx Date": "≈2023-06-07", "Approx Precision": "day",
            "Reason": "Самостоятельное open-source AI-приложение (desktop, self-hosted Docker, Cloud); historical catch-up, не новый Tool октября.",
            "Decision Code": "HISTORICAL_RELEASE", "Decision Date": DAY,
            "Decision Sources": " | ".join((ALLM_ANNOUNCE, ALLM_REPO, ALLM_RELEASE, ALLM_PRICING)),
            "Official Source": ALLM_SITE, "Secondary Source": ALLM_RELEASE, "Last Verified": DAY,
            "On Local": "NO", "On Production": "NO",
            "Notes": "%s Historical catch-up. Дата ≈2023-06-07 — публичный анонс автора (Medium, 7 июня 2023); первичный пост не открылся для проверки (HTTP 403), "
                     "поэтому Exact пуст. GitHub repo создан 2023-06-04 (initial commit), что не доказывает публичность. v1.17.0 — 2026-10-01, это обновление версии, не дата продукта. "
                     "Docker не является controlled platform term: self-host оформлен через Access/Offer/Facts. AnythingLLM Mobile — отдельный продукт, в Platforms не включён." % MARK,
            "Version": "1.17.0", "Category": "ai_app", "Purposes": "retrieval; agents; documents; local inference",
            "Local Execution": "yes", "Official URL": ALLM_SITE, "Platforms": "web; desktop; windows; macos; linux",
            "Catalog Status": "active", "Developer Country": "USA",
            "Description EN": "AnythingLLM is Mintplex Labs' MIT-licensed all-in-one AI application for chatting with documents, RAG and agents, available as a desktop app, a self-hosted Docker deployment and a managed cloud.",
            "Description RU": "AnythingLLM — AI-приложение Mintplex Labs под лицензией MIT для работы с документами, RAG и агентами: desktop-приложение, самостоятельное развёртывание в Docker и управляемое облако.",
            "Ecosystem EN": "Local and cloud LLM, embedding and vector-database providers, including Ollama, OpenAI, Anthropic, AWS Bedrock and Google Gemini",
            "Ecosystem RU": "Локальные и облачные провайдеры LLM, эмбеддингов и векторных баз, в том числе Ollama, OpenAI, Anthropic, AWS Bedrock и Google Gemini",
            "Source Title": "AnythingLLM", "Source URL": ALLM_SITE, "Source Publisher": "Mintplex Labs Inc", "Checked (DB)": DAY,
            "Approx Evidence (JSON)": json_text({"checked": DAY, "approx": "2023-06-07", "precision": "day", "date_kind": "first_public_announcement",
                                                 "source_urls": [ALLM_ANNOUNCE], "primary_not_retrievable": "HTTP 403 on 2026-10-02",
                                                 "repository_initial_commit_utc": "2023-06-04T02:28:07Z", "repository_creation_not_public_release": True,
                                                 "not_exact_first_release": True}),
            "Release Evidence (JSON)": json_text({"checked": DAY, "approx": "2023-06-07", "precision": "day", "date_kind": "first_public_announcement",
                                                  "source_url": ALLM_ANNOUNCE, "current_version": "1.17.0", "current_version_released_utc": "2026-10-01T22:17:40Z",
                                                  "version_date_not_product_date": True}),
            "Research Date Hint": "≈2023-06-07 (day)",
            "Import Sources (unverified)": " | ".join((ALLM_ANNOUNCE, ALLM_REPO, ALLM_RELEASE, ALLM_PRICING)),
            "Import Batch": BATCH,
        })
        self.access("access-022-anythingllm-desktop", "tool", ALLM_ID, "AnythingLLM Desktop", "app",
                    "https://anythingllm.com/desktop", "Mintplex Labs Inc", "local", ALLM_SITE)
        self.access("access-022-anythingllm-docker", "tool", ALLM_ID, "AnythingLLM Docker (self-hosted)", "download",
                    ALLM_DOCKER, "Mintplex Labs Inc", "local", ALLM_PRICING)
        self.access("access-022-anythingllm-cloud", "tool", ALLM_ID, "AnythingLLM Cloud", "web",
                    ALLM_PRICING, "Mintplex Labs Inc", "cloud", ALLM_PRICING)
        offers = (
            ("selfhost", "AnythingLLM Docker (self-hosted)", "app", ALLM_DOCKER, "local", "0", "NO",
             "Free self-hosted software (Docker); hardware, model and API provider costs are separate. Not free inference.",
             "Бесплатное ПО для самостоятельного развёртывания (Docker); оборудование, модели и API-провайдеры оплачиваются отдельно. Это не бесплатный inference."),
            ("desktop", "AnythingLLM Desktop", "app", "https://anythingllm.com/desktop", "local", "0", "NO",
             "Free desktop app running on your device; model and API provider costs are separate.",
             "Бесплатное desktop-приложение на вашем устройстве; модели и API-провайдеры оплачиваются отдельно."),
            ("cloud-basic", "AnythingLLM Cloud", "web", ALLM_PRICING, "cloud", "50", "YES",
             "Cloud Basic: private instance; per month; LLM API key and model costs are separate.",
             "Cloud Basic: приватный инстанс; в месяц; ключ LLM API и стоимость моделей — отдельно."),
            ("cloud-pro", "AnythingLLM Cloud", "web", ALLM_PRICING, "cloud", "99", "NO",
             "Cloud Pro: private instance for larger teams with 72-hour support SLA; per month; model costs are separate.",
             "Cloud Pro: приватный инстанс для больших команд, SLA поддержки 72 часа; в месяц; стоимость моделей — отдельно."),
        )
        for slug, service, kind, url, location, amount, primary, en, ru in offers:
            key = "offer-022-anythingllm-%s" % slug
            self.aux("Offers", key, {
                "Key": key, "Record Type": "tool", "Record ID": ALLM_ID, "Service": service, "Service Kind": kind,
                "Service URL": url, "Provider": "Mintplex Labs Inc", "Compute Location": location, "Amount": amount,
                "Unit": "month", "Billing Unit": "", "Conditions EN": en, "Conditions RU": ru, "Conditions Extra (JSON)": "",
                "Primary": primary, "Active": "YES", "Source URL": ALLM_PRICING, "Checked": DAY,
                "Research Key": "release022:anythingllm:%s:month" % slug,
            })
        self.fact("fact-022-anythingllm-enterprise", "tool", ALLM_ID, "enterprise_pricing", {
            "checked": DAY, "plan": "Cloud Enterprise", "price": "contact_sales", "amount": None,
            "includes": ["on-premise option", "custom SLA", "SSO", "RBAC"],
        }, ALLM_PRICING)
        self.fact("fact-022-anythingllm-license", "tool", ALLM_ID, "software_license", {
            "checked": DAY, "core_license": "MIT", "repository": ALLM_REPO,
        }, ALLM_REPO)
        self.fact("fact-022-anythingllm-deployment", "tool", ALLM_ID, "deployment_modes", {
            "checked": DAY, "modes": ["desktop (Windows, macOS, Linux)", "self-hosted Docker", "AnythingLLM Cloud"],
            "docker_is_not_a_controlled_platform_term": True,
            "separate_product_not_in_platforms": "AnythingLLM Mobile (Android)",
            "providers": "local and cloud LLM providers; specific model versions not enumerated",
        }, ALLM_SITE)
        self.fact("fact-022-anythingllm-1170", "tool", ALLM_ID, "release_update", {
            "checked": DAY, "version": "1.17.0", "released_utc": "2026-10-01T22:17:40Z", "prerelease": False,
            "changes": ["SearchApi engines for agent web browsing", "Firecrawl agent web-search provider",
                        "Gemini image-generation provider", "OpenAI models through AWS Bedrock", "reasoning-effort controls"],
            "version_date_not_product_date": True,
        }, ALLM_RELEASE)
        self.fact("fact-022-anythingllm-origin", "tool", ALLM_ID, "entity_verification", {
            "checked": DAY, "developer": "Mintplex Labs Inc", "country": "USA",
            "evidence": "GitHub organization Mintplex-Labs location: United States of America",
        }, ALLM_ORG)

    # ------------------------------------------------------------ GitHub Copilot
    def apply_copilot(self):
        copilot = next(row for row in self.rows["Tools"] if row.get("Record ID") == COPILOT_ID)
        self.main("Tools", COPILOT_ID, {
            "Platforms": "web; cli; ide; desktop; windows; macos",
            "Last Verified": DAY,
            "Notes": self.note(copilot, MARK, "%s Computer Use и Dynamic Workflows (public preview, 2026-10-01) — функции существующего Copilot, не отдельные Tool. "
                                              "Платформы дополнены desktop/windows/macos по GitHub Copilot app. Retirements 2026-10-02 относятся только к Copilot "
                                              "(Facts.ecosystem_model_retirement); глобальные карточки моделей не архивируются; Supported Models не менялись (0 удалений)." % MARK),
        })
        self.fact("fact-022-copilot-computer-use", "tool", COPILOT_ID, "release_update", {
            "checked": DAY, "effective_date": "2026-10-01", "feature": "Computer Use", "status": "public preview",
            "surfaces": ["GitHub Copilot CLI", "GitHub Copilot app"], "platforms": ["Windows", "macOS"],
            "capabilities": ["accessible app content", "visual context", "click", "type/edit text", "keypress", "scroll", "drag", "GUI workflows across apps"],
            "user_approval_required": True, "macos_permissions": ["Accessibility", "Screen Recording"],
            "organization_managed_settings_can_disable": True, "not_a_standalone_tool": True,
        }, COPILOT_COMPUTER_USE)
        self.fact("fact-022-copilot-dynamic-workflows", "tool", COPILOT_ID, "release_update", {
            "checked": DAY, "effective_date": "2026-10-01", "feature": "Dynamic Workflows", "status": "public preview",
            "surfaces": ["Copilot CLI", "Copilot app", "Copilot SDK"], "plans": "all Copilot plans",
            "combines": "deterministic code-defined steps with one or more agents", "stages": ["sequential", "parallel"],
            "features": ["structured handoffs between stages", "checkpoints", "pause and resume after review"],
            "app_setup": "none", "cli_enablement": "experimental (--experimental or /experimental on)",
            "not_a_standalone_tool": True,
        }, COPILOT_WORKFLOWS)
        self.fact("fact-022-copilot-model-retirements", "tool", COPILOT_ID, "ecosystem_model_retirement", {
            "checked": DAY, "effective_date": "2026-10-02", "scope": "GitHub Copilot only",
            "retired": [
                {"model": "Gemini 3.5 Flash", "replacement": "Gemini 3.8 Flash"},
                {"model": "Gemini 3.6 Flash", "replacement": "Gemini 3.8 Flash"},
                {"model": "Kimi K2.7 Code", "replacement": "Kimi K3"},
                {"model": "Claude Opus 4.7", "replacement": "Claude Opus 5.5"},
            ],
            "replacement_discrepancy": "The 2026-09-16 notice named Claude Opus 5; the 2026-10-02 deprecation post names Claude Opus 5.5 (fresher source used).",
            "global_model_status_changed": False, "supported_models_removed": 0,
        }, COPILOT_RETIRED)

    def drop_platform_rows(self):
        """Tool Platforms rows are written by `import` from Local after sync;
        the Platforms cell is the master source (an early draft added them)."""
        keep = []
        for row in self.rows["Tool Platforms"]:
            if row.get("Key", "").startswith("platform-022-"):
                self.log("Tool Platforms", row.get("Record ID", ""), "Aux row", row["Key"], "",
                         REASON + ": remove draft row; platforms sync from the Platforms cell")
                self.updated.append("Tool Platforms:%s:removed" % row["Key"])
            else:
                keep.append(row)
        self.rows["Tool Platforms"] = keep

    # ------------------------------------------------------------ owner fix pass (2026-10-02)
    def apply_web_search(self):
        """Cloudflare Web Search API beta (2026-10-02): a standalone API product
        with its own docs, endpoint and changelog product tag, like the xAI
        Speech to Text API Tools; not a capability of an existing card."""
        self.main("Tools", WEB_SEARCH_ID, {
            "Status": "PUBLISHED", "Publication Decision": "PUBLIC", "Name": "Cloudflare Web Search API",
            "Developer": "Cloudflare", "Exact Release Date": "2026-10-02",
            "Reason": "Самостоятельный API-продукт Cloudflare (beta) с отдельной документацией, REST endpoint и продуктовым тегом changelog; не функция существующей карточки.",
            "Decision Code": "CURRENT_RELEASE", "Decision Date": DAY,
            "Decision Sources": " | ".join((WEB_SEARCH_CHANGELOG, WEB_SEARCH_DOCS, WEB_SEARCH_PROVIDERS)),
            "Aliases": "Web Search API", "Official Source": WEB_SEARCH_CHANGELOG, "Secondary Source": WEB_SEARCH_DOCS,
            "Last Verified": DAY, "On Local": "NO", "On Production": "NO",
            "Notes": "%s Beta 2026-10-02. Работает через AI Gateway (логи, оплата кредитами AI Gateway по прайсу провайдера без наценки Cloudflare) или BYOK. "
                     "Провайдеры Ceramic.ai (по умолчанию), Exa, Linkup. Расхождение официальных страниц: changelog утверждает ZDR у всех трёх провайдеров, "
                     "страница Providers — ZDR Yes у Ceramic.ai и Linkup, No у Exa; в Facts записаны обе формулировки. Проверено Cloudflare AI Search (RAG) — другая сущность." % MARK,
            "Version": "beta", "Category": "api_service", "Purposes": "search; retrieval; agents",
            "Local Execution": "no", "Official URL": WEB_SEARCH_DOCS, "Platforms": "api", "Catalog Status": "active",
            "Developer Country": "USA",
            "Description EN": "Cloudflare Web Search API (beta) lets AI agents and applications search the web through AI Gateway and get structured results from Ceramic.ai, Exa or Linkup to ground model responses in live information.",
            "Description RU": "Cloudflare Web Search API (beta) позволяет AI-агентам и приложениям искать в интернете через AI Gateway и получать структурированные результаты Ceramic.ai, Exa или Linkup, чтобы опирать ответы моделей на актуальные данные.",
            "Ecosystem EN": "AI Gateway (logs, unified billing), Workers AI binding env.AI.websearch, REST API; providers Ceramic.ai, Exa and Linkup; bring your own provider key",
            "Ecosystem RU": "AI Gateway (логи, единая оплата), Workers AI binding env.AI.websearch, REST API; провайдеры Ceramic.ai, Exa и Linkup; можно использовать собственный ключ провайдера",
            "Source Title": "Introducing Web Search API", "Source URL": WEB_SEARCH_CHANGELOG, "Source Publisher": "Cloudflare",
            "Checked (DB)": DAY,
            "Release Evidence (JSON)": json_text({"checked": DAY, "date_text": "2026-10-02", "precision": "day", "date_kind": "beta_launch",
                                                  "source_url": WEB_SEARCH_CHANGELOG, "docs": WEB_SEARCH_DOCS}),
            "Research Date Hint": "2026-10-02 (day)",
            "Import Sources (unverified)": " | ".join((WEB_SEARCH_CHANGELOG, WEB_SEARCH_DOCS, WEB_SEARCH_PROVIDERS)),
            "Import Batch": BATCH,
        })
        self.access("access-022-web-search-rest", "tool", WEB_SEARCH_ID, "Cloudflare Web Search API", "api",
                    WEB_SEARCH_HOWTO, "Cloudflare", "cloud", WEB_SEARCH_CHANGELOG)
        for slug, provider, amount, primary in (("ceramic", "Ceramic.ai", "0.25", "YES"), ("exa", "Exa", "7.00", "NO"),
                                                ("linkup", "Linkup", "5.00", "NO")):
            key = "offer-022-web-search-%s" % slug
            self.aux("Offers", key, {
                "Key": key, "Record Type": "tool", "Record ID": WEB_SEARCH_ID, "Service": "Cloudflare Web Search API",
                "Service Kind": "api", "Service URL": WEB_SEARCH_HOWTO, "Provider": "Cloudflare", "Compute Location": "cloud",
                "Amount": amount, "Unit": "other", "Billing Unit": "1000 запросов",
                "Conditions EN": "Beta; %s provider (provider=%s), list price per 1,000 requests billed to AI Gateway credits with no Cloudflare markup; with your own key the provider bills you directly." % (provider, slug),
                "Conditions RU": "Beta; провайдер %s (provider=%s), прайс провайдера за 1 000 запросов из кредитов AI Gateway без наценки Cloudflare; с собственным ключом оплата напрямую провайдеру." % (provider, slug),
                "Conditions Extra (JSON)": "", "Primary": primary, "Active": "YES", "Source URL": WEB_SEARCH_PROVIDERS,
                "Checked": DAY, "Research Key": "release022:web-search:%s:1k-requests" % slug,
            })
        self.fact("fact-022-web-search-capabilities", "tool", WEB_SEARCH_ID, "release_update", {
            "checked": DAY, "launched": "2026-10-02", "status": "beta",
            "access": ["REST POST /client/v4/accounts/{account_id}/ai/websearch/", "Workers AI binding env.AI.websearch"],
            "runs_through": "AI Gateway (logs, AI Gateway credits)", "byok": True, "default_provider": "Ceramic.ai",
            "providers": {"ceramic": {"zdr": True, "usd_per_1k_requests": 0.25}, "exa": {"zdr": False, "usd_per_1k_requests": 7.0},
                          "linkup": {"zdr": True, "usd_per_1k_requests": 5.0}},
            "zdr_discrepancy": "Changelog: all three providers support ZDR for requests through Cloudflare; Providers page: Exa Zero Data Retention = No.",
            "verified_bot_commitment": True, "not_ai_search": "Cloudflare AI Search (RAG) is a different product",
        }, WEB_SEARCH_PROVIDERS)

    def apply_xai_stt(self):
        """grok-voice-transcribe-1.0 EOL (2026-10-02): the Speech to Text API
        products continue; only their underlying model slug is retired."""
        for record_id in XAI_STT_IDS:
            row = next(r for r in self.rows["Tools"] if r.get("Record ID") == record_id)
            self.main("Tools", record_id, {
                "Last Verified": DAY,
                "Notes": self.note(row, MARK, "%s 2026-10-02: grok-voice-transcribe-1.0 достиг EOL, запросы к этому slug маршрутизируются на grok-voice-transcribe-2.0 (по умолчанию с 2026-09-17) по той же цене. Продукт API активен; это не закрытие семейства и не новая карточка." % MARK),
            })
            self.fact("fact-022-%s-transcribe-eol" % record_id, "tool", record_id, "release_update", {
                "checked": DAY, "effective_date": "2026-10-02", "retired_model": "grok-voice-transcribe-1.0",
                "routed_to": "grok-voice-transcribe-2.0", "same_price": True, "default_since": "2026-09-17",
                "applies_to": ["REST /v1/stt", "WebSocket wss://api.x.ai/v1/stt"],
                "product_status_changed": False, "not_a_family_archive": True,
            }, XAI_RELEASE_NOTES)

    def apply(self):
        self.drop_platform_rows()
        self.apply_web_search()
        self.apply_xai_stt()
        self.apply_clef()
        self.apply_strands()
        self.apply_kev()
        self.apply_anythingllm()
        self.apply_copilot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=cm.WORKBOOK_PATH)
    args = parser.parse_args()
    update = Update(args.path)
    update.apply()
    update.save()

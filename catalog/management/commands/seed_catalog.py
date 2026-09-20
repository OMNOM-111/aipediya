from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Source, Organization, ModelFamily, ModelVersion, Service, Access, Offer, Benchmark, Evaluation, Fact

CHECKED = date(2026, 9, 18)


def bi(ru, en):
    return {"ru": ru, "en": en}


class Command(BaseCommand):
    help = "Add the reviewed initial selection. Existing models and editorial changes are preserved."

    @transaction.atomic
    def handle(self, *args, **options):
        def source(title, url, publisher):
            return Source.objects.get_or_create(url=url, defaults={"title": title, "publisher": publisher})[0]
        def org(name, src):
            return Organization.objects.get_or_create(name=name, defaults={"source": src, "checked": CHECKED})[0]
        pricing = source("Gemini API · Pricing", "https://ai.google.dev/gemini-api/docs/pricing", "Google")
        report = source("Gemini 2.5 · Technical report (Table 3, Appendix 8.1)", "https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf", "Google")
        qwen_src = source("Qwen3-8B · Model card", "https://huggingface.co/Qwen/Qwen3-8B", "Qwen")
        flux_src = source("FLUX.1 [schnell] · Model card", "https://huggingface.co/black-forest-labs/FLUX.1-schnell", "Black Forest Labs")
        vox_src = source("Voxtral Mini 3B 2507 · Model card", "https://huggingface.co/mistralai/Voxtral-Mini-3B-2507", "Mistral AI")
        fal_src = source("FLUX.1 [schnell] · fal pricing", "https://fal.ai/models/fal-ai/flux/schnell", "fal")
        google = org("Google", pricing)
        qwen = org("Qwen", qwen_src)
        bfl = org("Black Forest Labs", flux_src)
        mistral = org("Mistral AI", vox_src)
        fal = org("fal", fal_src)
        api = Service.objects.get_or_create(name="Gemini API", provider=google, kind="api", defaults={"url": pricing.url})[0]
        studio = Service.objects.get_or_create(name="Google AI Studio", provider=google, kind="web", defaults={"url": "https://aistudio.google.com/"})[0]
        fal_api = Service.objects.get_or_create(name="fal · FLUX.1 [schnell]", provider=fal, kind="api", defaults={"url": fal_src.url})[0]
        bench = Benchmark.objects.get_or_create(name="GPQA Diamond", protocol="Google 2025 · single attempt · Table 3", defaults={"category": "text", "unit": "%"})[0]
        math = Benchmark.objects.get_or_create(name="AIME 2025", protocol="Google 2025 · single attempt · Table 3", defaults={"category": "text", "unit": "%"})[0]
        data = [
            {"name": "Gemini 2.5 Flash", "slug": "gemini-2-5-flash", "version": "gemini-2.5-flash", "family": "Gemini 2.5", "org": google, "category": "text", "tasks": ["coding", "documents"], "context": 1048576,
             "source": source("Gemini 2.5 Flash · Documentation", "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash", "Google"),
             "description": bi("Мультимодальная модель для обработки документов, написания кода и ответов на вопросы.", "A multimodal model for documents, coding and question answering."),
             "suitable": bi("Обработка больших объёмов информации и задачи с управляемым бюджетом рассуждений.", "High-volume processing and tasks with a configurable thinking budget."),
             "limitations": bi("Создаёт только текст. Генерация изображений и аудио в этой версии не поддерживается.", "Produces text only. This version does not generate images or audio."),
             "prices": [("input", "0.30", bi("Standard · текст, изображения, видео", "Standard · text, images, video"), True), ("output", "2.50", bi("Standard · включая токены рассуждений", "Standard · including thinking tokens"), True), ("input", "1.00", bi("Standard · аудиовход", "Standard · audio input"), False)], "scores": ["82.8", "72.0"]},
            {"name": "Gemini 2.5 Pro", "slug": "gemini-2-5-pro", "version": "gemini-2.5-pro", "family": "Gemini 2.5", "org": google, "category": "text", "tasks": ["reasoning", "coding", "documents"], "context": 1048576,
             "source": source("Gemini 2.5 Pro · Documentation", "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro", "Google"),
             "description": bi("Модель с рассуждениями для сложного кода, научных задач и больших документов.", "A reasoning model for complex code, science and long documents."),
             "suitable": bi("Анализ кодовых баз и задач, требующих нескольких шагов решения.", "Codebase analysis and problems requiring multi-step reasoning."),
             "limitations": bi("Выход только текстовый. При входе свыше 200 000 токенов действует повышенный тариф.", "Text output only. Prompts above 200,000 tokens use a higher price tier."),
             "prices": [("input", "1.25", bi("Standard · вход ≤ 200k токенов", "Standard · prompt ≤ 200k tokens"), True), ("output", "10", bi("Standard · вход ≤ 200k; включая рассуждения", "Standard · prompt ≤ 200k; includes thinking"), True), ("input", "2.50", bi("Standard · вход > 200k токенов", "Standard · prompt > 200k tokens"), False), ("output", "15", bi("Standard · вход > 200k; включая рассуждения", "Standard · prompt > 200k; includes thinking"), False)], "scores": ["86.4", "88.0"]},
            {"name": "Gemini 2.5 Flash-Lite", "slug": "gemini-2-5-flash-lite", "version": "gemini-2.5-flash-lite", "family": "Gemini 2.5", "org": google, "category": "text", "tasks": ["translation", "documents"], "context": 1048576,
             "source": source("Gemini 2.5 Flash-Lite · Documentation", "https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite", "Google"),
             "description": bi("Компактная облачная модель для классификации, перевода и извлечения данных.", "A compact cloud model for classification, translation and data extraction."),
             "suitable": bi("Массовая обработка коротких запросов с небольшим бюджетом.", "High-volume short requests on a small budget."),
             "limitations": bi("Создаёт текст; не генерирует изображения, видео или аудио.", "Produces text; does not generate images, video or audio."),
             "prices": [("input", "0.10", bi("Standard · текст, изображения, видео", "Standard · text, images, video"), True), ("output", "0.40", bi("Standard · включая рассуждения", "Standard · including thinking"), True), ("input", "0.30", bi("Standard · аудиовход", "Standard · audio input"), False)]},
            {"name": "Qwen3-8B", "slug": "qwen3-8b", "version": "Qwen/Qwen3-8B", "family": "Qwen3", "org": qwen, "category": "text", "tasks": ["coding", "reasoning", "translation"], "context": 32768, "open_weights": True, "license": "Apache-2.0", "source": qwen_src,
             "description": bi("Языковая модель с открытыми весами и переключением режима рассуждений.", "An open-weight language model with switchable thinking mode."),
             "suitable": bi("Локальные приложения, эксперименты с кодом и многоязычные задачи.", "Local applications, coding experiments and multilingual tasks."),
             "limitations": bi("Нативный контекст 32 768 токенов. Расширение до 131 072 требует YaRN; условия и оборудование влияют на работу.", "Native context is 32,768 tokens. Extending to 131,072 requires YaRN; configuration and hardware matter."),
             "origin": bi("Входит в семейство Qwen3; опубликована после предварительного и последующего обучения.", "Part of the Qwen3 family; released after pre-training and post-training."),
             "philosophy": bi("По заявлению команды, режимы рассуждений позволяют регулировать вычислительные затраты.", "The team describes thinking modes as a way to control computational effort.")},
            {"name": "FLUX.1 [schnell]", "slug": "flux-1-schnell", "version": "FLUX.1-schnell", "family": "FLUX.1", "org": bfl, "category": "image", "tasks": ["images"], "open_weights": True, "license": "Apache-2.0", "source": flux_src,
             "description": bi("Модель с открытыми весами для создания изображений по текстовому описанию.", "An open-weight model that creates images from text descriptions."),
             "suitable": bi("Визуальные эскизы и локальные процессы генерации изображений.", "Visual drafts and local image-generation workflows."),
             "limitations": bi("Не является источником фактов. Изображение может не соответствовать запросу; скачивание требует принятия условий хостинга.", "Not a factual source. Images may not match prompts; downloading requires accepting hosting terms."),
             "origin": bi("Использует дистилляцию латентной диффузии; разработчик описывает генерацию за 1–4 шага.", "Uses latent diffusion distillation; the developer describes generation in 1–4 steps."),
             "philosophy": bi("Разработчик разрешает личное, научное и коммерческое использование по Apache-2.0.", "The developer permits personal, scientific and commercial use under Apache-2.0.")},
            {"name": "Voxtral Mini 3B", "slug": "voxtral-mini-3b-2507", "version": "Voxtral-Mini-3B-2507", "family": "Voxtral", "org": mistral, "category": "audio", "tasks": ["audio", "translation"], "context": 32000, "open_weights": True, "license": "Apache-2.0", "source": vox_src,
             "description": bi("Аудиоязыковая модель для расшифровки речи и вопросов по аудиозаписям.", "An audio-language model for transcription and questions about recordings."),
             "suitable": bi("Транскрибация, перевод и краткое содержание записей.", "Transcription, translation and recording summaries."),
             "limitations": bi("В карточке заявлены восемь языков; русский в этом списке отсутствует. Системные сообщения не поддерживаются.", "The card lists eight languages, excluding Russian. System messages are not supported."),
             "origin": bi("Построена на Ministral 3B с добавлением обработки аудиовхода.", "Built on Ministral 3B with audio-input capabilities.")},
            {"name": "Veo 3.1", "slug": "veo-3-1", "version": "veo-3.1-generate-preview", "family": "Veo", "org": google, "category": "video", "tasks": ["video"], "source": pricing,
             "description": bi("Облачная модель генерации видео со звуком через Gemini API.", "A cloud model generating video with audio through the Gemini API."),
             "suitable": bi("Создание коротких видеосцен со звуковой дорожкой.", "Creating short video scenes with an audio track."),
             "limitations": bi("Предварительная версия. Стоимость зависит от разрешения; бесплатного API-тарифа нет.", "Preview version. Pricing depends on resolution; there is no free API tier."),
             "prices": [("second", "0.40", bi("Standard · видео со звуком, 720p / 1080p", "Standard · video with audio, 720p / 1080p"), True), ("second", "0.60", bi("Standard · видео со звуком, 4K", "Standard · video with audio, 4K"), False)]},
        ]
        added = 0
        modalities = {
            "gemini-2-5-flash": (["text", "image", "video", "audio"], ["text"]),
            "gemini-2-5-pro": (["text", "image", "video", "audio"], ["text"]),
            "gemini-2-5-flash-lite": (["text", "image", "video", "audio"], ["text"]),
            "qwen3-8b": (["text"], ["text"]),
            "flux-1-schnell": (["text"], ["image"]),
            "voxtral-mini-3b-2507": (["audio", "text"], ["text"]),
            "veo-3-1": (["text", "image"], ["video", "audio"]),
        }
        for item in data:
            existing = ModelVersion.objects.filter(slug=item["slug"]).first()
            if existing:
                inputs, outputs = modalities[item["slug"]]
                existing.input_modalities = inputs
                existing.output_modalities = outputs
                existing.save(update_fields=["input_modalities", "output_modalities"])
                continue
            family = ModelFamily.objects.get_or_create(name=item["family"], developer=item["org"])[0]
            keys = {key: item[key] for key in ("name", "slug", "version", "category", "tasks", "description", "suitable", "limitations", "source", "context", "open_weights", "license", "origin", "philosophy") if key in item}
            model = ModelVersion.objects.create(family=family, checked=CHECKED, **keys)
            model.input_modalities, model.output_modalities = modalities[item["slug"]]
            model.save(update_fields=["input_modalities", "output_modalities"])
            added += 1
            if item["org"] == google:
                Access.objects.create(model=model, service=api, source=pricing, checked=CHECKED)
                if item["category"] == "text":
                    Access.objects.create(model=model, service=studio, source=item["source"], checked=CHECKED)
                    Fact.objects.create(model=model, key="modalities", value=bi("Вход: текст, изображения, видео, аудио. Выход: текст.", "Input: text, images, video, audio. Output: text."), source=item["source"], checked=CHECKED)
                    Fact.objects.create(model=model, key="service_price", value=bi("Для выбранных моделей есть бесплатные квоты AI Studio и API; ограничения зависят от модели и аккаунта. Тариф подписки на Gemini здесь не проверен.", "AI Studio and API free quotas exist for selected models; limits depend on the model and account. Gemini subscription pricing is not verified here."), source=pricing, checked=CHECKED)
            if model.open_weights:
                download = Service.objects.get_or_create(name=model.name + " · weights", provider=item["org"], kind="download", defaults={"url": item["source"].url})[0]
                Access.objects.create(model=model, service=download, source=item["source"], checked=CHECKED)
            for unit, amount, conditions, primary in item.get("prices", []):
                Offer.objects.create(model=model, service=api, unit=unit, amount=Decimal(amount), conditions=conditions, primary=primary, source=pricing, checked=CHECKED)
            for benchmark, score in zip([bench, math], item.get("scores", [])):
                Evaluation.objects.create(model=model, benchmark=benchmark, score=score, evaluator="Google" if benchmark == bench else "MathArena (via Google report)", independent=benchmark == math, public=benchmark == math, source=report, checked=CHECKED,
                    conditions=bi("Таблица 3 технического отчёта Gemini 2.5 (2025). Одна попытка, динамические рассуждения. Результат относится к версии отчёта, а не к повторному тесту текущего API. Протокол: приложение 8.1. Дата измерения отдельно не указана.", "Table 3, Gemini 2.5 technical report (2025). Single attempt, dynamic thinking. Refers to the report's model version, not a retest of the current API. Protocol: Appendix 8.1. Measurement date is not separately stated."))
            if item["slug"] == "flux-1-schnell":
                Access.objects.create(model=model, service=fal_api, source=fal_src, checked=CHECKED)
                Offer.objects.create(model=model, service=fal_api, unit="megapixel", amount="0.003", primary=True,
                    conditions=bi("Округление вверх до целого мегапикселя", "Rounded up to the next whole megapixel"), source=fal_src, checked=CHECKED)
            if item["slug"] == "voxtral-mini-3b-2507":
                Fact.objects.create(model=model, key="memory", value=bi("Около 9,5 GB видеопамяти при bf16 / fp16 по инструкции разработчика. Это требование запуска, не измерение энергии.", "About 9.5 GB GPU memory at bf16 / fp16 according to the developer's instructions. A runtime requirement, not an energy measurement."), source=vox_src, checked=CHECKED)
                Fact.objects.create(model=model, key="modalities", value=bi("Вход: аудио и текст. Выход: текст.", "Input: audio and text. Output: text."), source=vox_src, checked=CHECKED)
            if item["slug"] == "qwen3-8b":
                Fact.objects.create(model=model, key="modalities", value=bi("Текстовый вход и выход.", "Text input and output."), source=qwen_src, checked=CHECKED)
        self.stdout.write(self.style.SUCCESS(f"Added {added} models; existing records preserved."))

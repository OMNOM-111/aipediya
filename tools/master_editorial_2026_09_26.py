"""One-off, reproducible editorial pass that turns master v012 into v013.

Input : v012 (sha256 3ea32a46…7208, audit copy) + read-only Local snapshot +
        the public Production sitemap (read-only HTTP GET).
Output: a new workbook (path given by --out) plus CSV/JSON evidence in
        --evidence. Nothing is written to any database; Production is only read.

Every field change is appended to the Changelog with Before/After and reason.
Decisions follow the owner's clarified scope of 2026-09-26: the publication
package is the existing core (what Production/Local publish now) plus a short,
source-checked list of additions; the remaining research stock stays in the
book as deferred, non-public candidates. Run from the project root:

  .venv\\Scripts\\python.exe tools\\master_editorial_2026_09_26.py --v012 <path> --out <path> --evidence <dir>
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402

V012_SHA256 = "3ea32a46204155fdf2cff3f0b6f2754e3925fe184de37e3aab96deca061b7208"
RUN = "v013 editorial 2026-09-26"
DEFERRED = ("[DEFERRED 2026-09-26] Отложенный исследовательский запас: не входит в текущий пакет публикации "
            "(ядро + отобранные дополнения). Publication Decision здесь — редакционное предложение, не команда "
            "публиковать; повторная проверка — по приоритету, отдельно.")

# ------------------------------------------------------------------ decisions
# Existing, justified ARCHIVE rows: (code, relation). Parent ids stay as in v012.
ARCHIVE_KEEP = {
    **{rid: ("ALIAS_SNAPSHOT", "ALIAS_OF") for rid in [
        "claude-3-opus-20240229-2a4107aa", "claude-3-sonnet-20240229-dae5b2e3",
        "claude-3-haiku-20240307-82490930", "claude-35-sonnet-20240620-f0d408d7",
        "claude-35-haiku-20241022-51029c52", "claude-37-sonnet-20250219-0b1374aa",
        "claude-opus-4-20250514-a5eb72f9", "claude-sonnet-4-20250514-27bffbfc",
        "claude-opus-41-20250805-34e09e29", "claude-sonnet-45-20250929-4491d3dd",
        "claude-haiku-45-20251001-f3ba3acc", "claude-opus-45-20251101-255d80a3"]},
    **{rid: ("API_SNAPSHOT", "SNAPSHOT_OF") for rid in [
        "claude-10-api-snapshot-ba4593ad", "claude-11-api-snapshot-11a647fb",
        "claude-12-api-snapshot-dbfa728e", "claude-13-api-snapshot-5074800f",
        "claude-instant-10-api-snapshot-dab976ca", "claude-instant-11-api-snapshot-09a2abfc",
        "claude-instant-12-api-snapshot-0d1acc44"]},
    "cohere-transcribe-arabic-0a352fb7": ("DUPLICATE", "DUPLICATE_OF"),
    "ocr-41-177c0fd1": ("DUPLICATE", "DUPLICATE_OF"),
    "sarvam-m-24b-58a80ce5": ("DUPLICATE", "DUPLICATE_OF"),
    "eleven-flash-turbo-0d8ef8ef": ("FAMILY_AGGREGATE", ""),
    "flux2-93b876e2": ("FAMILY_AGGREGATE", ""),
    "minimax-01-6a0acd8e": ("FAMILY_AGGREGATE", ""),
    "grok-voice-api-27080172": ("MODEL_APP_SPLIT", ""),
    "hebbian-learning-rule-b3a2079d": ("OUT_OF_SCOPE", ""),
    "stable-audio-3-optimized-6c2cc03d": ("TECHNICAL_CHECKPOINT", "VARIANT_OF"),
    "flux11-pro-raw-6db356c7": ("CONFIGURATION", "MODE_OF"),
}

# v012 proposed ARCHIVE only because the product closed: closure is not an
# editorial exclusion. Back to PUBLIC; lifecycle recorded in Catalog Status.
REVERT_CLOSED = {
    "continue-224ab02d": ("archived", "Официальный README: активная поддержка прекращена, репозиторий только для чтения, финальный релиз 2.0.0. Вывод: закрытие развития — жизненный цикл (Catalog Status=archived), не причина исключения; исторически значимый open-source coding assistant сохраняет карточку."),
    "humanloop-a16219fe": ("deprecated", "Официальный сайт объявляет sunset платформы; точный день закрытия не установлен. Вывод: объявленное закрытие — жизненный цикл (Catalog Status=deprecated), не причина исключения карточки."),
    "roo-code-c6a1ecaa": ("retired", "Официальный README: Roo Code Extension закрыт 15 мая, репозиторий архивирован 2026-05-15. Вывод: закрытый продукт остаётся исторической карточкой (Catalog Status=retired), не ARCHIVE."),
    "sora-bd047027": ("retired", "Официальная страница OpenAI: приложение Sora недоступно с 2026-04-26. Вывод: исторически значимый продукт сохраняет карточку с Catalog Status=retired; закрытие не основание для ARCHIVE."),
}

# New proven identities (sheet, rid, code, relation, parent, reason, sources).
NEW_ARCHIVE = [
    ("Models", "llama-4-scout-98884569", "DUPLICATE", "DUPLICATE_OF", "llama-4-scout-17b-16e-instruct-837f5a8d",
     "Факт: запись «Llama 4 Scout» ссылается на ту же официальную карточку Llama-4-Scout-17B-16E-Instruct и тот же доступ, что и llama-4-scout-17b-16e-instruct-837f5a8d; отдельный base-checkpoint (Llama-4-Scout-17B-16E) существует, но эта строка его не описывает. Вывод: короткое имя — alias Instruct-карточки; отдельная карточка не создаёт нового выбора. Base-checkpoint как самостоятельная запись — кандидат на будущее пополнение.",
     "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct | https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E"),
    ("Models", "llama-4-maverick-bf82d46d", "DUPLICATE", "DUPLICATE_OF", "llama-4-maverick-17b-128e-instruct-0a3c5b27",
     "Факт: запись «Llama 4 Maverick» ссылается на ту же официальную карточку Llama-4-Maverick-17B-128E-Instruct и тот же доступ, что и llama-4-maverick-17b-128e-instruct-0a3c5b27. Вывод: короткое имя — alias Instruct-карточки; base-checkpoint Maverick этой строкой не описан.",
     "https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct"),
    ("Models", "nemotron-3-super-120b-a12b-bf16-7aef286f", "FORMAT_VARIANT", "FORMAT_OF", "nemotron-3-super-2d4ec02c",
     "Факт: официальная страница Nemotron 3 Super описывает одну модель 120B total / 12B active и выпускает post-trained checkpoint в форматах BF16, FP8 и NVFP4 (плюс отдельный BF16 base). Эта строка — BF16-представление той же post-trained модели. Вывод: формат весов не отдельная модель; каноническая карточка — nemotron-3-super-2d4ec02c, BF16/FP8/NVFP4 — её aliases. Дата карточки HF (2026-03-11) сохранена в этой строке и Changelog.",
     "https://research.nvidia.com/labs/nemotron/Nemotron-3-Super/ | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16"),
]

MODEL_APP_SPLIT_NOTE = ("Факт: Grok Voice Agent API — сервис xAI (Tools: grok-voice-agent-64dc28d2); независимая версия модели "
                        "под этим названием не заявлена. Вывод: приложение/сервис не дублируется в Models.")

# Open questions in the core resolved with evidence (rid -> fields, sources).
RESOLVE_CORE = {
    "jurassic-2-light-275da84e": ("Jurassic-2 Large", "Light", "Large"),
    "jurassic-2-mid-d07628b1": ("Jurassic-2 Grande", "Mid", "Grande"),
    "jurassic-2-ultra-2edbabd7": ("Jurassic-2 Jumbo", "Ultra", "Jumbo"),
}
J2_SOURCES = "https://www.ai21.com/blog/simplifying-our-jurassic-2-offering/ | https://www.ai21.com/blog/introducing-j2/"
CODEX_REASON = ("Карточка описывает продукт OpenAI Codex (CLI, облачный агент, IDE-клиенты). Дата 2025-04-16 — первый "
                "публичный выпуск линейки (Codex CLI); облачный агент — 2025-05-16, это более поздняя форма того же продукта. "
                "Вопрос границы закрыт редакционно: одна карточка продукта, дата первой формы.")
CORE_KEPT_OPEN = {
    "hyperclova-x-seed-3b-3e1c5933": "Ядро каталога сохранено: ошибка не доказана. Открытый вопрос (не блокирует карточку): обозначает ли SEED 3B именно Vision-Instruct-3B и какую ревизию.",
    "fugu-ultra-30efec3e": "Ядро каталога сохранено: ошибка не доказана. Открытый вопрос (не блокирует карточку): привязка Fugu Ultra к версии API (текущая v2.0) и дата 2026-06-22.",
}

# Merges checked on 2026-09-26 but NOT applied to an existing public card:
# the card stays as it is, with the concrete question (owner rule 2026-09-26).
KEPT_WITH_QUESTION = {
    ("Models", "kimi-k3-max-8906b43f"): (
        "Идентичность по v012: та же модель kimi-k3 с reasoning_effort=max. Объединение не применено: цены "
        "(3/15/0.3 USD за 1M), контекст 1M, лицензия и оценка ECI есть только в этой карточке, а в Kimi K3 их нет; "
        "перенос связанных строк без смешения конфигураций sync-local пока не выполняет. Вопрос: перенести цены, "
        "контекст и лицензию в Kimi K3, оценку ECI оставить как конфигурацию max, затем архивировать эту строку как MODE_OF.",
        ""),
    ("Tools", "grok-voice-api-e5ae4c9e"): (
        "Объединение с Grok Voice Agent не применено (спорно). Анонс xAI 2025-12-17 называет продукт Grok Voice Agent "
        "API, но официальная страница x.ai/api/voice этой карточки объединяет speech-to-speech, TTS и STT, и её цены "
        "(15 USD за 1M символов, почасовые ставки) относятся к TTS/STT. Вопрос: это тот же Voice Agent API или "
        "зонтичный продукт Voice API? До ответа карточка остаётся, цены не переносятся.",
        "https://x.ai/news/grok-voice-agent-api | https://x.ai/api/voice"),
}
NEMOTRON_LICENSE = ("nemotron-3-super-2d4ec02c", "nemotron-3-super-120b-a12b-bf16-7aef286f")

# 30 tools: the site shows generated English with evident errors (e.g. "for
# coding" on video apps); the master text is the researched one. The manual
# Russian below is written for the chosen master English (RU is a manual locale).
TOOL_RU = {
    "adobe-firefly-9f88c8c9": "Веб-приложение Adobe для создания и редактирования визуального контента с помощью генеративного ИИ.",
    "amazon-nova-forge-e5333e99": "Сервис AWS для дообучения моделей Nova на ранних контрольных точках обучения и собственных данных; обучение и развёртывание встроены в инфраструктуру AWS.",
    "amazon-q-developer-d7b6203a": "Ассистент AWS для программирования и работы с сервисами AWS. Для доступа из IDE и подписок действуют отдельные ограничения жизненного цикла, в консоли AWS работа продолжается.",
    "antigravity-cli-b0aa4e36": "Терминальный агент Google для программирования из семейства Antigravity: локальный клиент и общая серверная среда агента.",
    "autogen-349a8269": "Открытый фреймворк Microsoft для многоагентных приложений, объединяющий вызовы моделей, инструменты и участие человека. Это программная библиотека, а не размещённая модель.",
    "aws-bedrock-224b9658": "Управляемый сервис AWS для доступа к базовым моделям и их настройки через облачные API. Доступность моделей, лимиты контекста, лицензии и тарифы зависят от выбранной модели.",
    "azure-ai-foundry-f8725f3f": "Платформа Microsoft Azure для разработки и управления ИИ-приложениями: каталог моделей, инструменты оценки, API инференса и портал управления.",
    "descript-f02c6933": "Приложение для редактирования аудио и видео с транскрипцией и монтажом через текст.",
    "eleven-sound-effects-fd3e24db": "ElevenLabs Sound Effects — API для генерации звуковых эффектов по текстовому описанию.",
    "eleven-speech-engine-5710146f": "ElevenLabs Speech Engine — голосовой конвейер реального времени для существующего чат-агента; разработчик сохраняет собственную языковую модель и оркестрацию.",
    "flow-050287a2": "Приложение Google для ИИ-кинопроизводства: генерация видеокадров, управление визуальными материалами и сборка сцен с помощью генеративных моделей Google.",
    "gemini-90ef8dfa": "Потребительский ИИ-ассистент Google (ранее Bard) для диалога с ИИ Google в вебе и мобильных приложениях. Не путать с семейством моделей Gemini.",
    "gemini-code-assist-611ff03b": "ИИ-ассистент Google для программирования в IDE: генерация и преобразование кода. Возможности различаются в потребительских и бизнес-подписках.",
    "google-vertex-ai-e3b72b54": "Платформа Google Cloud для обучения, развёртывания и управления моделями машинного обучения, включая сервисы предсказаний и инструменты жизненного цикла моделей.",
    "hailuo-ai-ab0a6ab6": "Hailuo AI — приложение MiniMax для генерации видео с помощью ИИ.",
    "ideogram-db27a255": "Творческое приложение для генерации и редактирования изображений и дизайна.",
    "kaggle-models-66ec6efe": "Каталог и платформа обмена моделями Kaggle; через CLI можно искать модели, публиковать записи и получать метаданные моделей.",
    "kling-ai-c89c43f2": "ИИ-приложение для генерации и редактирования видео и изображений.",
    "label-studio-7801d5fd": "Приложение для разметки данных: аудио, текст, изображения, видео и временные ряды; локальная установка и интеграции с машинным обучением.",
    "luma-dream-machine-7639cc3d": "Luma Dream Machine — творческий продукт для генерации изображений и видео с помощью ИИ, с API для разработчиков.",
    "microsoft-copilot-80bf3d4a": "Потребительский ИИ-чат-ассистент Microsoft в отдельном веб-интерфейсе. Запись описывает приложение, а не базовую модель и не Microsoft 365 Copilot.",
    "minimax-speech-recognition-b5f156c4": "MiniMax Speech Recognition — API распознавания речи с потоковой транскрипцией, разделением говорящих и экспортом субтитров SRT/VTT.",
    "notebooklm-6efd78c8": "Исследовательский ассистент Google для заметок: отвечает на вопросы и готовит сводки на основе документов и источников пользователя.",
    "nvidia-build-eab0ba05": "NVIDIA Build — веб-каталог для знакомства с ИИ-моделями, пробы размещённых API инференса и получения ресурсов для развёртывания.",
    "nvidia-ngc-7f095936": "NVIDIA NGC — каталог и реестр контейнеров с оптимизированным для GPU ПО для ИИ и артефактами моделей.",
    "pika-ea286fc1": "Творческое приложение для генерации и редактирования видео, изображений и аудио.",
    "recraft-5c5605ef": "ИИ-приложение для дизайна: генерация и редактирование растровых изображений, векторной графики, иллюстраций и иконок.",
    "runway-e34e79e1": "Runway — творческое приложение для генерации и редактирования изображений и видео с помощью ИИ.",
    "semantic-kernel-4a327f4f": "SDK Microsoft, не привязанный к конкретной модели, для оркестрации ИИ-агентов и подключения сервисов моделей, инструментов и плагинов; работает с облачными сервисами и локальными средами запуска моделей.",
    "sora-bd047027": "Закрытое приложение для генерации видео с помощью ИИ, ранее доступное на Sora.com.",
}

# v012 replaced these model-specific access links with the page of another size
# of the same family (e.g. Llama 3.2 3B -> the 1B page).
ACCESS_REVERT = ["access-167", "access-169", "access-171", "access-172", "access-179", "access-180",
                 "access-353", "access-354", "access-504"]

EXTRA_ALIASES = {
    ("Models", "llama-4-scout-17b-16e-instruct-837f5a8d"): ["Llama-4-Scout-17B-16E-Instruct"],
    ("Models", "llama-4-maverick-17b-128e-instruct-0a3c5b27"): ["Llama-4-Maverick-17B-128E-Instruct"],
    ("Models", "nemotron-3-super-2d4ec02c"): ["Nemotron 3 Super 120B A12B", "NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
                                              "NVIDIA-Nemotron-3-Super-120B-A12B-FP8", "NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4"],
    ("Tools", "grok-voice-agent-64dc28d2"): ["Grok Voice Agent API"],
}

# ------------------------------------------------------------------ additions
ADD = [
    # sheet, name, developer, family, version, exact, approx, category, tasks, inputs, outputs, context,
    # license, open weights, stage, official, secondary, description en, description ru, aliases, basis
    ("Models", "Gemma 2B IT", "Google", "Gemma", "gemma-2b-it", "2024-02-21", "", "text", "text", "text", "text", "",
     "Gemma Terms of Use", "YES", "released", "https://blog.google/technology/developers/gemma-open-models/", "https://www.kaggle.com/models/google/gemma",
     "Instruction-tuned 2B model of the first Gemma generation of open models from Google (released with a pretrained variant).",
     "Инструктивная 2B-модель первого поколения открытых моделей Gemma от Google (выпущена вместе с предобученным вариантом).",
     "gemma-2b-it", "Первое поколение Gemma — важная историческая ветка открытых моделей Google; 2B — отдельный практический размер для локального запуска."),
    ("Models", "Gemma 7B IT", "Google", "Gemma", "gemma-7b-it", "2024-02-21", "", "text", "text", "text", "text", "",
     "Gemma Terms of Use", "YES", "released", "https://blog.google/technology/developers/gemma-open-models/", "https://www.kaggle.com/models/google/gemma",
     "Instruction-tuned 7B model of the first Gemma generation of open models from Google (released with a pretrained variant).",
     "Инструктивная 7B-модель первого поколения открытых моделей Gemma от Google (выпущена вместе с предобученным вариантом).",
     "gemma-7b-it", "Первое поколение Gemma; 7B — отдельный размер с иным балансом качества и ресурсов."),
    ("Models", "Gemma 2 9B IT", "Google", "Gemma 2", "gemma-2-9b-it", "2024-06-27", "", "text", "text", "text", "text", "",
     "Gemma license", "YES", "released", "https://blog.google/technology/developers/google-gemma-2/", "",
     "Instruction-tuned 9B model of Google's second Gemma generation of open models.",
     "Инструктивная 9B-модель второго поколения открытых моделей Gemma от Google.",
     "gemma-2-9b-it", "Второе поколение Gemma — отдельный существенный выпуск; 9B — практический размер для одного GPU."),
    ("Models", "Gemma 2 27B IT", "Google", "Gemma 2", "gemma-2-27b-it", "2024-06-27", "", "text", "text", "text", "text", "",
     "Gemma license", "YES", "released", "https://blog.google/technology/developers/google-gemma-2/", "",
     "Instruction-tuned 27B model of Google's second Gemma generation of open models.",
     "Инструктивная 27B-модель второго поколения открытых моделей Gemma от Google.",
     "gemma-2-27b-it", "Второе поколение Gemma; 27B — флагманский размер поколения."),
    ("Models", "Gemma 3 1B IT", "Google", "Gemma 3", "gemma-3-1b-it", "2025-03-12", "", "text", "text", "text", "text", "",
     "", "YES", "released", "https://blog.google/technology/developers/gemma-3/", "",
     "Instruction-tuned 1B text model of Google's third Gemma generation of open models.",
     "Инструктивная текстовая 1B-модель третьего поколения открытых моделей Gemma от Google.",
     "gemma-3-1b-it", "Третье поколение Gemma; 1B — текстовый размер для устройств с малыми ресурсами."),
    ("Models", "Gemma 3 4B IT", "Google", "Gemma 3", "gemma-3-4b-it", "2025-03-12", "", "text", "text; vision", "text; image", "text", "128000",
     "", "YES", "released", "https://blog.google/technology/developers/gemma-3/", "",
     "Instruction-tuned 4B model of Google's third Gemma generation; accepts text and images, 128K-token context.",
     "Инструктивная 4B-модель третьего поколения Gemma от Google; принимает текст и изображения, контекст 128K токенов.",
     "gemma-3-4b-it", "Третье поколение Gemma; 4B — наименьший размер поколения с пониманием изображений."),
    ("Models", "Gemma 3 12B IT", "Google", "Gemma 3", "gemma-3-12b-it", "2025-03-12", "", "text", "text; vision", "text; image", "text", "128000",
     "", "YES", "released", "https://blog.google/technology/developers/gemma-3/", "",
     "Instruction-tuned 12B model of Google's third Gemma generation; accepts text and images, 128K-token context.",
     "Инструктивная 12B-модель третьего поколения Gemma от Google; принимает текст и изображения, контекст 128K токенов.",
     "gemma-3-12b-it", "Третье поколение Gemma; 12B — средний мультимодальный размер."),
    ("Models", "Gemma 3 27B IT", "Google", "Gemma 3", "gemma-3-27b-it", "2025-03-12", "", "text", "text; vision", "text; image", "text", "128000",
     "", "YES", "released", "https://blog.google/technology/developers/gemma-3/", "",
     "Instruction-tuned 27B model of Google's third Gemma generation; accepts text and images, 128K-token context.",
     "Инструктивная 27B-модель третьего поколения Gemma от Google; принимает текст и изображения, контекст 128K токенов.",
     "gemma-3-27b-it", "Третье поколение Gemma; 27B — флагманский размер поколения."),
    ("Models", "Segment Anything Model (SAM)", "Meta AI", "Segment Anything", "SAM ViT-H / ViT-L / ViT-B", "2023-04-05", "", "image", "vision", "image", "image", "",
     "Apache-2.0", "YES", "released", "https://ai.meta.com/blog/segment-anything-foundation-model-image-segmentation/", "https://github.com/facebookresearch/segment-anything",
     "Promptable image segmentation model from Meta AI that produces object masks from points or boxes; released with ViT-H, ViT-L and ViT-B checkpoints.",
     "Модель сегментации изображений Meta AI по подсказкам: строит маски объектов по точкам или рамкам; выпущена с checkpoint ViT-H, ViT-L и ViT-B.",
     "SAM | Segment Anything", "Отдельная задача (сегментация), не представленная в каталоге; значимый исторический выпуск открытой модели компьютерного зрения."),
    ("Models", "SAM 2", "Meta AI", "Segment Anything", "SAM 2", "2024-07-29", "", "video", "vision", "image; video", "image; video", "",
     "", "YES", "released", "https://github.com/facebookresearch/sam2/blob/main/RELEASE_NOTES.md", "",
     "Segment Anything Model 2: Meta AI's promptable segmentation model for images and videos.",
     "Segment Anything Model 2 — модель Meta AI для сегментации изображений и видео по подсказкам.",
     "Segment Anything Model 2", "Новое поколение с сегментацией видео — существенное расширение возможностей SAM."),
    ("Models", "SAM 2.1", "Meta AI", "Segment Anything", "SAM 2.1", "2024-09-30", "", "video", "vision", "image; video", "image; video", "",
     "", "YES", "released", "https://github.com/facebookresearch/sam2/blob/main/RELEASE_NOTES.md", "",
     "Updated SAM 2.1 checkpoints of Meta AI's promptable image and video segmentation model, released with training code.",
     "Обновлённые checkpoint SAM 2.1 модели Meta AI для сегментации изображений и видео, выпущенные вместе с кодом обучения.",
     "Segment Anything Model 2.1", "Официально выделенный обновлённый набор весов SAM 2.1 (по release notes) — отдельный выбор для загрузки."),
    ("Models", "Whisper large-v3-turbo", "OpenAI", "Whisper", "large-v3-turbo", "2024-10-01", "", "audio", "speech; text", "audio", "text", "",
     "MIT", "YES", "released", "https://github.com/openai/whisper/discussions/2363", "https://huggingface.co/openai/whisper-large-v3-turbo",
     "Optimized Whisper large-v3 speech-recognition model with 4 decoder layers instead of 32: much faster transcription with accuracy close to large-v2.",
     "Оптимизированная модель распознавания речи Whisper large-v3 с 4 слоями декодера вместо 32: заметно быстрее, точность близка к large-v2.",
     "turbo | whisper-large-v3-turbo", "Официально отдельный выпуск с иным балансом скорости и точности; turbo — его alias."),
    ("Models", "Janus-1.3B", "DeepSeek", "Janus", "Janus-1.3B", "", "≈2024-10", "image", "vision; image_generation", "text; image", "text; image", "4096",
     "DeepSeek Model License (weights)", "YES", "research", "https://github.com/deepseek-ai/Janus", "",
     "DeepSeek's autoregressive model that unifies multimodal understanding and image generation in one framework.",
     "Авторегрессионная модель DeepSeek, объединяющая мультимодальное понимание и генерацию изображений в одной архитектуре.",
     "Janus", "Первая модель серии Janus — самостоятельный подход к единой модели понимания и генерации изображений."),
    ("Models", "JanusFlow-1.3B", "DeepSeek", "Janus", "JanusFlow-1.3B", "2024-11-13", "", "image", "vision; image_generation", "text; image", "text; image", "4096",
     "DeepSeek Model License (weights)", "YES", "research", "https://github.com/deepseek-ai/Janus", "",
     "DeepSeek model that combines an autoregressive language model with rectified flow for unified image understanding and generation.",
     "Модель DeepSeek, сочетающая авторегрессионную языковую модель и rectified flow для понимания и генерации изображений.",
     "JanusFlow", "Отдельная архитектура серии (rectified flow), не размер Janus."),
    ("Models", "Janus-Pro-1B", "DeepSeek", "Janus", "Janus-Pro-1B", "2025-01-27", "", "image", "vision; image_generation", "text; image", "text; image", "4096",
     "DeepSeek Model License (weights)", "YES", "released", "https://github.com/deepseek-ai/Janus", "",
     "1B model of DeepSeek Janus-Pro, an improved unified model for multimodal understanding and text-to-image generation.",
     "1B-модель DeepSeek Janus-Pro — улучшенной единой модели для мультимодального понимания и генерации изображений по тексту.",
     "", "Существенная новая версия серии; 1B — отдельный размер."),
    ("Models", "Janus-Pro-7B", "DeepSeek", "Janus", "Janus-Pro-7B", "2025-01-27", "", "image", "vision; image_generation", "text; image", "text; image", "4096",
     "DeepSeek Model License (weights)", "YES", "released", "https://github.com/deepseek-ai/Janus", "",
     "7B model of DeepSeek Janus-Pro, an improved unified model for multimodal understanding and text-to-image generation.",
     "7B-модель DeepSeek Janus-Pro — улучшенной единой модели для мультимодального понимания и генерации изображений по тексту.",
     "", "Существенная новая версия серии; 7B — старший размер."),
    ("Models", "AlphaFold 3", "Google DeepMind", "AlphaFold", "AlphaFold 3", "2024-05-08", "", "other", "science", "text", "other", "",
     "AlphaFold 3 Model Parameters Terms of Use (weights); Apache-2.0 (code)", "NO", "released",
     "https://blog.google/technology/ai/google-deepmind-isomorphic-alphafold-3-ai-model/", "https://github.com/google-deepmind/alphafold3",
     "Google DeepMind and Isomorphic Labs model that predicts the structure and interactions of proteins, DNA, RNA, ligands and other biomolecules; launched via the free non-commercial AlphaFold Server.",
     "Модель Google DeepMind и Isomorphic Labs для предсказания структуры и взаимодействий белков, ДНК, РНК, лигандов и других биомолекул; запущена через бесплатный некоммерческий AlphaFold Server.",
     "", "Научная специализация и значимый исторический вклад; в каталоге нет модели предсказания биомолекулярных структур."),
    ("Models", "MusicGen", "Meta AI", "AudioCraft", "small / medium / large / melody", "", "≈2023-06", "audio", "music", "text; audio", "audio", "",
     "", "YES", "research", "https://github.com/facebookresearch/audiocraft/blob/main/CHANGELOG.md", "https://ai.meta.com/blog/audiocraft-musicgen-audiogen-encodec-generative-ai-audio/",
     "Meta AI text-to-music model family (300M–3.3B checkpoints, optional melody conditioning) distributed in the AudioCraft library.",
     "Семейство моделей Meta AI для генерации музыки по тексту (checkpoint 300M–3.3B, вариант с мелодической подсказкой) в библиотеке AudioCraft.",
     "", "Открытая модель генерации музыки — заметный пробел категории аудио; не путать с библиотекой AudioCraft."),
    ("Models", "AudioGen", "Meta AI", "AudioCraft", "audiogen-medium", "2023-08-02", "", "audio", "audio_generation", "text", "audio", "",
     "", "YES", "research", "https://ai.meta.com/blog/audiocraft-musicgen-audiogen-encodec-generative-ai-audio/", "https://github.com/facebookresearch/audiocraft",
     "Meta AI model that generates environmental sounds and sound effects from text; pretrained weights first released with AudioCraft.",
     "Модель Meta AI для генерации окружающих звуков и звуковых эффектов по тексту; предобученные веса впервые выпущены вместе с AudioCraft.",
     "", "Отдельная задача (звуковые эффекты), отличная от MusicGen."),
]
ADD_TOOLS = [
    # name, developer, version, exact, approx, category, purposes, local, official url, platforms, official, secondary, desc en, desc ru, aliases, basis, note
    ("ComfyUI", "Comfy Org", "ComfyUI", "", "≈2023-01", "creative_app", "image_generation; video_generation; specialized", "yes",
     "https://github.com/Comfy-Org/ComfyUI", "desktop; windows; macos; linux",
     "https://github.com/Comfy-Org/ComfyUI", "https://en.wikipedia.org/wiki/ComfyUI",
     "Open-source node-based application for building generative image, video, audio and 3D workflows with local models.",
     "Открытое приложение с визуальным графом узлов для построения генеративных сценариев изображений, видео, аудио и 3D с локальными моделями.",
     "Comfy UI", "Самостоятельный широко используемый инструмент локальной генерации; отдельная практическая возможность.",
     "Дата: ≈2023-01 по вторичному источнику (Wikipedia со ссылкой на интервью автора: первый выпуск на GitHub 2023-01-16); первичная датированная публикация не найдена, поэтому точность — месяц. Лицензия GPL-3.0 по репозиторию."),
    ("Google AI Studio", "Google", "Google AI Studio", "", "≈2023-12-13", "api_platform", "specialized; agents", "no",
     "https://aistudio.google.com/", "web",
     "https://ai.google.dev/gemini-api/docs/ai-studio-quickstart", "https://techcrunch.com/2023/12/13/with-ai-studio-google-launches-an-easy-to-use-tool-for-developing-apps-and-chatbots-based-on-its-gemini-model/",
     "Google's web environment for prototyping prompts with Gemini models, tuning parameters and tools, and exporting code for the Gemini API.",
     "Веб-среда Google для прототипирования запросов к моделям Gemini, настройки параметров и инструментов и экспорта кода для Gemini API.",
     "MakerSuite", "Основная среда разработчика для моделей Gemini — отдельный практический инструмент.",
     "Дата: ≈2023-12-13 — запуск под именем Google AI Studio (преемник MakerSuite) по вторичным источникам TechCrunch/9to5Google; первичная страница блога Google вернула HTTP 500 при проверке 2026-09-26. Alias MakerSuite — прежнее имя того же продукта."),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def new_record_id(sheet, name):
    return "%s-%s" % (slugify(name), hashlib.sha1(("aipediya-master:%s:%s" % (sheet, name)).encode()).hexdigest()[:8])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v012", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    if sha256(args.v012) != V012_SHA256:
        raise SystemExit("v012 checksum mismatch")
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)

    rows, meta, extra = cm.read_workbook(args.v012)
    stamp = cm.now_utc()
    today = stamp[:10]
    log = rows["Changelog"]
    by = {sheet: {r["Record ID"]: r for r in rows[sheet]} for sheet in cm.MAIN}
    before_rows = {sheet: {r["Record ID"]: dict(r) for r in rows[sheet]} for sheet in cm.MAIN}

    def setf(sheet, row, field, value, reason):
        old = row.get(field, "")
        if old == value:
            return
        row[field] = value
        log.append({"Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": row["Record ID"],
                    "Field": field, "Before": old, "After": value, "Reason": "%s: %s" % (RUN, reason)})

    # --- observed state: Local (read-only snapshot) and Production sitemap
    snapshot, _aux = cm.local_snapshot()
    live, release = cm.fetch_production()
    core = {}
    for sheet in cm.MAIN:
        local_public = {rid for rid, (lr, _v) in snapshot[sheet].items() if lr["On Local"] == "YES"}
        core[sheet] = sorted(local_public | live[sheet])
        for row in rows[sheet]:
            setf(sheet, row, "On Local", "YES" if row["Record ID"] in local_public else "NO",
                 "observed Local published flag (read-only snapshot %s)" % stamp)
            setf(sheet, row, "On Production", "YES" if row["Record ID"] in live[sheet] else "NO",
                 "observed public sitemap https://aipediya.com (release %s) at %s" % (release[:12], stamp))
        mismatch = sorted(local_public ^ live[sheet])
        json.dump({"sheet": sheet, "checked_utc": stamp, "production_release": release,
                   "source_local": "Local SQLite snapshot (isolated copy of data/local/aipedia.sqlite3)",
                   "source_production": "https://aipediya.com/sitemap.xml -> sitemaps/en.xml",
                   "local_public": len(local_public), "production_public": len(live[sheet]),
                   "local_vs_production_mismatch": mismatch, "record_ids": core[sheet]},
                  open(evidence / ("core_%s.json" % sheet.lower()), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    core_sets = {s: set(v) for s, v in core.items()}

    # --- 1. approximate-date format (≈ lost in some v012 cells)
    for sheet in cm.MAIN:
        for row in rows[sheet]:
            value = row.get("Approx Date", "")
            if value and not cm.APPROX_DATE.match(value) and re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", value):
                setf(sheet, row, "Approx Date", "≈" + value, "format: approximate date kept, ≈ prefix restored (no precision change)")

    # --- 2. decision dates of carried decisions (latest decision/verification event)
    def event_date(value):
        # Some v004-v012 Changelog timestamps are stored as Excel serial days.
        if re.match(r"^\d{5}(\.\d+)?$", value or ""):
            return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(value)))).isoformat()
        return (value or "")[:10]

    last_event = {}
    for event in log:
        if event.get("Field") in ("Publication Decision", "Verification result"):
            last_event[(event["Sheet"], event["Record ID"])] = event_date(event["Timestamp (UTC)"])

    # --- 2b. offer units outside the site contract
    for offer in rows["Offers"]:
        if offer.get("Unit") not in cm.OFFER_UNITS and offer.get("Billing Unit"):
            old = offer["Unit"]
            offer["Unit"] = "other"
            log.append({"Timestamp (UTC)": stamp, "Sheet": "Offers", "Record ID": offer["Record ID"],
                        "Field": "Unit (%s)" % offer["Key"], "Before": old, "After": "other",
                        "Reason": "%s: site unit contract; the explicit Billing Unit %r is kept" % (RUN, offer["Billing Unit"])})

    # --- 3. archive: keep justified ones, code them
    for rid, (code, relation) in ARCHIVE_KEEP.items():
        row = by["Models"][rid]
        assert row["Publication Decision"] == "ARCHIVE", rid
        setf("Models", row, "Decision Code", code, "code for existing justified ARCHIVE")
        if relation:
            setf("Models", row, "Relation Type", relation, "relation type for existing link")
        setf("Models", row, "Decision Date", last_event.get(("Models", rid), today), "date of the carried decision (Changelog)")
    setf("Models", by["Models"]["grok-voice-api-27080172"], "Reason", MODEL_APP_SPLIT_NOTE,
         "reason points to the canonical service card in Tools")
    setf("Models", by["Models"]["grok-voice-api-27080172"], "Decision Sources", "https://x.ai/news/grok-voice-agent-api", "decision source")

    for rid, (status, reason) in REVERT_CLOSED.items():
        row = by["Tools"][rid]
        assert row["Publication Decision"] == "ARCHIVE", rid
        setf("Tools", row, "Publication Decision", "PUBLIC", "closure is lifecycle, not an editorial exclusion (owner rule 2026-09-26)")
        setf("Tools", row, "Decision Code", "HISTORICAL_RELEASE", "historical product card")
        setf("Tools", row, "Catalog Status", status, "lifecycle from the official source already cited in v012")
        setf("Tools", row, "Reason", reason, "individual justification")
        setf("Tools", row, "Decision Date", today, "decision revised")
        setf("Tools", row, "Decision Sources", row.get("Official Source", ""), "decision source")

    for sheet, rid, code, relation, parent, reason, sources in NEW_ARCHIVE:
        row = by[sheet][rid]
        setf(sheet, row, "Publication Decision", "ARCHIVE", "proven same entity")
        setf(sheet, row, "Decision Code", code, "reason code")
        setf(sheet, row, "Canonical / Parent Record ID", parent, "canonical card")
        setf(sheet, row, "Relation Type", relation, "relation type")
        setf(sheet, row, "Reason", reason, "individual justification")
        setf(sheet, row, "Decision Date", today, "new decision")
        setf(sheet, row, "Decision Sources", sources or row.get("Official Source", ""), "decision sources")
        setf(sheet, row, "Last Verified", today, "sources opened for this decision")

    # --- 4. open questions inside the core
    for rid, (old_name, new_label, old_label) in RESOLVE_CORE.items():
        row = by["Models"][rid]
        setf("Models", row, "Publication Decision", "PUBLIC", "identity resolved by developer source")
        setf("Models", row, "Decision Code", "HISTORICAL_RELEASE", "historical model")
        setf("Models", row, "Reason", (
            "AI21 (2023-06-08): размеры Light, Mid и Ultra заменили Large, Grande и Jumbo соответственно — те же "
            "базовые модели под новыми названиями (с объединёнными instruct-возможностями). Поэтому %s = %s, дата "
            "2023-03-09 — выпуск Jurassic-2 под прежним именем." % (row["Name"], old_name)), "identity + date basis")
        setf("Models", row, "Aliases", old_name, "former name of the same model (AI21)")
        setf("Models", row, "Decision Date", today, "decision revised")
        setf("Models", row, "Decision Sources", J2_SOURCES, "decision sources")
        setf("Models", row, "Last Verified", today, "developer post opened")
    codex = by["Tools"]["codex-59301cf4"]
    setf("Tools", codex, "Publication Decision", "PUBLIC", "card boundary resolved editorially")
    setf("Tools", codex, "Decision Code", "CURRENT_RELEASE", "current product")
    setf("Tools", codex, "Reason", CODEX_REASON, "boundary + date basis")
    setf("Tools", codex, "Decision Date", today, "decision revised")
    for rid, text in CORE_KEPT_OPEN.items():
        row = by["Models"][rid]
        setf("Models", row, "Publication Decision", "PUBLIC", "core card kept: no proven error (owner rule 2026-09-26)")
        setf("Models", row, "Decision Code", "CURRENT_RELEASE", "current model")
        setf("Models", row, "Reason", text, "open question kept, not blocking")
        setf("Models", row, "Decision Date", today, "decision revised")

    # --- 4b. merges checked but kept, license of the same model, AA evaluations, texts
    for (sheet, rid), (question, sources) in KEPT_WITH_QUESTION.items():
        row = by[sheet][rid]
        setf(sheet, row, "Publication Decision", "PUBLIC", "merge not applied to the existing public card (owner rule 2026-09-26)")
        setf(sheet, row, "Decision Code", "CURRENT_RELEASE", "current card kept")
        setf(sheet, row, "Relation Type", "", "no same-entity relation applied")
        setf(sheet, row, "Reason", question, "open merge question")
        setf(sheet, row, "Decision Date", today, "decision revised")
        setf(sheet, row, "Decision Sources", sources or row.get("Official Source", ""), "decision sources")
    canonical, source = NEMOTRON_LICENSE
    setf("Models", by["Models"][canonical], "License", by["Models"][source]["License"],
         "license of the same model, from the HF model card of its BF16 weights (FORMAT_OF row %s)" % source)
    aa = [e for e in rows["Evaluations"] if e.get("Evaluator") == "Artificial Analysis" and e.get("Public") == "YES"]
    assert len(aa) == 11, len(aa)
    for evaluation in aa:
        log.append({"Timestamp (UTC)": stamp, "Sheet": "Evaluations", "Record ID": evaluation["Record ID"],
                    "Field": "Public (%s)" % evaluation["Key"], "Before": "YES", "After": "NO",
                    "Reason": "%s: basis for publishing Artificial Analysis results is not documented; kept "
                              "internally, excluded from public output (owner rule 2026-09-26)" % RUN})
        evaluation["Public"] = "NO"
    for rid, text in TOOL_RU.items():
        row = by["Tools"][rid]
        setf("Tools", row, "Description RU", text,
             "manual RU for the chosen master Description EN (site text was generated and contained errors)")

    # --- 4c. v012 access links that point to another size of the family: keep the
    # specific Local link (Service URL is what the site shows; Source URL is its evidence)
    for key in ACCESS_REVERT:
        access_row = next(a for a in rows["Access"] if a["Key"] == key)
        local_row = _aux["Access"][key]
        for column in ("Service URL", "Source URL"):
            if access_row.get(column, "") != local_row.get(column, ""):
                log.append({"Timestamp (UTC)": stamp, "Sheet": "Access", "Record ID": access_row["Record ID"],
                            "Field": "%s (%s)" % (column, key), "Before": access_row.get(column, ""),
                            "After": local_row.get(column, ""),
                            "Reason": "%s: v012 value is the page of a different model size; the specific link is kept" % RUN})
                access_row[column] = local_row.get(column, "")

    # --- 5. additions
    def most_common(values):
        values = [v for v in values if v]
        return max(set(values), key=values.count) if values else ""

    def known_country(developer):
        # Countries of a new record come only from existing records of the same
        # developer; an unknown developer keeps them empty (never guessed).
        return most_common([r.get("Developer Country", "") for s in cm.MAIN for r in rows[s]
                            if r.get("Developer") == developer and r.get("On Local") == "YES"])

    def known_origin(developer):
        return most_common([r.get("Origin Countries", "") for r in rows["Models"]
                            if r.get("Developer") == developer and r.get("On Local") == "YES"])

    added = []
    for (sheet, name, dev, family, version, exact, approx, category, tasks, inputs, outputs, context, license_,
         open_w, stage, official, secondary, desc_en, desc_ru, aliases, basis) in ADD:
        hit = [r["Record ID"] for r in rows["Models"]
               if cm._alias_key(name) in {cm._alias_key(n) for n in [r["Name"]] + cm.split_aliases(r.get("Aliases"))}]
        assert not hit, (name, hit)
        row = {c: "" for c in cm.MAIN["Models"]}
        row.update({
            "Record ID": new_record_id("Models", name), "Status": "NEEDS_REVIEW", "Publication Decision": "PUBLIC",
            "Name": name, "Developer": dev, "Exact Release Date": exact, "Approx Date": approx,
            "Reason": basis, "Decision Code": "CURRENT_RELEASE",
            "Decision Date": today, "Decision Sources": " | ".join(u for u in (official, secondary) if u),
            "Aliases": aliases, "Official Source": official, "Secondary Source": secondary, "Last Verified": today,
            "On Local": "NO", "On Production": "NO",
            "Notes": "[%s] Добавлено по аудиту 2026-09-25 (группы подтверждённых пропусков) после поиска по всей книге (Name/Aliases). "
                     "Проверены: идентичность, разработчик, назначение, дата, модальности/контекст/лицензия — только если указаны в источнике; "
                     "цены и оценки не заполнялись." % RUN,
            "Release Stage": stage, "Family": family, "Version": version, "Category": category, "Tasks": tasks,
            "Input Modalities": inputs, "Output Modalities": outputs, "Context": context, "License": license_,
            "Open Weights": open_w, "Catalog Status": "active", "Developer Country": known_country(dev),
            "Origin Countries": known_origin(dev),
            "Description EN": desc_en, "Description RU": desc_ru,
            "Source Title": "%s — official source" % family, "Source URL": official, "Source Publisher": dev,
            "Release Evidence (JSON)": json.dumps({"checked": today, "source_url": official, "run": RUN,
                                                   "date_kind": "public release / announcement with release of the model",
                                                   "exact": exact or None, "approx": approx or None}, ensure_ascii=False, sort_keys=True),
        })
        rows["Models"].append(row)
        by["Models"][row["Record ID"]] = row
        added.append(("Models", row["Record ID"], name))
    for (name, dev, version, exact, approx, category, purposes, local, url, platforms, official, secondary,
         desc_en, desc_ru, aliases, basis, note) in ADD_TOOLS:
        hit = [r["Record ID"] for r in rows["Tools"]
               if cm._alias_key(name) in {cm._alias_key(n) for n in [r["Name"]] + cm.split_aliases(r.get("Aliases"))}]
        assert not hit, (name, hit)
        row = {c: "" for c in cm.MAIN["Tools"]}
        row.update({
            "Record ID": new_record_id("Tools", name), "Status": "NEEDS_REVIEW", "Publication Decision": "PUBLIC",
            "Name": name, "Developer": dev, "Exact Release Date": exact, "Approx Date": approx, "Reason": basis,
            "Decision Code": "CURRENT_RELEASE", "Decision Date": today,
            "Decision Sources": " | ".join(u for u in (official, secondary) if u), "Aliases": aliases,
            "Official Source": official, "Secondary Source": secondary, "Last Verified": today,
            "On Local": "NO", "On Production": "NO",
            "Notes": "[%s] Добавлено по аудиту 2026-09-25 после поиска по всей книге. %s" % (RUN, note),
            "Version": version, "Category": category, "Purposes": purposes, "Local Execution": local,
            "Official URL": url, "Platforms": platforms, "Catalog Status": "active", "Developer Country": known_country(dev),
            "Description EN": desc_en, "Description RU": desc_ru, "Source Title": name, "Source URL": official,
            "Source Publisher": dev,
        })
        rows["Tools"].append(row)
        by["Tools"][row["Record ID"]] = row
        added.append(("Tools", row["Record ID"], name))
    for sheet, rid, name in added:
        log.append({"Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": rid, "Field": "row added",
                    "Before": "", "After": name, "Reason": "%s: selected addition with checked sources" % RUN})

    # --- 6. aliases of canonical cards (names of SAME_ENTITY archive rows + model IDs)
    for sheet in cm.MAIN:
        wanted = {}
        for row in rows[sheet]:
            if row.get("Relation Type") in cm.SAME_ENTITY and row.get("Canonical / Parent Record ID"):
                target = row["Canonical / Parent Record ID"]
                names = [row["Name"]]
                found = re.search(r"представление (\S+) дублирует", row.get("Reason", ""))
                if found:
                    names.append(found.group(1))
                wanted.setdefault(target, []).extend(names)
        for (s, rid), names in EXTRA_ALIASES.items():
            if s == sheet:
                wanted.setdefault(rid, []).extend(names)
        for rid, names in wanted.items():
            row = by[sheet][rid]
            current = cm.split_aliases(row.get("Aliases"))
            for name in names:
                if cm._alias_key(name) not in {cm._alias_key(n) for n in current + [row["Name"]]}:
                    current.append(name)
            setf(sheet, row, "Aliases", cm.ALIAS_SEPARATOR.join(current), "aliases of the proven same entity")

    # --- 7. codes and dates for every remaining decision
    scope_ids = {"ernie-bot-ernie-35-5f4efb19", "gigachat-746bcb71", "eleven-dubbing-v1-241c4ab4"}
    source_ids = {"mark-i-perceptron-adad9454"}
    identity_words = re.compile(r"Base|Instruct|checkpoint|тождеств|соответств|означает|Уточнить|Неоднозначн|конфигурац|вариант|v1/v2|ревизи|identity|alias|Chat|различ|Разделить|определить|original|представляет", re.I)
    for sheet in cm.MAIN:
        for row in rows[sheet]:
            decision = row["Publication Decision"]
            if not row.get("Decision Code"):
                if decision == "PUBLIC":
                    code = "HISTORICAL_RELEASE" if row.get("Catalog Status") in ("retired", "archived") else "CURRENT_RELEASE"
                elif decision == "NEEDS_REVIEW":
                    rid = row["Record ID"]
                    code = ("SCOPE" if rid in scope_ids else "SOURCE" if rid in source_ids
                            else "IDENTITY" if identity_words.search(row.get("Reason", "")) else "DATE")
                else:
                    raise SystemExit("uncoded ARCHIVE %s" % row["Record ID"])
                setf(sheet, row, "Decision Code", code, "decision code derived from the existing decision and Reason")
            if not row.get("Decision Date"):
                setf(sheet, row, "Decision Date", last_event.get((sheet, row["Record ID"]), today),
                     "date of the carried decision (Changelog)")

    # --- 8. Status: core + selected additions only
    added_ids = {rid for _s, rid, _n in added}
    for sheet in cm.MAIN:
        for row in rows[sheet]:
            rid, decision = row["Record ID"], row["Publication Decision"]
            missing = cm.missing_items(sheet, row)
            if rid in core_sets[sheet]:
                status = "PUBLISHED" if decision == "PUBLIC" else "NEEDS_REVIEW"
                why = ("core card kept (published now); gaps do not remove it" if status == "PUBLISHED"
                       else "core card leaves the public package: %s (see diff)" % decision)
            elif rid in added_ids:
                status = "PUBLISHED" if decision == "PUBLIC" and not missing else "NEEDS_REVIEW"
                why = "selected addition, checked" if status == "PUBLISHED" else "selected addition with blocking gap: %s" % missing
            else:
                status = "NEEDS_REVIEW"
                why = "not in the current package (deferred research stock / archive)"
                if decision == "PUBLIC" and DEFERRED not in row.get("Notes", ""):
                    setf(sheet, row, "Notes", (row.get("Notes", "") + "\n" + DEFERRED).strip(), "deferred marker")
            setf(sheet, row, "Status", status, why)

    # --- 9. derived fields, numbering plan, meta
    renumbered = cm.refresh_derived(rows, log, "%s: chronology recomputed for the package" % RUN, stamp)
    meta = dict(meta)
    meta.update({
        "Schema": cm.SCHEMA, "Version": "v013", "Built From": "v012 sha256 %s" % V012_SHA256,
        "Local Models (public/total)": "%d/%d" % (len([1 for r, _ in snapshot["Models"].values() if r["On Local"] == "YES"]), len(snapshot["Models"])),
        "Local Tools (public/total)": "%d/%d" % (len([1 for r, _ in snapshot["Tools"].values() if r["On Local"] == "YES"]), len(snapshot["Tools"])),
        "Production Checked (UTC)": stamp, "Production Release": release,
        "Production Sitemap (models/tools)": "%d/%d" % (len(live["Models"]), len(live["Tools"])),
        "Verification run": "%s — редакционный пакет: ядро + отобранные дополнения; остальное — отложенный запас" % RUN,
        "Следующий шаг": "См. docs/CATALOG_MASTER.md: приёмка diff владельцем, затем sync-local на Local и выпуск по docs/RELEASE.md только по команде владельца.",
    })
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, args.out, extra)

    # --- evidence: publication diff, numbering diff, field changes, summary
    with open(evidence / "publication_diff.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Sheet", "Record ID", "Name", "Change", "Publication Decision", "Decision Code", "Canonical", "Reason"])
        for sheet in cm.MAIN:
            for row in rows[sheet]:
                live_now = row["Record ID"] in core_sets[sheet]
                target = row["Status"] == "PUBLISHED"
                if live_now != target:
                    w.writerow([sheet, row["Record ID"], row["Name"], "HIDE" if live_now else "SHOW",
                                row["Publication Decision"], row["Decision Code"],
                                row.get("Canonical / Parent Record ID", ""), row.get("Reason", "")[:300]])
    with open(evidence / "numbering_diff.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Sheet", "Record ID", "Name", "Date", "Local Number (site now)", "v012 Public Number", "Planned Public Number"])
        for sheet in cm.MAIN:
            for row in rows[sheet]:
                old = before_rows[sheet].get(row["Record ID"], {})
                if row.get("Local Number", "") != row.get("Public Number", "") or old.get("Public Number", "") != row.get("Public Number", ""):
                    w.writerow([sheet, row["Record ID"], row["Name"], row.get("Exact Release Date") or row.get("Approx Date"),
                                row.get("Local Number", ""), old.get("Public Number", ""), row.get("Public Number", "")])
    run_events = [e for e in log if e["Timestamp (UTC)"] == stamp]
    with open(evidence / "changelog_this_run.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cm.CHANGELOG, delimiter=";")
        w.writeheader()
        w.writerows(run_events)
    summary = {"stamp": stamp, "renumbered_events": renumbered, "changelog_events": len(run_events), "added": added}
    for sheet in cm.MAIN:
        start = before_rows[sheet]
        summary[sheet] = {
            "before_rows": len(start), "after_rows": len(rows[sheet]), "core": len(core_sets[sheet]),
            "added": sum(1 for s, _r, _n in added if s == sheet),
            "published_target": sum(1 for r in rows[sheet] if r["Status"] == "PUBLISHED"),
            "decision": {d: sum(1 for r in rows[sheet] if r["Publication Decision"] == d) for d in cm.DECISIONS},
            "archive_same_entity": sum(1 for r in rows[sheet] if r.get("Relation Type") in cm.SAME_ENTITY),
            "deferred_public_proposals": sum(1 for r in rows[sheet] if r["Status"] != "PUBLISHED" and r["Publication Decision"] == "PUBLIC"),
            "lost_record_ids": sorted(set(start) - {r["Record ID"] for r in rows[sheet]}),
        }
    json.dump(summary, open(evidence / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

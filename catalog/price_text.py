"""Translate complete source conditions without shortening the original record."""
import re

CLAUSES = {
    'Draft только hd; это отдельный режим, не цена полного рендера.': 'Draft is hd only; a separate mode, not the price of a full render.',
    'Без аудио': 'Without audio', 'С аудио': 'With audio',
    'Бесплатные endpoints имеют квоты.': 'Free endpoints have quotas.',
    'Дополнительные опции распознавания оплачиваются отдельно.': 'Additional transcription options are billed separately.',
    'Международный endpoint; не подписка Coding Plan.': 'International endpoint; not a Coding Plan subscription.',
    'Минимальная цена; итог зависит от конфигурации.': 'Minimum price; total depends on configuration.',
    'Оплата записи кэша и других услуг не включена.': 'Cache writes and other services are not included.',
    'Применимость цены к разным входным модальностям проверять в источнике.': 'Check applicability to different input modalities in the source.',
    'Проверить ограничения длительности/разрешения для конкретного запроса.': 'Check duration/resolution limits for the specific request.',
    'Сторонний поставщик доступа; не разработчик модели.': 'Third-party access provider, not the model developer.',
    'Текстовые входы: 5 USD/1M; cached text: 1.25. Не цена за одно изображение.': 'Text input: 5 USD/1M; cached text: 1.25. Not a price per image.',
    'Точная версия endpoint требует сверки; имя не фиксирует snapshot.': 'Exact endpoint version needs verification; the name does not pin a snapshot.',
    'граница short/long не сверена. Кэш-запись — отдельная ставка. Дополнительные инструменты оплачиваются отдельно. Подходящие regional processing endpoints: +10%.': 'The short/long threshold has not been verified. Cache writes have a separate rate. Additional tools are billed separately. Eligible regional processing endpoints: +10%.',
    'Fast недоступен с EU data residency.': 'Fast is unavailable with EU data residency.',
    'Промотариф действует как минимум до 21.11.2026; точная дата окончания не объявлена.': 'Promotional rate applies at least through 2026-11-21; the exact end date has not been announced.',
    'Прямой Claude API; отдельно base input, cache write 5m/1h, cache hit и output. Не стоимость подписки Claude/Claude Code.': 'Direct Claude API; base input, 5m/1h cache writes, cache hits and output have separate rates. Not a Claude/Claude Code subscription price.',
    '$2/$10 — стандартный тариф, ранее планировавшееся повышение 01.09.2026 отменено.': '$2/$10 is the standard rate; the increase previously planned for 2026-09-01 was cancelled.',
    'Standard: текущие $0.75/$3.75 до 31.12.2026. С 01.01.2027 объявлены $1.50/$7.50; кэш $0.15. Хранение кэша и grounding отдельно. Это не фиксированная цена полного задания.': 'Standard: current $0.75/$3.75 through 2026-12-31. Announced rates from 2027-01-01: $1.50/$7.50; cache $0.15. Cache storage and grounding are separate. This is not a fixed price for an entire task.',
    'Бесплатный уровень с ограничениями и квотами; не обещание безлимитного использования. Квоты и условия обработки данных проверять перед использованием.': 'Free tier with limits and quotas; not unlimited use. Check quotas and data-processing terms before use.',
    'Указаны только аудиотокены: вход $3/M, выход $12/M; текст и видео имеют другие ставки. Не фиксированная цена одной минуты разговора.': 'Audio tokens only: input $3/M, output $12/M; text and video have different rates. Not a fixed price per minute of conversation.',
    'Только текстовые токены в Live-сессии. Аудио и изображения/видео оплачиваются отдельно.': 'Text tokens in a Live session only. Audio and images/video are billed separately.',
    'Цены разных типов токенов; нельзя сравнивать с чисто текстовой моделью без учёта единиц.': 'Rates differ by token type; comparison with a text-only model requires matching units.',
    'Peak: Пн–Пт 01:00–04:00 и 06:00–10:00 UTC, кроме государственных праздников Китая. Остальное время — Off-peak. API-алиас может менять целевую версию; сверять версию ответа.': 'Peak: Mon–Fri 01:00–04:00 and 06:00–10:00 UTC, excluding Chinese public holidays. Other times are off-peak. The API alias may change its target version; verify the response version.',
    'Оплата за 1M токенов; приблизительная цена за минуту не является фиксированным тарифом.': 'Billed per 1M tokens; the approximate per-minute cost is not a fixed rate.',
    'Встроенные инструменты/поиск оплачиваются отдельно; поставщик использует актуальный бренд в документации.': 'Built-in tools/search are billed separately; the provider uses its current brand in the documentation.',
    'Минимальная опубликованная цена. Итог зависит от разрешения и числа мегапикселей; не универсальный тариф за любое изображение.': 'Lowest published price. Total depends on resolution and megapixels; not a universal rate for any image.',
    '1 мегапиксель-секунда = 1 048 576 пикселей выходного кадра × 1 секунда; база 24 fps, больше fps — пропорциональная доплата; вход до 20 секунд.': '1 megapixel-second = 1,048,576 output-frame pixels × 1 second; base 24 fps, higher fps incurs a proportional surcharge; input up to 20 seconds.',
    'Тариф Runway Dev: 1 кредит = $0.01. Указана базовая конфигурация, возможен налог. ProRes/PNG: +$0.05/сек; HDR/10-bit профили: +$0.20/сек или +$0.40/сек свыше 4 MP.': 'Runway Dev rate: 1 credit = $0.01. Base configuration; tax may apply. ProRes/PNG: +$0.05/sec; HDR/10-bit profiles: +$0.20/sec or +$0.40/sec above 4 MP.',
    'Прямой Gemini API; не тариф посредника Runway. Списание за успешно созданное видео; бесплатного уровня нет.': 'Direct Gemini API, not the Runway intermediary rate. Charged for successfully generated video; no free tier.',
    'Базовая ставка распознавания. Entity detection: +$0.07/час; keyterm prompting: +$0.05/час, если включены.': 'Base transcription rate. Entity detection: +$0.07/hour; keyterm prompting: +$0.05/hour, when enabled.',
    'Подписка и квоты продукта; не равна неограниченному API. Набор доступных моделей зависит от тарифа.': 'Product subscription and quotas; not unlimited API access. Available models depend on the plan.',
    'Стоимость соответствующей подписки ChatGPT, не дополнительная подписка Codex. Доступ и лимиты зависят от плана; API-ключ оплачивается отдельно.': 'Price of the corresponding ChatGPT subscription, not an additional Codex subscription. Access and limits depend on the plan; API-key usage is billed separately.',
    'Цена подписки Claude с доступом к Claude Code, не вторая дополнительная оплата. Лимиты зависят от плана; BYOK отдельно.': 'Claude subscription with Claude Code access, not a second charge. Limits depend on the plan; BYOK is separate.',
    'API и Playground: одинаковые ставки. Цена определяется длительностью, режимом и разрешением; звук синхронизирован с видео.': 'API and Playground use the same rates. Price depends on duration, mode and resolution; audio is synchronized with video.',
    'Реальная оплата по входным и выходным аудиотокенам; опубликованные оценки за минуту не фиксированный тариф.': 'Actual billing uses input and output audio tokens; published per-minute estimates are not fixed rates.',
    'Прямой API; оплата за песню/запрос, не за минуту. Ограничения длительности сверять в документации.': 'Direct API; billed per song/request, not per minute. Check duration limits in the documentation.',
    'Стоимость транскрипции, не медицинская консультация и не подтверждение клинической точности. Дополнительные функции оплачиваются отдельно.': 'Transcription cost, not medical consultation or confirmation of clinical accuracy. Additional features are billed separately.',
    'Опубликованный базовый тариф. Налоги не включены; условия входного медиа и обработки отдельно.': 'Published base rate. Taxes excluded; input-media and processing conditions are separate.',
    'Комбинированный голосовой сервис, а не одна базовая модель. Burst-режим $0.16/мин; квоты и параллельность зависят от плана.': 'Combined voice service, not a single base model. Burst mode is $0.16/min; quotas and concurrency depend on the plan.',
    'Посекундный учёт без округления до целой минуты. Backend-модель и инструменты оплачиваются дополнительно.': 'Per-second billing without rounding up to a full minute. Backend model and tools are billed additionally.',
    'Отдельная тарифицируемая модальность одной модели. Строка image — только стоимость входа, не генерация изображения.': 'Separately billed modality of one model. The image row is input cost only, not image generation.',
    'Источник называет это estimated cost. Не выдавать за гарантированную ставку и не смешивать с точными тарифами за минуту.': 'The source calls this an estimated cost. It is not a guaranteed rate and must not be mixed with fixed per-minute rates.',
    'Оценка источника $0.006/мин — ориентир, не отдельный фиксированный тариф. Основные цены указаны за токены.': 'The source estimate of $0.006/min is indicative, not a separate fixed rate. Primary prices are per token.',
    'Оценка источника $0.003/мин — ориентир, не отдельный фиксированный тариф. Основные цены указаны за токены.': 'The source estimate of $0.003/min is indicative, not a separate fixed rate. Primary prices are per token.',
    'текстовая составляющая': 'text component', 'Прямой API': 'Direct API', 'с аудио': 'with audio',
    'Тариф Runway Dev: 1 кредит = $0.01. Указана базовая конфигурация, возможен налог.': 'Runway Dev rate: 1 credit = $0.01. Base configuration; tax may apply.',
    'В составе Pro': 'Included with Pro', 'В составе Max': 'Included with Max',
    'Голосовая сессия': 'Voice session', 'Опубликованная оценка': 'Published estimate',
}


def full_conditions(value, lang):
    from .comparison import localized
    translated = localized(value, lang)
    if lang != 'en' or not isinstance(value, dict): return translated
    original = localized(value, 'ru')
    if len(original) < len(translated) * 1.3: return translated
    text = original
    for ru, en in CLAUSES.items(): text = text.replace(ru, en)
    text = text.replace(' · от', ' · from')
    if re.search('[А-Яа-яЁё]', text):
        # Preserve every condition even when a new source phrase needs translation.
        return translated + ' · Source conditions (original): ' + original
    return text

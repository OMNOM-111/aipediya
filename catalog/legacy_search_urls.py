"""Exact legacy card URLs observed in GSC Pages on 2026-09-26.

Only these already-discovered URLs bypass the card-query robots block. This
finite migration list must not be replaced with a wildcard for ``?lang=``:
that would expose unbounded page/sort/facet/fragment combinations to crawlers.
Retired records return 404; published cards and aliases redirect; fragments
remain noindex. Keep the order and spelling from Search Console.
"""

GSC_LEGACY_CARD_URLS = (
    "/models/muse-spark-13-77a09338?lang=en&page=4",
    "/models/llama-33-70b-instruct-f9965971?lang=en",
    "/models/claude-sonnet-5-26497337?lang=en&page=3",
    "/models/gemini-38-live-a959d0c7?lang=en&page=4",
    "/models/gpt-4o-mini?lang=en",
    "/models/claude-11-api-snapshot-11a647fb?lang=en&page=3",
    "/models/gemini-15-flash-6f02af01?lang=en&page=5",
    "/models/llama-32-90b-vision-instruct-88a989e6?lang=en&page=3",
    "/models/veo-72ff5aff?lang=en&page=5",
    "/models/luminous-extended-32e3998d?lang=en",
    "/models/qwen15-18b-6ec524d9?lang=en&page=5",
    "/models/gemini-38-flash-c9fb1256?lang=en",
    "/models/glm-45-x-c6b9ab71?lang=zh-Hans&page=4",
    "/models/llama-3-70b-instruct-a953989a?lang=en",
    "/models/claude-35-haiku-20241022-51029c52?lang=en",
    "/models/fara-15-4b-02563a27?lang=en&page=4",
    "/models/stable-diffusion-35-large-bb09479e?lang=en",
    "/models/sarvam-m-ce03bf75?lang=en",
    "/models/claude-35-sonnet-20240620-f0d408d7?lang=en",
    "/models/grok-imagine-video-15-f891b2bd?lang=en",
    "/models/nemotron-35-lightning-30b-a3b-bf16-8af433db?lang=en&page=3",
    "/models/bert-base-27fa313c?lang=en&page=5",
    "/models/gpt-neo-125m-c4ce9056?lang=en",
    "/models/granite-31-moe-3b-4087930c?lang=en&page=6",
    "/models/grok-imagine-image-pro-6171d547?lang=en",
    "/models/flux11-pro-ultra-ff451a32?lang=en",
    "/models/gemini-38-live-extended-thinking-4ab0af55?lang=en&page=5",
    "/models/gpt-5-nano?lang=en&page=9",
    "/models/granite-31-moe-3b-4087930c?lang=en&page=5",
    "/models/mistral-large-21-eab00bf3?sort=purpose_asc&lang=zh-Hans&kind=model&tab=overview&page=2&partial=rows",
    "/models/codestral-de461143?lang=de&page=5",
    "/models/falcon-ocr-07e0429a?sort=context_asc&lang=hi&kind=model&page=5&partial=rows",
    "/models/llama-31-70b-instruct-441da955?lang=en",
    "/models/gemini-38-live-a959d0c7?lang=en&sort=status_asc&kind=model&page=3&partial=rows",
    "/models/qwen3-32b-d3d65117?lang=en&page=2",
    "/models/claude-haiku-45-20251001-f3ba3acc?lang=en",
    "/models/claude-opus-41-600423cc?lang=en",
    "/models/claude-21-abeffa80?lang=ru",
    "/models/gemma-4-31b-it-6490a505?lang=zh-Hans&page=3",
    "/models/claude-opus-46-fe255d9c?lang=zh-Hant&page=3",
    "/models/llama-3-8b-instruct-29fc646f?lang=en",
    "/models/hunyuan3d-2mini-turbo-c17df073?lang=en",
    "/models/tiny-aya-fire-d728b7ba?lang=ru&page=3",
    "/models/gemini-3-pro-preview-4c620280?lang=en&page=5",
    "/models/text-davinci-002-45ffa171?lang=bn&page=3",
)

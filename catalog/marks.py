"""Official developer and product marks shown beside a catalog name.

Simple Icons paths (CC0) are used for published brand glyphs and recolored
for the catalog. Official compact icons from developer sites and press kits
are kept as provided. An organization without a mark keeps the letter fallback.

"""
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from django.utils.safestring import mark_safe

MARK_DIR = Path(__file__).resolve().parent.parent / "static" / "marks"

# Normalized organization name -> file stem in static/marks/.
ALIASES = {
    "openai": "openai",
    "z.ai / zhipu ai": "zai",
    "z.ai": "zai",
    "google": "google",
    "google deepmind": "google",
    "h company": "hcompany",
    "black forest labs": "bfl",
    "elevenlabs": "elevenlabs",
    "mistral ai": "mistral",
    "anthropic": "anthropic",
    "meta": "meta",
    "minimax": "minimax",
    "tencent": "tencent",
    "spacexai / xai (бренд документации)": "xai",
    "xai": "xai",
    "runway": "runway",
    "stability ai": "stability",
    "bytedance": "bytedance",
    "cohere labs": "cohere",
    "cohere": "cohere",
    "nvidia": "nvidia",
    "qwen / alibaba": "qwen",
    "qwen": "qwen",
    "wan-ai": "wan",
    "microsoft": "microsoft",
    "technology innovation institute": "tii",
    "ai-sage": "gigachat",
    "ai singapore": "sealion",
    "deepseek": "deepseek",
    "moonshot ai": "kimi",
    "sarvam ai": "sarvam",
    "lg ai research": "lg",
    "swiss ai initiative": "swiss",
    "yandex": "yandex",
    "cursor": "cursor",
    "github": "github",
    "lm studio": "lmstudio",
    "manus": "manus",
    "midjourney": "midjourney",
    "ollama": "ollama",
    "suno": "suno",
    # Simple Icons CC0 path, Cloudflare orange: https://simpleicons.org/?q=cloudflare
    "cloudflare": "cloudflare",
    # Official project icon: https://strandsagents.com/favicon.svg
    "strands agents / aws": "strands",
}

# Exact product override for an official product mark. All other entries keep
# the developer mark. Sources: https://cue.im/assets/cue/favicon.svg;
# AnythingLLM https://github.com/Mintplex-Labs/anything-llm/blob/master/frontend/public/favicon.png
RECORD_ALIASES = {
    "cue-77457549": "cue",
    "anythingllm-90d04ca3": "anythingllm",
}

# Exact organization names of published Local developers that have a mark (40).
# Used by tests so a renamed Organization cannot silently drop its mark.
PUBLISHED_DEVELOPERS = (
    "AI Singapore",
    "Anthropic",
    "Black Forest Labs",
    "ByteDance",
    "Cloudflare",
    "Cohere Labs",
    "Cohere",
    "Cursor",
    "DeepSeek",
    "ElevenLabs",
    "GitHub",
    "Google",
    "Google DeepMind",
    "H Company",
    "LG AI Research",
    "LM Studio",
    "Manus",
    "Meta",
    "Microsoft",
    "Midjourney",
    "MiniMax",
    "Mistral AI",
    "Moonshot AI",
    "NVIDIA",
    "Ollama",
    "OpenAI",
    "Qwen / Alibaba",
    "Runway",
    "Sarvam AI",
    "SpaceXAI / xAI (бренд документации)",
    "Stability AI",
    "Strands Agents / AWS",
    "Suno",
    "Swiss AI Initiative",
    "Technology Innovation Institute",
    "Tencent",
    "Wan-AI",
    "Yandex",
    "Z.ai / Zhipu AI",
    "ai-sage",
)


def developer_key(name):
    if isinstance(name, dict):
        name = name.get("en") or name.get("ru") or ""
    text = unicodedata.normalize("NFKC", str(name or "")).casefold().replace("ё", "е")
    return re.sub(r"\s+", " ", text).strip()


def _stem_for(key):
    stem = ALIASES.get(key)
    if stem:
        return stem
    if key.startswith("spacexai") or key.startswith("xai"):
        return "xai"
    if key.startswith("z.ai"):
        return "zai"
    return None


@lru_cache(maxsize=None)
def _asset(stem):
    svg = MARK_DIR / f"{stem}.svg"
    if svg.is_file():
        return ("svg", mark_safe(svg.read_text(encoding="utf-8")))
    png = MARK_DIR / f"{stem}.png"
    if png.is_file():
        return ("img", f"marks/{stem}.png")
    return None


def mark_for(name, record_slug=""):
    stem = RECORD_ALIASES.get(str(record_slug or "")) or _stem_for(developer_key(name))
    if not stem:
        return None
    asset = _asset(stem)
    if not asset:
        return None
    kind, payload = asset
    if kind == "svg":
        return {"svg": payload, "file": ""}
    return {"svg": "", "file": payload}

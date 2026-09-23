"""Provider abstraction for the dynamic-catalog translation pipeline.

Providers are swappable and chosen via settings/environment; API keys never
live in code or Git. The mock provider is deterministic and offline, so Local
development and the automated tests never call an external service.
"""
import json
import time
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from django.conf import settings

from .token_guard import from_protected_html, to_protected_html


class TranslationError(RuntimeError):
    """Raised when a provider cannot produce a translation."""


class TranslationProvider:
    name = "base"

    def translate(self, text, target_language, source_language="en"):
        raise NotImplementedError

    def translate_batch(self, texts, target_language, source_language="en"):
        return [self.translate(text, target_language, source_language) for text in texts]


class NullTranslationProvider(TranslationProvider):
    """Never translates; every field stays on the English fallback."""

    name = "null"

    def translate(self, text, target_language, source_language="en"):
        raise TranslationError("translation provider is disabled")


class MockTranslationProvider(TranslationProvider):
    """Deterministic offline provider for Local development and tests."""

    name = "mock"

    def translate(self, text, target_language, source_language="en"):
        if not text:
            return ""
        return f"[{target_language}] {text}"


class AzureTranslationProvider(TranslationProvider):
    """Microsoft Azure Translator (Cognitive Services) REST adapter.

    Never invoked by the automated tests. Requires an environment key; a
    missing key raises :class:`TranslationError` instead of failing silently.
    """

    name = "azure"

    def __init__(self, key=None, endpoint=None, region=None, timeout=30, max_retries=5):
        self.key = key if key is not None else settings.AIPEDIA_AZURE_TRANSLATOR_KEY
        self.endpoint = (endpoint or settings.AIPEDIA_AZURE_TRANSLATOR_ENDPOINT).rstrip("/")
        self.region = region if region is not None else settings.AIPEDIA_AZURE_TRANSLATOR_REGION
        self.timeout = timeout
        self.max_retries = max_retries

    @staticmethod
    def _azure_code(language):
        # Azure keeps "zh-Hans"/"zh-Hant"; pt-BR maps to the "pt" it serves.
        return {"pt-BR": "pt"}.get(language, language)

    @staticmethod
    def _retry_delay(exc, attempt):
        """Honor a Retry-After header on throttling, else exponential backoff."""
        header = exc.headers.get("Retry-After") if getattr(exc, "headers", None) else None
        if header:
            try:
                return min(float(header), 60.0)
            except ValueError:
                pass
        return min(2.0 ** attempt, 30.0)

    def translate_batch(self, texts, target_language, source_language="en"):
        if not self.key:
            raise TranslationError("AIPEDIA_AZURE_TRANSLATOR_KEY is not configured")
        # HTML mode lets technical tokens (1M, 128K, 7B, model/version IDs, API,
        # URLs) be wrapped as non-translatable so Azure cannot turn them into
        # words or units (e.g. "1M" -> "1 metre").
        url = (
            f"{self.endpoint}/translate?api-version=3.0&textType=html"
            f"&from={source_language}&to={self._azure_code(target_language)}"
        )
        body = json.dumps([{"text": to_protected_html(text or "")} for text in texts]).encode("utf-8")
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json; charset=UTF-8",
        }
        if self.region:
            headers["Ocp-Apim-Subscription-Region"] = self.region
        # Free-tier (F0) throttling returns HTTP 429; transient 5xx and network
        # errors are also retried with backoff so a long backfill survives them.
        for attempt in range(1, self.max_retries + 2):
            req = urllib_request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib_request.urlopen(req, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt <= self.max_retries:
                    time.sleep(self._retry_delay(exc, attempt))
                    continue
                # The URL carries only language codes; the key lives in a header.
                raise TranslationError(f"Azure Translator HTTP {exc.code}") from exc
            except (URLError, TimeoutError, ValueError) as exc:
                if attempt <= self.max_retries:
                    time.sleep(min(2.0 ** attempt, 30.0))
                    continue
                raise TranslationError(f"Azure Translator request failed: {exc}") from exc
        results = []
        for item in payload:
            translations = item.get("translations") or []
            results.append(from_protected_html(translations[0]["text"]) if translations else "")
        return results

    def translate(self, text, target_language, source_language="en"):
        return self.translate_batch([text], target_language, source_language)[0]


_PROVIDERS = {
    "mock": MockTranslationProvider,
    "azure": AzureTranslationProvider,
    "null": NullTranslationProvider,
}


def get_provider(name=None):
    """Return a provider instance for ``name`` or the configured default."""
    key = (name or settings.AIPEDIA_TRANSLATION_PROVIDER or "mock").strip().lower()
    provider = _PROVIDERS.get(key)
    if provider is None:
        raise TranslationError(f"unknown translation provider: {key}")
    return provider()

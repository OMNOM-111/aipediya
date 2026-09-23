"""Safely verify Azure Translator credentials with one minimal request.

Prints only PASS/FAIL, provider, region and a sanitized reason. The API key is
never read out, printed, measured, or embedded in any message. No secret is
required to run this against the offline mock provider.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.translation_providers import TranslationError, get_provider


def _safe_reason(message):
    # Defensively redact the key value if it ever appears, and cap length so no
    # large provider payload is echoed.
    key = settings.AIPEDIA_AZURE_TRANSLATOR_KEY
    text = str(message)
    if key and key in text:
        text = text.replace(key, "***")
    text = " ".join(text.split())
    return text[:300]


class Command(BaseCommand):
    help = "Verify the translation provider with one minimal request. Never prints the API key."

    def add_arguments(self, parser):
        parser.add_argument("--provider", default="azure", help="Provider to check: azure (default), mock, null.")
        parser.add_argument("--text", default="Hello", help="Short sample text to translate.")
        parser.add_argument("--to", default="fr", help="Target language for the sample.")

    def handle(self, *args, **options):
        provider_name = (options["provider"] or "azure").strip().lower()
        region = settings.AIPEDIA_AZURE_TRANSLATOR_REGION or "(unset)"
        endpoint = settings.AIPEDIA_AZURE_TRANSLATOR_ENDPOINT
        # Presence check only — never reveal the key, its length, or any part.
        if provider_name == "azure" and not settings.AIPEDIA_AZURE_TRANSLATOR_KEY:
            raise CommandError(
                f"FAIL: AIPEDIA_AZURE_TRANSLATOR_KEY is not set in the environment. "
                f"provider=azure region={region} endpoint={endpoint}"
            )
        try:
            provider = get_provider(provider_name)
            result = provider.translate(options["text"], options["to"], "en")
        except TranslationError as exc:
            raise CommandError(
                f"FAIL: provider={provider_name} region={region} reason={_safe_reason(exc)}"
            )
        except Exception as exc:  # noqa: BLE001 - report safely, never leak details
            raise CommandError(
                f"FAIL: provider={provider_name} region={region} reason={_safe_reason(exc)}"
            )
        if not (result and result.strip()):
            raise CommandError(
                f"FAIL: provider={provider_name} region={region} reason=empty translation result"
            )
        self.stdout.write(
            f"PASS: provider={provider_name} region={region} sample_to={options['to']} "
            f"result_chars={len(result)}"
        )

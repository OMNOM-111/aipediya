from .settings import *  # noqa: F403

# Test behavior is independent of any developer's optional diagnostics flag.
AIPEDIA_REQUEST_METRICS_ENABLED = False
MIDDLEWARE = [item for item in MIDDLEWARE if item != "catalog.observability.RequestMetricsMiddleware"]


# Tests render templates but must not depend on a locally collected production
# manifest. Production continues to use hashed WhiteNoise assets.
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# The test suite never calls a real translation provider, even if .env.local
# supplies an Azure key on the developer machine.
AIPEDIA_TRANSLATION_PROVIDER = "mock"
AIPEDIA_AZURE_TRANSLATOR_KEY = ""
AIPEDIA_AUTO_TRANSLATE = False

# Tests never send IndexNow requests; dispatcher tests inject a fake transport.
AIPEDIA_INDEXNOW_ENABLED = False
AIPEDIA_DATASETS_PUBLIC = True

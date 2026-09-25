import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_local_env(path):
    """Load KEY=VALUE lines from a local, git-ignored secret file (.env.local).

    Values already present in the real environment win, so the launcher and
    shell keep precedence. Secrets are read into the process environment only;
    they are never printed, logged, or returned.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # An empty or unset environment value is filled from .env.local; a real
        # non-empty value already in the environment keeps precedence.
        if key and value and not os.environ.get(key):
            os.environ[key] = value


_load_local_env(BASE_DIR / ".env.local")

AIPEDIA_ENV = os.environ.get("AIPEDIA_ENV", "local").strip().lower()
if AIPEDIA_ENV not in {"local", "production"}:
    raise RuntimeError("AIPEDIA_ENV must be local or production")
DEBUG = AIPEDIA_ENV == "local"
SECRET_KEY = os.environ.get("AIPEDIA_SECRET_KEY", "local-preview-only-not-for-production")
if AIPEDIA_ENV == "production" and (SECRET_KEY.startswith(("local-", "REPLACE_")) or len(SECRET_KEY) < 50):
    raise RuntimeError("Set a random AIPEDIA_SECRET_KEY of at least 50 characters")
if AIPEDIA_ENV == "production" and not os.environ.get("AIPEDIA_ALLOWED_HOSTS"):
    raise RuntimeError("Production requires AIPEDIA_ALLOWED_HOSTS")
ALLOWED_HOSTS = os.environ.get("AIPEDIA_ALLOWED_HOSTS", "127.0.0.1,localhost,[::1]").split(",")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "catalog.apps.CatalogConfig", "contributions",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "catalog.middleware.LanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "catalog.middleware.HeadersMiddleware",
]
ROOT_URLCONF = "aipedia.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"],
              "APP_DIRS": True, "OPTIONS": {"context_processors": [
                  "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
                  "django.contrib.messages.context_processors.messages", "catalog.context.site_context"]}}]
WSGI_APPLICATION = "aipedia.wsgi.application"
LOCAL_DB_ROOT = (BASE_DIR / "data" / "local").resolve()
if AIPEDIA_ENV == "local":
    default_db = LOCAL_DB_ROOT / "aipedia.sqlite3"
else:
    db_value = os.environ.get("AIPEDIA_DB")
    if not db_value:
        raise RuntimeError("Production requires AIPEDIA_DB")
    default_db = Path(db_value)
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                          "NAME": os.environ.get("AIPEDIA_DB", str(default_db)),
                          "OPTIONS": {"timeout": 20}}}
if AIPEDIA_ENV == "production":
    production_db = Path(DATABASES["default"]["NAME"]).resolve()
    try:
        production_db.relative_to(LOCAL_DB_ROOT)
    except ValueError:
        pass
    else:
        raise RuntimeError("Production must not use the Local SQLite")
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_COOKIE_NAME = "aipedia_session"
CSRF_COOKIE_NAME = "aipedia_csrf"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
if os.environ.get("AIPEDIA_TRUST_PROXY") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [x for x in os.environ.get("AIPEDIA_TRUSTED_ORIGINS", "").split(",") if x]
AIPEDIA_PUBLIC_ORIGIN = os.environ.get("AIPEDIA_PUBLIC_ORIGIN", "https://aipediya.com").rstrip("/")
# Only Production may be indexed. Local always answers robots "Disallow: /" and
# X-Robots-Tag noindex; production-mode SEO output is verified in isolated tests
# with override_settings, never by switching this on for Local.
AIPEDIA_INDEXING_ALLOWED = AIPEDIA_ENV == "production"
# Public dataset downloads stay off until the owner decides the data license
# (GSD-07 publication blocker). Local QA may enable them via the environment.
AIPEDIA_DATASETS_PUBLIC = os.environ.get("AIPEDIA_DATASETS_PUBLIC", "1" if AIPEDIA_ENV == "local" else "0") == "1"
# IndexNow: submissions happen only from the outbox dispatcher, only when this
# is explicitly enabled in Production. Local never sends.
AIPEDIA_INDEXNOW_ENABLED = AIPEDIA_ENV == "production" and os.environ.get("AIPEDIA_INDEXNOW_ENABLED", "0") == "1"
AIPEDIA_INDEXNOW_ENDPOINT = os.environ.get("AIPEDIA_INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow")
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
BING_SITE_VERIFICATION = os.environ.get("BING_SITE_VERIFICATION", "")
YANDEX_SITE_VERIFICATION = os.environ.get("YANDEX_SITE_VERIFICATION", "")
# Public Naver ownership token; this is verification metadata, not a secret.
NAVER_SITE_VERIFICATION = os.environ.get("NAVER_SITE_VERIFICATION", "") or (
    "9c99ee04834598097c2ba9b6a809819418e5d74d" if AIPEDIA_ENV == "production" else ""
)
AIPEDIA_ADS_ENABLED = os.environ.get("AIPEDIA_ADS_ENABLED", "0") == "1"
AIPEDIA_ADS_CLIENT = os.environ.get("AIPEDIA_ADS_CLIENT", "")
AIPEDIA_ADS_SLOT = os.environ.get("AIPEDIA_ADS_SLOT", "")
AIPEDIA_ADS_TXT = os.environ.get("AIPEDIA_ADS_TXT", "")
AIPEDIA_INDEXNOW_KEY = os.environ.get("AIPEDIA_INDEXNOW_KEY", "")
AIPEDIA_PRIVACY_CONTACT = os.environ.get("AIPEDIA_PRIVACY_CONTACT", "")
# Dynamic catalog translation pipeline. Provider is swappable; the API key is
# read only from the environment and never stored in code. "mock" needs no key
# and is the Local/test default. Endpoint and region are non-secret config.
AIPEDIA_TRANSLATION_PROVIDER = os.environ.get("AIPEDIA_TRANSLATION_PROVIDER", "mock").strip().lower()
AIPEDIA_AZURE_TRANSLATOR_KEY = os.environ.get("AIPEDIA_AZURE_TRANSLATOR_KEY", "")
AIPEDIA_AZURE_TRANSLATOR_ENDPOINT = os.environ.get(
    "AIPEDIA_AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com"
)
AIPEDIA_AZURE_TRANSLATOR_REGION = os.environ.get("AIPEDIA_AZURE_TRANSLATOR_REGION", "eastus2")
# Optional: translate a new/changed model or tool automatically right after it
# is saved. Off by default so bulk imports and tests never call the provider on
# the save path; enable only for interactive editing. Bulk data loads should run
# the translate_catalog command.
AIPEDIA_AUTO_TRANSLATE = os.environ.get("AIPEDIA_AUTO_TRANSLATE", "").strip().lower() in {"1", "true", "yes", "on"}

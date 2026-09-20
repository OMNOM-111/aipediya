import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("AIPEDIA_ENV", "local") == "local"
SECRET_KEY = os.environ.get("AIPEDIA_SECRET_KEY", "local-preview-only-not-for-production")
if not DEBUG and (SECRET_KEY.startswith(("local-", "REPLACE_")) or len(SECRET_KEY) < 50):
    raise RuntimeError("Set a random AIPEDIA_SECRET_KEY of at least 50 characters")
ALLOWED_HOSTS = os.environ.get("AIPEDIA_ALLOWED_HOSTS", "127.0.0.1,localhost,[::1]").split(",")
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "catalog.apps.CatalogConfig", "contributions",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
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
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                          "NAME": os.environ.get("AIPEDIA_DB", str(BASE_DIR / "data" / "aipedia.sqlite3")),
                          "OPTIONS": {"timeout": 20}}}
LANGUAGE_CODE = "ru"
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
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
BING_SITE_VERIFICATION = os.environ.get("BING_SITE_VERIFICATION", "")
YANDEX_SITE_VERIFICATION = os.environ.get("YANDEX_SITE_VERIFICATION", "")
AIPEDIA_ADS_ENABLED = os.environ.get("AIPEDIA_ADS_ENABLED", "0") == "1"
AIPEDIA_ADS_CLIENT = os.environ.get("AIPEDIA_ADS_CLIENT", "")
AIPEDIA_ADS_SLOT = os.environ.get("AIPEDIA_ADS_SLOT", "")
AIPEDIA_ADS_TXT = os.environ.get("AIPEDIA_ADS_TXT", "")
AIPEDIA_INDEXNOW_KEY = os.environ.get("AIPEDIA_INDEXNOW_KEY", "")
AIPEDIA_PRIVACY_CONTACT = os.environ.get("AIPEDIA_PRIVACY_CONTACT", "")

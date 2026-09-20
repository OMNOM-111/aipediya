from .settings import *  # noqa: F403


# Tests render templates but must not depend on a locally collected production
# manifest. Production continues to use hashed WhiteNoise assets.
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

from django.apps import AppConfig

class CatalogConfig(AppConfig):
    name = "catalog"
    verbose_name = "AIpediya"

    def ready(self):
        from . import signals  # noqa: F401

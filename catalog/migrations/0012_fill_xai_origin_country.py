from datetime import date

from django.db import migrations


def fill_xai_origin(apps, schema_editor):
    ModelOriginCountry = apps.get_model("catalog", "ModelOriginCountry")
    ModelVersion = apps.get_model("catalog", "ModelVersion")
    Source = apps.get_model("catalog", "Source")
    using = schema_editor.connection.alias
    source, _ = Source.objects.using(using).get_or_create(
        url="https://x.ai/company",
        defaults={"title": "xAI organization profile", "publisher": "xAI"},
    )
    for model in ModelVersion.objects.using(using).filter(
        entry_type="model", family__developer__name__startswith="SpaceXAI / xAI"
    ):
        ModelOriginCountry.objects.using(using).get_or_create(
            model=model,
            country_id="US",
            defaults={"source": source, "checked": date(2026, 9, 21), "position": 0},
        )


def reverse_fill_xai_origin(apps, schema_editor):
    ModelOriginCountry = apps.get_model("catalog", "ModelOriginCountry")
    using = schema_editor.connection.alias
    ModelOriginCountry.objects.using(using).filter(
        country_id="US", model__family__developer__name__startswith="SpaceXAI / xAI"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0011_split_models_tools")]

    operations = [migrations.RunPython(fill_xai_origin, reverse_fill_xai_origin)]

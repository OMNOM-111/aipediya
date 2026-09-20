from django.db import migrations, models


def assign_initial_numbers(apps, schema_editor):
    ModelVersion = apps.get_model("catalog", "ModelVersion")
    known = ModelVersion.objects.filter(published=True, released__isnull=False).order_by("released", "pk")
    unknown = ModelVersion.objects.filter(published=True, released__isnull=True).order_by("pk")
    for number, model in enumerate(list(known) + list(unknown), 1):
        model.public_number = number
        model.save(update_fields=["public_number"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_evaluation_public")]
    operations = [
        migrations.AddField(model_name="modelversion", name="public_number", field=models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True)),
        migrations.AddField(model_name="modelversion", name="catalog_status", field=models.CharField(choices=[("active", "Активна"), ("archived", "Архив")], default="active", max_length=10)),
        migrations.RunPython(assign_initial_numbers, migrations.RunPython.noop),
    ]

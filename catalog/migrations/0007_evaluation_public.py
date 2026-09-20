from django.db import migrations, models


def preserve_existing_visibility(apps, schema_editor):
    apps.get_model("catalog", "Evaluation").objects.update(public=True)


def restore_default_visibility(apps, schema_editor):
    # Reverse migration removes the column; no separate data rewrite is needed.
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_expand_offer_unit")]

    operations = [
        migrations.AddField(
            model_name="evaluation",
            name="public",
            field=models.BooleanField(
                default=False,
                help_text="Publish only after identity and source-reuse permission are verified.",
            ),
        ),
        migrations.RunPython(preserve_existing_visibility, restore_default_visibility),
    ]

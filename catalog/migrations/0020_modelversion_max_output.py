from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0019_catalog_master_aliases"),
    ]

    operations = [
        migrations.AddField(
            model_name="modelversion",
            name="max_output",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]

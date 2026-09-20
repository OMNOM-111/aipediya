from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0009_evaluation_observations')]
    operations = [migrations.AddField(model_name='modelversion', name='release_evidence',
                                     field=models.JSONField(default=dict, blank=True))]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_modelversion_research_entity_id_offer_billing_unit_and_more")]

    operations = [migrations.AlterField(
        model_name="offer",
        name="unit",
        field=models.CharField(
            choices=[("input", "1M входных токенов"), ("output", "1M выходных токенов"),
                     ("image", "изображение"), ("megapixel", "мегапиксель"), ("second", "секунда видео"),
                     ("minute", "минута аудио"), ("month", "месяц"), ("year", "год"), ("hour", "час"),
                     ("million_characters", "1M символов"), ("thousand_characters", "1000 символов"),
                     ("other", "единица из источника"), ("request", "запрос"), ("credit", "кредит"),
                     ("cache_read", "1M токенов чтения кэша"), ("cache_write", "1M токенов записи кэша")],
            max_length=24,
        ),
    )]

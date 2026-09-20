from django.db import migrations


def backfill_source_ids(apps, schema_editor):
    ResearchRecord = apps.get_model("catalog", "ResearchRecord")
    for record in ResearchRecord.objects.filter(source_record_id__isnull=True).iterator():
        payload = record.payload if isinstance(record.payload, dict) else {}
        item = payload.get("record") if isinstance(payload.get("record"), dict) else {}
        record_id = item.get("record_id")
        if isinstance(record_id, str) and record_id:
            record.source_record_id = record_id
            record.save(update_fields=["source_record_id"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_researchrecord_source_record_id_researchrevision")]
    operations = [migrations.RunPython(backfill_source_ids, migrations.RunPython.noop)]

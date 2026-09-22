from django.db import migrations


def normalize_generic_platforms(apps, schema_editor):
    Platform = apps.get_model("catalog", "Platform")
    Tool = apps.get_model("catalog", "Tool")
    ToolPlatform = apps.get_model("catalog", "ToolPlatform")
    using = schema_editor.connection.alias
    desktop, _ = Platform.objects.using(using).update_or_create(
        code="desktop", defaults={"labels": {"ru": "Desktop", "en": "Desktop"}, "position": 15}
    )
    mobile, _ = Platform.objects.using(using).update_or_create(
        code="mobile", defaults={"labels": {"ru": "Mobile", "en": "Mobile"}, "position": 18}
    )
    inferred_codes = {"windows", "macos", "linux", "ios", "android"}
    for tool in Tool.objects.using(using).select_related("legacy_version"):
        legacy = tool.legacy_version
        if not legacy:
            continue
        accesses = list(legacy.accesses.select_related("service", "source"))
        app_accesses = [item for item in accesses if item.service.kind in {"app", "download"}]
        if not app_accesses:
            continue
        ToolPlatform.objects.using(using).filter(
            tool=tool, platform__code__in=inferred_codes
        ).delete()
        for access in app_accesses:
            is_mobile = "mobile" in access.service.name.casefold()
            platform = mobile if is_mobile else desktop
            ToolPlatform.objects.using(using).get_or_create(
                tool=tool,
                platform=platform,
                defaults={"source": access.source, "checked": access.checked},
            )


def reverse_noop(apps, schema_editor):
    # Exact operating systems were not present in the source records, so a
    # reverse migration must not recreate inferred facts.
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0012_fill_xai_origin_country")]

    operations = [migrations.RunPython(normalize_generic_platforms, reverse_noop)]

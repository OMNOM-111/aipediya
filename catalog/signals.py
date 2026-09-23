import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from .models import ModelVersion, Offer, Evaluation, Fact, Access, Revision, Tool

TRACKED = (ModelVersion, Offer, Evaluation, Fact, Access)


@receiver(pre_save, sender=ModelVersion)
@receiver(pre_save, sender=Tool)
def invalidate_translations(sender, instance, raw=False, **kwargs):
    # A changed English source outdates its machine translations before the row
    # is written; this never calls a provider, so a save can't fail here.
    if raw:
        return
    from .translation_pipeline import invalidate_stale
    try:
        invalidate_stale(instance)
    except Exception:
        pass


@receiver(post_save, sender=ModelVersion)
@receiver(post_save, sender=Tool)
def auto_translate(sender, instance, raw=False, **kwargs):
    # Optional hook: localize a new or changed object right after it is saved so
    # future catalog data never needs a manual backfill. Disabled by default
    # (AIPEDIA_AUTO_TRANSLATE); bulk imports should run the translate_catalog
    # command instead. Runs after commit, off the request's critical path, and a
    # provider error is contained so it can neither break the save nor the site.
    from django.conf import settings
    if raw or getattr(instance, "_aipedia_translation_write", False):
        return
    if not getattr(settings, "AIPEDIA_AUTO_TRANSLATE", False):
        return
    from .translation_pipeline import translations_suppressed
    if translations_suppressed():
        return
    from django.db import transaction

    def _run():
        try:
            from .translation_providers import get_provider
            from .translation_pipeline import (
                load_translation_memory, prime_translation_memory, translate_object,
            )
            provider = get_provider()
            if provider.name == "null":
                return
            memory = load_translation_memory()
            prime_translation_memory([instance], provider, memory=memory)
            translate_object(instance, provider=provider, memory=memory)
        except Exception:
            pass

    transaction.on_commit(_run)

@receiver(post_save)
def record_save(sender, instance, created, raw=False, **kwargs):
    if raw or sender not in TRACKED:
        return
    # A machine-translation fill is not an editorial change; it has its own
    # audit trail in ContentTranslation, so it is kept out of the history log.
    if getattr(instance, "_aipedia_translation_write", False):
        return
    model_id = instance.pk if sender is ModelVersion else instance.model_id
    snapshot = json.loads(json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder))
    Revision.objects.create(model_id=model_id, entity=sender.__name__,
                            action="created" if created else "updated", snapshot=snapshot)

@receiver(pre_delete)
def record_delete(sender, instance, **kwargs):
    if sender not in TRACKED or sender is ModelVersion:
        return
    snapshot = json.loads(json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder))
    Revision.objects.create(model_id=instance.model_id, entity=sender.__name__, action="deleted", snapshot=snapshot)

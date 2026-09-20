import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import ModelVersion, Offer, Evaluation, Fact, Access, Revision

TRACKED = (ModelVersion, Offer, Evaluation, Fact, Access)

@receiver(post_save)
def record_save(sender, instance, created, raw=False, **kwargs):
    if raw or sender not in TRACKED:
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

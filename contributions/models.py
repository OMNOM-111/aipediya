from django.conf import settings
from django.db import models
from catalog.models import ModelVersion

class Contribution(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("rolled_back", "Rolled back")]
    kind = models.CharField(max_length=30)
    model = models.ForeignKey(ModelVersion, blank=True, null=True, on_delete=models.SET_NULL, related_name="contributions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)
    expected_hash = models.CharField(max_length=64, blank=True)
    source_url = models.URLField(max_length=600, blank=True)
    translation_only = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    decision_reason = models.TextField(blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name="+")
    decided_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        ordering = ["-created", "-pk"]

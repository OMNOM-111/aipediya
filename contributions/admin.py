from django.contrib import admin
from django.utils import timezone
from .models import Contribution

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ["kind", "model", "author", "status", "created", "decided_at"]
    list_filter = ["status", "kind", "translation_only"]
    readonly_fields = ["author", "created", "payload", "expected_hash", "source_url", "translation_only", "decided_by", "decided_at"]
    @admin.action(description="Approve selected proposals")
    def approve(self, request, queryset):
        queryset.filter(status="pending").update(status="approved", decided_by=request.user, decided_at=timezone.now())
    @admin.action(description="Reject selected proposals")
    def reject(self, request, queryset):
        queryset.filter(status="pending").update(status="rejected", decided_by=request.user, decided_at=timezone.now())
    actions = ["approve", "reject"]

from django.contrib import admin
from .models import (
    Access, AuditReport, Benchmark, Category, Country, ErrorReport, Evaluation,
    Fact, ModelFamily, ModelOriginCountry, ModelVersion, Offer, Organization,
    Platform, ResearchRecord, ResearchRevision, Revision, Service, Source, Tool,
    ToolModelSupport, ToolPlatform,
)

class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
class AccessInline(admin.TabularInline):
    model = Access
    extra = 0
class EvaluationInline(admin.TabularInline):
    model = Evaluation
    extra = 0
class FactInline(admin.TabularInline):
    model = Fact
    extra = 0
class ModelOriginCountryInline(admin.TabularInline):
    model = ModelOriginCountry
    extra = 0

@admin.register(ModelVersion)
class ModelAdmin(admin.ModelAdmin):
    list_display = ["name", "version", "category", "checked", "published"]
    list_filter = ["category", "published", "open_weights"]
    search_fields = ["name", "version", "family__developer__name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ModelOriginCountryInline, AccessInline, OfferInline, EvaluationInline, FactInline]

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "developer", "released", "published"]
    list_filter = ["category", "local_execution", "published"]
    search_fields = ["name", "developer__name", "ecosystem"]
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ["model", "created", "entity", "action"]
    readonly_fields = ["model", "created", "entity", "action", "snapshot"]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(ErrorReport)
class ErrorReportAdmin(admin.ModelAdmin):
    list_display = ["model", "created", "resolved"]
    list_filter = ["resolved"]
    readonly_fields = ["created"]

admin.site.register([Source, Organization, ModelFamily, Service, Benchmark])
admin.site.register([ResearchRecord, Category, AuditReport, Country, Platform])

@admin.register(ResearchRevision)
class ResearchRevisionAdmin(admin.ModelAdmin):
    list_display = ["record", "batch", "action", "created"]
    readonly_fields = ["record", "batch", "action", "before", "after", "created"]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
admin.site.site_header = "AIpediya · Редакция"
admin.site.site_title = "AIpediya"

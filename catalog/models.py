from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class Source(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=600, unique=True)
    publisher = models.CharField(max_length=120)
    def __str__(self):
        return self.title


class Organization(models.Model):
    name = models.CharField(max_length=120, unique=True)
    country = models.CharField(max_length=120, blank=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    def __str__(self):
        return self.name


class ModelFamily(models.Model):
    name = models.CharField(max_length=120)
    developer = models.ForeignKey(Organization, on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "developer"], name="unique_family")]
    def __str__(self):
        return self.name


class ModelVersion(models.Model):
    CATEGORIES = [("text", "Текст и код"), ("image", "Изображения"), ("video", "Видео"), ("audio", "Аудио"), ("other", "Другие")]
    family = models.ForeignKey(ModelFamily, on_delete=models.PROTECT)
    name = models.CharField(max_length=140)
    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=150)
    category = models.CharField(max_length=10, choices=CATEGORIES)
    tasks = models.JSONField(default=list, help_text='Task keys: coding, documents, reasoning, images, video, audio, translation')
    description = models.JSONField(default=dict, help_text='{"ru": "Описание", "en": "Description"}')
    suitable = models.JSONField(default=dict)
    limitations = models.JSONField(default=dict)
    origin = models.JSONField(default=dict, blank=True)
    philosophy = models.JSONField(default=dict, blank=True)
    context = models.PositiveIntegerField(null=True, blank=True)
    released = models.DateField(null=True, blank=True)
    release_evidence = models.JSONField(default=dict, blank=True)
    # Approximate public/release-evidence date used only when no exact date is
    # proven; precision is "month" or "day". Rendered with a ≈ prefix and never
    # presented as an exact release.
    approx_released = models.DateField(null=True, blank=True)
    approx_precision = models.CharField(max_length=5, blank=True, default="")
    approx_evidence = models.JSONField(default=dict, blank=True)
    # Public release stage shown next to the date: released (GA) shows no badge;
    # preview/beta/research are labelled. Empty means unspecified/GA.
    release_stage = models.CharField(
        max_length=10, blank=True, default="",
        choices=[("released", "Released"), ("preview", "Preview"), ("beta", "Beta"), ("research", "Research")],
    )
    license = models.CharField(max_length=200, blank=True)
    open_weights = models.BooleanField(default=False)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    published = models.BooleanField(default=True)
    public_number = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    catalog_status = models.CharField(
        max_length=12,
        default="active",
        choices=[
            ("active", "Активна"),
            ("deprecated", "Deprecated"),
            ("retired", "Снята"),
            ("archived", "Архив"),
        ],
    )
    entry_type = models.CharField(max_length=16, default="model", choices=[("model", "Модель"), ("product", "Продукт"), ("api_service", "API-сервис"), ("runtime", "Среда запуска")])
    input_modalities = models.JSONField(default=list, blank=True)
    output_modalities = models.JSONField(default=list, blank=True)
    translations_need_review = models.BooleanField(default=False)
    research_entity_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    # Catalog-master identity data: alternative names of this same entity
    # (searchable) and, for a hidden duplicate/alias row, the slug of the
    # canonical card its URL permanently redirects to.
    aliases = models.JSONField(default=list, blank=True)
    redirect_to = models.SlugField(blank=True, default="")
    class Meta:
        ordering = ["name"]
    def save(self, *args, **kwargs):
        # A public number is a permanent identity, assigned once and never
        # recomputed; refining a date/price/rating never changes it. Stable
        # slugs/pks preserve every URL.
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            if not self._state.adding:
                # Never write a stale in-memory number over the stored one.
                self.public_number = type(self).objects.using(using).values_list('public_number', flat=True).get(pk=self.pk)
            super().save(*args, **kwargs)
            if self.entry_type == 'model' and self.published and self.public_number is None:
                from .chronology import assign_catalog_numbers
                assign_catalog_numbers(using=using)
                self.public_number = type(self).objects.using(using).values_list('public_number', flat=True).get(pk=self.pk)
    def __str__(self):
        return self.name


class Country(models.Model):
    """Normalized model-origin country (ISO 3166-1 alpha-2)."""

    code = models.CharField(max_length=2, primary_key=True)
    name_ru = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80)

    class Meta:
        ordering = ["code"]

    def clean(self):
        self.code = self.code.upper()
        if len(self.code) != 2 or not self.code.isalpha():
            raise ValidationError("Country code must be ISO 3166-1 alpha-2.")

    def __str__(self):
        return self.code


class ModelOriginCountry(models.Model):
    model = models.ForeignKey(
        ModelVersion, related_name="origin_country_links", on_delete=models.CASCADE
    )
    country = models.ForeignKey(Country, related_name="model_links", on_delete=models.PROTECT)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "country__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["model", "country"], name="unique_model_origin_country"
            )
        ]


class Platform(models.Model):
    code = models.SlugField(unique=True)
    labels = models.JSONField(default=dict)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "code"]

    def __str__(self):
        return self.labels.get("en") or self.code


class Tool(models.Model):
    CATEGORIES = [
        ("ai_app", "AI-приложение"),
        ("coding_assistant", "Coding assistant"),
        ("coding_agent", "Coding agent"),
        ("runtime", "Runtime"),
        ("api_platform", "API-платформа"),
        ("api_service", "API-сервис"),
        ("ide_tool", "IDE-инструмент"),
        ("client", "Клиент / интерфейс"),
        ("agent_platform", "Agent platform"),
        ("creative_app", "Творческое AI-приложение"),
    ]
    LOCAL_EXECUTION = [
        ("yes", "Да"),
        ("no", "Нет"),
        ("hybrid", "Гибрид"),
    ]
    STATUSES = ModelVersion._meta.get_field("catalog_status").choices

    # Existing ModelVersion rows are retained for pricing/access/history. The
    # public Tools catalogue queries this table, not the legacy universal one.
    legacy_version = models.OneToOneField(
        ModelVersion,
        related_name="tool_record",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=140)
    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=150, blank=True)
    developer = models.ForeignKey(Organization, related_name="tools", on_delete=models.PROTECT)
    category = models.CharField(max_length=24, choices=CATEGORIES)
    purposes = models.JSONField(default=list, blank=True)
    description = models.JSONField(default=dict, blank=True)
    ecosystem = models.JSONField(default=dict, blank=True)
    local_execution = models.CharField(max_length=8, choices=LOCAL_EXECUTION, blank=True)
    official_url = models.URLField(max_length=600, blank=True)
    released = models.DateField(null=True, blank=True)
    release_evidence = models.JSONField(default=dict, blank=True)
    approx_released = models.DateField(null=True, blank=True)
    approx_precision = models.CharField(max_length=5, blank=True, default="")
    approx_evidence = models.JSONField(default=dict, blank=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    published = models.BooleanField(default=True)
    public_number = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    catalog_status = models.CharField(max_length=12, default="active", choices=STATUSES)
    platforms = models.ManyToManyField(Platform, through="ToolPlatform", related_name="tools")
    supported_models = models.ManyToManyField(
        ModelVersion, through="ToolModelSupport", related_name="supported_by_tools"
    )
    aliases = models.JSONField(default=list, blank=True)
    redirect_to = models.SlugField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or self._state.db or "default"
        with transaction.atomic(using=using):
            if not self._state.adding:
                self.public_number = type(self).objects.using(using).values_list(
                    "public_number", flat=True
                ).get(pk=self.pk)
            super().save(*args, **kwargs)
            if self.published and self.public_number is None:
                from .chronology import assign_tool_numbers

                assign_tool_numbers(using=using)
                self.public_number = type(self).objects.using(using).values_list(
                    "public_number", flat=True
                ).get(pk=self.pk)

    def __str__(self):
        return self.name


class ToolPlatform(models.Model):
    tool = models.ForeignKey(Tool, related_name="platform_links", on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()

    class Meta:
        ordering = ["platform__position", "platform__code"]
        constraints = [
            models.UniqueConstraint(fields=["tool", "platform"], name="unique_tool_platform")
        ]


class ToolModelSupport(models.Model):
    tool = models.ForeignKey(Tool, related_name="model_links", on_delete=models.CASCADE)
    model = models.ForeignKey(ModelVersion, on_delete=models.PROTECT)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    note = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tool", "model"], name="unique_tool_model_support")
        ]


class ToolPublicationRevision(models.Model):
    tool = models.ForeignKey(Tool, related_name="publication_revisions", on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-pk"]


class Service(models.Model):
    name = models.CharField(max_length=150)
    provider = models.ForeignKey(Organization, on_delete=models.PROTECT)
    kind = models.CharField(max_length=10, choices=[("api", "API"), ("web", "Сайт"), ("download", "Локально"), ("app", "Приложение"), ("cli", "CLI"), ("ide", "Расширение IDE")])
    url = models.URLField(max_length=600)
    compute_location = models.CharField(max_length=10, blank=True, choices=[("local", "Устройство"), ("cloud", "Облако"), ("hybrid", "Гибрид")])
    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"


class Access(models.Model):
    model = models.ForeignKey(ModelVersion, related_name="accesses", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=["model", "service"], name="unique_access")]


class Offer(models.Model):
    UNITS = [("input", "1M входных токенов"), ("output", "1M выходных токенов"),
             ("image", "изображение"), ("megapixel", "мегапиксель"), ("second", "секунда видео"), ("minute", "минута аудио"), ("month", "месяц"),
             ("year", "год"), ("hour", "час"), ("million_characters", "1M символов"), ("thousand_characters", "1000 символов"), ("other", "единица из источника"), ("request", "запрос"), ("credit", "кредит"), ("cache_read", "1M токенов чтения кэша"), ("cache_write", "1M токенов записи кэша")]
    model = models.ForeignKey(ModelVersion, related_name="offers", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=8, null=True, blank=True, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=24, choices=UNITS)
    conditions = models.JSONField(default=dict)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    active = models.BooleanField(default=True)
    primary = models.BooleanField(default=False, help_text="Display in the catalog; select one coherent provider/tier.")
    research_key = models.CharField(max_length=120, unique=True, null=True, blank=True)
    billing_unit = models.CharField(max_length=180, blank=True)
    class Meta:
        ordering = ["unit", "amount", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0), name="positive_price")]
    @property
    def stale(self):
        return self.checked < timezone.localdate() - timedelta(days=30)
    def clean(self):
        if self.service_id and self.unit in {"month", "year"} and self.service.kind not in {"web", "app", "cli", "ide"}:
            raise ValidationError("Monthly subscriptions must belong to a user-facing service.")
        if self.service_id and self.unit not in {"month", "year"} and self.service.kind != "api":
            raise ValidationError("Usage pricing must belong to an API provider.")
        if not self.conditions or not self.conditions.get("ru"):
            raise ValidationError("Specify pricing conditions in Russian.")


class Benchmark(models.Model):
    name = models.CharField(max_length=150)
    protocol = models.CharField(max_length=250)
    category = models.CharField(max_length=10, choices=ModelVersion.CATEGORIES)
    unit = models.CharField(max_length=40, default="%")
    higher_is_better = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "protocol"], name="unique_protocol")]
    def __str__(self):
        return f"{self.name} · {self.protocol}"


class Evaluation(models.Model):
    model = models.ForeignKey(ModelVersion, related_name="evaluations", on_delete=models.CASCADE)
    benchmark = models.ForeignKey(Benchmark, on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=12, decimal_places=3)
    evaluator = models.CharField(max_length=140)
    independent = models.BooleanField(default=False)
    public = models.BooleanField(default=False, help_text="Publish only after identity and source-reuse permission are verified.")
    measured = models.DateField(null=True, blank=True)
    conditions = models.JSONField(default=dict)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    observation_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    configuration = models.CharField(max_length=250, blank=True)
    source_model = models.CharField(max_length=250, blank=True)
    source_record_id = models.CharField(max_length=250, blank=True)
    snapshot = models.CharField(max_length=80, blank=True)
    source_sha256 = models.CharField(max_length=64, blank=True)
    result_kind = models.CharField(max_length=20, default="independent", choices=[
        ("independent", "Independent run"), ("composite", "Composite index"),
        ("developer", "Developer-reported"), ("preference", "User preferences")])
    confidence_low = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    confidence_high = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    class Meta:
        ordering = ["benchmark__name", "configuration", "-checked", "pk"]
    def clean(self):
        if (self.model_id and self.benchmark_id and self.model.category != self.benchmark.category
                and not (self.benchmark.category == "text" and ("text" in self.model.output_modalities
                    or any(task in self.model.tasks for task in ("text", "code", "coding", "reasoning"))))):
            raise ValidationError("Benchmark category must match the model.")


class Fact(models.Model):
    KEYS = [("modalities", "Форматы"), ("languages", "Языки"), ("speed", "Скорость"),
            ("memory", "Память и оборудование"), ("energy", "Энергопотребление"),
            ("training", "Обучение"), ("ownership", "Владение и финансирование"), ("service_price", "Цена сервиса")]
    model = models.ForeignKey(ModelVersion, related_name="facts", on_delete=models.CASCADE)
    key = models.CharField(max_length=25, choices=KEYS)
    value = models.JSONField(default=dict)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=["model", "key"], name="unique_fact")]


class Revision(models.Model):
    model = models.ForeignKey(ModelVersion, related_name="revisions", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    entity = models.CharField(max_length=80)
    action = models.CharField(max_length=20)
    snapshot = models.JSONField()
    class Meta:
        ordering = ["-created", "-pk"]


class ErrorReport(models.Model):
    model = models.ForeignKey(ModelVersion, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField(max_length=3000)
    created = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


class ResearchRecord(models.Model):
    external_id = models.CharField(max_length=200, unique=True)
    source_record_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    batch = models.CharField(max_length=200)
    payload = models.JSONField()
    state = models.CharField(max_length=20, default="review_required", choices=[("review_required", "Требует проверки"), ("accepted", "Принято"), ("rejected", "Отклонено")])
    review_reason = models.CharField(max_length=300, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)


class ResearchRevision(models.Model):
    record = models.ForeignKey(ResearchRecord, on_delete=models.CASCADE, related_name="revisions")
    batch = models.CharField(max_length=200)
    action = models.CharField(max_length=20)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-pk"]


class PublicationRevision(models.Model):
    entity_id = models.CharField(max_length=80)
    model = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="publication_revisions")
    action = models.CharField(max_length=30)
    source_record_ids = models.JSONField(default=list)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-pk"]


class Category(models.Model):
    code = models.SlugField(unique=True)
    labels = models.JSONField(default=dict)
    position = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["position", "code"]
    def __str__(self):
        return self.labels.get("ru", self.code)


class AuditReport(models.Model):
    model = models.ForeignKey(ModelVersion, related_name="audits", on_delete=models.CASCADE)
    auditor = models.CharField(max_length=180)
    scope = models.JSONField(default=dict)
    version = models.CharField(max_length=150)
    period = models.CharField(max_length=150, blank=True)
    method = models.JSONField(default=dict)
    conclusions = models.JSONField(default=dict)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()


class ContentTranslation(models.Model):
    """Machine or reviewed translation of one localizable catalog field.

    English stays the canonical source and is never stored here. Each row is
    bound to the sha-256 hash of the English source text; when the source
    changes the hash no longer matches, the row becomes ``outdated`` and the
    site falls back to English until a fresh translation is produced.
    """

    STATES = [
        ("current", "Current"),
        ("outdated", "Outdated"),
        ("missing", "Missing"),
        ("reviewed", "Reviewed"),
    ]
    entity_type = models.CharField(max_length=20)
    object_id = models.PositiveIntegerField()
    field = models.CharField(max_length=40)
    language = models.CharField(max_length=12)
    source_hash = models.CharField(max_length=64)
    text = models.TextField(blank=True)
    state = models.CharField(max_length=12, default="missing", choices=STATES)
    provider = models.CharField(max_length=40, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "object_id", "field", "language"],
                name="unique_content_translation",
            )
        ]
        indexes = [
            models.Index(fields=["entity_type", "object_id"]),
            models.Index(fields=["state"]),
        ]

    def __str__(self):
        return f"{self.entity_type}:{self.object_id}:{self.field}:{self.language} ({self.state})"


class DiscoveryEvent(models.Model):
    """Outbox of public-URL changes for search-engine notification (IndexNow).

    Written by model signals when a public record is created, significantly
    updated, unpublished/removed, or when one locale's translation changes.
    Reading a page never writes here. ``indexnow_dispatch`` sends pending rows
    only in Production with IndexNow explicitly enabled, after checking that
    the Production state is live; Local only records and dry-runs.
    """

    UPSERT = "upsert"
    REMOVE = "remove"
    STATES = [("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed"), ("skipped", "Skipped")]

    url = models.URLField(max_length=600)
    lang = models.CharField(max_length=12, blank=True)
    entity_kind = models.CharField(max_length=12, blank=True)
    record_id = models.CharField(max_length=120, blank=True)
    action = models.CharField(max_length=10, choices=[(UPSERT, "Created or updated"), (REMOVE, "Removed")])
    reason = models.CharField(max_length=40)
    state = models.CharField(max_length=10, choices=STATES, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt = models.DateTimeField(null=True, blank=True)
    last_status = models.PositiveSmallIntegerField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created", "pk"]
        indexes = [models.Index(fields=["state", "next_attempt"])]
        constraints = [
            # Dedup: at most one pending notification per URL; a newer change
            # updates the pending row instead of adding another.
            models.UniqueConstraint(fields=["url"], condition=models.Q(state="pending"),
                                    name="one_pending_event_per_url"),
        ]

    def __str__(self):
        return f"{self.action} {self.url} ({self.state})"

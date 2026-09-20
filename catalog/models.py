from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max
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
    license = models.CharField(max_length=200, blank=True)
    open_weights = models.BooleanField(default=False)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    checked = models.DateField()
    published = models.BooleanField(default=True)
    public_number = models.PositiveIntegerField(null=True, blank=True, unique=True, db_index=True)
    catalog_status = models.CharField(
        max_length=10, default="active", choices=[("active", "Активна"), ("archived", "Архив")]
    )
    entry_type = models.CharField(max_length=16, default="model", choices=[("model", "Модель"), ("product", "Продукт"), ("api_service", "API-сервис"), ("runtime", "Среда запуска")])
    input_modalities = models.JSONField(default=list, blank=True)
    output_modalities = models.JSONField(default=list, blank=True)
    translations_need_review = models.BooleanField(default=False)
    research_entity_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    class Meta:
        ordering = ["name"]
    def save(self, *args, **kwargs):
        # Permanent public numbers are assigned once and never recycled.
        if self._state.adding and self.published and self.public_number is None:
            self.public_number = (ModelVersion.objects.aggregate(last=Max("public_number"))["last"] or 0) + 1
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name


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

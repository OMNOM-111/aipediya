"""Event-driven discovery outbox (GSD-08).

Model signals call :func:`record_entity_change` / :func:`record_translation_change`;
nothing here runs on a page view. Each call writes at most one pending
``DiscoveryEvent`` per URL (a newer change updates the pending row), so
repeated saves are deduplicated and re-running is idempotent.

URLs:
* create / significant update of a public record -> ``upsert`` for every
  locale that is indexable *now*;
* unpublish / delete -> ``remove`` for every locale URL that was indexable
  *before* the change (computed from the stored row before the save), so a
  removal is never lost because the record is no longer indexable;
* translation change -> ``upsert`` for that one locale URL only.
"""
import hashlib
import json
from contextlib import contextmanager
from threading import local
from urllib.parse import urlsplit

from django.conf import settings
from django.db import IntegrityError, transaction

from .locale_urls import absolute

_state = local()

# Fields whose change is significant for a public card (visible facts).
SIGNIFICANT_MODEL_FIELDS = (
    "name", "version", "slug", "description", "suitable", "limitations", "released", "approx_released",
    "approx_precision", "context", "catalog_status", "open_weights", "license", "category", "tasks",
    "input_modalities", "output_modalities", "published", "entry_type",
)
SIGNIFICANT_TOOL_FIELDS = (
    "name", "version", "slug", "description", "released", "approx_released", "approx_precision",
    "catalog_status", "category", "purposes", "local_execution", "official_url", "published",
)


def capture_enabled():
    return getattr(settings, "AIPEDIA_DISCOVERY_CAPTURE", True) and not getattr(_state, "suppressed", False)


@contextmanager
def suppress_capture():
    """For bulk maintenance that must not enqueue notifications."""
    previous = getattr(_state, "suppressed", False)
    _state.suppressed = True
    try:
        yield
    finally:
        _state.suppressed = previous


def entity_path(kind, slug):
    return f"/{'tools' if kind == 'tool' else 'models'}/{slug}"


def fingerprint(obj):
    from .models import Tool
    fields = SIGNIFICANT_TOOL_FIELDS if isinstance(obj, Tool) else SIGNIFICANT_MODEL_FIELDS
    data = {field: getattr(obj, field, None) for field in fields}
    raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def snapshot(obj):
    """State of the stored row before a save: (public?, slug, ready locales, fingerprint)."""
    from . import readiness
    from .models import Tool

    if not obj.pk:
        return None
    model = type(obj)
    try:
        stored = model.objects.get(pk=obj.pk)
    except model.DoesNotExist:
        return None
    kind = "tool" if isinstance(obj, Tool) else "model"
    public = readiness._is_public(stored)
    return {
        "kind": kind,
        "slug": stored.slug,
        "public": public,
        "ready": readiness.ready_locales(stored) if public else [],
        "fingerprint": fingerprint(stored),
    }


def enqueue(neutral_path, lang, action, reason, kind="", record_id=""):
    """Create or refresh the single pending event for one URL."""
    from django.utils import timezone

    from .models import DiscoveryEvent

    url = absolute(neutral_path, lang)
    defaults = {"lang": lang, "entity_kind": kind, "record_id": record_id, "action": action,
                "reason": reason, "attempts": 0, "next_attempt": timezone.now(), "last_error": ""}
    with transaction.atomic():
        updated = DiscoveryEvent.objects.filter(url=url, state="pending").update(**defaults)
        if updated:
            return
        try:
            with transaction.atomic():
                DiscoveryEvent.objects.create(url=url, state="pending", **defaults)
        except IntegrityError:
            DiscoveryEvent.objects.filter(url=url, state="pending").update(**defaults)


def record_entity_change(obj, before, created=False, deleted=False):
    from . import readiness
    from .models import Tool

    if not capture_enabled():
        return
    kind = "tool" if isinstance(obj, Tool) else "model"
    now_public = (not deleted) and readiness._is_public(obj)
    now_ready = readiness.ready_locales(obj) if now_public else []
    was_ready = before["ready"] if before else []
    old_slug = before["slug"] if before else obj.slug
    if before and before["public"] and (not now_public or old_slug != obj.slug):
        for lang in was_ready:
            enqueue(entity_path(kind, old_slug), lang, "remove",
                    "deleted" if deleted else ("unpublished" if not now_public else "slug-changed"),
                    kind, old_slug)
    if not now_public:
        return
    if created or not before or not before["public"] or old_slug != obj.slug:
        reason = "created" if created else "published"
        langs = now_ready
    elif before["fingerprint"] != fingerprint(obj):
        reason = "updated"
        langs = now_ready
        # Locales that stopped being indexable get a removal-style signal too.
        for lang in set(was_ready) - set(now_ready):
            enqueue(entity_path(kind, obj.slug), lang, "remove", "locale-not-ready", kind, obj.slug)
    else:
        return
    for lang in langs:
        enqueue(entity_path(kind, obj.slug), lang, "upsert", reason, kind, obj.slug)


def record_related_change(model_version, reason):
    """A price, access, fact or evaluation of a public record changed."""
    from . import readiness
    from .models import Tool

    if not capture_enabled() or model_version is None:
        return
    targets = []
    if readiness._is_public(model_version):
        targets.append(("model", model_version))
    tool = Tool.objects.filter(legacy_version=model_version, published=True).first()
    if tool is not None:
        targets.append(("tool", tool))
    for kind, obj in targets:
        for lang in readiness.ready_locales(obj):
            enqueue(entity_path(kind, obj.slug), lang, "upsert", reason, kind, obj.slug)


def record_translation_change(translation):
    """Only the affected locale URL of the affected record is notified."""
    from . import readiness
    from .models import ModelVersion, Tool

    if not capture_enabled():
        return
    model = Tool if translation.entity_type == "tool" else ModelVersion
    obj = model.objects.filter(pk=translation.object_id).first()
    if obj is None or not readiness._is_public(obj):
        return
    result = readiness.entity_readiness(obj).get(translation.language)
    if result is not None and result.indexable:
        kind = "tool" if model is Tool else "model"
        enqueue(entity_path(kind, obj.slug), translation.language, "upsert", "translation", kind, obj.slug)


def allowed_host(url):
    origin = urlsplit(settings.AIPEDIA_PUBLIC_ORIGIN)
    parts = urlsplit(url)
    return parts.scheme == origin.scheme and parts.netloc == origin.netloc


def outbox_status():
    """Operational view of the IndexNow outbox (read-only).

    Separates work that still needs attention from history:
    * ``active_pending`` - pending and never attempted;
    * ``active_retry`` - pending with at least one failed attempt (backoff);
    * ``failed_unresolved`` - failed rows whose URL has no later accepted send
      (these URLs were really not delivered);
    * ``failed_resolved_historical`` - failed attempts whose URL was accepted by a
      later send; kept as audit history, not undelivered URLs.
    Acceptance by IndexNow is not indexing.
    """
    from django.db.models import Max

    from .models import DiscoveryEvent

    last_sent = dict(
        DiscoveryEvent.objects.filter(state="sent").order_by().values_list("url").annotate(last=Max("pk"))
    )
    failed = DiscoveryEvent.objects.filter(state="failed").values_list("pk", "url")
    resolved = sum(1 for pk, url in failed if last_sent.get(url, 0) > pk)
    failed_total = DiscoveryEvent.objects.filter(state="failed").count()
    pending = DiscoveryEvent.objects.filter(state="pending")
    sent = DiscoveryEvent.objects.filter(state="sent")
    return {
        "active_pending": pending.filter(attempts=0).count(),
        "active_retry": pending.filter(attempts__gt=0).count(),
        "sent_events": sent.count(),
        "urls_accepted": len(last_sent),
        "failed_unresolved": failed_total - resolved,
        "failed_resolved_historical": resolved,
        "skipped": DiscoveryEvent.objects.filter(state="skipped").count(),
        "last_sent_at": sent.aggregate(last=Max("sent_at"))["last"],
        "sending_enabled": bool(getattr(settings, "AIPEDIA_INDEXNOW_ENABLED", False)),
        "note": "accepted by IndexNow is not indexed; failed_resolved_historical are superseded attempts",
    }

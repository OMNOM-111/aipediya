"""Catalog freshness snapshot derived from real catalog release plans."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings
from django.utils import timezone as django_timezone


SCHEMA = "aipedia-catalog-freshness/1"


def snapshot_path():
    value = getattr(settings, "AIPEDIA_CATALOG_FRESHNESS_PATH", settings.BASE_DIR / "data" / "catalog_freshness.json")
    if not value:
        return None
    return Path(value)


def utc_stamp(value=None):
    value = value or django_timezone.now()
    if isinstance(value, str):
        return value if value.endswith("Z") else value.replace("+00:00", "Z")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


# Plan operations that change what an existing public card shows. Chronology
# renumbering ("number") and shared-object metadata (service provider,
# benchmark category) are not an update of one card; master-only Facts never
# reach the plan.
RELATION_KINDS = {"platforms", "offer", "offer_new", "access_new", "access_service", "origin_new",
                  "evaluation", "evaluation_new", "reassign", "org_country"}


def _legacy_tool_slug(slug):
    try:
        from .models import Tool
        return Tool.objects.filter(legacy_version__slug=slug).values_list("slug", flat=True).first()
    except Exception:  # no database (e.g. a plan read offline)
        return None


def _change_owner(change):
    """(record_type, record_id) of the existing public card a change updates."""
    kind = change.get("kind")
    sheet = change.get("sheet")
    if kind in {"update", "platforms"} and sheet in {"Models", "Tools"}:
        return ("model" if sheet == "Models" else "tool", change.get("id", ""))
    if kind == "org_country":
        return ("tool" if sheet == "Tools" else "model", change.get("record", ""))
    owner = (change.get("after") or {}).get("owner") if kind == "reassign" else change.get("owner")
    if owner and ":" in owner:
        record_type, _sep, record_id = owner.partition(":")
        return (record_type, record_id)
    slug = (change.get("identity") or {}).get("model") or ((change.get("locator") or {}).get("access") or {}).get("model")
    if slug:
        tool = _legacy_tool_slug(slug)
        return ("tool", tool) if tool else ("model", slug)
    return None


def snapshot_from_plan(plan, updated_at_utc=None, rows=None):
    """ADD/UPD snapshot of one real catalog update.

    ``added``: a new catalog record. ``updated``: an existing public card whose
    own fields or supported related rows (platforms, prices, access, origin
    countries, evaluations) changed. It never claims that a product was
    released now: release recency is :func:`is_recent_release`.
    """
    names = {}
    for sheet, record_type in (("Models", "model"), ("Tools", "tool")):
        for row in (rows or {}).get(sheet, []):
            names[(record_type, row.get("Record ID"))] = row.get("Name") or ""
    entries, seen = [], {}
    for change in plan.get("changes", []):
        kind = change.get("kind")
        if kind == "create" and change.get("sheet") in {"Models", "Tools"}:
            key = ("model" if change["sheet"] == "Models" else "tool", change.get("id", ""))
            row = change.get("row") or {}
            exact_date = row.get("Exact Release Date") or ""
            approx_date = str(row.get("Approx Date") or "").lstrip("\u2248").strip()
            item = {
                "record_type": key[0], "action": "added", "record_id": key[1],
                "name": row.get("Name") or change.get("name") or key[1],
                "release_date": exact_date or approx_date,
                "release_date_approx": not bool(exact_date) and bool(approx_date),
                "release_date_precision": row.get("Approx Precision") or ("day" if exact_date else ""),
            }
        elif kind == "update" or kind in RELATION_KINDS:
            key = _change_owner(change)
            if not key or not key[1]:
                continue
            row = change.get("row") if kind == "update" else None
            item = {
                "record_type": key[0], "action": "updated", "record_id": key[1],
                "name": names.get(key) or (row or {}).get("Name") or change.get("name") or key[1],
                "release_date": "", "release_date_approx": False, "release_date_precision": "",
            }
        else:
            continue
        if key in seen:
            if seen[key]["action"] == "updated" and item["action"] == "added":
                seen[key].update(item)
            continue
        seen[key] = item
        entries.append(item)
    counts = {
        "added_models": sum(1 for item in entries if item["record_type"] == "model" and item["action"] == "added"),
        "added_tools": sum(1 for item in entries if item["record_type"] == "tool" and item["action"] == "added"),
        "updated_models": sum(1 for item in entries if item["record_type"] == "model" and item["action"] == "updated"),
        "updated_tools": sum(1 for item in entries if item["record_type"] == "tool" and item["action"] == "updated"),
    }
    counts["updated_records"] = counts["updated_models"] + counts["updated_tools"]
    return {
        "schema": SCHEMA,
        "release": plan.get("release", ""),
        "updated_at_utc": utc_stamp(updated_at_utc),
        "counts": counts,
        "entries": entries,
    }


def release_today(now=None):
    now = now or django_timezone.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).date()


def is_recent_release(released, today=None):
    """The one predicate for the row NEW badge and the recent-releases list.

    The catalog stores confirmed release *dates* (no times), so a release counts
    as recent when its exact date is today or yesterday in UTC. Approximate
    dates never qualify, and the date AIpediya added a record is never used.
    """
    if not released:
        return False
    today = today or release_today()
    return 0 <= (today - released).days <= 1


def recent_releases(today=None):
    """Published Models and Tools whose confirmed release date is recent."""
    from .models import ModelVersion, Tool
    today = today or release_today()
    window = (today - timedelta(days=1), today)
    out = []
    for record_type, qs in (
            ("model", ModelVersion.objects.filter(published=True, entry_type="model", released__range=window)),
            ("tool", Tool.objects.filter(published=True, released__range=window))):
        for obj in qs.order_by("-released", "name").only("slug", "name", "released"):
            out.append({"record_type": record_type, "record_id": obj.slug, "name": obj.name,
                        "release_date": obj.released.isoformat(), "release_date_approx": False,
                        "release_date_precision": "day"})
    return out


def write_snapshot(snapshot, path=None):
    path = Path(path) if path else snapshot_path()
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_plan_snapshot(plan, updated_at_utc=None, path=None):
    snapshot = plan.get("catalog_update") or snapshot_from_plan(plan, updated_at_utc)
    if updated_at_utc is not None:
        snapshot = {**snapshot, "updated_at_utc": utc_stamp(updated_at_utc)}
    write_snapshot(snapshot, path)
    return snapshot


def load_snapshot(path=None):
    path = Path(path) if path else snapshot_path()
    if path is None or not path.exists():
        return None
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema") != SCHEMA:
        return None
    return snapshot


def _parse_stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _plural_ru(value, one, few, many):
    if value % 10 == 1 and value % 100 != 11:
        return one
    if value % 10 in {2, 3, 4} and value % 100 not in {12, 13, 14}:
        return few
    return many


def relative_label(updated_at, lang, now=None):
    now = now or django_timezone.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    seconds = max(0, int((now.astimezone(timezone.utc) - updated_at).total_seconds()))
    minutes = seconds // 60
    if lang == "ru":
        if minutes < 1:
            return "только что"
        if minutes < 60:
            return f"{minutes} мин назад"
        hours, mins = divmod(minutes, 60)
        if hours < 24:
            return f"{hours} ч {mins} мин назад" if mins else f"{hours} ч назад"
        days = hours // 24
        return f"{days} {_plural_ru(days, 'день', 'дня', 'дней')} назад"
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours, mins = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {mins}m ago" if mins else f"{hours}h ago"
    days = hours // 24
    return f"{days} day ago" if days == 1 else f"{days} days ago"


def _release_date_label(item, lang):
    value = item.get("release_date") or ""
    if not value:
        return ""
    precision = item.get("release_date_precision") or "day"
    approximate = item.get("release_date_approx")
    months_ru = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = value.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
    except (TypeError, ValueError, IndexError):
        return ("≈" if approximate else "") + value
    names = months_ru if lang == "ru" else months_en
    prefix = "≈" if approximate else ""
    if precision == "year" or len(parts) == 1:
        return f"{prefix}{year}"
    if precision == "month" or len(parts) == 2:
        return f"{prefix}{names[month - 1]} {year}" if lang != "ru" else f"{prefix}{months_ru[month - 1]} {year}"
    return f"{prefix}{day} {months_ru[month - 1]} {year}" if lang == "ru" else f"{prefix}{names[month - 1]} {day}, {year}"


def context(lang):
    snapshot = load_snapshot()
    if not snapshot:
        return None
    from .context import t

    updated_at = _parse_stamp(snapshot["updated_at_utc"])
    age_seconds = max(0, int((django_timezone.now().astimezone(timezone.utc) - updated_at).total_seconds()))
    if age_seconds < 24 * 3600:
        state = "accent"
        status = t("catalog_freshness_accent", lang)
    elif age_seconds <= 3 * 24 * 3600:
        state = "neutral"
        status = t("catalog_freshness_neutral", lang)
    else:
        state = "amber"
        status = t("catalog_freshness_amber", lang)
    exact = updated_at.strftime("%d.%m.%Y %H:%M UTC") if lang == "ru" else updated_at.strftime("%Y-%m-%d %H:%M UTC")
    entries = []
    for item in snapshot.get("entries", []):
        action = item.get("action")
        entries.append({
            **item,
            "badge": "ADD" if action == "added" else "UPD",
            "action_label": t("catalog_action_added", lang) if action == "added" else t("catalog_action_updated", lang),
            "release_date_label": _release_date_label(item, lang),
        })
    counts = snapshot.get("counts", {})
    recent = [{**item, "release_date_label": _release_date_label(item, lang)} for item in recent_releases()]
    relative = relative_label(updated_at, lang)
    aria = (f"{t('catalog_latest_update', lang)}. {t('catalog_updated', lang)} {relative}")
    return {
        "release": snapshot.get("release", ""),
        "updated_at_utc": snapshot["updated_at_utc"],
        "date_iso": updated_at.date().isoformat(),
        "date_label": exact,
        "relative_label": relative,
        "state": state,
        "status": status,
        "counts": counts,
        "entries": entries,
        "model_entries": [item for item in entries if item.get("record_type") == "model"],
        "tool_entries": [item for item in entries if item.get("record_type") == "tool"],
        "recent_releases": recent,
        "aria_label": aria,
    }

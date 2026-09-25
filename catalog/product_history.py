"""Local-only view of the existing product timeline and its checked sources."""
import json
import subprocess
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


ROOT = Path(settings.BASE_DIR)
SOURCES = {
    "execution-state": ("Текущее состояние / Execution state", "docs/EXECUTION_STATE.md"),
    "decisions": ("Решения / Decisions", "docs/DECISIONS.md"),
    "release": ("Порядок выпуска / Release procedure", "docs/RELEASE.md"),
    "search-discovery": ("Поисковая доступность / Search discovery", "docs/SEARCH_DISCOVERY.md"),
    "2026-09-20-chronology-release": ("Выпуск 20 сентября / Sep 20 release", "docs/history/2026-09-20-chronology-release.md"),
    "2026-09-22-global-catalog-release": ("Выпуск 22 сентября / Sep 22 release", "docs/history/2026-09-22-global-catalog-release.md"),
    "2026-09-25-local-approved-release": ("Выпуск 25 сентября / Sep 25 release", "docs/history/2026-09-25-local-approved-release.md"),
    "GSD-1.0-release-scope": ("Пакет GSD-1.0 / GSD-1.0 scope", "docs/history/GSD-1.0-release-scope.md"),
}


def _local_only():
    if settings.AIPEDIA_ENV != "local":
        raise Http404


def _git_state():
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL, timeout=2).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"],
                                             cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=3).strip())
        return head, dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


@require_safe
def history(request):
    _local_only()
    registry = json.loads((ROOT / "docs/timeline.json").read_text(encoding="utf-8"))
    product = registry["product_history"]
    english = request.aipedia_lang != "ru"
    suffix = "en" if english else "ru"
    labels = {
        "title": "Site development" if english else "История развития сайта",
        "intro": "Confirmed releases and the open Local package" if english else "Подтверждённые выпуски и открытый пакет Local",
        "local": "Local — working state" if english else "Local — рабочее состояние",
        "production": "Production — confirmed release" if english else "Production — подтверждённый выпуск",
        "git": "Git — saved code" if english else "Git — сохранённый код",
        "current": "Open package" if english else "Открытый пакет",
        "history": "Product history" if english else "История продукта",
        "details": "Details" if english else "Подробнее",
        "close": "Close" if english else "Закрыть",
        "sources": "Technical evidence" if english else "Техническое подтверждение",
        "tasks": "Separate tasks" if english else "Самостоятельные задачи",
        "goal": "Goal" if english else "Цель",
        "done": "Implemented" if english else "Реализовано",
        "qa": "Local technical QA" if english else "Техническая проверка Local",
        "owner": "Owner decision" if english else "Решение владельца",
        "next": "Open notes and next step" if english else "Замечания и следующий шаг",
        "pub": "Production publication" if english else "Публикация в Production",
        "unconfirmed": "Not confirmed" if english else "Не подтверждено",
        "not_released": "Not released" if english else "Не опубликовано",
        "released": "Published and checked" if english else "Опубликовано и проверено",
        "local_qa": "Local QA in progress" if english else "Проверка Local продолжается",
    }
    entries = {entry["release_id"]: entry for entry in registry["entries"]}
    milestones = []
    for item in product["milestones"]:
        release = entries[item["release_id"]]
        milestones.append({
            "id": item["release_id"], "date": item["date"], "title": item[f"title_{suffix}"],
            "tags": item[f"tags_{suffix}"], "capabilities": item.get(f"capabilities_{suffix}", []),
            "icon": item["icon"], "revision": item.get("revision"),
            "source": item["source"], "open": item.get("open", False),
            "stage": release["stage"], "owner_decision": item.get("owner_decision"),
        })
    gsd = entries["GSD-1.0"]
    tasks = []
    for item in gsd["items"]:
        verified = [criterion for criterion in item["criteria"] if criterion["verified"]]
        pending = [criterion for criterion in item["criteria"] if not criterion["verified"]]
        tasks.append({
            "id": item["id"], "title": item["title"], "goal": item["title"],
            "done": "; ".join(c["text"] for c in verified) or labels["unconfirmed"],
            "qa": f"{len(verified)}/{len(item['criteria'])} " + ("criteria verified in registry" if english else "критериев проверено по реестру"),
            "owner": "GSD-1.0 scope awaits an owner release decision." if english else "Объём GSD-1.0 ожидает решения владельца о выпуске.",
            "next": "; ".join(c["text"] for c in pending) if pending else ("Owner review and release decision" if english else "Просмотр владельцем и решение о выпуске"),
            "source": "GSD-1.0-release-scope", "decision": None,
        })
    for item in product["additional_tasks"]:
        tasks.append({"id": item["id"], "title": item[f"title_{suffix}"],
                      **{key: item[f"{key}_{suffix}"] for key in ("goal", "done", "qa", "owner", "next")},
                      "source": item["source"], "decision": item.get("decision")})
    production = milestones[-2]
    local_head, local_dirty = _git_state()
    context = {
        "labels": labels, "milestones": milestones, "tasks": tasks,
        "production": production, "local_head": local_head, "local_dirty": local_dirty, "gsd": gsd,
        "sources": SOURCES, "product": product,
        "seo": {"title": f"{labels['title']} | AIpediya", "description": "", "noindex": True,
                "canonical": "", "alternates": [], "x_default": "", "json_ld": [],
                "og_type": "website", "og_url": "", "og_locale": request.aipedia_lang},
    }
    response = render(request, "product_history.html", context)
    response["Cache-Control"] = "private, no-store"
    return response


@require_safe
def history_source(request, slug):
    _local_only()
    if slug not in SOURCES:
        raise Http404
    title, relative = SOURCES[slug]
    body = (ROOT / relative).read_text(encoding="utf-8")
    response = HttpResponse(f"# {title}\n\n{body}", content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "private, no-store"
    return response

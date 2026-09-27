"""Local-only view of the existing product timeline and its checked sources."""
import json
import subprocess
from pathlib import Path
from datetime import date

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
    "2026-09-25-gsd-1-0-release": ("Выпуск GSD-1.0 / GSD-1.0 release", "docs/history/2026-09-25-gsd-1-0-release.md"),
    "2026-09-25-naver-indexnow-activation": ("Активация поиска / Search activation", "docs/history/2026-09-25-naver-indexnow-activation.md"),
    "2026-09-26-search-visibility-release": ("Оптимизация поисковой видимости / Search visibility release", "docs/history/2026-09-26-search-visibility-release.md"),
    "2026-09-26-offline-product-history": ("Автономный просмотр истории / Offline product history", "docs/history/2026-09-26-offline-product-history.md"),
    "2026-09-26-offline-history-reference-match": ("Доводка истории по эталону / History reference match", "docs/history/2026-09-26-offline-history-reference-match.md"),
    "2026-09-26-catalog-master-v015": ("Новые модели v015 / Catalog master v015", "docs/history/2026-09-26-catalog-master-v015.md"),
    "2026-09-27-catalog-master-v015-final": ("Финальная синхронизация v015 / v015 final sync", "docs/history/2026-09-27-catalog-master-v015-final.md"),
    "2026-09-27-adaptive-ui-release": ("Адаптивный интерфейс / Adaptive UI release", "docs/history/2026-09-27-adaptive-ui-release.md"),
    "2026-09-27-tools-count-cloudflare-csp-local": ("Tools и Cloudflare CSP / Tools and Cloudflare CSP", "docs/history/2026-09-27-tools-count-cloudflare-csp-local.md"),
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
    context = _history_context(request.aipedia_lang)
    response = render(request, "product_history.html", context)
    response["Cache-Control"] = "private, no-store"
    return response


def _history_context(language):
    registry = json.loads((ROOT / "docs/timeline.json").read_text(encoding="utf-8"))
    product = registry["product_history"]
    english = language != "ru"
    suffix = "en" if english else "ru"
    labels = {
        "title": "AIpediya history" if english else "История AIpediya",
        "intro": "Confirmed releases and the open Local package" if english else "Подтверждённые выпуски и открытый пакет Local",
        "local": "Local — working state" if english else "Local — рабочее состояние",
        "production": "Production — confirmed release" if english else "Production — подтверждённый выпуск",
        "git": "Git — saved code" if english else "Git — сохранённый код",
        "current": "Current work" if english else "Текущая работа",
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
        "page_intro": "Working states, confirmed releases and next steps." if english else "Состояния, подтверждённые выпуски и следующий шаг.",
        "local_env": "LOCAL · WORKING STATE" if english else "LOCAL · РАБОЧЕЕ СОСТОЯНИЕ",
        "local_modified": "Updated" if english else "Изменено",
        "production_env": "PRODUCTION · LAST LIVE CHECK" if english else "PRODUCTION · ПОСЛЕДНЯЯ LIVE-ПРОВЕРКА",
        "built": "Built" if english else "Сборка",
        "dirty_tree": "The working tree has uncommitted changes; Local is not a release." if english else "Рабочее дерево содержит незакоммиченные изменения; Local не является выпуском.",
        "clean_tree": "The working tree is clean." if english else "Рабочее дерево чистое.",
        "unknown_tree": "Could not verify the working tree." if english else "Рабочее дерево не удалось проверить.",
        "local_only": "Local-only" if english else "Только Local",
        "no_deploy": "No deployment is needed for this offline history viewer." if english else "Автономный просмотр истории не требует deploy.",
        "production_verified": "Live /healthz confirmed commit" if english else "Live `/healthz` подтвердил commit",
        "evidence_source": "Source" if english else "Источник",
        "production_state": "Status" if english else "Состояние",
        "timeline_heading": "Change timeline" if english else "Лента изменений",
        "timeline_hint": "Scroll horizontally →" if english else "Прокручивайте по горизонтали →",
        "timeline_overline": "RELEASES AND WORK" if english else "ВЫПУСКИ И РАБОТА",
        "done_heading": "Implemented" if english else "Что сделано",
        "checked_heading": "Checked" if english else "Проверено",
        "owner_heading": "Owner decision" if english else "Решение владельца",
        "remaining_heading": "Remaining and next step" if english else "Остаток и следующий шаг",
        "publication_heading": "Publication" if english else "Публикация",
        "source_report": "Source report" if english else "Исходный отчёт",
        "change": "Change" if english else "Изменение",
        "change_local": "Local-only" if english else "Только Local",
        "change_local_done": "Complete in Local" if english else "Готово в Local",
        "change_published": "Published" if english else "Опубликовано",
        "criteria": "Verification criteria" if english else "Критерии из реестра",
        "local_not_published": "Local-only. Not published to Production." if english else "Local-only. На Production не опубликовано.",
        "no_owner_decision": "No separate owner approval is recorded for this card." if english else "Отдельное утверждение владельца этой карточки не зафиксировано.",
        "closed_next": "No further action is recorded for this completed milestone." if english else "Новых действий по этому завершённому этапу не зафиксировано.",
        "local_work_next": "Production was not changed; this Local step does not need deployment." if english else "Production не менялся; этот Local этап не требует deploy.",
        "proof_in_report": "Milestone status and evidence are in the release report." if english else "Статус этапа и доказательства — в исходном отчёте выпуска.",
        "confirmed_milestone": "Confirmed milestone from the project history." if english else "Подтверждённый этап из реестра истории.",
        "local_history_summary": "offline history viewer · owner visual check complete; no deploy planned" if english else "автономная история · владелец визуально проверил; deploy не требуется",
        "release_owner_approval": "Owner approved the release under decision" if english else "Владелец утвердил выпуск по решению",
    }
    entries = {entry["release_id"]: entry for entry in registry["entries"]}
    ru_months = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
    en_months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    milestones = []
    for item in product["milestones"]:
        release = entries[item["release_id"]]
        event_date = date.fromisoformat(item["date"])
        date_label = (f"{event_date.day} {ru_months[event_date.month - 1]} {event_date.year}"
                      if not english else
                      f"{en_months[event_date.month - 1]} {event_date.day}, {event_date.year}")
        milestones.append({
            "id": item["release_id"], "date": item["date"], "date_label": date_label,
            "title": item[f"title_{suffix}"],
            "tags": item[f"tags_{suffix}"], "capabilities": item.get(f"capabilities_{suffix}", []),
            "icon": item["icon"], "revision": item.get("revision"),
            "source": item["source"], "open": item.get("open", False),
            "progress": item.get("progress", "in_progress" if item.get("open", False) else "done"),
            "stage": release["stage"], "owner_decision": item.get("owner_decision"),
        })
    gsd = entries["GSD-1.0"]
    feature_titles_en = {
        "GSD-01": "Baseline and release record",
        "GSD-02": "Stable localized URL architecture",
        "GSD-03": "Server-rendered cards and indexability",
        "GSD-04": "International SEO signals and sitemaps",
        "GSD-05": "Filters, pagination and crawl controls",
        "GSD-06": "Public methodology and structured data",
        "GSD-07": "Two safe public data exports",
        "GSD-08": "Search engines, AI crawlers and IndexNow",
        "GSD-09": "Search hubs and authority content",
        "GSD-10": "Monitoring, end-to-end checks and Local handoff",
    }
    features = [
        {"id": item["id"], "number": item["id"].rsplit("-", 1)[-1],
         "title": feature_titles_en[item["id"]] if english else item["title"]}
        for item in gsd["items"]
    ]
    tasks = []
    for item in gsd["items"]:
        verified = [criterion for criterion in item["criteria"] if criterion["verified"]]
        pending = [criterion for criterion in item["criteria"] if not criterion["verified"]]
        tasks.append({
            "id": item["id"], "title": item["title"], "goal": item["title"],
            "done": "; ".join(c["text"] for c in verified) or labels["unconfirmed"],
            "qa": f"{len(verified)}/{len(item['criteria'])} " + ("criteria verified in registry" if english else "критериев проверено по реестру"),
            "owner": ("Owner approved the GSD-1.0 release on 2026-09-25." if english else "Владелец утвердил выпуск GSD-1.0 25.09.2026.")
            if product.get("production_released") else
            ("GSD-1.0 scope awaits an owner release decision." if english else "Объём GSD-1.0 ожидает решения владельца о выпуске."),
            "next": "; ".join(c["text"] for c in pending) if pending else ("Owner review and release decision" if english else "Просмотр владельцем и решение о выпуске"),
            "source": "GSD-1.0-release-scope", "decision": None,
        })
    for item in product["additional_tasks"]:
        tasks.append({"id": item["id"], "title": item[f"title_{suffix}"],
                      **{key: item[f"{key}_{suffix}"] for key in ("goal", "done", "qa", "owner", "next")},
                      "source": item["source"], "decision": item.get("decision")})
    production = product.get("current_production") or next(
        (milestone for milestone in reversed(milestones) if not milestone["open"]), milestones[0]
    )
    local_head, local_dirty = _git_state()
    context = {
        "labels": labels, "milestones": milestones, "tasks": tasks,
        "production": production, "local_head": local_head, "local_dirty": local_dirty, "gsd": gsd,
        "features": features,
        "generated_at": product.get("generated_at", ""),
        "local_only_summary": labels["local_history_summary"],
        "sources": SOURCES, "product": product,
        "edition": "en" if english else "ru",
        "seo": {"title": f"{labels['title']} | AIpediya", "description": "", "noindex": True,
                "canonical": "", "alternates": [], "x_default": "", "json_ld": [],
                "og_type": "website", "og_url": "", "og_locale": language},
    }
    task_by_id = {task["id"]: task for task in tasks}
    for milestone in context["milestones"]:
        milestone["task"] = task_by_id.get(milestone["id"])
        if milestone["id"] == "GSD-1.0":
            change_cards = []
            for item in gsd["items"]:
                criteria = item["criteria"]
                verified_count = sum(1 for criterion in criteria if criterion["verified"])
                change_cards.append({
                    "number": item["id"].rsplit("-", 1)[-1],
                    "title": feature_titles_en[item["id"]] if english else item["title"],
                    "status": (f"{verified_count}/{len(criteria)} verified" if english else
                               f"{verified_count}/{len(criteria)} критериев подтверждено"),
                    "criteria": [criterion["text"] for criterion in criteria],
                })
            milestone["change_cards"] = change_cards
        else:
            milestone["change_cards"] = [
                {
                    "number": f"{index + 1:02d}",
                    "title": milestone["tags"][index] if index < len(milestone["tags"])
                    else f"{labels['change']} {index + 1:02d}",
                    "summary": description,
                    "status": "PLANNED" if milestone["progress"] == "planned" else
                    (("Ready for owner review" if english else "Ожидает подтверждения владельца")
                     if milestone["progress"] == "review" else
                    (labels["change_local_done"] if milestone["progress"] == "done" and milestone["open"] else
                     (labels["change_local"] if milestone["open"] else labels["change_published"]))),
                    "criteria": [],
                }
                for index, description in enumerate(milestone["capabilities"])
            ]
    return context


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

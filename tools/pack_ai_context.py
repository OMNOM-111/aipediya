"""Assemble a secret-free transferable context pack for a new chat.

Facts (git, timestamps, file lists, reachable reports) come from the working
tree. Narrative (task, decisions, next step) is copied from project documents.
This script must not invent owner requirements from file names.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "AI_CONTEXT"
SOURCE_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/EXECUTION_STATE.md",
    "docs/DECISIONS.md",
    "docs/PROJECT_MAP.md",
    "docs/RELEASE.md",
    "docs/COMPARISON_RULES.md",
    "docs/ACCEPTANCE.md",
    "docs/VERIFICATION.md",
    "docs/history/2026-09-20-chronology-release.md",
    ".cursor/rules/aipedia.mdc",
    "AI_CONTEXT/README.md",
    "tools/pack_ai_context.py",
    "tools/local/install-shortcuts.ps1",
    "catalog/tests/test_pack_ai_context.py",
]
DENIED_PARTS = {".venv", "__pycache__", "data/local", "node_modules"}
DENIED_SUFFIXES = {
    ".sqlite3", ".sqlite3-wal", ".sqlite3-shm", ".env", ".log", ".pyc",
    ".pem", ".p12", ".pfx", ".key",
}
DENIED_NAMES = {
    "secret.key", "secret.env", ".env", "aipedia.pid", "port.txt",
    "credentials.json", "cookies.txt",
}
DENIED_NAME_BITS = ("secret.key", ".env", "id_rsa", "credentials")
TEXT_SUFFIXES = {".py", ".md", ".mdc", ".ps1", ".html", ".css", ".txt", ".json"}
PEM_MARKERS = (
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN PRIVATE KEY-----",
)
MAX_COPY_BYTES = 2_000_000
STATE_UPDATED_RE = re.compile(r"Обновлено \(UTC\):\s*(\S+)")
PRODUCTION_COMMIT_RE = re.compile(
    r"публичный сайт работает на commit `([0-9a-f]{7,40})`",
    re.IGNORECASE,
)
EVIDENCE_RE = re.compile(
    r"## Доказательства для архива\n(.*?)(?:\n## |\Z)",
    re.S,
)


def posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def deny(name: str) -> bool:
    path = posix(name).lstrip("/")
    lowered = path.lower()
    parts = path.split("/")
    if any(part in DENIED_PARTS for part in parts):
        return True
    if lowered.startswith("data/local/") or "/data/local/" in lowered:
        return True
    if Path(path).name.lower() in DENIED_NAMES:
        return True
    suffix = Path(path).suffix.lower()
    if suffix in DENIED_SUFFIXES:
        return True
    if path.endswith(".sqlite3-wal") or path.endswith(".sqlite3-shm"):
        return True
    base = Path(path).name.lower()
    if any(bit in lowered for bit in DENIED_NAME_BITS):
        return True
    if base.endswith(".env") or base.startswith(".env"):
        return True
    return False


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_ok(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return result.returncode, (result.stdout or "").strip()


def read_text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_state_updated(text: str) -> str:
    match = STATE_UPDATED_RE.search(text)
    return match.group(1) if match else ""


def parse_production_commit(text: str) -> str:
    match = PRODUCTION_COMMIT_RE.search(text)
    return match.group(1) if match else ""


def parse_evidence_paths(text: str) -> list[str]:
    match = EVIDENCE_RE.search(text)
    if not match:
        return []
    found = []
    for line in match.group(1).splitlines():
        item = line.strip()
        if item.startswith("- "):
            item = item[2:].strip()
        if not item or item.startswith("(") or item.startswith("Относительные"):
            continue
        found.append(posix(item))
    return found


def name_status(output: str) -> list[str]:
    lines = []
    for raw in output.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t", 1)
        path = parts[-1].strip()
        if " => " in path:
            path = path.split(" => ", 1)[-1]
        if path:
            lines.append(posix(path))
    return lines


def collect_git() -> dict:
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "HEAD"
    head = git("rev-parse", "HEAD")
    head_short = git("rev-parse", "--short", "HEAD")
    origin = git("rev-parse", "origin/main")
    origin_short = git("rev-parse", "--short", "origin/main")
    code, counts = git_ok("rev-list", "--left-right", "--count", "origin/main...HEAD")
    ahead = behind = None
    if code == 0 and counts:
        bits = counts.split()
        if len(bits) == 2:
            behind, ahead = bits[0], bits[1]
    porcelain = git("status", "--porcelain=v1", "-uall")
    staged = name_status(git("diff", "--cached", "--name-only"))
    unstaged = name_status(git("diff", "--name-only"))
    untracked = [posix(p) for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p]
    dirty = bool(porcelain.strip())
    log = git("log", "-5", "--format=%h %ci %s")
    diff_stat = git("diff", "--stat")
    cached_stat = git("diff", "--cached", "--stat")
    return {
        "branch": branch,
        "head": head,
        "head_short": head_short,
        "origin_main": origin,
        "origin_main_short": origin_short,
        "ahead_of_origin": ahead,
        "behind_origin": behind,
        "dirty": dirty,
        "porcelain": porcelain,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "log": log,
        "diff_stat": diff_stat,
        "cached_stat": cached_stat,
    }


def local_health() -> dict:
    port = 18810
    port_file = ROOT / "data" / "local" / "port.txt"
    if port_file.is_file():
        raw = port_file.read_text(encoding="utf-8", errors="replace").strip()
        if raw.isdigit():
            port = int(raw)
    url = f"http://127.0.0.1:{port}/healthz"
    try:
        with urlopen(url, timeout=2) as response:
            body = response.read()[:500].decode("utf-8", "replace")
            return {"checked": True, "url": url, "status": response.status, "body": body}
    except (URLError, OSError, TimeoutError) as exc:
        return {"checked": True, "url": url, "error": str(exc)}


def list_reports() -> list[str]:
    names = []
    artifacts = ROOT / "artifacts"
    if not artifacts.is_dir():
        return names
    for pattern in ("*.txt", "*.json", "**/*.txt", "**/*.json"):
        for path in artifacts.glob(pattern):
            if not path.is_file() or deny(str(path.relative_to(ROOT))):
                continue
            rel = posix(path.relative_to(ROOT))
            if rel not in names:
                names.append(rel)
            if len(names) >= 40:
                return names
    return names


def bullets(items: list[str], empty: str = "нет") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def mentioned_in_state(path: str, state: str) -> bool:
    if path in state or Path(path).name in state:
        return True
    prefix = ""
    for part in posix(path).split("/")[:-1]:
        prefix += part + "/"
        if prefix in state or (prefix + "*") in state:
            return True
    return False


def freshness_warnings(state: str, facts: dict) -> list[str]:
    warnings = []
    updated = parse_state_updated(state)
    if not updated:
        warnings.append("В `docs/EXECUTION_STATE.md` нет строки «Обновлено (UTC)».")
    dirty_files = facts["staged"] + facts["unstaged"] + facts["untracked"]
    missing = []
    for path in dirty_files:
        if not mentioned_in_state(path, state):
            missing.append(path)
    if missing:
        warnings.append(
            "Незакоммиченные файлы не упомянуты в EXECUTION_STATE: "
            + ", ".join(f"`{p}`" for p in missing[:20])
        )
    if facts["dirty"]:
        warnings.append(
            "Local содержит незакоммиченные изменения; одного номера commit недостаточно."
        )
    if facts["ahead_of_origin"] not in (None, "0"):
        warnings.append(f"HEAD впереди origin/main на {facts['ahead_of_origin']} commit.")
    warnings.append(
        "Production в этой сборке не запрашивался. Указан последний подтверждённый commit из `docs/RELEASE.md`, не живая проверка сайта."
    )
    return warnings


def table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def assemble_markdown(assembled_at: str, facts: dict, health: dict, warnings: list[str], reports: list[str]) -> str:
    agents = read_text("AGENTS.md")
    state = read_text("docs/EXECUTION_STATE.md")
    decisions = read_text("docs/DECISIONS.md")
    project_map = read_text("docs/PROJECT_MAP.md")
    release = read_text("docs/RELEASE.md")
    production = parse_production_commit(release)
    sources_mtime = []
    for rel in SOURCE_FILES:
        path = ROOT / rel
        if path.is_file():
            stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            sources_mtime.append(f"- `{rel}` (mtime UTC {stamp})")
        else:
            sources_mtime.append(f"- `{rel}` (нет файла)")
    health_line = health.get("body") or health.get("error") or "нет"
    warning_block = "\n".join(f"- {item}" for item in warnings) if warnings else "- Предупреждений нет."
    dirty_label = "есть незакоммиченные изменения" if facts["dirty"] else "рабочее дерево чистое"
    md = f"""# AIpedia — пакет контекста для нового чата

Собран (UTC): {assembled_at}
Скрипт: `tools/pack_ai_context.py`
Этот файл — **сборка**, не независимый источник. Правила — `AGENTS.md`.
Живой статус пишет исполнитель в `docs/EXECUTION_STATE.md`, затем снова запускает сборщик.
Документ передаёт контекст, а не доступ к компьютеру и не доказательство каждой строки кода.

Обычно достаточно прикрепить этот файл. Расширенный архив: `AI_CONTEXT/AI_CONTEXT.zip`
(копии источников, git-факты, разрешённые рабочие файлы). Секреты, `.env` и SQLite туда не входят.

## Свежесть сборки

{warning_block}

Источники:

{chr(10).join(sources_mtime)}

## Три слоя: Local / GitHub / Production

Это факты сборки, не оценка «всё готово».

{table_row(["Слой", "Указатель", "Как получено"])}
{table_row(["---", "---", "---"])}
{table_row(["Local HEAD", f"`{facts['head_short']}` (`{facts['head']}`)", "git rev-parse HEAD"])}
{table_row(["Local ветка", facts["branch"], "git rev-parse --abbrev-ref HEAD"])}
{table_row(["Local грязное дерево", dirty_label, "git status --porcelain"])}
{table_row(["GitHub origin/main", f"`{facts['origin_main_short']}` (`{facts['origin_main']}`)", "git rev-parse origin/main"])}
{table_row(["HEAD vs origin", f"ahead {facts['ahead_of_origin']}, behind {facts['behind_origin']}", "git rev-list --left-right --count"])}
{table_row(["Production (последний подтверждённый)", f"`{production or 'не найден в docs/RELEASE.md'}`", "текст docs/RELEASE.md; сайт при сборке не вызывался"])}

Local `/healthz`: `{health.get("url", "")}` → {health_line}

Запись исполнителя о слоях и таблице изменений — в разделе «Фактическое состояние» ниже. Если она расходится с этой таблицей, считать верными **факты сборки** и явно указать расхождение, а не выбирать удобную версию.

## Незакоммиченные изменения

Подготовленные к commit (staged):

{bullets(facts["staged"])}

Изменённые, не в индексе (unstaged):

{bullets(facts["unstaged"])}

Неотслеживаемые (untracked):

{bullets(facts["untracked"])}

```
{facts["porcelain"] or "(чисто)"}
```

diff --stat (unstaged):

```
{facts["diff_stat"] or "(пусто)"}
```

Полные патчи разрешённых tracked-файлов — в zip: `facts/unstaged.patch`, `facts/staged.patch`.
Неотслеживаемые дампы `data/research/` в архив по умолчанию не кладутся.

## Проект и договорённости

Источник: `AGENTS.md` на момент сборки.

{agents}

## Устройство проекта

Источник: `docs/PROJECT_MAP.md` на момент сборки.

{project_map}

## Фактическое состояние

Источник: `docs/EXECUTION_STATE.md` на момент сборки.

{state}

## Решения и история

Источник: `docs/DECISIONS.md` на момент сборки. Идея в обсуждении без статуса в этом журнале — не требование.

{decisions}

Последние commit:

```
{facts["log"] or "(нет)"}
```

Отчёт выпуска хронологии: `docs/history/2026-09-20-chronology-release.md` (полная копия в zip).

## Проверки

Список доступных текстовых отчётов в `artifacts/` (имена, не содержимое; не запускались этим скриптом):

{bullets(reports, "на диске не найдено")}

Скрипт **не** делает вывод PASS/FAIL из названий файлов. Итоги и пробелы пишет исполнитель в `docs/EXECUTION_STATE.md`.

## Следующий шаг

См. «Следующий шаг» в `docs/EXECUTION_STATE.md` выше. Если там общая фраза без конкретного действия — пакет неполный: исполнитель должен исправить статус и собрать его снова.
"""
    return md.replace("\r\n", "\n")


def copy_allowed(rel: str) -> bytes | None:
    if deny(rel):
        return None
    path = ROOT / rel
    if not path.is_file():
        return None
    size = path.stat().st_size
    if size > MAX_COPY_BYTES:
        return None
    data = path.read_bytes()
    suffix = Path(rel).suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        text = data.decode("ascii", errors="ignore")
        if any(marker in text for marker in PEM_MARKERS):
            return None
    return data


def build_zip_bytes(markdown: str, manifest: dict, facts: dict, state: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        def add(name: str, data: bytes) -> None:
            if deny(name):
                raise SystemExit(f"Refusing to pack denied path: {name}")
            zf.writestr(name, data)

        add("AI_CONTEXT.md", markdown.encode("utf-8"))
        add("MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))
        for rel in SOURCE_FILES:
            data = copy_allowed(rel)
            if data is not None:
                add("sources/" + posix(rel), data)
        add("facts/git-status.txt", (facts["porcelain"] + "\n").encode("utf-8"))
        add("facts/git-log.txt", (facts["log"] + "\n").encode("utf-8"))
        add("facts/diff-stat.txt", (facts["diff_stat"] + "\n").encode("utf-8"))
        unstaged_patch = git("diff")
        staged_patch = git("diff", "--cached")
        if unstaged_patch:
            add("facts/unstaged.patch", unstaged_patch.encode("utf-8"))
        if staged_patch:
            add("facts/staged.patch", staged_patch.encode("utf-8"))
        for rel in facts["unstaged"] + facts["staged"] + facts["untracked"]:
            if posix(rel).startswith("data/research/") and rel not in parse_evidence_paths(state):
                continue
            data = copy_allowed(rel)
            if data is not None:
                add("working-tree/" + posix(rel), data)
        for rel in parse_evidence_paths(state):
            data = copy_allowed(rel)
            if data is not None:
                add("evidence/" + posix(rel), data)
        names = zf.namelist()
        if any(deny(name) or name.endswith(".sqlite3") or name.endswith(".env") for name in names):
            raise SystemExit("Refusing to pack a database or secret")
    return buf.getvalue()


def pack() -> dict:
    assembled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = read_text("docs/EXECUTION_STATE.md")
    facts = collect_git()
    health = local_health()
    reports = list_reports()
    warnings = freshness_warnings(state, facts)
    markdown = assemble_markdown(assembled_at, facts, health, warnings, reports)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = OUT_DIR / "AI_CONTEXT.md"
    zip_path = OUT_DIR / "AI_CONTEXT.zip"
    manifest_path = OUT_DIR / "MANIFEST.json"
    production = parse_production_commit(read_text("docs/RELEASE.md"))
    manifest = {
        "assembled_at_utc": assembled_at,
        "state_updated_utc": parse_state_updated(state),
        "branch": facts["branch"],
        "head": facts["head"],
        "origin_main": facts["origin_main"],
        "dirty": facts["dirty"],
        "production_commit_from_docs": production,
        "production_live_checked": False,
        "warnings": warnings,
        "script": "tools/pack_ai_context.py",
    }
    archive = build_zip_bytes(markdown, manifest, facts, state)
    md_path.write_text(markdown, encoding="utf-8", newline="\n")
    zip_path.write_bytes(archive)
    manifest["sha256_zip"] = hashlib.sha256(archive).hexdigest()
    manifest["ai_context_md"] = str(md_path)
    manifest["ai_context_zip"] = str(zip_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble AI_CONTEXT.md and AI_CONTEXT.zip")
    parser.parse_args()
    os.chdir(ROOT)
    manifest = pack()
    print(json.dumps({
        "assembled_at_utc": manifest["assembled_at_utc"],
        "head": manifest["head"],
        "dirty": manifest["dirty"],
        "md": manifest["ai_context_md"],
        "zip": manifest["ai_context_zip"],
        "warnings": len(manifest["warnings"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

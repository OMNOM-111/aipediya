"""Surface verified product updates in existing Local card descriptions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from catalog import catalog_master as cm

rows, meta, extra = cm.read_workbook(cm.WORKBOOK_PATH)
stamp = cm.now_utc()
updates = {
    ("Models", "gpt-6-sol"): (
        "On 2026-09-25, OpenAI fixed image encoding that had degraded image understanding in the API and Codex, including computer-use tasks.",
        "25.09.2026 OpenAI исправила кодирование изображений, ухудшавшее их понимание в API и Codex, включая задачи управления компьютером."),
    ("Models", "gpt-6-luna"): (
        "On 2026-09-25, OpenAI fixed image encoding that had degraded image understanding in the API and Codex, including computer-use tasks.",
        "25.09.2026 OpenAI исправила кодирование изображений, ухудшавшее их понимание в API и Codex, включая задачи управления компьютером."),
    ("Tools", "codex-59301cf4"): (
        "A 0.159.0-alpha.9 pre-release appeared on 2026-09-27; the listed stable version remains 0.157.1.",
        "27.09.2026 вышла предварительная версия 0.159.0-alpha.9; указанная стабильная версия остаётся 0.157.1."),
    ("Tools", "llamacpp-bd626fa5"): (
        "Pre-release builds b11203, b11205 and b11216 on 2026-09-26/27 updated the SYCL and CUDA inference backends.",
        "Предварительные сборки b11203, b11205 и b11216 за 26–27.09.2026 обновили подсистемы инференса SYCL и CUDA."),
    ("Tools", "replit-agent-e4e5c5fc"): (
        "The 2026-09-25 update added Muse, apps for Meta devices, Atta charts, Airwallex MCP and model choices including GPT-6 Sol, GPT-6 Luna Fast and Claude Opus 5.5; availability depends on plan and workspace.",
        "Обновление 25.09.2026 добавило Muse, приложения для устройств Meta, графики Atta, Airwallex MCP и выбор GPT-6 Sol, GPT-6 Luna Fast и Claude Opus 5.5; доступ зависит от тарифа и рабочей области."),
    ("Tools", "qwen-code-984fcfb7"): (
        "Version 0.24.6 adds Managed Runtime v2, qwen sessions ps and a native advisor tool.",
        "Версия 0.24.6 добавляет Managed Runtime v2, команду qwen sessions ps и встроенный инструмент advisor."),
    ("Tools", "cline-e0d25424"): (
        "Cline Desktop 0.0.37 (2026-09-26) adds an About page, What's New and macOS diagnostics; desktop, IDE extension and CLI have separate versions.",
        "Cline Desktop 0.0.37 (26.09.2026) добавляет страницу About, раздел What's New и диагностику macOS; версии Desktop, расширения IDE и CLI различаются."),
}
for (sheet, record_id), (en, ru) in updates.items():
    row = next(r for r in rows[sheet] if r["Record ID"] == record_id)
    for field, suffix in (("Description EN", en), ("Description RU", ru)):
        before = row.get(field, "")
        after = before.rstrip() + " " + suffix if suffix not in before else before
        if after != before:
            row[field] = after
            rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": sheet,
                "Record ID": record_id, "Field": field, "Before": before,
                "After": after, "Reason": "Verified 25–27 September product update visible in Local"})

# Tool cards have no dedicated license field; make the verified license visible
# in their public descriptions while preserving the master evidence in Notes.
for record_id, en, ru in (
    ("gpt-researcher", "License: Apache-2.0.", "Лицензия: Apache-2.0."),
    ("koboldcpp", "License: AGPL-3.0.", "Лицензия: AGPL-3.0."),
    ("darkbloom", "License: proprietary / all rights reserved.", "Лицензия: проприетарная, все права защищены."),
):
    row = next(r for r in rows["Tools"] if r["Record ID"] == record_id)
    for field, suffix in (("Description EN", en), ("Description RU", ru)):
        before = row.get(field, "")
        if suffix not in before:
            row[field] = before.rstrip() + " " + suffix
            rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Tools",
                "Record ID": record_id, "Field": field, "Before": before,
                "After": row[field], "Reason": "Show verified tool license in Local card"})

for row in rows["Offers"]:
    if row.get("Record ID") != "longcat-2-5-preview":
        continue
    unit_label = {
        "input": "входных", "cache_read": "кэшированных входных",
        "output": "выходных",
    }[row["Unit"]]
    after = (f"Временная акционная цена за 1 млн {unit_label} токенов через "
             "Vercel AI Gateway; не постоянный тариф прямой платформы.")
    before = row.get("Conditions RU", "")
    if before != after:
        row["Conditions RU"] = after
        rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Offers",
            "Record ID": "longcat-2-5-preview", "Field": "Conditions RU",
            "Before": before, "After": after, "Reason": "Localized promotional price conditions"})

for record_id in ("qwen3guard-stream-0-6b", "qwen3guard-stream-4b"):
    key = f"fact-20260927-{record_id}-kv-cache-code-update"
    if not any(r["Key"] == key for r in rows["Facts"]):
        import json
        value = {"date": "2026", "change": "KV-cache fix", "kind": "code update, not a new model release",
                 "scope": record_id, "checked": "2026-09-27"}
        rows["Facts"].append({"Key": key, "Record Type": "model", "Record ID": record_id,
            "Fact": "code_update", "Value (JSON)": json.dumps(value, ensure_ascii=False),
            "Source URL": f"https://huggingface.co/Qwen/Qwen3Guard-Stream-{ '0.6B' if record_id.endswith('0-6b') else '4B' }/commits/main",
            "Checked": "2026-09-27"})
        rows["Changelog"].append({"Timestamp (UTC)": stamp, "Sheet": "Facts",
            "Record ID": record_id, "Field": key, "Before": "", "After": json.dumps(value, ensure_ascii=False),
            "Reason": "Record KV-cache correction as code update; exclude 8B"})
cm.write_workbook(rows, meta, cm.WORKBOOK_PATH, extra)
print("Updated public descriptions:", len(updates))

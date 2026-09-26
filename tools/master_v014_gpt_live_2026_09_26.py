"""Master v013 -> v014: owner acceptance fix for one entity (GPT-Live 1).

Owner acceptance 2026-09-26: GPT-Live 1 is a voice model; the Tools record
gpt-live-1-e666ccf6 was a wrong classification. The Models record
gpt-live-1-60f09da9 becomes the public card (both release events kept with
sources), the Tools record is archived with a cross-sheet link to the model,
and its existing price/access rows move to the model. Every field change goes
to the Changelog; numbers are recomputed by the standard refresh.

  .venv\\Scripts\\python.exe tools\\master_v014_gpt_live_2026_09_26.py --book AI_CONTEXT\\AIpediya_Model_Verification_Master.xlsx
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipedia.settings")
import django  # noqa: E402

django.setup()
from catalog import catalog_master as cm  # noqa: E402

RUN = "v014 owner acceptance 2026-09-26"
MODEL, TOOL = "gpt-live-1-60f09da9", "gpt-live-1-e666ccf6"
S_MODEL = "https://developers.openai.com/api/docs/models/gpt-live-1"
S_CHATGPT = "https://openai.com/index/introducing-gpt-live/"
S_API = "https://openai.com/index/introducing-gpt-live-1-in-the-api/"
EVENTS = [
    {"event": "release of GPT-Live in ChatGPT Voice (model introduced, powering ChatGPT Voice)",
     "date": "2026-07-08", "precision": "day", "source_url": S_CHATGPT},
    {"event": "general availability in the OpenAI API as gpt-live-1 (Live endpoint v1/live/sessions)",
     "date": "2026-09-10", "precision": "day", "source_url": S_API},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    args = parser.parse_args()
    book = Path(args.book)
    before_sha = hashlib.sha256(book.read_bytes()).hexdigest()
    rows, meta, extra = cm.read_workbook(book)
    stamp = cm.now_utc()
    today = stamp[:10]
    log = rows["Changelog"]
    models = {r["Record ID"]: r for r in rows["Models"]}
    tools = {r["Record ID"]: r for r in rows["Tools"]}
    model, tool = models[MODEL], tools[TOOL]

    def setf(sheet, row, field, value, reason, key=None):
        old = row.get(field, "")
        if old == value:
            return
        row[field] = value
        log.append({"Timestamp (UTC)": stamp, "Sheet": sheet, "Record ID": row.get("Record ID", ""),
                    "Field": field if key is None else "%s (%s)" % (field, key),
                    "Before": old, "After": value, "Reason": "%s: %s" % (RUN, reason)})

    reason_model = ("Голосовая модель OpenAI с полнодуплексным диалогом (официальная страница модели gpt-live-1). "
                    "Два события сохранены раздельно: 2026-07-08 — выпуск GPT-Live в ChatGPT Voice; 2026-09-10 — "
                    "доступность в API как gpt-live-1. Датой выпуска модели принята первая: сентябрьская — дата "
                    "способа доступа (API), а не появления модели. Приёмка владельца 2026-09-26.")
    evidence = json.loads(model.get("Release Evidence (JSON)") or "{}")
    evidence.update({"events": EVENTS, "checked": today, "run": RUN, "date_kind": "first public release (ChatGPT Voice)",
                     "source_url": S_CHATGPT})
    for field, value in (
            ("Status", "PUBLISHED"), ("Publication Decision", "PUBLIC"), ("Decision Code", "CURRENT_RELEASE"),
            ("Decision Date", today), ("Decision Sources", " | ".join([S_MODEL, S_CHATGPT, S_API])),
            ("Reason", reason_model), ("Approx Date", ""), ("Exact Release Date", "2026-07-08"),
            ("Official Source", S_MODEL), ("Secondary Source", S_API), ("Last Verified", today),
            ("Aliases", "GPT-Live | gpt-live-1 | GPT-Live-1"), ("Release Stage", "released"),
            ("Tasks", "speech; text; agents"), ("Input Modalities", "audio; text"), ("Output Modalities", "audio; text"),
            ("Description EN", "Full-duplex voice model from OpenAI: it listens and speaks at the same time and hands "
                               "reasoning and tool use to a backend model. Introduced in ChatGPT Voice on 8 July 2026; "
                               "available in the API as gpt-live-1 since 10 September 2026."),
            ("Description RU", "Полнодуплексная голосовая модель OpenAI: слушает и говорит одновременно, а рассуждения и "
                               "работу с инструментами передаёт backend-модели. Представлена в ChatGPT Voice 8 июля 2026 г.; "
                               "в API — как gpt-live-1 с 10 сентября 2026 г."),
            ("Suitable EN", "Input: Audio, Text; Output: Audio, Text; real-time voice agents with streaming and function calling"),
            ("Suitable RU", "Вход: аудио, текст; выход: аудио, текст; голосовые агенты реального времени со стримингом и вызовом функций"),
            ("Limitations EN", "Closed weights. API use goes through the Live endpoint only; structured outputs and "
                               "fine-tuning are not supported. The API price covers the voice session; the backend model "
                               "and tools are billed separately. Context window is not verified."),
            ("Limitations RU", "Закрытые веса. В API работает только через Live endpoint; структурированный вывод и "
                               "дообучение не поддерживаются. Цена в API — за голосовую сессию; backend-модель и "
                               "инструменты оплачиваются отдельно. Контекстное окно не подтверждено."),
            ("Source Title", "GPT-Live 1 — OpenAI API model page"), ("Source URL", S_MODEL), ("Source Publisher", "OpenAI"),
            ("Release Evidence (JSON)", json.dumps(evidence, ensure_ascii=False, sort_keys=True)),
    ):
        setf("Models", model, field, value, "GPT-Live 1 is a voice model (owner acceptance)")
    notes = (model.get("Notes", "") + "\n[%s] Карточка модели допущена к публикации; сведения, цена и доступ "
             "ошибочной записи Tools %s собраны здесь. События: 2026-07-08 ChatGPT Voice (%s); 2026-09-10 API (%s)."
             % (RUN, TOOL, S_CHATGPT, S_API)).strip()
    notes = notes.replace("[DEFERRED 2026-09-26] Отложенный исследовательский запас: не входит в текущий пакет публикации "
                          "(ядро + отобранные дополнения). Publication Decision здесь — редакционное предложение, не команда "
                          "публиковать; повторная проверка — по приоритету, отдельно.", "").strip()
    setf("Models", model, "Notes", notes, "notes")

    reason_tool = ("Ошибочная классификация: модель представлена как отдельный инструмент. GPT-Live 1 — голосовая "
                   "модель OpenAI (Models:%s); наличие API не делает её приложением. Цена и доступ этой строки "
                   "перенесены к модели, история сохранена; старый адрес ведёт 301 на карточку модели." % MODEL)
    for field, value in (
            ("Status", "NEEDS_REVIEW"), ("Publication Decision", "ARCHIVE"), ("Decision Code", "MODEL_APP_SPLIT"),
            ("Relation Type", "DUPLICATE_OF"), ("Canonical / Parent Record ID", "Models:" + MODEL),
            ("Reason", reason_tool), ("Decision Date", today), ("Decision Sources", " | ".join([S_MODEL, S_API])),
            ("Last Verified", today)):
        setf("Tools", tool, field, value, "wrong classification (owner acceptance)")

    for sheet, key in (("Offers", "offer-476"), ("Access", "access-250")):
        row = next(r for r in rows[sheet] if r["Key"] == key)
        assert (row["Record Type"], row["Record ID"]) == ("tool", TOOL), row
        setf(sheet, row, "Record Type", "model", "price/access of the model moves from the misclassified tool", key)
        setf(sheet, row, "Record ID", MODEL, "price/access of the model moves from the misclassified tool", key)

    for event in EVENTS:
        key = "fact-v014-%s-%s" % (MODEL, event["date"])
        if not any(f["Key"] == key for f in rows["Facts"]):
            rows["Facts"].append({"Key": key, "Record Type": "model", "Record ID": MODEL, "Fact": "release_event",
                                  "Value (JSON)": json.dumps(event, ensure_ascii=False, sort_keys=True),
                                  "Source URL": event["source_url"], "Checked": today})
            log.append({"Timestamp (UTC)": stamp, "Sheet": "Facts", "Record ID": MODEL, "Field": "row added (%s)" % key,
                        "Before": "", "After": event["event"], "Reason": "%s: separate release events" % RUN})

    renumbered = cm.refresh_derived(rows, log, "%s: chronology recomputed (GPT-Live 1 added, tool archived)" % RUN, stamp)
    meta = dict(meta)
    meta.update({"Version": "v014", "Built From": "v013 sha256 %s + %s" % (before_sha, RUN),
                 "Verification run": "%s — GPT-Live 1: модель допущена, ошибочная запись Tools в архиве" % RUN})
    meta = cm.refresh_meta(meta, rows, stamp)
    cm.write_workbook(rows, meta, book, extra)
    print(json.dumps({"book": str(book), "before_sha256": before_sha,
                      "after_sha256": hashlib.sha256(book.read_bytes()).hexdigest(), "renumbered_events": renumbered,
                      "published": {s: sum(1 for r in rows[s] if r["Status"] == "PUBLISHED") for s in cm.MAIN}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

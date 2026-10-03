"""Register Rating labels in the existing context.t lookup mechanism."""
import json
from pathlib import Path
from .content import source_labels

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'data/rating/ui_translations.json'

def register(text,translations):
    text.update(source_labels(ROOT/'data/rating/v1.0'))
    if PATH.exists():
        overlay=json.loads(PATH.read_text(encoding='utf-8'))
        for lang,values in overlay['translations'].items():translations.setdefault(lang,{}).update(values)

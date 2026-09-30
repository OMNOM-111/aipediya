"""Build the standalone, offline product timeline from its canonical sources."""
from __future__ import annotations

import html
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "timeline.html"


def _render_edition(language: str, generated_at: str) -> str:
    os.environ["DJANGO_SETTINGS_MODULE"] = "aipedia.test_settings"
    os.environ["AIPEDIA_ENV"] = "local"
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from django.template.loader import render_to_string
    from catalog.product_history import _history_context

    context = _history_context(language)
    context["generated_at"] = generated_at
    markup = render_to_string("product_history_standalone.html", context)
    markup = re.sub(
        r'href="/history/source/([^"?#]+)"',
        lambda match: f'href="#source-{match.group(1)}" data-history-source="{match.group(1)}"',
        markup,
    )
    return markup


def _source_templates() -> str:
    from catalog.product_history import SOURCES

    parts = []
    for slug, (title, relative) in SOURCES.items():
        source_path = ROOT / relative
        text = source_path.read_text(encoding="utf-8")
        # Account emails and browser session identifiers are private and not part of this export.
        text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[адрес скрыт]", text)
        text = re.sub(r'(cua\.getTab\()\s*["\'][^"\']+["\']', r"\1[идентификатор скрыт]", text)
        text = re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "[идентификатор скрыт]", text)
        text = re.sub(r"\b\d{10,}\b", "[идентификатор скрыт]", text)
        safe = html.escape(text)
        safe_title = html.escape(title)
        parts.append(
            f'<template data-history-source-template="{html.escape(slug, quote=True)}">'
            f'<article class="ph-detail ph-source-document"><p class="ph-lead">{safe_title}</p>'
            f'<pre>{safe}</pre></article></template>'
        )
    return "\n".join(parts)


def _current_registry_hash() -> str:
    registry = json.loads((ROOT / "docs/timeline.json").read_text(encoding="utf-8"))
    return hashlib.sha256(json.dumps(registry, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _generated_at_for(timeline_sha256: str) -> str:
    if OUTPUT.exists():
        text = OUTPUT.read_text(encoding="utf-8", errors="replace")
        same = re.search(r'name="aipediya-timeline-sha256" content="([0-9a-f]{64})"', text)
        stamp = re.search(r'name="aipediya-history-generated-utc" content="([^"]+)"', text)
        if same and stamp and same.group(1) == timeline_sha256:
            return stamp.group(1)
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def build() -> Path:
    timeline_sha256 = _current_registry_hash()
    generated_at = _generated_at_for(timeline_sha256)
    ru = _render_edition("ru", generated_at)
    en = _render_edition("en", generated_at)
    css = (ROOT / "static/product-history-offline.css").read_text(encoding="utf-8")
    history_js = (ROOT / "static/product-history.js").read_text(encoding="utf-8")
    sources = json.dumps(_source_templates(), ensure_ascii=False).replace("</", "<\\/")
    # The HTML is the only runtime artifact: no external assets, fetches, or server dependencies.
    registry = json.loads((ROOT / "docs/timeline.json").read_text(encoding="utf-8"))
    from tools.release_history import validate
    issues = validate(registry)
    if issues:
        raise ValueError("Invalid timeline: " + "; ".join(issues))
    document = f'''<!doctype html>
<html lang="ru" dir="ltr" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'">
<meta name="aipediya-history-generated-utc" content="{generated_at}"><meta name="aipediya-timeline-sha256" content="{timeline_sha256}"><title>История AIpediya</title><style>{css}</style></head>
<body><div id="edition-root"></div><template id="edition-ru">{ru}</template><template id="edition-en">{en}</template>
<script>{history_js}</script><script>
(() => {{
 const root=document.getElementById('edition-root');
 const sourceMarkup={sources};
 const safeGet=(key,fallback)=>{{try{{return localStorage.getItem(key)||fallback}}catch(_){{return fallback}}}};
 const safeSet=(key,value)=>{{try{{localStorage.setItem(key,value)}}catch(_){{}}}};
 function activate(edition){{
  const selected=edition==='en'?'en':'ru';
  document.documentElement.lang=selected;document.documentElement.dir='ltr';
  document.title=selected==='en'?'AIpediya history':'История AIpediya';
  root.replaceChildren(document.getElementById(`edition-${{selected}}`).content.cloneNode(true));
  root.insertAdjacentHTML('beforeend',sourceMarkup);
  root.querySelectorAll('a[data-history-source]').forEach(a=>a.addEventListener('click',event=>event.preventDefault()));
  const theme=safeGet('aipedia-history-theme','dark');document.documentElement.dataset.theme=theme==='light'?'light':'dark';
  const button=root.querySelector('#theme');
  const updateThemeLabel=()=>{{const dark=document.documentElement.dataset.theme==='dark';button.querySelector('.ph-theme-label').textContent=dark?button.dataset.lightLabel:button.dataset.darkLabel;button.querySelector('.ph-theme-icon').textContent=dark?'☀':'☾';button.setAttribute('aria-pressed',String(!dark));button.setAttribute('aria-label',dark?'Включить светлую тему':'Включить тёмную тему')}};
  updateThemeLabel();button.addEventListener('click',()=>{{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;safeSet('aipedia-history-theme',next);updateThemeLabel()}});
  root.querySelector('#edition-toggle').addEventListener('click',()=>{{safeSet('aipedia-history-edition',selected==='ru'?'en':'ru');activate(selected==='ru'?'en':'ru')}});
  if(window.initAipediaProductHistory)window.initAipediaProductHistory(root);
 }}
 activate(safeGet('aipedia-history-edition','ru'));
}})();
</script></body></html>'''
    if OUTPUT.is_file():
        previous = OUTPUT.read_text(encoding="utf-8")
        stamp = re.search(r'name="aipediya-history-generated-utc" content="([^"]+)"', previous)
        if stamp and previous.replace(stamp.group(1), "<generated>") == document.replace(generated_at, "<generated>"):
            return OUTPUT
    OUTPUT.write_text(document, encoding="utf-8", newline="\n")
    return OUTPUT


if __name__ == "__main__":
    print(build())

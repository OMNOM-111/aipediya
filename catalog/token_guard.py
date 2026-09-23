"""Protect machine-readable technical tokens from machine translation.

Numeric/technical tokens such as ``1M``, ``128K``, ``7B``, ``405B``, model and
version identifiers (``gpt-5-pro``, ``claude-3-haiku-20240307``, ``GPT-5.2``),
acronyms (``API``, ``OCR``), and URLs must never be semantically translated
(e.g. Azure rendering ``1M`` as "۱ متر" — 1 metre). This module wraps such tokens
in ``translate="no"`` spans so an HTML-mode translation request preserves them
verbatim, then strips the markup back out of the result. It also detects tokens
that a previously stored translation dropped, so existing data can be repaired.
"""
import html as _html
import re

# A token is protected when it is a URL, contains a digit (1M, 128K, 7B,
# gpt-5-pro, 2026-09-20, v4.1, GPT-5.2), or is an all-caps acronym (API, OCR).
TECHNICAL_TOKEN_RE = re.compile(
    r"https?://\S+"
    r"|\b[0-9A-Za-z_./\-]*[0-9][0-9A-Za-z_./\-]*\b"
    r"|\b[A-Z]{2,}\b"
)


def find_tokens(text):
    """Ordered unique technical tokens in ``text``."""
    seen = []
    for match in TECHNICAL_TOKEN_RE.finditer(text or ""):
        token = match.group(0)
        if token not in seen:
            seen.append(token)
    return seen


def missing_tokens(source, translation):
    """Source technical tokens that do not appear verbatim in ``translation``."""
    text = translation or ""
    return [token for token in find_tokens(source) if token not in text]


def to_protected_html(text):
    """Escape ``text`` as HTML with technical tokens wrapped as non-translatable."""
    out, last = [], 0
    for match in TECHNICAL_TOKEN_RE.finditer(text):
        out.append(_html.escape(text[last:match.start()]))
        out.append('<span translate="no">' + _html.escape(match.group(0)) + "</span>")
        last = match.end()
    out.append(_html.escape(text[last:]))
    return "".join(out)


def from_protected_html(html_text):
    """Strip translation markup and unescape, leaving protected tokens verbatim."""
    stripped = re.sub(r"<[^>]+>", "", html_text)
    return _html.unescape(stripped)

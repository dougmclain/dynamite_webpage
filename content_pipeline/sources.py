"""Fetch official source text and verify that every statute quote in a draft is verbatim."""
import html
import re

import requests

UA = {"User-Agent": "Mozilla/5.0 (content-pipeline; +https://dynamitemanagement.com)"}


def fetch_text(url: str, limit: int = 60000) -> str:
    r = requests.get(url, headers=UA, timeout=45)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "")
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        try:
            import io
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
        except Exception:  # pypdf missing or unreadable
            text = ""
    else:
        text = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", r.text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def gather(urls: list[str]) -> tuple[str, list[str]]:
    blocks, errors = [], []
    for u in urls:
        try:
            blocks.append(f"=== SOURCE: {u}\n{fetch_text(u)}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{u}: {e}")
    return "\n\n".join(blocks), errors


def _norm(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\[[^\]]*\]|\.\.\.|…", " ", s)  # allow [brackets] and ellipses inside quotes
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", s.lower())).strip()


def extract_quotes(body: str) -> list[str]:
    quotes = re.findall(r"(?m)^>\s?(.+)$", body)                       # markdown blockquotes
    quotes += re.findall(r"<blockquote[^>]*>(.*?)</blockquote>", body, re.S)
    quotes += re.findall(r'"([^"]{40,})"', body) + re.findall(r"\u201c([^\u201d]{40,})\u201d", body)
    return [re.sub(r"<[^>]+>", "", q).strip() for q in quotes if len(q.split()) >= 6]


def verify(body: str, source_text: str) -> tuple[bool, str]:
    src = _norm(source_text)
    lines, ok_all = [], True
    for q in extract_quotes(body):
        chunks = [c for c in re.split(r"\.\.\.|…|\[[^\]]*\]", q) if len(c.split()) >= 4]
        ok = all(_norm(c) in src for c in chunks) if chunks else True
        ok_all &= ok
        lines.append(("OK       " if ok else "NOT FOUND") + "  " + q[:160])
    if not lines:
        return True, "No statute quotes found in the draft."
    return ok_all, "\n".join(lines)

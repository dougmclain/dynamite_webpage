"""
Real-photo covers.

1. Claude turns the post into 2-3 short stock-photo search queries.
2. We pull candidates from Pexels (free API key, commercial use, no attribution required)
   and fall back to Openverse CC0/public-domain photos (no key needed).
3. Claude looks at the candidate thumbnails and picks the one that best fits the post
   (rejecting visible text, logos, watermarks, obviously foreign scenes, cheesy stock poses).
4. We download it, crop to 1200x630, and return JPEG bytes plus credit info.

Photo IDs already used on this site are skipped, so posts don't share covers.
"""
from __future__ import annotations

import base64
import io
import os

import requests

from . import claude

UA = {"User-Agent": "content-pipeline/1.0 (+https://dynamitemanagement.com)"}
W, H = 1200, 630


# --------------------------------------------------------------------------- sources
def _pexels(query: str, n: int = 10) -> list[dict]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key, **UA},
                     params={"query": query, "orientation": "landscape", "per_page": n, "size": "large"}, timeout=30)
    if r.status_code != 200:
        return []
    return [dict(id=f"pexels:{p['id']}", thumb=p["src"]["medium"], full=p["src"]["large2x"],
                 width=p["width"], height=p["height"], credit=f"Photo by {p['photographer']} on Pexels",
                 page=p["url"], license="Pexels License")
            for p in r.json().get("photos", [])]


def _openverse(query: str, n: int = 10) -> list[dict]:
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=30,
                     params={"q": query, "license": "cc0,pdm", "aspect_ratio": "wide", "page_size": n})
    if r.status_code != 200:
        return []
    return [dict(id=f"openverse:{x['id']}", thumb=x.get("thumbnail") or x["url"], full=x["url"],
                 width=x.get("width") or 0, height=x.get("height") or 0,
                 credit=f"{x.get('title') or 'Photo'} ({x['license'].upper()}, via {x.get('source')})",
                 page=x.get("foreign_landing_url") or x["url"], license=x["license"].upper())
            for x in r.json().get("results", []) if (x.get("width") or 0) >= 900]


def lookup(photo_id: str) -> dict:
    """Re-fetch a candidate by id from its source (never trust a URL sent by a client)."""
    src, _, pid = photo_id.partition(":")
    if src == "pexels":
        key = os.environ.get("PEXELS_API_KEY")
        r = requests.get(f"https://api.pexels.com/v1/photos/{int(pid)}", headers={"Authorization": key or "", **UA}, timeout=30)
        r.raise_for_status()
        p = r.json()
        return dict(id=f"pexels:{p['id']}", thumb=p["src"]["medium"], full=p["src"]["large2x"], width=p["width"],
                    height=p["height"], credit=f"Photo by {p['photographer']} on Pexels", page=p["url"],
                    license="Pexels License")
    if src == "openverse":
        r = requests.get(f"https://api.openverse.org/v1/images/{pid}/", headers=UA, timeout=30)
        r.raise_for_status()
        x = r.json()
        if x.get("license") not in ("cc0", "pdm"):
            raise ValueError("Only CC0 / public-domain Openverse photos are allowed")
        return dict(id=f"openverse:{x['id']}", thumb=x.get("thumbnail") or x["url"], full=x["url"],
                    width=x.get("width") or 0, height=x.get("height") or 0,
                    credit=f"{x.get('title') or 'Photo'} ({x['license'].upper()}, via {x.get('source')})",
                    page=x.get("foreign_landing_url") or x["url"], license=x["license"].upper())
    raise ValueError(f"Unknown photo id {photo_id}")


def candidates(queries: list[str], exclude_ids: set[str], per_query: int = 8, cap: int = 12) -> list[dict]:
    out, seen = [], set(exclude_ids)
    for q in queries:
        words = q.split()
        found = _pexels(q, per_query) or _openverse(q, per_query)
        while not found and len(words) > 2:  # thin results: loosen the search one word at a time
            words = words[:-1]
            found = _pexels(" ".join(words), per_query) or _openverse(" ".join(words), per_query)
        for c in found:
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append(c)
    return out[:cap]


# --------------------------------------------------------------------------- choose + crop
def _thumb_b64(url: str) -> str | None:
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(requests.get(url, headers=UA, timeout=30).content)).convert("RGB")
        im.thumbnail((512, 512))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:  # noqa: BLE001
        return None


def choose(cands: list[dict], post_title: str, state: str) -> tuple[dict, str]:
    """Claude looks at the thumbnails and picks one. Returns (candidate, alt_text)."""
    images, kept = [], []
    for c in cands:
        b = _thumb_b64(c["thumb"])
        if b:
            kept.append(c)
            images.append(b)
    if not kept:
        raise ValueError("No usable photo candidates")
    prompt = (f"These are candidate cover photos (numbered 0-{len(kept)-1} in order) for a blog post titled "
              f"\"{post_title}\" for an HOA/condominium audience{f' in {state}' if state else ''}. "
              "Pick the single best cover. It must look like a real, professional photo; must NOT contain readable "
              "text, logos, watermarks, brand names, or people looking at the camera; should fit the topic and region "
              "(no obviously foreign cities for a US state post); should still look good cropped to a wide 1200x630 banner. "
              'Reply ONLY with JSON: {"index": n, "alt": "literal description of the photo, <= 125 chars", '
              '"crop_y": 0.0-1.0 vertical focus (0=top, 0.5=center)}')
    data = claude.parse_json(claude.complete_with_images(prompt, images, max_tokens=400)[0])
    i = max(0, min(int(data.get("index", 0)), len(kept) - 1))
    kept[i]["crop_y"] = float(data.get("crop_y", 0.5))
    return kept[i], data.get("alt", post_title)[:255]


def render(c: dict) -> bytes:
    from PIL import Image, ImageOps
    raw = requests.get(c["full"], headers=UA, timeout=90).content
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, min(max(c.get("crop_y", 0.5), 0), 1)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    return buf.getvalue()


def make_cover(queries: list[str], post_title: str, state: str, exclude_ids: set[str]) -> dict:
    """Returns {jpg, alt, photo_id, credit, page} or raises if nothing usable was found."""
    cands = candidates(queries, exclude_ids)
    if not cands:
        raise ValueError(f"No photos found for {queries}")
    c, alt = choose(cands, post_title, state)
    return dict(jpg=render(c), alt=alt, photo_id=c["id"], credit=c["credit"], page=c["page"])

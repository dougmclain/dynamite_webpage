"""Brief -> draft -> quote check -> real-photo cover -> site draft post.

Two engines share everything except who writes:
  * cowork: a Claude Cowork scheduled task (Max plan) calls build_context() via the API in api.py,
            writes the post itself, and sends it back to apply_draft().
  * api:    draft() calls the Anthropic API directly from a Render cron.
"""
import xml.etree.ElementTree as ET

import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

from . import conf, covers, photos, publisher, sources
from .models import ContentBrief

SITE_ROLE = {
    "dynamite": ("dynamitemanagement.com — Dynamite Management, LLC, a boutique HOA/condo management firm that handles "
                 "the administrative and financial side for associations in any state (no on-site presence). Owns: state law "
                 "roundups, finance/collections/reserves/resale statutes, budgets, HOA tax returns (Form 1120-H), local pages. "
                 "CTA: talk to Dynamite about financial management or 1120-H preparation."),
    "hoafiscal": ("hoafiscal.com — HOA Fiscal, national software for fully self-managed associations (accounting, budgets, "
                  "owner portal). Owns: national self-managed accounting/software/tax/federal topics and 'new HOA laws by "
                  "state' hubs; national posts carry a by-state table. CTA: try HOA Fiscal; associations can upgrade to Dynamite "
                  "Management for the financial side while self-managing the rest."),
    "hoameeting": ("hoameeting.com — HOA Board Minutes, part of HOA Fiscal. Owns: meetings, minutes, notice, voting, records "
                   "statutes. Its job is to be a funnel into hoafiscal.com and dynamitemanagement.com, so link to them."),
}

EDITORIAL_RULES = """
Author: Doug McLain — CPA licensed in Washington, auditing community associations since 2011, founder of Dynamite Management (2025) and HOA Fiscal.
Voice: plain, practical, written for volunteer board members. Answer-first: the first paragraph directly answers the target query.
Standing editorial rules (never break these):
- Never advise a condo to pursue Fannie Mae warrantability. You may explain the rules and what they mean for owners' loans.
- Form 1120-H can only be filed within one year of the return's due date including extensions; never promise older years can go on 1120-H (those fall to Form 1120).
- 1120-H preparation price is $175 flat; state return +$100 flat, any state.
- Be candid in software/provider comparisons, including where competitors are cheaper.
- Quote statutes ONLY from the SOURCE TEXT provided, verbatim, as markdown blockquotes (lines starting with "> "), with the section cited. If the source text doesn't contain it, paraphrase and cite instead. Never invent section numbers, dates, bill numbers or thresholds; if something isn't in the sources, say it should be confirmed.
- Include a short "This is not legal advice" line near the end for law posts.
"""

OUTPUT_SPEC = """
Return ONLY a JSON object, no preamble:
{
 "title": "H1, <= 70 chars, contains the target keyword",
 "seo_title": "<= 60 chars",
 "slug": "short-keyword-slug",
 "meta_description": "<= 155 chars, answer-first",
 "meta_keywords": "comma separated, <= 250 chars",
 "excerpt": "1-2 sentences",
 "body_markdown": "the full post in Markdown: H2/H3 structure, a quick-answer box at the top, tables where useful, 3-6 internal links using the exact URLs provided, 1-2 cross-site links, an FAQ section at the end",
 "faq": [{"q": "...", "a": "..."}],
 "photo_queries": ["2-3 short stock-photo searches for a realistic cover photo, concrete and visual, e.g. 'seattle skyline mount rainier', 'townhouse row suburb', 'board meeting conference table'. Include the state's scenery when it's a state post. No abstract words like 'law' or 'compliance'."],
 "cover_spec": {"state": "...", "building": "...", "props": ["..."], "seed": 1},
 "cover_alt": "fallback alt text, <= 125 chars"
}
"""


def _sitemap_urls(url, limit=80):
    try:
        root = ET.fromstring(requests.get(url, timeout=20).content)
        locs = [e.text for e in root.iter() if e.tag.endswith("loc")]
        return [u for u in locs if "/blog/" in u and "/category/" not in u][:limit]
    except Exception:  # noqa: BLE001
        return []


def used_photo_ids(exclude_brief=None):
    qs = ContentBrief.objects.exclude(cover_photo_id="")
    if exclude_brief is not None:
        qs = qs.exclude(pk=exclude_brief.pk)
    return set(qs.values_list("cover_photo_id", flat=True))


# --------------------------------------------------------------------------- shared steps
def build_context(brief: ContentBrief) -> dict:
    """Everything a writer needs for one brief. Fetches + caches the official source text."""
    urls = [u.strip() for u in brief.source_urls.splitlines() if u.strip()]
    if brief.is_law_post and conf.get("REQUIRE_SOURCES_FOR_LAW") and not urls:
        raise ValueError("Law post has no official source URLs — add them to the brief first.")
    source_text, fetch_errors = sources.gather(urls)
    brief.source_text = source_text
    brief.save(update_fields=["source_text"])
    current_body = ""
    if brief.refresh_slug:
        M = publisher.post_model()
        fm = conf.get("FIELD_MAP")
        old = M.objects.filter(**{fm["slug"]: brief.refresh_slug}).first()
        if old:
            current_body = getattr(old, fm["body"])[:20000]
    return {
        "brief_id": brief.pk,
        "site": conf.get("SITE_KEY"),
        "site_role": SITE_ROLE[conf.get("SITE_KEY")],
        "editorial_rules": EDITORIAL_RULES,
        "output_spec": OUTPUT_SPEC,
        "working_title": brief.title,
        "target_keyword": brief.target_keyword,
        "secondary_keywords": [k for k in brief.secondary_keywords.splitlines() if k.strip()],
        "state": brief.state,
        "angle": brief.angle,
        "publish_at": brief.publish_at.isoformat() if brief.publish_at else None,
        "refresh_slug": brief.refresh_slug,
        "current_body_to_rewrite": current_body,
        "internal_links": [{"title": t, "url": u} for t, u in publisher.existing_posts()],
        "cross_site_links": [u for sm in conf.get("CROSS_SITE_SITEMAPS") for u in _sitemap_urls(sm)],
        "source_text": source_text,
        "source_fetch_errors": fetch_errors,
        "illustration_help": covers.spec_prompt_help(),
    }


def _cover_from_photo_id(brief: ContentBrief, photo_id: str, alt: str, crop_y: float) -> bytes:
    c = photos.lookup(photo_id)
    c["crop_y"] = crop_y
    brief.cover_photo_id = c["id"]
    brief.cover_credit = c["credit"][:255] if c["id"].startswith("pexels:") else ""
    brief.cover_source_page = c["page"][:500]
    brief.cover_alt = (alt or brief.draft_title)[:255]
    return photos.render(c)


def make_cover(brief: ContentBrief) -> bytes:
    """API engine: real photo chosen by Claude via the API; branded illustration only if none found."""
    if conf.get("COVER_MODE") == "photo" and brief.photo_queries:
        try:
            exclude = used_photo_ids(brief) | set(brief.rejected_photo_ids)
            res = photos.make_cover(brief.photo_queries, brief.draft_title or brief.title, brief.state, exclude)
            brief.cover_photo_id = res["photo_id"]
            brief.cover_credit = res["credit"][:255] if res["photo_id"].startswith("pexels:") else ""
            brief.cover_source_page, brief.cover_alt = res["page"][:500], res["alt"]
            return res["jpg"]
        except Exception as e:  # noqa: BLE001
            brief.verification_report = f"PHOTO COVER FAILED ({e}); used illustration fallback.\n\n" + brief.verification_report
    brief.cover_photo_id = brief.cover_credit = brief.cover_source_page = ""
    return covers.render_jpg({**(brief.cover_spec or {}), "site": conf.get("SITE_KEY")})


def apply_draft(brief: ContentBrief, data: dict, tokens: int = 0, fetch_errors=None) -> ContentBrief:
    """Save a finished draft (from either engine): quote check, cover, site draft post."""
    site = conf.get("SITE_KEY")
    brief.draft_title = data["title"][:200]
    brief.seo_title = data.get("seo_title", "")[:200]
    brief.post_slug = brief.refresh_slug or slugify(data.get("slug") or data["title"])[:200]
    brief.meta_description = data.get("meta_description", "")[:160]
    brief.meta_keywords = data.get("meta_keywords", "")[:255]
    brief.excerpt = data.get("excerpt", "")
    brief.body = data["body_markdown"]
    brief.faq = data.get("faq", [])
    brief.photo_queries = data.get("photo_queries") or brief.photo_queries
    brief.cover_spec = {**data.get("cover_spec", {}), "site": site}
    brief.cover_alt = data.get("cover_alt", brief.draft_title)[:255]
    brief.tokens_used += tokens

    ok, report = sources.verify(brief.body, brief.source_text)
    if fetch_errors:
        report = "SOURCE FETCH ERRORS:\n" + "\n".join(fetch_errors) + "\n\n" + report
    brief.quotes_verified = ok
    brief.verification_report = report

    photo = data.get("photo") or {}
    jpg = None
    if photo.get("id"):
        try:
            jpg = _cover_from_photo_id(brief, photo["id"], photo.get("alt", ""), float(photo.get("crop_y", 0.5)))
        except Exception as e:  # noqa: BLE001
            brief.verification_report = f"CHOSEN PHOTO FAILED ({e}).\n\n" + brief.verification_report
    if jpg is None:
        jpg = make_cover(brief)
    brief.cover.save(f"{brief.post_slug}.jpg", ContentFile(jpg), save=False)

    post = publisher.upsert_draft(brief, jpg)
    brief.post_id = str(post.pk)
    brief.status = ContentBrief.DRAFTED
    brief.error = ""
    brief.save()
    return brief


# --------------------------------------------------------------------------- api engine
def draft(brief: ContentBrief) -> ContentBrief:
    from . import claude
    brief.status, brief.error = ContentBrief.DRAFTING, ""
    brief.save(update_fields=["status", "error"])
    ctx = build_context(brief)
    system = (f"You write SEO blog posts for {ctx['site_role']}\n{EDITORIAL_RULES}\n"
              f"Fallback illustration: {ctx['illustration_help']}\n{OUTPUT_SPEC}")
    refresh = (f"\nREWRITE IN PLACE. Keep the slug '{brief.refresh_slug}'. Current post:\n{ctx['current_body_to_rewrite']}\n"
               if ctx["current_body_to_rewrite"] else "")
    user = (f"BRIEF\nWorking title: {brief.title}\nTarget keyword: {brief.target_keyword}\n"
            f"Secondary keywords:\n{brief.secondary_keywords}\nState: {brief.state or 'national'}\n"
            f"Angle / must-say notes:\n{brief.angle}\n{refresh}\n"
            "INTERNAL LINKS (this site):\n" + ("\n".join(f"- {l['title']}: {l['url']}" for l in ctx["internal_links"]) or "(none yet)") +
            "\n\nCROSS-SITE LINKS:\n" + ("\n".join(f"- {u}" for u in ctx["cross_site_links"]) or "(none)") +
            f"\n\nSOURCE TEXT (the only text you may quote):\n{ctx['source_text'] or '(no sources)'}")
    text, used = claude.complete(system, user)
    return apply_draft(brief, claude.parse_json(text), used, ctx["source_fetch_errors"])


def regenerate_cover(brief: ContentBrief):
    """Reject the current photo and pick a different one (never reuses a rejected or already-used photo)."""
    if brief.cover_photo_id:
        brief.rejected_photo_ids = list({*brief.rejected_photo_ids, brief.cover_photo_id})
    else:
        brief.cover_spec = {**(brief.cover_spec or {}), "seed": int((brief.cover_spec or {}).get("seed", 1)) + 1}
    if conf.get("DRAFT_ENGINE") == "api":
        jpg = make_cover(brief)
    else:
        # no API key in cowork mode: take the best not-yet-used search result, else an illustration
        cands = photos.candidates(brief.photo_queries or [brief.target_keyword],
                                  used_photo_ids(brief) | set(brief.rejected_photo_ids)) if brief.photo_queries else []
        jpg = (_cover_from_photo_id(brief, cands[0]["id"], brief.cover_alt, 0.5) if cands
               else covers.render_jpg({**(brief.cover_spec or {}), "site": conf.get("SITE_KEY")}))
    brief.cover.save(f"{brief.post_slug or slugify(brief.title)}.jpg", ContentFile(jpg), save=False)
    if brief.post_id:
        post = publisher.post_model().objects.get(pk=brief.post_id)
        publisher.save_cover(post, jpg, brief.post_slug, brief.cover_alt, brief.cover_credit, brief.cover_source_page)
        post.save()
    brief.save()

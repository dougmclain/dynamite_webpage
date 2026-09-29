"""Lead attribution: which pages and channels bring contact / demo / sign-up submissions.

Every public page loads {% lead_attribution_script %} (pipeline_tags). It remembers the first page of
the visit and the referrer in sessionStorage and adds them as hidden fields to any POST form.
The form's success path calls record_lead(request, "contact"). Tracking must never break a form,
so record_lead swallows its own errors.
"""
import logging
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__name__)

SEARCH_HOSTS = ("google.", "bing.", "duckduckgo.", "yahoo.", "ecosia.", "search.brave.", "yandex.", "baidu.")
AI_HOSTS = ("chatgpt.com", "chat.openai.com", "perplexity.ai", "claude.ai", "gemini.google.com",
            "copilot.microsoft.com", "you.com", "phind.com")
OUR_SITES = ("dynamitemanagement.com", "hoafiscal.com", "hoameeting.com")


def _host(url):
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def classify(referrer, landing, own_host=""):
    q = parse_qs(urlsplit(landing).query) if landing else {}
    medium = (q.get("utm_medium") or [""])[0].lower()
    if "gclid" in q or "msclkid" in q or medium in ("cpc", "ppc", "paid", "paidsearch", "paid_search"):
        return "paid"
    host = _host(referrer)
    if not host:
        return "direct"
    if any(host == h or host.endswith("." + h) for h in AI_HOSTS):
        return "ai"
    if any(h in host for h in SEARCH_HOSTS):
        return "search"
    own = (own_host or "").lower().removeprefix("www.")
    if own and host.removeprefix("www.") == own:
        return "direct"  # visit started on our own page (e.g. a new tab) — no outside source
    if any(host == s or host.endswith("." + s) for s in OUR_SITES):
        return "our_sites"
    return "referral"


def _path(url):
    if not url:
        return ""
    p = urlsplit(url)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")


def record_lead(request, form):
    try:
        from .models import Lead
        landing = (request.POST.get("lead_landing") or "")[:500]
        referrer = (request.POST.get("lead_referrer") or "")[:500]
        q = parse_qs(urlsplit(landing).query)
        Lead.objects.create(
            form=form[:40],
            channel=classify(referrer, landing, request.get_host().split(":")[0]),
            landing_page=_path(landing)[:500],
            referrer=referrer,
            form_page=_path(request.META.get("HTTP_REFERER", ""))[:500],
            utm_source=(q.get("utm_source") or [""])[0][:100],
            utm_medium=(q.get("utm_medium") or [""])[0][:100],
            utm_campaign=(q.get("utm_campaign") or [""])[0][:150],
        )
    except Exception:  # noqa: BLE001 — a tracking problem must never block an inquiry
        logger.exception("record_lead failed")


def summary(days):
    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    from .models import Lead
    qs = Lead.objects.filter(created__gte=timezone.now() - timedelta(days=days))
    return {
        "total": qs.count(),
        "by_form": dict(qs.values_list("form").annotate(n=Count("id")).order_by()),
        "by_channel": dict(qs.values_list("channel").annotate(n=Count("id")).order_by()),
        "top_landing_pages": [[p or "(unknown)", n] for p, n in
                              qs.values_list("landing_page").annotate(n=Count("id")).order_by("-n")[:10]],
    }

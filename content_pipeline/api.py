"""Small JSON API so a Claude Cowork scheduled task (Max plan) can write posts without an API key.

All endpoints need the header  X-Pipeline-Token: <PIPELINE_TOKEN env var>.

GET  /pipeline/api/queue/?days=10            briefs ready to write (oldest publish date first)
GET  /pipeline/api/briefs/<id>/context/      everything needed to write one brief (incl. official source text)
GET  /pipeline/api/briefs/<id>/photos/?q=..  real-photo candidates (not already used on this site)
POST /pipeline/api/briefs/<id>/draft/        the finished draft JSON -> quote check, cover, site DRAFT post
POST /pipeline/api/briefs/                   create a brief (used by the law-radar skill)
GET  /pipeline/api/status/                   drafted / approved / published counts + last week's search numbers
"""
import hmac
import json
import os
from datetime import timedelta
from functools import wraps

from django.db.models import Q, Sum
from django.http import JsonResponse
from django.urls import path
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import conf, drafting, photos
from .models import ContentBrief, SearchSnapshot


def _auth(view):
    @csrf_exempt
    @wraps(view)
    def wrapped(request, *a, **kw):
        token = os.environ.get("PIPELINE_TOKEN", "")
        sent = request.headers.get("X-Pipeline-Token", "")
        if not token or not hmac.compare_digest(token, sent):
            return JsonResponse({"error": "unauthorized"}, status=401)
        try:
            return view(request, *a, **kw)
        except ContentBrief.DoesNotExist:
            return JsonResponse({"error": "brief not found"}, status=404)
        except Exception as e:  # noqa: BLE001
            return JsonResponse({"error": str(e)}, status=400)
    return wrapped


def _admin_url(request, brief):
    return request.build_absolute_uri(f"/admin/content_pipeline/contentbrief/{brief.pk}/change/")


@_auth
def queue(request):
    days = int(request.GET.get("days", 10))
    horizon = timezone.now() + timedelta(days=days)
    stale = timezone.now() - timedelta(hours=2)  # a run that died mid-draft gets retried
    qs = ContentBrief.objects.filter(
        Q(status__in=[ContentBrief.QUEUED, ContentBrief.FAILED]) | Q(status=ContentBrief.DRAFTING, updated__lt=stale)
    ).filter(Q(publish_at__isnull=True) | Q(publish_at__lte=horizon))
    return JsonResponse({"site": conf.get("SITE_KEY"), "briefs": [
        {"id": b.pk, "title": b.title, "target_keyword": b.target_keyword, "state": b.state,
         "publish_at": b.publish_at.isoformat() if b.publish_at else None, "status": b.status,
         "has_sources": bool(b.source_urls.strip()) or not b.is_law_post, "error": b.error} for b in qs]})


@_auth
def context(request, pk):
    b = ContentBrief.objects.get(pk=pk)
    b.status, b.error = ContentBrief.DRAFTING, ""
    b.save(update_fields=["status", "error"])
    try:
        return JsonResponse(drafting.build_context(b))
    except Exception as e:
        b.status, b.error = ContentBrief.FAILED, str(e)
        b.save(update_fields=["status", "error"])
        raise


@_auth
def photo_candidates(request, pk):
    b = ContentBrief.objects.get(pk=pk)
    qs = request.GET.getlist("q") or b.photo_queries or [b.target_keyword]
    exclude = drafting.used_photo_ids(b) | set(b.rejected_photo_ids)
    return JsonResponse({"candidates": [
        {k: c[k] for k in ("id", "thumb", "width", "height", "credit", "page")} for c in photos.candidates(qs, exclude)]})


@_auth
def submit_draft(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    b = ContentBrief.objects.get(pk=pk)
    data = json.loads(request.body)
    if not b.source_text and b.source_urls.strip():
        drafting.build_context(b)  # make sure quotes are checked against real text
    b = drafting.apply_draft(b, data)
    return JsonResponse({"ok": True, "brief_id": b.pk, "status": b.status, "post_slug": b.post_slug,
                         "quotes_verified": b.quotes_verified, "verification_report": b.verification_report,
                         "cover": b.cover_credit or ("photo" if b.cover_photo_id else "illustration"),
                         "review_url": _admin_url(request, b)})


@_auth
def create_brief(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    d = json.loads(request.body)
    if ContentBrief.objects.filter(target_keyword__iexact=d["target_keyword"]).exists():
        return JsonResponse({"ok": False, "reason": "a brief for this keyword already exists"})
    allowed = {"title", "target_keyword", "secondary_keywords", "state", "is_law_post", "category_name", "tags",
               "angle", "source_urls", "refresh_slug", "publish_at"}
    fields = {k: v for k, v in d.items() if k in allowed}
    for k in ("secondary_keywords", "source_urls"):
        if isinstance(fields.get(k), list):
            fields[k] = "\n".join(fields[k])
    b = ContentBrief.objects.create(**fields)
    return JsonResponse({"ok": True, "brief_id": b.pk, "review_url": _admin_url(request, b)})


@_auth
def status(request):
    counts = {s: ContentBrief.objects.filter(status=s).count() for s, _ in ContentBrief.STATUS_CHOICES}
    last = SearchSnapshot.objects.order_by("-week_start").values_list("week_start", flat=True).first()
    week = SearchSnapshot.objects.filter(week_start=last).aggregate(c=Sum("clicks"), i=Sum("impressions")) if last else {}
    return JsonResponse({"site": conf.get("SITE_KEY"), "briefs": counts,
                         "awaiting_review": [{"id": b.pk, "title": b.draft_title, "quotes_verified": b.quotes_verified,
                                              "review_url": _admin_url(request, b)}
                                             for b in ContentBrief.objects.filter(status=ContentBrief.DRAFTED)],
                         "search_last_week": {"week_start": str(last) if last else None, **week}})


urlpatterns = [
    path("queue/", queue),
    path("status/", status),
    path("briefs/", create_brief),
    path("briefs/<int:pk>/context/", context),
    path("briefs/<int:pk>/photos/", photo_candidates),
    path("briefs/<int:pk>/draft/", submit_draft),
]

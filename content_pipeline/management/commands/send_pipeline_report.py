"""
Weekly pipeline report by email.

    python manage.py send_pipeline_report            # email the report
    python manage.py send_pipeline_report --dry-run  # print it instead

Why this exists: the Monday "Weekly search report" runs as a Claude scheduled task in the cloud,
and that task is not allowed to send the pipeline token to the sites. So instead of Claude calling
/pipeline/api/status/ and /pipeline/api/queue/, each site emails the same data to Doug once a week
and the scheduled task reads it from Gmail. The token never leaves the server.

The email contains:
  - status:  exactly what GET /pipeline/api/status/ returns (brief counts, search_last_week, leads)
  - queue:   exactly what GET /pipeline/api/queue/?days=60 returns (target keywords)
  - search_snapshots: raw SearchSnapshot rows for the last N weeks (default 5), so the report can
    rebuild per-page / per-query numbers and backfill missed weeks
It never contains the pipeline token.

Settings (all optional):
  PIPELINE_REPORT_TO     recipient(s), str or list. Default "dougm@hoafiscal.com"
  PIPELINE_REPORT_HOST   public host name used in the subject, e.g. "hoameeting.com".
                         Default: the host of CONTENT_PIPELINE["SITE_URL"] (without "www."),
                         then the first real entry in ALLOWED_HOSTS
  DEFAULT_FROM_EMAIL     sender (the site's normal outgoing address)

Schedule it weekly, Monday morning, AFTER the job that refreshes SearchSnapshot (pipeline_cron
runs gsc_report at 14:xx UTC on Mondays) and BEFORE the Monday 8:52 AM Pacific report, e.g.
cron (server clock in UTC):
  0 15 * * 1  python manage.py send_pipeline_report
"""
import datetime as dt
import inspect
import json
import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.test import RequestFactory
from django.utils import timezone

from content_pipeline import api, conf
from content_pipeline.models import SearchSnapshot

SUBJECT_TAG = "[pipeline-report]"
JSON_BEGIN = "-----BEGIN PIPELINE REPORT JSON-----"
JSON_END = "-----END PIPELINE REPORT JSON-----"
DEFAULT_TO = "dougm@hoafiscal.com"


def _site_host():
    host = getattr(settings, "PIPELINE_REPORT_HOST", "")
    if host:
        return host
    site = urlparse(conf.get("SITE_URL") or "").hostname or ""
    if site:
        return site[4:] if site.startswith("www.") else site
    for h in getattr(settings, "ALLOWED_HOSTS", []):
        h = h.lstrip(".")
        if h and h not in ("*", "localhost", "127.0.0.1") and "." in h:
            return h
    return "unknown-host"


def _server_token():
    """The token api._auth compares against (same env var). Only used to scrub the payload."""
    return os.environ.get("PIPELINE_TOKEN", "")


def _call_view(view, path, host):
    """Call an API view in-process and return its JSON. Same output as the HTTP endpoint.

    The view is unwrapped past api._auth (and csrf_exempt), so no token is sent at all.
    """
    req = RequestFactory().get(path, HTTP_HOST=host, secure=True)
    # build_absolute_uri() (review_url) would raise DisallowedHost when the public host isn't in
    # ALLOWED_HOSTS, e.g. locally; this request never comes from outside, so skip that check.
    req.get_host = lambda: host
    resp = inspect.unwrap(view)(req)
    if resp.status_code != 200:
        raise CommandError("%s returned HTTP %s: %s" % (path, resp.status_code, resp.content[:300]))
    return json.loads(resp.content)


def _snapshots(weeks):
    since = timezone.localdate() - dt.timedelta(weeks=weeks)
    qs = SearchSnapshot.objects.filter(week_start__gte=since).order_by("week_start")
    return list(qs.values()[:5000])


def _scrub(obj, secret):
    """Belt and braces: make sure the token can never end up in the email."""
    if not secret:
        return obj
    text = json.dumps(obj, cls=DjangoJSONEncoder)
    if secret in text:
        text = text.replace(secret, "[removed]")
    return json.loads(text)


def _summary_lines(host, status):
    lines = ["Weekly pipeline report for %s" % host, ""]
    s = status.get("search_last_week") or {}
    if s:
        lines.append("Search last week: %s" % ", ".join("%s=%s" % (k, v) for k, v in s.items()
                                                       if not isinstance(v, (list, dict))))
    else:
        lines.append("Search last week: no data in status")
    leads = status.get("leads")
    if leads is None:
        lines.append("Leads: not in status (lead tracking not deployed on this site yet)")
    else:
        for k in ("last_7_days", "last_28_days"):
            if isinstance(leads, dict) and k in leads:
                v = leads[k]
                total = v.get("total", v) if isinstance(v, dict) else v
                lines.append("Leads %s: %s" % (k.replace("_", " "), total))
    lines += ["", "Machine-readable data for the Monday search report is below. Please don't edit it.", ""]
    return lines


def build_report(weeks=5):
    """(host, subject, body) for this week's report."""
    host = _site_host()
    status = _call_view(api.status, "/pipeline/api/status/", host)
    queue = _call_view(api.queue, "/pipeline/api/queue/?days=60", host)

    today = timezone.localdate()
    week_start = today - dt.timedelta(days=today.weekday() + 7)  # last full Mon–Sun week
    week_end = week_start + dt.timedelta(days=6)

    payload = {
        "report_version": 1,
        "site": host,
        "generated_at": timezone.now(),
        "week_start": week_start,
        "week_end": week_end,
        "status": status,
        "queue": queue,
        "search_snapshots": _snapshots(weeks),
    }
    secret = _server_token()
    payload = _scrub(payload, secret)

    summary = "\n".join(_summary_lines(host, status))
    if secret:
        summary = summary.replace(secret, "[removed]")
    body = summary + "\n" + JSON_BEGIN + "\n" + \
        json.dumps(payload, cls=DjangoJSONEncoder, indent=1) + "\n" + JSON_END + "\n"
    subject = "%s %s week %s" % (SUBJECT_TAG, host, week_start.isoformat())
    return host, subject, body


class Command(BaseCommand):
    help = "Email this site's weekly pipeline status, queue and search snapshots to Doug."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print the email instead of sending it")
        parser.add_argument("--weeks", type=int, default=5, help="Weeks of SearchSnapshot rows to include")
        parser.add_argument("--to", default=None, help="Override the recipient")

    def handle(self, *args, **opts):
        _host, subject, body = build_report(opts["weeks"])

        to = opts["to"] or getattr(settings, "PIPELINE_REPORT_TO", DEFAULT_TO)
        to = [to] if isinstance(to, str) else list(to)

        if opts["dry_run"]:
            self.stdout.write("To: %s\nSubject: %s\n\n%s" % (", ".join(to), subject, body))
            return

        EmailMessage(subject=subject, body=body, to=to,
                     from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None)).send(fail_silently=False)
        self.stdout.write(self.style.SUCCESS("Sent %s to %s" % (subject, ", ".join(to))))

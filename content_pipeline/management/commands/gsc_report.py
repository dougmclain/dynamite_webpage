import json
import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from content_pipeline import conf
from content_pipeline.models import SearchSnapshot


class Command(BaseCommand):
    help = "Weekly: pulls last week's Search Console clicks/impressions per page into Search snapshots."

    def handle(self, *a, **o):
        prop, raw = conf.get("GSC_PROPERTY"), os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
        if not (prop and raw):
            self.stdout.write(self.style.ERROR("Set CONTENT_PIPELINE['GSC_PROPERTY'] and GSC_SERVICE_ACCOUNT_JSON"))
            return
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_info(
            json.loads(raw), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
        svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        end = date.today() - timedelta(days=3)  # GSC data lags ~2-3 days
        start = end - timedelta(days=6)
        body = {"startDate": str(start), "endDate": str(end), "dimensions": ["page"], "rowLimit": 500}
        pages = svc.searchanalytics().query(siteUrl=prop, body=body).execute().get("rows", [])
        qbody = {**body, "dimensions": ["page", "query"], "rowLimit": 5000}
        top = {}
        for r in svc.searchanalytics().query(siteUrl=prop, body=qbody).execute().get("rows", []):
            pg, q = r["keys"]
            if pg not in top or r["clicks"] + r["impressions"] / 100 > top[pg][1]:
                top[pg] = (q, r["clicks"] + r["impressions"] / 100)
        tc = ti = 0
        for r in pages:
            pg = r["keys"][0]
            SearchSnapshot.objects.update_or_create(week_start=start, page=pg, defaults=dict(
                week_end=end, clicks=r["clicks"], impressions=r["impressions"], ctr=r["ctr"],
                position=r["position"], top_query=top.get(pg, ("",))[0][:255]))
            tc += r["clicks"]; ti += r["impressions"]
        prev = SearchSnapshot.objects.filter(week_start=start - timedelta(days=7))
        pc = sum(s.clicks for s in prev)
        self.stdout.write(self.style.SUCCESS(
            f"{start}..{end}: {tc} clicks, {ti} impressions across {len(pages)} pages (prior week clicks: {pc})"))

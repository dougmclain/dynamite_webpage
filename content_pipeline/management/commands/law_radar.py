import os
from datetime import date

import requests
from django.core.management.base import BaseCommand

from content_pipeline import conf
from content_pipeline.models import LawAlert

API = "https://api.legiscan.com/"


class Command(BaseCommand):
    help = "Weekly: finds HOA/condo bills in the watched states via LegiScan and saves new ones as Law alerts."

    def handle(self, *a, **o):
        key = os.environ.get("LEGISCAN_API_KEY")
        if not key:
            self.stdout.write(self.style.ERROR("LEGISCAN_API_KEY not set (free key at legiscan.com/legiscan)"))
            return
        new = 0
        for st in conf.get("LEGISCAN_STATES"):
            for q in conf.get("LEGISCAN_QUERIES"):
                r = requests.get(API, params={"key": key, "op": "getSearch", "state": st, "query": q, "year": 1}, timeout=40)
                res = r.json().get("searchresult", {})
                for k, bill in res.items():
                    if k == "summary" or not isinstance(bill, dict):
                        continue
                    d = bill.get("last_action_date")
                    _, created = LawAlert.objects.get_or_create(
                        bill_id=str(bill["bill_id"]),
                        defaults=dict(state=st, bill_number=bill.get("bill_number", ""), title=bill.get("title", ""),
                                      url=bill.get("text_url") or bill.get("url", ""),
                                      last_action=(bill.get("last_action") or "")[:255],
                                      last_action_date=date.fromisoformat(d) if d else None, matched_query=q))
                    new += created
        self.stdout.write(self.style.SUCCESS(f"{new} new bills. Review them under Content pipeline > Law alerts."))

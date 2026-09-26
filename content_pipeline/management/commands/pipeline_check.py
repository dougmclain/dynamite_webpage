import os

from django.apps import apps
from django.core.management.base import BaseCommand

from content_pipeline import conf


class Command(BaseCommand):
    help = "Checks the pipeline is wired to this site's blog models and has its keys."

    def handle(self, *a, **o):
        ok = True
        self.stdout.write(f"SITE_KEY = {conf.get('SITE_KEY')}   DRAFT_ENGINE = {conf.get('DRAFT_ENGINE')}")
        try:
            M = apps.get_model(conf.get("POST_MODEL"))
        except LookupError:
            self.stdout.write(self.style.ERROR(f"POST_MODEL {conf.get('POST_MODEL')} not found"))
            return
        fields = {f.name: type(f).__name__ for f in M._meta.get_fields()}
        self.stdout.write(f"\n{conf.get('POST_MODEL')} fields: " + ", ".join(f"{k}({v})" for k, v in sorted(fields.items())))
        self.stdout.write("\nFIELD_MAP:")
        for key, name in conf.get("FIELD_MAP").items():
            hit = name in fields
            req = key in ("title", "slug", "body")
            ok &= hit or not req
            style = self.style.SUCCESS if hit else (self.style.ERROR if req else self.style.WARNING)
            self.stdout.write(style(f"  {key:17} -> {name or '-':24} {'OK' if hit else ('MISSING (required)' if req else 'not on model, skipped')}"))
        if "status" in fields:
            ch = getattr(M._meta.get_field(conf.get('FIELD_MAP')['status']), "choices", None)
            self.stdout.write(f"\nstatus choices: {ch}   STATUS_VALUES: {conf.get('STATUS_VALUES')}")
        for env in (("ANTHROPIC_API_KEY",) if conf.get("DRAFT_ENGINE") == "api" else ("PIPELINE_TOKEN",)) + ("PEXELS_API_KEY", "LEGISCAN_API_KEY", "GSC_SERVICE_ACCOUNT_JSON"):
            self.stdout.write((self.style.SUCCESS if os.environ.get(env) else self.style.WARNING)(
                f"{env}: {'set' if os.environ.get(env) else 'not set'}"))
        if os.environ.get("PEXELS_API_KEY"):
            import requests
            r = requests.get("https://api.pexels.com/v1/search", params={"query": "condominium", "per_page": 1},
                             headers={"Authorization": os.environ["PEXELS_API_KEY"]}, timeout=20)
            left = r.headers.get("X-Ratelimit-Remaining", "?")
            self.stdout.write((self.style.SUCCESS if r.ok else self.style.ERROR)(
                f"Pexels test search: HTTP {r.status_code} ({left} requests left this month)"))
        try:
            import cairosvg  # noqa: F401
            self.stdout.write(self.style.SUCCESS("cairosvg: OK (covers can render)"))
        except Exception as e:  # noqa: BLE001
            ok = False
            self.stdout.write(self.style.ERROR(f"cairosvg: {e}"))
        self.stdout.write(self.style.SUCCESS("\nReady.") if ok else self.style.ERROR("\nFix the red items first."))

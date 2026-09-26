import json

from django.core.management.base import BaseCommand

from content_pipeline import conf, covers


class Command(BaseCommand):
    help = 'One-off cover: render_cover out.jpg \'{"state":"WA","building":"condo","props":["calculator","calendar"]}\''

    def add_arguments(self, p):
        p.add_argument("out")
        p.add_argument("spec")

    def handle(self, *a, out, spec, **o):
        s = json.loads(spec)
        s.setdefault("site", conf.get("SITE_KEY"))
        open(out, "wb").write(covers.render_jpg(s))
        self.stdout.write(self.style.SUCCESS(f"Wrote {out}"))

from django.core.management.base import BaseCommand

from content_pipeline import claude, conf, photos, publisher


class Command(BaseCommand):
    help = "Finds posts on this site with no cover image and gives each one a real photo cover."

    def add_arguments(self, p):
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--slug", help="Only this post (also replaces an existing cover)")
        p.add_argument("--query", help="Photo search to use (cowork mode), e.g. 'seattle skyline mount rainier'")

    def handle(self, *a, dry_run=False, slug=None, query=None, **o):
        M = publisher.post_model()
        fm = conf.get("FIELD_MAP")
        names = publisher.field_names(M)
        qs = M.objects.all()
        if slug:
            qs = qs.filter(**{fm["slug"]: slug})
        used = set()
        for post in qs:
            has_img = (fm["image"] in names and getattr(post, fm["image"])) or \
                      (fm["image_static"] in names and getattr(post, fm["image_static"]))
            if has_img and not slug:
                continue
            title = getattr(post, fm["title"])
            if dry_run:
                self.stdout.write(f"needs cover: {title}")
                continue
            if conf.get("DRAFT_ENGINE") == "api":
                q = claude.parse_json(claude.complete(
                    "You pick stock-photo searches for blog covers.",
                    f'Post title: "{title}". Return ONLY JSON {{"queries": [2-3 short concrete visual stock-photo '
                    f'searches], "state": "two-letter US state or empty"}}. Include the state\'s scenery for state posts.',
                    max_tokens=300)[0])
                res = photos.make_cover(q["queries"], title, q.get("state", ""), used)
            else:
                # no API key: use --query if given, else the title's words; take the top search result
                queries = [query] if query else [" ".join(w for w in title.split() if w.isalpha())[:60]]
                cands = photos.candidates(queries, used)
                if not cands:
                    self.stdout.write(self.style.WARNING(f"no photo found: {title} (try --slug ... --query '...')"))
                    continue
                c = cands[0]
                res = dict(jpg=photos.render(c), alt=title, photo_id=c["id"], credit=c["credit"], page=c["page"])
            used.add(res["photo_id"])
            publisher.save_cover(post, res["jpg"], getattr(post, fm["slug"]), res["alt"],
                                 res["credit"] if res["photo_id"].startswith("pexels:") else "", res["page"])
            post.save()
            self.stdout.write(self.style.SUCCESS(f"{title}  <-  {res['credit']}"))

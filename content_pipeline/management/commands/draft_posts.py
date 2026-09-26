from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from content_pipeline import drafting
from content_pipeline.models import ContentBrief


class Command(BaseCommand):
    help = "Drafts queued briefs (Claude writes the post + cover, saves it on the site as a DRAFT)."

    def add_arguments(self, p):
        p.add_argument("--limit", type=int, default=2)
        p.add_argument("--days-ahead", type=int, default=10, help="Only briefs scheduled within N days (or unscheduled)")
        p.add_argument("--id", type=int)

    def handle(self, *a, limit, days_ahead, id=None, **o):
        from content_pipeline import conf
        if conf.get("DRAFT_ENGINE") != "api":
            self.stdout.write(self.style.WARNING('DRAFT_ENGINE is "cowork": drafts come from your Cowork scheduled task.'))
            return
        if id:
            qs = ContentBrief.objects.filter(pk=id)
        else:
            horizon = timezone.now() + timedelta(days=days_ahead)
            qs = ContentBrief.objects.filter(status=ContentBrief.QUEUED).filter(
                Q(publish_at__isnull=True) | Q(publish_at__lte=horizon))[:limit]
        for b in qs:
            try:
                drafting.draft(b)
                flag = "quotes OK" if b.quotes_verified else "CHECK QUOTES"
                self.stdout.write(self.style.SUCCESS(f"Drafted #{b.pk} {b.draft_title} [{flag}]"))
            except Exception as e:  # noqa: BLE001
                b.status, b.error = ContentBrief.FAILED, str(e)
                b.save(update_fields=["status", "error"])
                self.stdout.write(self.style.ERROR(f"#{b.pk} failed: {e}"))

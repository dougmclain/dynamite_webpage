from django.core.management.base import BaseCommand
from django.utils import timezone

from content_pipeline import publisher
from content_pipeline.models import ContentBrief


class Command(BaseCommand):
    help = "Publishes APPROVED briefs whose publish_at has arrived. Run hourly."

    def handle(self, *a, **o):
        for b in ContentBrief.objects.filter(status=ContentBrief.APPROVED, publish_at__lte=timezone.now()):
            publisher.publish(b)
            b.status = ContentBrief.PUBLISHED
            b.save(update_fields=["status"])
            self.stdout.write(self.style.SUCCESS(f"Published {b.draft_title}"))

"""One cron job per site instead of four (fewer Render services to pay for).

Schedule it hourly ("5 * * * *"). Times below are UTC:
  every run          publish_scheduled
  13:xx daily        draft_posts --limit 2        (6am Pacific; only when DRAFT_ENGINE = "api" —
                     with "cowork", your Cowork scheduled task does the writing instead)
  14:xx Mondays      gsc_report, and law_radar if RUN_LAW_RADAR=1 in settings
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from content_pipeline import conf


class Command(BaseCommand):
    help = "Hourly entry point: publishes due posts, drafts in the morning, reports on Mondays."

    def add_arguments(self, p):
        p.add_argument("--force", choices=["draft", "report", "radar"], help="Run one step now regardless of the clock")

    def _step(self, name, *args):
        try:
            call_command(name, *args, stdout=self.stdout)
        except Exception as e:  # noqa: BLE001  one failing step shouldn't stop the others
            self.stdout.write(self.style.ERROR(f"{name} failed: {e}"))

    def handle(self, *a, force=None, **o):
        now = timezone.now()  # UTC
        self._step("publish_scheduled")
        if force == "draft" or (force is None and now.hour == 13 and conf.get("DRAFT_ENGINE") == "api"):
            self._step("draft_posts", "--limit", "2")
        if force == "report" or (force is None and now.weekday() == 0 and now.hour == 14):
            self._step("gsc_report")
        if force == "radar" or (force is None and now.weekday() == 0 and now.hour == 14 and conf.get("RUN_LAW_RADAR")):
            self._step("law_radar")

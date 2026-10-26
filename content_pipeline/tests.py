import datetime as dt
import json
import os
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from content_pipeline.management.commands import send_pipeline_report as cmd
from content_pipeline.models import ContentBrief, SearchSnapshot

TOKEN = "tok-SECRET-1234567890"


@override_settings(PIPELINE_REPORT_HOST="dynamitemanagement.com",
                   EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@mock.patch.dict(os.environ, {"PIPELINE_TOKEN": TOKEN})
class SendPipelineReportTests(TestCase):
    def setUp(self):
        # The token planted where the payload would carry it, to prove the scrub catches it.
        ContentBrief.objects.create(title="Queued " + TOKEN, target_keyword="hoa reserve study")
        ContentBrief.objects.create(title="Drafted", target_keyword="hoa budget",
                                    status=ContentBrief.DRAFTED, draft_title="Draft " + TOKEN)
        week = dt.date.today() - dt.timedelta(days=9)
        SearchSnapshot.objects.create(week_start=week, week_end=week + dt.timedelta(days=6),
                                      page="https://dynamitemanagement.com/blog/x/", clicks=7, impressions=300,
                                      top_query="q " + TOKEN)

    def _dry_run(self):
        out = StringIO()
        call_command("send_pipeline_report", "--dry-run", stdout=out)
        return out.getvalue()

    def _payload(self, text):
        return json.loads(text.split(cmd.JSON_BEGIN, 1)[1].split(cmd.JSON_END, 1)[0])

    def test_dry_run_prints_markers_and_does_not_send(self):
        out = self._dry_run()
        self.assertIn(cmd.JSON_BEGIN, out)
        self.assertIn(cmd.JSON_END, out)
        self.assertIn("To: dougm@hoafiscal.com", out)
        self.assertEqual(mail.outbox, [])
        data = self._payload(out)
        self.assertEqual(data["site"], "dynamitemanagement.com")
        self.assertEqual(data["status"]["search_last_week"]["c"], 7)
        self.assertEqual([b["target_keyword"] for b in data["queue"]["briefs"]], ["hoa reserve study"])
        self.assertEqual(len(data["search_snapshots"]), 1)
        self.assertIn("leads", data["status"])

    def test_token_never_in_output(self):
        out = self._dry_run()
        self.assertNotIn(TOKEN, out)
        self.assertIn("[removed]", out)

    def test_scrub(self):
        self.assertEqual(cmd._scrub({"a": [TOKEN, "x" + TOKEN]}, TOKEN), {"a": ["[removed]", "x[removed]"]})
        self.assertEqual(cmd._scrub({"a": 1}, ""), {"a": 1})

    def test_subject_format(self):
        with mock.patch.object(cmd.timezone, "localdate", return_value=dt.date(2026, 10, 19)):  # a Monday
            _host, subject, _body = cmd.build_report()
        self.assertEqual(subject, "[pipeline-report] dynamitemanagement.com week 2026-10-12")

    def test_sends_email(self):
        call_command("send_pipeline_report", "--to", "someone@example.com", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["someone@example.com"])
        self.assertTrue(msg.subject.startswith("[pipeline-report] dynamitemanagement.com week "))
        self.assertNotIn(TOKEN, msg.body)
        self.assertNotIn(TOKEN, msg.subject)

    @override_settings(PIPELINE_REPORT_HOST="")
    def test_host_defaults_to_site_url(self):
        self.assertEqual(cmd._site_host(), "dynamitemanagement.com")

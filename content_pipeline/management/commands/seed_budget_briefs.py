from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content_pipeline import conf
from content_pipeline.models import ContentBrief

RCW = "https://app.leg.wa.gov/RCW/default.aspx?cite="
ESSB_5129_REPORT = "https://lawfilesext.leg.wa.gov/biennium/2025-26/Pdf/Bill%20Reports/House/5129-S.E%20HBA%20CRJ%2025.pdf"

BRIEFS = {
    "dynamite": [
        dict(title="RCW 64.90.525 Budget Ratification: Your First Cycle as a Pre-2018 Washington HOA",
             target_keyword="RCW 64.90.525", state="WA", category_name="Washington HOA Law",
             tags="Washington, WUCIOA, HOA budgets",
             secondary_keywords="washington hoa budget ratification\nwucioa budget requirements\nhoa budget meeting washington\nessb 5129 budget",
             angle="ESSB 5129 made RCW 64.90.525 apply to pre-July-2018 communities on Jan 1, 2026, so fall 2026 is their "
                   "first ratification cycle. Walk through the 30-day / 14-50-day timeline as a dated checklist, the required "
                   "budget disclosures (reserve study statement, conformity, per-unit deficiency), special-assessment "
                   "ratification, and what happens if owners reject. Link the hoameeting ratification post and the WUCIOA pillar.",
             source_urls="\n".join([RCW + "64.90.525", RCW + "64.90.365", ESSB_5129_REPORT])),
        dict(title="RCW 64.90.545: Every Washington HOA Now Needs a Reserve Study",
             target_keyword="RCW 64.90.545", state="WA", category_name="Washington HOA Law",
             tags="Washington, WUCIOA, reserves",
             secondary_keywords="washington hoa reserve study requirement\nwucioa reserve study\nrcw 64.90.550",
             angle="Reserve study requirement now reaches pre-2018 communities (via RCW 64.90.365). Cover who is exempt, "
                   "update frequency, site-visit rule, and how the study feeds the budget disclosure under 64.90.525.",
             source_urls="\n".join([RCW + "64.90.545", RCW + "64.90.550", RCW + "64.90.365"])),
        dict(title="Colorado HB26-1099: Developers Must Fund a Reserve Study Before Turnover",
             target_keyword="colorado hb26-1099", state="CO", category_name="Colorado HOA Law",
             tags="Colorado, reserves",
             secondary_keywords="colorado hoa reserve study law 2026\ncolorado hoa turnover reserve study",
             angle="New 2026 law (effective Aug 12, 2026): independent 30-year reserve study paid by the developer before "
                   "control passes to owners; existing communities stay on disclosure rules. What incoming boards should demand. "
                   "ADD the enrolled bill URL from leg.colorado.gov before drafting.",
             source_urls=""),
        dict(title="Florida Condo Budgets After SIRS: No More Waiving Structural Reserves",
             target_keyword="florida condo budget sirs reserves", state="FL", category_name="Florida HOA Law",
             tags="Florida, reserves, HOA budgets",
             secondary_keywords="718.112(2)(f)\nflorida condo reserve waiver\nsirs budget",
             angle="Budgets adopted on/after Jan 1, 2025 cannot waive or reduce SIRS component funding. Budget-season "
                   "checklist for Florida condo boards; contrast with HOA reserve waiver rules under 720.303(6).",
             source_urls="https://www.flsenate.gov/Laws/Statutes/2025/718.112\nhttps://www.flsenate.gov/Laws/Statutes/2025/720.303"),
        dict(title="California Civil Code 5300: The Annual Budget Report Deadline Explained",
             target_keyword="civil code 5300", state="CA", category_name="California HOA Law",
             tags="California, HOA budgets",
             secondary_keywords="california hoa annual budget report\ndavis-stirling budget disclosure",
             angle="Timing window (30-90 days before fiscal year end), required contents, reserve disclosures. Calendar-year "
                   "associations are in the window now. leginfo may block bots: if the fetch fails, paste the section text "
                   "into the angle notes.",
             source_urls="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=5300"),
    ],
    "hoameeting": [
        dict(title="Ratifying the HOA Budget in Washington (2026 Update)",
             target_keyword="hoa budget ratification washington", state="WA", category_name="Meeting Minutes",
             tags="Washington, HOA budgets",
             refresh_slug="ratifying-the-hoa-budget-in-washington-state-a-board-members-complete-guide",
             angle="Rewrite in place: pre-2018 communities now follow RCW 64.90.525 (ESSB 5129). Add the ratification-meeting "
                   "notice, quorum-not-required point, and a sample minutes entry for a ratification vote. Link Dynamite's "
                   "RCW 64.90.525 post and hoafiscal's budget template.",
             source_urls="\n".join([RCW + "64.90.525", RCW + "64.90.365"])),
    ],
    "hoafiscal": [
        dict(title="Fannie Mae's 2026 Reserve Rule: What It Means for Your Owners' Mortgages",
             target_keyword="fannie mae hoa reserve requirement 2026", state="", category_name="HOA Budgets",
             tags="reserves, HOA budgets",
             angle="LL-2026-03: Limited Review ends for established projects >10 units (apps on/after Aug 3, 2026); reserve study "
                   "alternative to 15% requires funding at the study's highest recommended level. Explain impact on owners "
                   "refinancing/selling. Per editorial rule, do NOT advise boards to pursue warrantability. ADD the Fannie Mae "
                   "lender letter URL before drafting.",
             source_urls=""),
        dict(title="HOA Budget Deadlines by State (2027 Budget Season)",
             target_keyword="hoa budget deadlines by state", state="", is_law_post=True, category_name="HOA Budgets",
             tags="HOA budgets",
             angle="National hub with a by-state table (WA, OR, CA, FL, AZ, TX, CO, NV, GA, IL, NC, VA): when the budget must go "
                   "to owners, ratification/approval rule, reserve disclosure. Only include rows supported by the sources; "
                   "mark others 'confirm with your governing documents'. Link the 2027 budget template.",
             source_urls="\n".join([RCW + "64.90.525", "https://www.flsenate.gov/Laws/Statutes/2025/720.303",
                                    "https://www.flsenate.gov/Laws/Statutes/2025/718.112"])),
    ],
}


class Command(BaseCommand):
    help = "Loads the fall-2026 budget-season briefs for this site, scheduled Tue/Thu starting next Tuesday."

    def handle(self, *a, **o):
        site = conf.get("SITE_KEY")
        today = timezone.localdate()
        day = today + timedelta(days=(1 - today.weekday()) % 7 or 7)  # next Tuesday
        n = 0
        for spec in BRIEFS.get(site, []):
            if ContentBrief.objects.filter(target_keyword=spec["target_keyword"]).exists():
                continue
            spec = {"is_law_post": True, **spec}
            ContentBrief.objects.create(publish_at=timezone.make_aware(datetime.combine(day, time(7, 0))), **spec)
            n += 1
            day += timedelta(days=2 if day.weekday() == 1 else 5)
        self.stdout.write(self.style.SUCCESS(f"Added {n} briefs for {site}."))

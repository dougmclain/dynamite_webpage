from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import BlogPost, Category
from staff_portal.services import fetch_pexels_image


ARTICLE_TITLE = (
    "Best HOA Accounting Service Providers in 2026: 5 Companies HOA Boards Should Know"
)
ARTICLE_SLUG = "best-hoa-accounting-service-providers-2026"
ARTICLE_EXCERPT = (
    "Hiring an outsourced HOA accounting partner is one of the highest-leverage decisions a "
    "board makes. Here are the 5 providers worth shortlisting in 2026, with real pricing and "
    "honest tradeoffs."
)
META_DESCRIPTION = (
    "Compare the 5 best HOA accounting service providers in 2026 — real pricing, service "
    "depth, geographic coverage, and which boards each is built for."
)
META_KEYWORDS = (
    "HOA accounting services, condo accounting services, HOA financial management, "
    "HOA bookkeeping, Form 1120-H, condo bookkeeping services"
)
CATEGORY_NAME = "Finances"

FEATURED_QUERY = "condominium building exterior"
PROVIDER_QUERIES = [
    "accountant calculator office desk",
    "team office collaboration meeting",
    "remote work laptop home office",
    "california condominium building",
    "large apartment building aerial",
]

CONTENT_HTML = """<p><em>Last updated: May 23, 2026.</em></p>

<p>Hiring an outsourced HOA accounting partner is one of the highest-leverage decisions a board makes. The right provider catches the fraud you didn't see coming, files Form 1120-H on time, and delivers a clean monthly board packet without you chasing it. We compared 5 firms across pricing, service depth, and geography &mdash; <a href="/condo-financial-management/">Dynamite Management</a> takes our Editor's Choice spot.</p>

<h2>How We Ranked These Providers</h2>
<ul>
<li><strong>Pricing transparency</strong> &mdash; published flat rates rank higher than "request a quote" black boxes.</li>
<li><strong>Service depth</strong> &mdash; AP/AR, monthly reporting, audit support, and Form 1120-H tax prep all in one place.</li>
<li><strong>Internal controls and fraud detection</strong> &mdash; positive pay, dual approval, segregation of duties.</li>
<li><strong>Geographic coverage</strong> &mdash; does the provider serve your state and understand its statutes?</li>
<li><strong>Professional credentials</strong> &mdash; CAI, CMCA, CACM, ECHO memberships signal industry investment.</li>
</ul>
<p>We weighed all five together. <a href="/about/">More on our methodology.</a></p>

<h2>At-a-Glance Comparison</h2>
<p>Here's the shortlist before we go deep on each one. <a href="/contact/">Need help picking? Get in touch.</a></p>
<table>
<thead>
<tr><th>Provider</th><th>Best-For</th><th>Service Area</th><th>Pricing Model</th><th>Standout Feature</th></tr>
</thead>
<tbody>
<tr><td><strong>Dynamite Management</strong></td><td>Self-managed boards</td><td>Nationwide</td><td>Flat-fee ($150 1120-H; $750/mo WA condo)</td><td>Fraud-detection focus + HOA Fiscal portal</td></tr>
<tr><td>Community Financials</td><td>Nationwide coverage</td><td>Nationwide</td><td>Quote-based</td><td>BBB A+, veteran-owned, CMCA founder</td></tr>
<tr><td>Clark Simson Miller</td><td>Remote back-office</td><td>Nationwide (TN HQ)</td><td>Quote-based</td><td>Full remote management model</td></tr>
<tr><td>HOA Accounting Services LLC</td><td>West Coast associations</td><td>CA, WA, TX, NV, HI</td><td>Quote-based</td><td>CAI/CACM/ECHO membership</td></tr>
<tr><td>Associa</td><td>Large communities, full management</td><td>US and Canada</td><td>Quote-based</td><td>Largest US HOA management firm</td></tr>
</tbody>
</table>

<h2>What Outsourced HOA Accounting Actually Covers</h2>
<p>"HOA accounting" gets used loosely. Most boards want full <a href="/condo-financial-management/">financial management</a>, which is broader than bookkeeping alone. A complete outsourced engagement includes:</p>
<ul>
<li>Monthly financial reports &mdash; balance sheet, income/expense statement, general ledger.</li>
<li>Accounts payable processing with dual board approval.</li>
<li>Accounts receivable and ACH dues collection, plus automated delinquency notices.</li>
<li>Bank reconciliation with positive pay.</li>
<li>Audit support across the three CPA assurance levels: compilation, review, and audit.</li>
<li>Annual Form 1120-H federal tax filing.</li>
<li>Reserve fund vs. operating fund tracking, tied to your reserve study.</li>
<li>Owner-facing portal for statements, payment, and document access.</li>
</ul>
<p>A bookkeeper typically handles the first three. A full financial-management partner handles all eight.</p>

<h2>Top 5 HOA Accounting Service Providers in 2026</h2>
<p>We ranked these from #1 (our Editor's Choice) to #5. Sub-100-unit boards will gravitate to the first four; larger master-planned communities should weigh #5 seriously.</p>

<h3>1. Dynamite Management &mdash; Editor's Choice / Best Overall</h3>
<p><img src="__IMG1__" alt="Dynamite Management HOA accounting" /></p>
<p>Dynamite Management is our top pick because it's the only firm on this list that publishes flat-fee pricing, treats fraud detection as a first-class concern, and operates entirely independent of any property-management company. For self-managed boards and boards that keep property management separate from their books, it's the cleanest fit.</p>
<p><strong>Service features:</strong></p>
<ul>
<li>Monthly financial reporting with board-ready packet.</li>
<li>AP/AR with positive pay and dual-approval controls.</li>
<li>ACH dues collection through the HOA Fiscal owner portal.</li>
<li><a href="/hoa-taxes/">Form 1120-H preparation</a> at a flat $150.</li>
<li>Audit support across compilation, review, and full CPA audit.</li>
</ul>
<p><strong>Real strengths:</strong></p>
<ul>
<li><strong>Flat-fee pricing.</strong> Most providers in this category hide pricing behind a quote form. Dynamite publishes it: $150 for 1120-H prep, $750/mo all-in for the <a href="/wa-condo/">Washington self-managed condo package</a> (8&ndash;99 unit buildings).</li>
<li><strong>Fraud-detection focus.</strong> The firm built its practice around catching the mistakes and outright fraud that destroy small-association reserves &mdash; segregation of duties, positive pay, and dual approval are default workflow, not upsells.</li>
<li><strong>Dedicated back-office team.</strong> Your accounting team isn't shared with a management company's wider portfolio. That's a structural difference in incentive alignment.</li>
</ul>
<p><strong>Honest tradeoffs:</strong> Dynamite is back-office financial management only &mdash; they don't do on-site property management, maintenance coordination, or vendor walk-throughs. Boards needing a single firm to handle physical property plus accounting will need a different model (see Associa, below).</p>
<p><strong>Pricing:</strong> Flat-fee. $150 Form 1120-H prep; $750/month all-in for the WA self-managed condo package; other engagements quoted by unit count and scope.</p>
<p><strong>Best for:</strong> Self-managed boards (especially 8&ndash;99 unit condominiums) and boards that keep property management separate from their accountant.</p>

<h3>2. Community Financials &mdash; Best for Nationwide Coverage</h3>
<p><img src="__IMG2__" alt="Community Financials nationwide HOA accounting" /></p>
<p>Community Financials has been doing HOA-only financial management since 2003. They're nationwide, BBB A+ rated, veteran-owned, and founder Russell Munz holds the <a href="https://www.caionline.org/" rel="nofollow noopener">CMCA credential from CAI</a>. Their tooling around dues collection and bill approval is the most polished of the firms we reviewed.</p>
<p><strong>Service features:</strong></p>
<ul>
<li>Collect: emailed and mailed statements, coupon books, ACH and credit card payments, late notices.</li>
<li>Protect: dual board-member bill approval, positive pay, internal controls.</li>
<li>Report: monthly emailed reports, income statements, bank reconciliation.</li>
<li>Communicate: phone and email support, video training, owner portal.</li>
</ul>
<p><strong>Real strengths:</strong> deep tooling around the "collect" workflow (their stated 70% fraud-risk reduction is one of the more specific claims you'll see on the SERP); strong customer testimonial volume; CAI partnership and CMCA-credentialed founder.</p>
<p><strong>Honest tradeoffs:</strong> the feature surface area is large &mdash; a tiny self-managed board may find the portal more complex than they need. Pricing is quote-based, so direct apples-to-apples comparison takes a discovery call.</p>
<p><strong>Pricing:</strong> Quote-based. Request via <a href="https://www.communityfinancials.com/" rel="nofollow noopener">communityfinancials.com</a>.</p>
<p><strong>Best for:</strong> Mid-sized boards (50+ units) that want a polished, well-credentialed nationwide partner and aren't price-shopping.</p>

<h3>3. Clark Simson Miller &mdash; Best for Remote Back-Office Management</h3>
<p><img src="__IMG3__" alt="Clark Simson Miller remote HOA accounting" /></p>
<p><a href="https://www.clarksimsonmiller.com/" rel="nofollow noopener">Clark Simson Miller (CSM)</a> built its model around full remote management. They're Knoxville, TN-based but serve clients across the country, offering financial management, back-office services, collections, and consulting under one roof.</p>
<p><strong>Service features:</strong></p>
<ul>
<li>Monthly financial reports (balance sheet, income statement, GL, AP, cash disbursements).</li>
<li>Audit support across compilation, review, and audit.</li>
<li>Bank account and asset management.</li>
<li>Homeowner bankruptcy handling.</li>
<li>QuickBooks-based accounting backbone.</li>
</ul>
<p><strong>Real strengths:</strong> the most comprehensive remote-only model on this list; clear documentation of monthly deliverables; explicit handling of edge cases like homeowner bankruptcy.</p>
<p><strong>Honest tradeoffs:</strong> no on-site presence anywhere outside Tennessee. Pricing isn't published. The website leans heavily on educational content rather than direct service pages, so the actual scope of an engagement takes a sales conversation.</p>
<p><strong>Pricing:</strong> Quote-based.</p>
<p><strong>Best for:</strong> Boards anywhere in the US explicitly looking for a remote back-office partner and that value depth of monthly reporting.</p>

<h3>4. HOA Accounting Services LLC &mdash; Best for West Coast Associations</h3>
<p><img src="__IMG4__" alt="HOA Accounting Services LLC West Coast" /></p>
<p><a href="https://hoa-accounting.com/" rel="nofollow noopener">HOA Accounting Services LLC</a> is one of the few firms in this category that holds memberships in all three major West Coast HOA industry organizations: CAI, CACM, and ECHO. They serve California, Washington, Texas, Nevada, and Hawaii.</p>
<p><strong>Service features:</strong></p>
<ul>
<li>Monthly and annual financial reporting.</li>
<li>Billing and accounts receivable.</li>
<li>Invoice approvals workflow.</li>
<li>Quote and proposal generation.</li>
<li>Multi-state operating coverage.</li>
</ul>
<p><strong>Real strengths:</strong> strong West Coast statutory familiarity (California's Davis-Stirling Act especially); independent of property management (similar structural advantage to Dynamite); CAI/CACM/ECHO triple membership is rare.</p>
<p><strong>Honest tradeoffs:</strong> minimal pricing transparency &mdash; the site uses "affordable" without specifics. Geographic concentration on the West Coast means boards in the Midwest or Northeast will get less specialized service.</p>
<p><strong>Pricing:</strong> Quote-based.</p>
<p><strong>Best for:</strong> California, Washington, or other Pacific-state boards that want a regionally-specialized independent accounting partner.</p>

<h3>5. Associa &mdash; Best for Large Communities Wanting Full Management</h3>
<p><img src="__IMG5__" alt="Associa large HOA full-service management" /></p>
<p><a href="https://hub.associaonline.com/" rel="nofollow noopener">Associa</a> is the largest HOA management firm in the United States, with branch offices across North America. Unlike the other four on this list, Associa's primary model bundles on-site property management with the financial management.</p>
<p><strong>Service features:</strong></p>
<ul>
<li>Full-service property management with on-site staff.</li>
<li>Financial management, including monthly reporting and budgeting.</li>
<li>Vendor management and physical maintenance coordination.</li>
<li>Reserve studies and capital project planning.</li>
<li>National branch network for direct on-site presence.</li>
</ul>
<p><strong>Real strengths:</strong> the largest network of HOA professionals in North America; the only provider on this list with true on-site staffing in most major markets; extensive educational content (their <a href="https://hub.associaonline.com/blog/hoa-accounting-services" rel="nofollow noopener">Hub blog</a> is a go-to reference for boards doing their homework).</p>
<p><strong>Honest tradeoffs:</strong> their model is built for larger communities &mdash; minimum unit counts and pricing tiers tend to put them out of reach for sub-100-unit self-managed boards. The bundled model also means accounting incentives sit inside the management company, which is the exact structural issue smaller boards often want to avoid.</p>
<p><strong>Pricing:</strong> Quote-based, sized by community.</p>
<p><strong>Best for:</strong> Large master-planned communities (200+ units) that want one provider for both on-site management and financial back-office.</p>

<h2>How to Choose the Right HOA Accounting Provider</h2>
<p>Four questions narrow the field quickly:</p>
<p><strong>1. Are you self-managed or working with a separate property manager?</strong> Self-managed boards benefit most from an independent firm like Dynamite or HOA Accounting Services LLC. If you already have a management company doing the on-site work, you specifically don't want the same company doing your books &mdash; that's a structural conflict-of-interest issue.</p>
<p><strong>2. What's your unit count and budget?</strong> Sub-50-unit boards usually do best with a flat-fee specialist. 50&ndash;200 unit boards have the most options. 200+ unit communities often outgrow the back-office-only model and need a full-service firm.</p>
<p><strong>3. Do you need on-site presence or only back-office accounting?</strong> If you need physical staff walking the property, you're in Associa territory. If you only need clean books and reporting, the other four serve you better at a lower cost.</p>
<p><strong>4. What credentials should you require?</strong> At minimum, look for <a href="https://www.caionline.org/" rel="nofollow noopener">CAI membership</a>. CMCA is the gold standard for individual professionals. CACM is a strong signal for California-focused work.</p>
<p>Still not sure? <a href="/contact/">Talk through your specific situation with us</a> &mdash; even if Dynamite isn't the right fit, we'll tell you which of the others is.</p>

<h2>Common HOA Accounting Pitfalls These Providers Solve</h2>
<ul>
<li><strong>Weak internal controls:</strong> A single person handling deposits, AP, and bank reconciliation is the highest fraud-risk configuration possible. Dynamite, Community Financials, and CSM all build segregation of duties into the default workflow.</li>
<li><strong>Reserve-fund mis-tracking:</strong> Operating-fund money quietly subsidizing reserve projects (or vice versa) is the most common reporting error in self-managed associations. A proper monthly report flags it before year-end.</li>
<li><strong>Missed Form 1120-H filings:</strong> The IRS doesn't send reminders. <a href="/hoa-taxes/">Outsourced 1120-H prep</a> is the cheapest peace-of-mind purchase your board makes all year.</li>
<li><strong>Slow AR and growing delinquencies:</strong> ACH dues collection plus automated late-notice workflows cut delinquency rates significantly &mdash; Community Financials publishes specific numbers.</li>
<li><strong>Opaque monthly reporting:</strong> If your board can't tell from this month's packet whether last month's variance is fixed, your reporting is the bottleneck, not your bookkeeping.</li>
</ul>

<h2>Frequently Asked Questions</h2>
<p><strong>What does HOA accounting cost?</strong> It depends on the model. Flat-fee specialists like Dynamite Management publish rates (<a href="/hoa-taxes/">$150 for Form 1120-H prep</a>; $750/mo for the WA self-managed condo package). Most providers are quote-based, with monthly engagements ranging from a few hundred dollars for a small association up to thousands for full-service large communities.</p>
<p><strong>How is HOA bookkeeping different from full financial management?</strong> Bookkeeping is recording transactions: dues received, bills paid, ledger maintained. Financial management is the full picture: monthly reporting, AP/AR, bank reconciliation, audit support, tax filing, reserve tracking, and board advisory. Most boards need the full picture.</p>
<p><strong>Do small HOAs really need outsourced accounting?</strong> Even 8-unit condominiums benefit, because the fraud-control case is structural. A board of three volunteers can't realistically run dual approval and segregation of duties internally &mdash; an outside firm closes that gap.</p>
<p><strong>What is Form 1120-H?</strong> The federal tax return designed specifically for HOAs and condominium associations. It's simpler than Form 1120 (the corporate return) and usually lower-tax, but it has to be filed correctly to qualify. Missing it is the most common HOA tax problem.</p>
<p><strong>Self-managed vs. management-company-bundled &mdash; which is better?</strong> Neither is universally better. Bundled (Associa-style) makes sense for large communities that want one throat to choke. Self-managed with a separate accounting firm (the model Dynamite is built for) makes sense for smaller boards that want independent eyes on the books &mdash; and is usually cheaper.</p>
"""


class Command(BaseCommand):
    help = (
        "Create the 'Best HOA Accounting Service Providers 2026' blog post as a draft, "
        "fetching one featured + five inline Pexels images via the existing pipeline."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Set status to published (default: draft).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and recreate the post if a draft with the target slug already exists.",
        )

    def handle(self, *args, **options):
        existing = BlogPost.objects.filter(slug=ARTICLE_SLUG).first()
        if existing and not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Post already exists (id={existing.id}, status={existing.status}). "
                    "Pass --force to recreate."
                )
            )
            return

        author = (
            get_user_model().objects.filter(is_staff=True).order_by("id").first()
        )
        if not author:
            self.stdout.write(self.style.ERROR("No staff user found to assign as author."))
            return

        self.stdout.write("Fetching featured image from Pexels...")
        featured = fetch_pexels_image(FEATURED_QUERY)
        if not featured:
            self.stdout.write(
                self.style.ERROR(
                    "Failed to fetch featured image. Is PEXELS_API_KEY set in env?"
                )
            )
            return

        inline_urls = []
        for i, query in enumerate(PROVIDER_QUERIES, 1):
            self.stdout.write(f"Fetching inline image {i}/5: '{query}'...")
            img = fetch_pexels_image(query)
            if not img:
                self.stdout.write(
                    self.style.ERROR(f"Failed to fetch inline image {i} for query '{query}'.")
                )
                return
            inline_urls.append(default_storage.url(img["path"]))

        content = CONTENT_HTML
        for i, url in enumerate(inline_urls, 1):
            content = content.replace(f"__IMG{i}__", url)

        category, _ = Category.objects.get_or_create(
            slug="finances",
            defaults={"name": CATEGORY_NAME},
        )

        if existing:
            existing.delete()

        post = BlogPost.objects.create(
            title=ARTICLE_TITLE,
            slug=ARTICLE_SLUG,
            content=content,
            excerpt=ARTICLE_EXCERPT,
            featured_image=featured["path"],
            author=author,
            category=category,
            status="published" if options["publish"] else "draft",
            meta_description=META_DESCRIPTION,
            meta_keywords=META_KEYWORDS,
        )

        self.stdout.write(self.style.SUCCESS(f"\nCreated post id={post.id}"))
        self.stdout.write(f"  slug:     {post.slug}")
        self.stdout.write(f"  status:   {post.status}")
        self.stdout.write(f"  author:   {author.username}")
        self.stdout.write(f"  category: {category.name}")
        self.stdout.write(f"  featured: {featured['path']}")
        self.stdout.write(f"  inline images: {len(inline_urls)}")
        self.stdout.write(f"\n  Admin:  /admin/blog/blogpost/{post.id}/change/")
        self.stdout.write(f"  Public: /blog/{post.slug}/")
        if post.status == "draft":
            self.stdout.write(
                self.style.WARNING(
                    "\nPost is in DRAFT status. Review in admin, then change status to 'published' "
                    "(or re-run this command with --publish --force)."
                )
            )

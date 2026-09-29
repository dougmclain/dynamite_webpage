from django.db import models


def cover_storage():
    """The storage covers go to (settings CONTENT_PIPELINE["COVER_STORAGE"], else the default)."""
    from django.core.files.storage import default_storage, storages

    from . import conf
    alias = conf.get("COVER_STORAGE")
    return storages[alias] if alias else default_storage


class ContentBrief(models.Model):
    QUEUED, DRAFTING, DRAFTED, APPROVED, PUBLISHED, FAILED = (
        "queued", "drafting", "drafted", "approved", "published", "failed")
    STATUS_CHOICES = [(s, s.title()) for s in (QUEUED, DRAFTING, DRAFTED, APPROVED, PUBLISHED, FAILED)]

    # --- what to write (you or law_radar fill these in)
    title = models.CharField(max_length=200, help_text="Working title")
    target_keyword = models.CharField(max_length=200)
    secondary_keywords = models.TextField(blank=True, help_text="One per line")
    state = models.CharField(max_length=10, blank=True, help_text="WA, FL, CA… blank = national")
    is_law_post = models.BooleanField(default=True, help_text="Requires official statute/bill sources")
    category_name = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma separated")
    angle = models.TextField(blank=True, help_text="What the post must say / editorial notes")
    source_urls = models.TextField(blank=True, help_text="Official statute / bill / agency URLs, one per line")
    refresh_slug = models.CharField(max_length=200, blank=True,
                                    help_text="Slug of an existing post to rewrite in place instead of creating a new one")
    publish_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=QUEUED)

    # --- what the pipeline produced
    post_id = models.CharField(max_length=64, blank=True)
    post_slug = models.CharField(max_length=200, blank=True)
    draft_title = models.CharField(max_length=200, blank=True)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    faq = models.JSONField(default=list, blank=True)
    cover_spec = models.JSONField(default=dict, blank=True)
    cover = models.ImageField(upload_to="pipeline/covers/", storage=cover_storage, blank=True)
    cover_alt = models.CharField(max_length=255, blank=True)
    photo_queries = models.JSONField(default=list, blank=True, help_text="Stock-photo searches for the cover")
    cover_photo_id = models.CharField(max_length=80, blank=True)
    cover_credit = models.CharField(max_length=255, blank=True)
    cover_source_page = models.URLField(max_length=500, blank=True)
    rejected_photo_ids = models.JSONField(default=list, blank=True)
    source_text = models.TextField(blank=True, help_text="Official text fetched from source_urls (quotes are checked against this)")
    verification_report = models.TextField(blank=True)
    quotes_verified = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    tokens_used = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["publish_at", "created"]

    def __str__(self):
        return self.draft_title or self.title


class LawAlert(models.Model):
    """A bill the weekly law radar found. Turn the good ones into briefs."""
    NEW, BRIEFED, IGNORED = "new", "briefed", "ignored"
    state = models.CharField(max_length=4)
    bill_id = models.CharField(max_length=40, unique=True)
    bill_number = models.CharField(max_length=40)
    title = models.TextField()
    url = models.URLField(max_length=500)
    last_action = models.CharField(max_length=255, blank=True)
    last_action_date = models.DateField(null=True, blank=True)
    matched_query = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, default=NEW,
                              choices=[(NEW, "New"), (BRIEFED, "Briefed"), (IGNORED, "Ignored")])
    brief = models.ForeignKey(ContentBrief, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_action_date", "-created"]

    def __str__(self):
        return f"{self.state} {self.bill_number}: {self.title[:60]}"


class SearchSnapshot(models.Model):
    """Weekly Search Console numbers per page (Ahrefs API isn't on our plan)."""
    week_start = models.DateField()
    week_end = models.DateField()
    page = models.URLField(max_length=500)
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    ctr = models.FloatField(default=0)
    position = models.FloatField(default=0)
    top_query = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-week_start", "-clicks"]
        unique_together = [("week_start", "page")]


class Lead(models.Model):
    """One contact / demo / sign-up form submission, with where the visitor first came from.

    No personal details are stored here (the form's own email or model keeps those); this table
    only answers "which pages and channels bring inquiries?" for the weekly search report.
    """
    CHANNELS = [("search", "Search engine"), ("ai", "AI assistant"), ("paid", "Paid ads"),
                ("our_sites", "Our other sites"), ("referral", "Other website"), ("direct", "Direct / unknown")]
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    form = models.CharField(max_length=40, help_text="contact, signup, register…")
    channel = models.CharField(max_length=20, choices=CHANNELS, default="direct")
    landing_page = models.CharField(max_length=500, blank=True, help_text="First page of the visit")
    referrer = models.CharField(max_length=500, blank=True, help_text="Where the visit came from")
    form_page = models.CharField(max_length=500, blank=True, help_text="Page the form was sent from")
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.form} via {self.channel} — {self.landing_page or '?'} ({self.created:%Y-%m-%d})"

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from . import drafting, publisher
from .models import ContentBrief, LawAlert, Lead, SearchSnapshot


@admin.register(ContentBrief)
class ContentBriefAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "state", "publish_at", "quotes_ok", "thumb")
    list_filter = ("status", "state", "is_law_post")
    search_fields = ("title", "target_keyword", "draft_title")
    readonly_fields = ("cover_preview", "cover_credit_link", "verification_report", "quotes_verified", "post_id", "post_slug",
                       "tokens_used", "error", "created", "updated")
    fieldsets = (
        ("Brief", {"fields": ("title", "target_keyword", "secondary_keywords", "state", "is_law_post",
                              "category_name", "tags", "angle", "source_urls", "refresh_slug", "publish_at", "status")}),
        ("Review", {"fields": ("cover_preview", "cover_alt", "cover_credit_link", "photo_queries",
                               "quotes_verified", "verification_report", "error")}),
        ("Draft", {"classes": ("collapse",), "fields": ("draft_title", "seo_title", "meta_description",
                                                        "meta_keywords", "excerpt", "body", "faq", "cover_spec")}),
        ("System", {"classes": ("collapse",), "fields": ("post_id", "post_slug", "tokens_used", "created", "updated")}),
    )
    actions = ["draft_now", "new_cover", "approve", "publish_now"]

    @admin.display(boolean=True, description="Quotes OK")
    def quotes_ok(self, obj):
        return obj.quotes_verified if obj.body else None

    @admin.display(description="Cover")
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:40px;border-radius:4px">', obj.cover.url) if obj.cover else "—"

    @admin.display(description="Cover preview")
    def cover_preview(self, obj):
        return format_html('<img src="{}" style="max-width:600px;border-radius:8px">', obj.cover.url) if obj.cover else "—"

    @admin.display(description="Photo credit")
    def cover_credit_link(self, obj):
        if not obj.cover_credit:
            return "Illustration" if obj.cover else "—"
        return format_html('<a href="{}" target="_blank">{}</a>', obj.cover_source_page, obj.cover_credit)

    @admin.action(description="Draft now (Claude writes it + picks a photo)")
    def draft_now(self, request, qs):
        from . import conf
        if conf.get("DRAFT_ENGINE") != "api":
            self.message_user(request, "Drafts are written by your Cowork scheduled task (hoa-blog-writer). "
                                       "Run it now from Cowork > Scheduled.", messages.INFO)
            return
        for b in qs:
            try:
                drafting.draft(b)
                self.message_user(request, f"Drafted: {b}")
            except Exception as e:  # noqa: BLE001
                b.status, b.error = ContentBrief.FAILED, str(e)
                b.save(update_fields=["status", "error"])
                self.message_user(request, f"{b}: {e}", messages.ERROR)

    @admin.action(description="Different photo (edit Photo queries first to steer it)")
    def new_cover(self, request, qs):
        for b in qs:
            drafting.regenerate_cover(b)
        self.message_user(request, "New covers generated.")

    @admin.action(description="Approve (publishes at Publish at, or next hourly run)")
    def approve(self, request, qs):
        for b in qs:
            if b.status != ContentBrief.DRAFTED:
                self.message_user(request, f"{b}: only drafted posts can be approved.", messages.WARNING)
                continue
            if not b.quotes_verified and "override" not in b.angle.lower():
                self.message_user(request, f"{b}: statute quotes not verified — fix them, or add the word "
                                           f"'override' to the angle notes.", messages.ERROR)
                continue
            if not b.cover:
                self.message_user(request, f"{b}: no cover image.", messages.ERROR)
                continue
            b.status = ContentBrief.APPROVED
            b.publish_at = b.publish_at or timezone.now()
            b.save(update_fields=["status", "publish_at"])
            self.message_user(request, f"Approved: {b} (goes live {b.publish_at:%b %d %H:%M})")

    @admin.action(description="Publish now (approved only)")
    def publish_now(self, request, qs):
        for b in qs.filter(status=ContentBrief.APPROVED):
            publisher.publish(b)
            b.status = ContentBrief.PUBLISHED
            b.save(update_fields=["status"])
        self.message_user(request, "Published.")


@admin.register(LawAlert)
class LawAlertAdmin(admin.ModelAdmin):
    list_display = ("state", "bill_number", "title", "last_action_date", "last_action", "status")
    list_filter = ("status", "state")
    search_fields = ("title", "bill_number")
    actions = ["make_brief", "ignore"]

    @admin.action(description="Turn into a content brief")
    def make_brief(self, request, qs):
        for a in qs.filter(brief__isnull=True):
            b = ContentBrief.objects.create(
                title=f"{a.state} {a.bill_number}: what it changes for HOA and condo boards",
                target_keyword=f"{a.state} {a.bill_number} HOA", state=a.state, is_law_post=True,
                angle=f"New legislation: {a.title}\nLast action: {a.last_action} ({a.last_action_date}).\n"
                      f"Add the official bill text / enrolled version URL and the amended statute URL before drafting.",
                source_urls=a.url, status=ContentBrief.QUEUED)
            a.brief, a.status = b, LawAlert.BRIEFED
            a.save(update_fields=["brief", "status"])
        self.message_user(request, "Briefs created — add sources, then Draft now.")

    @admin.action(description="Ignore")
    def ignore(self, request, qs):
        qs.update(status=LawAlert.IGNORED)


@admin.register(SearchSnapshot)
class SearchSnapshotAdmin(admin.ModelAdmin):
    list_display = ("week_start", "page", "clicks", "impressions", "ctr_pct", "position", "top_query")
    list_filter = ("week_start",)
    search_fields = ("page", "top_query")

    @admin.display(description="CTR")
    def ctr_pct(self, obj):
        return f"{obj.ctr * 100:.1f}%"


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created", "form", "channel", "landing_page", "form_page", "referrer")
    list_filter = ("form", "channel", "created")
    search_fields = ("landing_page", "referrer", "form_page", "utm_campaign")
    readonly_fields = [f.name for f in Lead._meta.fields]

    def has_add_permission(self, request):
        return False

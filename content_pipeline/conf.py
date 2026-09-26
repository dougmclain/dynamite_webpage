"""Settings for the content pipeline. Override any key in settings.CONTENT_PIPELINE."""
from django.conf import settings

DEFAULTS = {
    # which site this repo is: "dynamite" | "hoafiscal" | "hoameeting"
    "SITE_KEY": "dynamite",
    "SITE_URL": "https://dynamitemanagement.com",
    # Who writes the drafts:
    #   "cowork" = a Claude Cowork scheduled task (your Max plan) pulls briefs from /pipeline/api/ and posts drafts back
    #   "api"    = Render cron calls the Anthropic API itself (needs ANTHROPIC_API_KEY, billed separately)
    "DRAFT_ENGINE": "cowork",
    # Claude (only used when DRAFT_ENGINE = "api")
    "MODEL": "claude-opus-5-5",
    "MAX_TOKENS": 32000,
    # the site's blog models
    "POST_MODEL": "blog.Post",
    "CATEGORY_MODEL": "blog.Category",
    "TAG_MODEL": "blog.Tag",
    "BODY_FORMAT": "markdown",          # "markdown" or "html" (TinyMCE sites)
    "FIELD_MAP": {
        "title": "title", "slug": "slug", "body": "content", "excerpt": "excerpt",
        "seo_title": "seo_title", "meta_description": "meta_description",
        "meta_keywords": "meta_keywords", "structured_data": "structured_data",
        "image": "featured_image",            # ImageField/CloudinaryField (preferred)
        "image_static": "featured_image_static",  # static path string (fallback)
        "image_alt": "featured_image_alt",
        "status": "status", "published_at": "published_at",
        "author": "author", "category": "category", "tags": "tags",
    },
    "STATUS_VALUES": {"draft": "draft", "published": "published"},
    "AUTHOR_USERNAME": None,             # username of "Doug McLain" staff user
    "FIELD_LIMITS": {"title": 200, "meta_description": 160, "meta_keywords": 255},
    # covers: "photo" (Pexels, then Openverse CC0) with illustration fallback, or "illustration"
    "COVER_MODE": "photo",
    # other sites' sitemaps, for cross-links
    "CROSS_SITE_SITEMAPS": [],
    # law radar (turn on in ONE site only — the dynamite repo)
    "RUN_LAW_RADAR": False,
    "LEGISCAN_STATES": ["WA", "OR", "CA", "FL", "AZ", "TX", "CO", "NV", "GA", "IL", "NC", "VA"],
    "LEGISCAN_QUERIES": ["homeowners association", "common interest community", "condominium association"],
    # search console property, e.g. "sc-domain:hoafiscal.com"
    "GSC_PROPERTY": None,
    # drafting will refuse law posts without official source URLs
    "REQUIRE_SOURCES_FOR_LAW": True,
}


def get(key):
    user = getattr(settings, "CONTENT_PIPELINE", {})
    if key == "FIELD_MAP":
        merged = dict(DEFAULTS["FIELD_MAP"])
        merged.update(user.get("FIELD_MAP", {}))
        return merged
    return user.get(key, DEFAULTS[key])

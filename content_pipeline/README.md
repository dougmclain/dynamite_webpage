# content_pipeline: blog automation for dynamitemanagement.com, hoafiscal.com, hoameeting.com

One Django app, dropped into each of the three repos.

## Who does what

| Step | Where it runs | Cost |
|---|---|---|
| Write the post and pick the cover photo | **Claude Cowork scheduled task** using the `hoa-blog-writer` skill (your Max plan) | included in Max |
| Find new laws and queue briefs | Cowork scheduled task using the `hoa-law-radar` skill | included in Max |
| Fetch official statute text and check every quote word-for-word | the site (Render) | – |
| Crop and store the photo, save the post as a DRAFT | the site | – |
| Approve | you, in `/admin/ > Content pipeline > Content briefs` | – |
| Publish on schedule, weekly Search Console numbers | one Render cron per site (`pipeline_cron`) | small Render cron |

Cowork can never publish a post. Its token only lets it read briefs and submit drafts. Approval happens behind your
admin login.

(Alternative: set `"DRAFT_ENGINE": "api"` and add `ANTHROPIC_API_KEY` to have the Render cron write drafts itself.
That is billed separately from Max.)

## 1. Install (per repo)

1. Copy the `content_pipeline/` folder into the repo root.
2. Add the lines from `requirements-pipeline.txt` to `requirements.txt`. `anthropic` is only needed in "api" mode.
3. Update `settings.py`:

```python
INSTALLED_APPS += ["content_pipeline"]
CONTENT_PIPELINE = {
    "SITE_KEY": "dynamite",                      # or "hoafiscal" / "hoameeting"
    "SITE_URL": "https://dynamitemanagement.com",
    "DRAFT_ENGINE": "cowork",
    "BODY_FORMAT": "html",                       # TinyMCE sites = "html"; hoafiscal (Markdown) = "markdown"
    "AUTHOR_USERNAME": "<Doug's staff username>",
    "GSC_PROPERTY": "https://dynamitemanagement.com/",   # hoafiscal: "sc-domain:hoafiscal.com"
    "CROSS_SITE_SITEMAPS": ["https://www.hoafiscal.com/sitemap.xml", "https://hoameeting.com/sitemap.xml"],
    # "RUN_LAW_RADAR": False,                    # LegiScan radar; not needed when the Cowork law-radar skill is used
    # "FIELD_MAP": {"body": "body"},             # only if pipeline_check says a field name differs
}
```

4. Update `urls.py`:

```python
path("pipeline/api/", include("content_pipeline.urls")),
```

5. Run `python manage.py migrate`, then `python manage.py pipeline_check`. Fix anything shown in red.
6. Run `python manage.py seed_budget_briefs` to load the fall budget-season slate.

## 2. Render environment

| Var | Notes |
|---|---|
| `PIPELINE_TOKEN` | Generate a long random string, for example with `python3 -c "import secrets;print(secrets.token_hex(32))"`. Use the same value on all three sites. |
| `PEXELS_API_KEY` | Free at pexels.com/api. Without it, the pipeline falls back to Openverse CC0 photos. |
| `GSC_SERVICE_ACCOUNT_JSON` | Optional, for the weekly Search Console numbers. |

## 3. Render cron job (one per site)

- Schedule: `5 * * * *`
- Command: `python manage.py pipeline_cron`

Each run publishes approved posts that are due. On Mondays it also pulls the Search Console report. In "cowork" mode
it does no writing.

## 4. Cowork

1. **Upload the skills.** In Claude, go to Settings > Capabilities > Skills and upload `hoa-blog-writer.skill.zip`
   and `hoa-law-radar.skill.zip`.
2. **Create a Cowork project** called "HOA blogs". In its instructions, put `Pipeline token: <PIPELINE_TOKEN>`.
3. **Allow network access** to dynamitemanagement.com, www.hoafiscal.com, and hoameeting.com if Cowork asks.
4. **Create the scheduled tasks** (sidebar > Scheduled > New task):
   - **Tue & Thu, 5:00am:** "Run hoa-blog-writer: write the next 2 briefs across all three sites and give me the review links."
   - **Mondays, 6:00am:** "Run hoa-law-radar for the last 30 days, then run hoa-blog-writer's blog status."

## API (used by the skills)

All endpoints require the header `X-Pipeline-Token`. See `api.py` for the endpoints: `queue`, `context`, `photos`,
`draft`, `create brief`, and `status`. Photo IDs are re-fetched from Pexels or Openverse on the server, so no
client-supplied image URL is ever downloaded.

## Covers

- Real photos come from Pexels, with Openverse CC0 as the fallback.
- Photos are cropped to 1200×630. A photo that's already used on the site, or that you rejected, is never picked
  again.
- Pexels covers get an automatic "Cover: Photo by … on Pexels" credit line, as their API guidelines ask.
- The branded illustration is used only if no photo can be found.
- Covers are saved through the post's image field, so each site's media storage is used (Cloudinary on Dynamite and
  hoameeting, Azure on hoafiscal).
- To change a cover: edit **Photo queries** on the brief, then run the admin action **Different photo**.
- `python manage.py backfill_covers` gives every post that has no cover a real photo. In "cowork" mode, run it from
  a Cowork session.

## og:image fix (dynamitemanagement.com)

```django
{% load pipeline_tags %}
<meta property="og:image" content="{{ post.featured_image.url|absolute_url:request }}">
```

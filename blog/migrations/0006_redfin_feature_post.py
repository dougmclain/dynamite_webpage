"""Data migration: publish the "featured on Redfin" post.

Redfin quoted Doug McLain in "How to Rent Out Your House" (Oct 20, 2026). The
collaboration asks us to link the article from our site using one of their
press-kit options with the links left unchanged, so the post opens with their
"Customized text" option verbatim. Running as a data migration publishes it on
production during `manage.py migrate` on deploy. Skips if the slug already
exists; the reverse deletes only this post.
"""
from django.db import migrations
from django.utils import timezone

SLUG = "dynamite-featured-redfin-how-to-rent-a-house"

TITLE = "Dynamite Management Featured on Redfin: Renting Out a Home in an HOA"
SEO_TITLE = "Featured on Redfin: Renting Out a Home in an HOA"
EXCERPT = (
    "Doug McLain of Dynamite Management was featured as an expert in Redfin's guide, "
    "How to Rent Out Your House. His advice: check your HOA's rental rules before you "
    "sign a lease."
)
META_DESCRIPTION = (
    "Doug McLain of Dynamite Management shares advice in Redfin's guide to renting out "
    "your house: check your HOA's rental rules before you sign a lease."
)
META_KEYWORDS = (
    "renting out your house, HOA rental restrictions, condo rental rules, "
    "first-time landlord, Redfin"
)
CATEGORY_NAME = "News"
CATEGORY_SLUG = "news"
FEATURED_IMAGE_STATIC = "images/blog/redfin-renting-out-your-house.jpg"

ARTICLE_URL = "https://www.redfin.com/blog/how-to-rent-a-house/"

CONTENT_HTML = f"""<p>We were featured as an expert on <a href="http://redfin.com">Redfin</a>, Powered by <a href="http://rocketmortgage.com">Rocket</a>! Read the full article here: <a href="{ARTICLE_URL}">How to Rent Out Your House | Redfin</a></p>

<p>Redfin's guide walks first-time landlords through the whole process, starting with whether you can legally rent out your home at all. That first step is where HOA and condo owners most often get caught off guard. Here's what Doug McLain, owner of Dynamite Management, told Redfin:</p>

<blockquote>
<p>&ldquo;The fines for breaking HOA or condo association rules land on you, not your tenant. You're also still on the hook for assessments or any damage your tenant causes to the common areas. A quick call to your association's manager before you sign a lease can save you from an expensive surprise.&rdquo;</p>
<p>Source: <a href="{ARTICLE_URL}">How to Rent Out Your House | Redfin</a></p>
</blockquote>

<h2>Thinking About Renting Out a Unit in Your Community?</h2>
<p>Before you list it, pull your association's declaration, bylaws and rules and look for:</p>
<ul>
<li>A rental cap or waiting list</li>
<li>A minimum lease term (many associations prohibit short-term rentals)</li>
<li>Tenant registration or lease-copy requirements</li>
<li>Who pays fines and damage to common areas (usually the owner)</li>
</ul>

<p>If you're a board looking for help writing or enforcing a fair rental policy, <a href="/contact/">contact Dynamite Management</a>.</p>
"""


def create_post(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    Category = apps.get_model("blog", "Category")
    User = apps.get_model("auth", "User")

    if BlogPost.objects.filter(slug=SLUG).exists():
        return
    author = User.objects.filter(is_staff=True).order_by("id").first()
    if not author:
        # Fresh databases (tests, local dev) have no staff user to credit.
        return
    category = (
        Category.objects.filter(slug=CATEGORY_SLUG).first()
        or Category.objects.filter(name=CATEGORY_NAME).first()
        or Category.objects.create(name=CATEGORY_NAME, slug=CATEGORY_SLUG)
    )
    BlogPost.objects.create(
        title=TITLE,
        slug=SLUG,
        seo_title=SEO_TITLE,
        content=CONTENT_HTML,
        excerpt=EXCERPT,
        featured_image_static=FEATURED_IMAGE_STATIC,
        author=author,
        category=category,
        status="published",
        published_at=timezone.now(),
        meta_description=META_DESCRIPTION,
        meta_keywords=META_KEYWORDS,
    )


def delete_post(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogPost.objects.filter(slug=SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0005_current_cpa_wording"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(create_post, delete_post)]

from django.db import migrations


# Maps each existing published post (by slug) to a featured image that is
# committed to the repo under static/images/blog/ and served by WhiteNoise.
# These replace the old MEDIA uploads that lived on Render's ephemeral disk and
# 404'd after every deploy. Running as a data migration means production's
# Postgres rows are updated automatically during `manage.py migrate` on deploy.
SLUG_TO_STATIC = {
    "best-hoa-accounting-service-providers-2026": "images/blog/accounting-providers.jpg",
    "wucioa-2028-what-every-washington-hoa-board-needs-to-do-now": "images/blog/wucioa-washington.jpg",
    "why-self-managed-hoas-need-a-backend-financial-manager-more-than-ever": "images/blog/self-managed-financial-manager.jpg",
    "how-much-cash-should-your-hoa-keep-in-its-operating-account": "images/blog/operating-account-cash.jpg",
}


def set_static_images(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    for slug, static_path in SLUG_TO_STATIC.items():
        BlogPost.objects.filter(slug=slug).update(featured_image_static=static_path)


def unset_static_images(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogPost.objects.filter(slug__in=SLUG_TO_STATIC).update(featured_image_static="")


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_blogpost_featured_image_static"),
    ]

    operations = [
        migrations.RunPython(set_static_images, unset_static_images),
    ]

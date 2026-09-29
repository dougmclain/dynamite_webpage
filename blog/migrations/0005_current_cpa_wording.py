"""Data migration: Doug McLain renewed his Washington CPA license (2026).

Replaces the old "former CPA" wording stored in blog posts (body, excerpt,
meta description, structured data). CharFields are only changed when the new
text still fits the column. Safe to re-run; the reverse is a no-op.
"""
from django.db import migrations

REPLACEMENTS = [
    ("a former CPA who audited association financial statements",
     "a CPA licensed in Washington who has audited association financial statements"),
    ("A former CPA's guide", "A CPA's guide"),
    ("A former CPA&#x27;s guide", "A CPA&#x27;s guide"),
    ("A former CPA&#39;s guide", "A CPA&#39;s guide"),
    ("A former HOA auditor compares", "A CPA and longtime HOA auditor compares"),
    ("a former HOA auditor", "a CPA and longtime HOA auditor"),
    ("a former CPA", "a CPA licensed in Washington"),
    ("A former CPA", "A CPA licensed in Washington"),
    ("former CPA", "CPA"),
]

FIELDS = ['content', 'excerpt', 'meta_description', 'structured_data']


def forwards(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    for post in BlogPost.objects.all():
        changed = []
        for name in FIELDS:
            old = getattr(post, name, None)
            if not old:
                continue
            new = old
            for a, b in REPLACEMENTS:
                new = new.replace(a, b)
            if new == old:
                continue
            max_len = BlogPost._meta.get_field(name).max_length
            if max_len and len(new) > max_len:
                continue
            setattr(post, name, new)
            changed.append(name)
        if changed:
            BlogPost.objects.filter(pk=post.pk).update(
                **{n: getattr(post, n) for n in changed}
            )


class Migration(migrations.Migration):

    dependencies = [("blog", "0004_blogpost_seo_title_structured_data_blogredirect")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

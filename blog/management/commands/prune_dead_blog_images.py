import re

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import BlogPost

# An <img> whose src points anywhere under MEDIA (".../media/<name>"). Captures
# the storage-relative name (everything after "/media/") so we can ask the
# active storage backend whether the file still exists. Matches absolute,
# root-relative and ../-relative srcs alike (TinyMCE stores the last form).
INLINE_MEDIA_IMG = re.compile(
    r'<img\b[^>]*?\bsrc=["\'][^"\']*?/media/(?P<name>[^"\']+?)["\'][^>]*?>',
    re.IGNORECASE,
)
# Paragraphs left empty once their only child <img> is removed.
EMPTY_P = re.compile(r"<p>\s*</p>", re.IGNORECASE)


def _missing(name):
    """True when ``name`` is provably absent from the active storage backend.
    On any storage error we return False so the data is never touched blindly."""
    try:
        return not default_storage.exists(name)
    except Exception:
        return False


class Command(BaseCommand):
    help = (
        "Remove references to blog images whose file no longer exists in the "
        "active storage backend. Render's MEDIA disk is ephemeral and wiped on "
        "every deploy, so a reference to a vanished upload renders a broken "
        "<img>. This clears two vectors: the featured_image field, and <img> "
        "tags embedded in post body content. It only removes references to "
        "provably-missing files (when Cloudinary is active and the file is "
        "present, it is kept), so it is safe to run on every deploy."
    )

    def handle(self, *args, **options):
        featured_cleared = self._prune_featured()
        inline_cleared = self._prune_inline()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Cleared {featured_cleared} featured + {inline_cleared} "
                "inline dead image reference(s)."
            )
        )

    def _prune_featured(self):
        cleared = 0
        posts = BlogPost.objects.exclude(featured_image="").exclude(
            featured_image__isnull=True
        )
        for post in posts:
            name = post.featured_image.name
            if _missing(name):
                post.featured_image = ""
                post.save(update_fields=["featured_image", "updated_at"])
                cleared += 1
                self.stdout.write(
                    f"  featured cleared [id={post.id}] {post.slug} (missing: {name})"
                )
        return cleared

    def _prune_inline(self):
        cleared = 0
        for post in BlogPost.objects.filter(content__icontains="/media/"):
            removed = []

            def repl(match):
                if _missing(match.group("name")):
                    removed.append(match.group("name"))
                    return ""
                return match.group(0)

            new_content = INLINE_MEDIA_IMG.sub(repl, post.content)
            if removed:
                new_content = EMPTY_P.sub("", new_content)
                post.content = new_content
                post.save(update_fields=["content", "updated_at"])
                cleared += len(removed)
                self.stdout.write(
                    f"  inline removed {len(removed)} from [id={post.id}] {post.slug}"
                )
        return cleared

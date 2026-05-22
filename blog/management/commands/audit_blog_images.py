from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import BlogPost


class Command(BaseCommand):
    help = (
        "List BlogPost rows whose featured_image references a file that does not "
        "exist in the configured storage backend. Useful after a deploy that "
        "wiped Render's ephemeral filesystem, so you know which posts need a "
        "re-upload via the Django admin."
    )

    def handle(self, *args, **options):
        posts = BlogPost.objects.exclude(featured_image="").exclude(featured_image__isnull=True)
        missing = []
        ok = 0
        for post in posts:
            name = post.featured_image.name
            if default_storage.exists(name):
                ok += 1
            else:
                missing.append(post)

        self.stdout.write(self.style.SUCCESS(f"Checked {posts.count()} posts with featured_image set."))
        self.stdout.write(f"  OK:      {ok}")
        self.stdout.write(self.style.WARNING(f"  Missing: {len(missing)}"))

        if not missing:
            return

        self.stdout.write("\nPosts that need a featured image re-uploaded:")
        for post in missing:
            self.stdout.write(
                f"  [id={post.id}] {post.status:9} {post.slug}  ->  {post.featured_image.name}"
            )
        self.stdout.write(
            "\nFix by opening each post in /admin/blog/blogpost/, uploading a new "
            "featured image, and saving. With Cloudinary configured, the new "
            "upload will be stored remotely and survive future deploys."
        )

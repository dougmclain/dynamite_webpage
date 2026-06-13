from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import BlogPost


class Command(BaseCommand):
    help = (
        "Clear featured_image references whose underlying file no longer exists "
        "in the active storage backend. On Render the MEDIA disk is ephemeral and "
        "wiped on every deploy, so a reference to a vanished upload renders a "
        "broken <img>. This command makes the data self-heal: it only clears "
        "references that provably point at a missing file, so it is safe to run "
        "on every deploy. Posts whose image is gone fall back to the static "
        "featured image (if set) or the template placeholder."
    )

    def handle(self, *args, **options):
        cleared = 0
        posts = (
            BlogPost.objects.exclude(featured_image="")
            .exclude(featured_image__isnull=True)
        )
        for post in posts:
            name = post.featured_image.name
            try:
                exists = default_storage.exists(name)
            except Exception as exc:  # storage backend unreachable: never touch data
                self.stderr.write(
                    f"  skip [id={post.id}] {post.slug}: storage check failed ({exc})"
                )
                continue
            if not exists:
                post.featured_image = ""
                post.save(update_fields=["featured_image", "updated_at"])
                cleared += 1
                self.stdout.write(
                    f"  cleared [id={post.id}] {post.slug} (missing file: {name})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Cleared {cleared} dead featured_image reference(s)."
            )
        )

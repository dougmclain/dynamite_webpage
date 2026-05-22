from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from blog.models import BlogPost
from staff_portal.services import fetch_pexels_image


class Command(BaseCommand):
    help = (
        "Find BlogPost rows whose featured_image is missing from storage and "
        "re-fetch a Pexels image using the post title as the query. Saves "
        "through Django's storage backend, so when Cloudinary is configured "
        "the new image lands in Cloudinary and persists across deploys."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List posts that would be re-fetched without making changes.",
        )
        parser.add_argument(
            "--id",
            type=int,
            help="Only re-fetch for this BlogPost id (skips the missing-file check).",
        )

    def handle(self, *args, **options):
        if options["id"]:
            posts = BlogPost.objects.filter(pk=options["id"])
        else:
            posts = [
                p
                for p in BlogPost.objects.exclude(featured_image="").exclude(featured_image__isnull=True)
                if not default_storage.exists(p.featured_image.name)
            ]

        if not posts:
            self.stdout.write(self.style.SUCCESS("No posts need re-fetching."))
            return

        self.stdout.write(f"Posts to refetch: {len(posts)}")
        for post in posts:
            self.stdout.write(f"  [id={post.id}] {post.slug} (was: {post.featured_image.name})")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        fixed = 0
        failed = []
        for post in posts:
            image_data = fetch_pexels_image(post.title)
            if not image_data:
                failed.append(post)
                self.stdout.write(self.style.ERROR(f"  FAILED to fetch image for id={post.id}"))
                continue
            post.featured_image = image_data["path"]
            post.save(update_fields=["featured_image", "updated_at"])
            fixed += 1
            self.stdout.write(self.style.SUCCESS(f"  OK   id={post.id} -> {image_data['path']}"))

        self.stdout.write(self.style.SUCCESS(f"\nFixed: {fixed}"))
        if failed:
            self.stdout.write(
                self.style.WARNING(
                    f"Failed: {len(failed)} (check PEXELS_API_KEY env var and Pexels availability)"
                )
            )

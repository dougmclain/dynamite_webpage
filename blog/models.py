from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import re


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, max_length=500)
    featured_image = models.ImageField(
        upload_to="blog/featured_images/", blank=True, null=True
    )
    # Path (relative to STATIC_URL) of a featured image committed to the repo and
    # served by WhiteNoise. Unlike featured_image — uploaded to MEDIA on Render's
    # ephemeral disk and wiped on every deploy — a static image ships with the
    # code and never disappears. When set it takes precedence; see
    # featured_image_src / has_featured_image below.
    featured_image_static = models.CharField(max_length=200, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-set published_at
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        # Auto-generate excerpt from content
        if not self.excerpt and self.content:
            clean_text = re.sub(r"<[^>]+>", "", self.content)
            self.excerpt = clean_text[:300].rsplit(" ", 1)[0] + "..."

        super().save(*args, **kwargs)

    @property
    def _media_upload_persists(self):
        """True only when an uploaded ``featured_image`` will actually survive a
        Render deploy. MEDIA uploads live on Render's ephemeral disk and are
        wiped on every deploy unless Cloudinary is the active media backend
        (``CLOUDINARY_URL`` set). When it isn't, linking the upload would render
        a broken <img> after the next deploy, so we treat the post as having no
        image and let the template fall back to its placeholder instead."""
        from django.conf import settings

        return bool(self.featured_image) and getattr(settings, "USE_CLOUDINARY", False)

    @staticmethod
    def _static_url(path):
        from django.conf import settings
        from django.templatetags.static import static

        try:
            return static(path)
        except ValueError:
            # Missing manifest entry (e.g. collectstatic hasn't run yet). Fall
            # back to the unhashed static URL rather than crash the page.
            return settings.STATIC_URL + path

    @property
    def featured_image_src(self):
        """URL for the featured image. Prefers the persistent static asset
        committed to the repo, then a Cloudinary-backed upload. Never returns an
        ephemeral /media/ URL that would 404 after a deploy. Returns "" when the
        post has no image guaranteed to persist."""
        if self.featured_image_static:
            return self._static_url(self.featured_image_static)
        if self._media_upload_persists:
            return self.featured_image.url
        return ""

    @property
    def has_featured_image(self):
        return bool(self.featured_image_static) or self._media_upload_persists

    @property
    def reading_time(self):
        clean_text = re.sub(r"<[^>]+>", "", self.content)
        word_count = len(clean_text.split())
        minutes = max(1, round(word_count / 200))
        return minutes

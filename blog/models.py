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
    def featured_image_src(self):
        """URL for the featured image, preferring the persistent static asset
        over the ephemeral MEDIA upload. Returns "" when neither is set."""
        if self.featured_image_static:
            from django.conf import settings
            from django.templatetags.static import static

            try:
                return static(self.featured_image_static)
            except ValueError:
                # Missing manifest entry (e.g. collectstatic hasn't run yet).
                # Fall back to the unhashed static URL rather than crash the page.
                return settings.STATIC_URL + self.featured_image_static
        if self.featured_image:
            return self.featured_image.url
        return ""

    @property
    def has_featured_image(self):
        return bool(self.featured_image_static or self.featured_image)

    @property
    def reading_time(self):
        clean_text = re.sub(r"<[^>]+>", "", self.content)
        word_count = len(clean_text.split())
        minutes = max(1, round(word_count / 200))
        return minutes

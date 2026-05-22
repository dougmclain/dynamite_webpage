from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost, Category


STATES = [
    "california", "florida", "georgia", "hawaii", "illinois",
    "new-york", "oregon", "texas", "washington",
]

CITIES = [
    ("california", "san-francisco"),
    ("florida", "miami"),
    ("illinois", "chicago"),
    ("oregon", "portland"),
]


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        return [
            "core:home",
            "core:about",
            "core:financial_management",
            "core:hoa_taxes",
            "core:wa_condo",
            "core:contact",
            "core:privacy_policy",
            "core:terms_of_service",
            "blog:post_list",
        ]

    def location(self, item):
        return reverse(item)


class StateSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        return STATES

    def location(self, item):
        return reverse("core:state_detail", kwargs={"location_name": item})


class CitySitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        return CITIES

    def location(self, item):
        state, city = item
        return reverse("core:city_detail", kwargs={"state_name": state, "location_name": city})


class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return BlogPost.objects.filter(status="published")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("blog:post_detail", kwargs={"slug": obj.slug})


class BlogCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Category.objects.filter(posts__status="published").distinct()

    def location(self, obj):
        return reverse("blog:category_detail", kwargs={"slug": obj.slug})


sitemaps = {
    "static": StaticViewSitemap,
    "states": StateSitemap,
    "cities": CitySitemap,
    "posts": BlogPostSitemap,
    "categories": BlogCategorySitemap,
}

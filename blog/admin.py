from django.contrib import admin
from .models import BlogRedirect, Category, Tag, BlogPost


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "published_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"


@admin.register(BlogRedirect)
class BlogRedirectAdmin(admin.ModelAdmin):
    list_display = ("old_slug", "post", "created_at")
    search_fields = ("old_slug", "post__title", "post__slug")
    raw_id_fields = ("post",)

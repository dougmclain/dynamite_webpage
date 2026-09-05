from django.core.paginator import Paginator
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import BlogPost, BlogRedirect, Category, Tag

SITE = "https://dynamitemanagement.com"


def _paged_canonical(path, page_obj):
    """Self-referencing canonical for a paginated archive.

    Page 2+ canonicalises to itself (with ?page=N) rather than to page 1, so
    the posts that only appear on later pages stay discoverable.
    """
    url = f"{SITE}{path}"
    if page_obj.number > 1:
        url += f"?page={page_obj.number}"
    return url


def post_list(request):
    posts = (
        BlogPost.objects.filter(status="published")
        .select_related("author", "category")
        .prefetch_related("tags")
    )
    categories = Category.objects.all()

    category_slug = request.GET.get("category")
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts = paginator.get_page(page)

    return render(
        request,
        "blog/post_list.html",
        {
            "posts": posts,
            "categories": categories,
            "current_category": category_slug,
            "canonical_url": _paged_canonical(reverse("blog:post_list"), posts),
        },
    )


def post_detail(request, slug):
    post = (
        BlogPost.objects.select_related("author", "category")
        .prefetch_related("tags")
        .filter(slug=slug, status="published")
        .first()
    )
    if post is None:
        # A renamed or replaced post leaves a BlogRedirect behind; honour it
        # with a 301 so old links and search results keep working.
        moved = (
            BlogRedirect.objects.select_related("post")
            .filter(old_slug=slug, post__status="published")
            .first()
        )
        if moved is not None:
            return HttpResponsePermanentRedirect(moved.post.get_absolute_url())
        raise Http404("No published post with that slug.")

    related_posts = (
        BlogPost.objects.filter(status="published", category=post.category)
        .exclude(pk=post.pk)
        .select_related("author", "category")[:3]
    )

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "related_posts": related_posts,
        },
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = (
        BlogPost.objects.filter(status="published", category=category)
        .select_related("author", "category")
        .prefetch_related("tags")
    )

    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts = paginator.get_page(page)

    return render(
        request,
        "blog/category_detail.html",
        {
            "category": category,
            "posts": posts,
            "canonical_url": _paged_canonical(
                reverse("blog:category_detail", kwargs={"slug": category.slug}), posts,
            ),
        },
    )


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = (
        BlogPost.objects.filter(status="published", tags=tag)
        .select_related("author", "category")
        .prefetch_related("tags")
    )

    paginator = Paginator(posts, 9)
    page = request.GET.get("page")
    posts = paginator.get_page(page)

    return render(
        request,
        "blog/tag_detail.html",
        {
            "tag": tag,
            "posts": posts,
            # Tag archives are thin; keep them crawlable for link equity but
            # out of the index (they are not in the sitemap either).
            "robots_meta": "noindex, follow",
            "canonical_url": _paged_canonical(
                reverse("blog:tag_detail", kwargs={"slug": tag.slug}), posts,
            ),
        },
    )

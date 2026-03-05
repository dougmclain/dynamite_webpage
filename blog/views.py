from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost, Category, Tag


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
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related("author", "category").prefetch_related("tags"),
        slug=slug,
        status="published",
    )

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
        },
    )

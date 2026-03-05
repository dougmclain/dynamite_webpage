import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from blog.models import BlogPost
from .decorators import staff_required
from .forms import AIGenerationForm, BlogPostForm, StaffLoginForm
from .services import BlogGenerationError, generate_blog_post


def staff_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("staff_portal:dashboard")

    if request.method == "POST":
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect("staff_portal:dashboard")
            else:
                messages.error(request, "You do not have staff access.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = StaffLoginForm()

    return render(request, "staff_portal/login.html", {"form": form})


def staff_logout(request):
    logout(request)
    return redirect("/")


@staff_required
def dashboard(request):
    total_posts = BlogPost.objects.count()
    published_posts = BlogPost.objects.filter(status="published").count()
    draft_posts = BlogPost.objects.filter(status="draft").count()
    recent_posts = BlogPost.objects.select_related("author", "category").order_by("-created_at")[:5]

    return render(
        request,
        "staff_portal/dashboard.html",
        {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "recent_posts": recent_posts,
        },
    )


@staff_required
def post_list(request):
    posts = BlogPost.objects.select_related("author", "category").order_by("-created_at")

    status_filter = request.GET.get("status")
    if status_filter in ("draft", "published"):
        posts = posts.filter(status=status_filter)

    return render(request, "staff_portal/post_list.html", {"posts": posts, "status_filter": status_filter})


@staff_required
def post_create(request):
    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            # Apply AI-generated image if provided
            ai_image_path = request.POST.get("ai_featured_image", "")
            if ai_image_path and not request.FILES.get("featured_image"):
                full_path = os.path.join(settings.MEDIA_ROOT, ai_image_path)
                if os.path.exists(full_path):
                    post.featured_image = ai_image_path

            post.save()
            form.save_m2m()
            messages.success(request, "Post created successfully!")
            return redirect("staff_portal:post_edit", pk=post.pk)
    else:
        form = BlogPostForm()

    ai_form = AIGenerationForm()
    return render(request, "staff_portal/post_form.html", {"form": form, "ai_form": ai_form, "is_edit": False})


@staff_required
def post_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post_obj = form.save(commit=False)

            # Apply AI-generated image if provided
            ai_image_path = request.POST.get("ai_featured_image", "")
            if ai_image_path and not request.FILES.get("featured_image"):
                full_path = os.path.join(settings.MEDIA_ROOT, ai_image_path)
                if os.path.exists(full_path):
                    post_obj.featured_image = ai_image_path

            post_obj.save()
            form.save_m2m()
            messages.success(request, "Post updated successfully!")
            return redirect("staff_portal:post_edit", pk=post.pk)
    else:
        form = BlogPostForm(instance=post)

    ai_form = AIGenerationForm()
    return render(request, "staff_portal/post_form.html", {"form": form, "ai_form": ai_form, "post": post, "is_edit": True})


@staff_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    post.delete()
    messages.success(request, "Post deleted successfully.")
    return redirect("staff_portal:post_list")


@staff_required
def generate_blog_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    form = AIGenerationForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "Invalid form data", "details": form.errors}, status=400)

    try:
        result = generate_blog_post(
            topic=form.cleaned_data["topic"],
            tone=form.cleaned_data["tone"],
            length=int(form.cleaned_data["length"]),
            audience=form.cleaned_data["audience"],
        )
        return JsonResponse({"success": True, "data": result})
    except BlogGenerationError as e:
        return JsonResponse({"error": str(e)}, status=500)

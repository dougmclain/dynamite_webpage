import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from blog.models import BlogPost
from .decorators import staff_required
from .forms import AIGenerationForm, BlogPostForm, StaffLoginForm
from .services import BlogGenerationError, fetch_pexels_image_or_raise, generate_blog_post


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

            # Apply AI-generated image if provided. The path was produced by our
            # own fetch endpoint, so we trust it instead of calling
            # default_storage.exists() (unreliable under Cloudinary). Match the
            # folder anywhere in the path: local FileSystemStorage returns
            # "blog/featured_images/x.jpg" while Cloudinary returns the public_id
            # "media/blog/featured_images/x" (prefixed, extension stripped).
            ai_image_path = request.POST.get("ai_featured_image", "").strip()
            if ai_image_path and not request.FILES.get("featured_image"):
                if "blog/featured_images/" in ai_image_path:
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

            # Apply AI-generated image if provided (see post_create for why we
            # match the folder anywhere rather than requiring a prefix).
            ai_image_path = request.POST.get("ai_featured_image", "").strip()
            if ai_image_path and not request.FILES.get("featured_image"):
                if "blog/featured_images/" in ai_image_path:
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


@staff_required
@require_POST
def fetch_image_api(request):
    """Fetch a single featured image for a given topic (e.g. the post title)
    without generating any blog text. Used by the 'Fetch image automatically'
    button on the post editor."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    topic = (data.get("topic") or "").strip()
    if not topic:
        return JsonResponse({"error": "A topic (or post title) is required."}, status=400)

    try:
        image = fetch_pexels_image_or_raise(topic)
    except BlogGenerationError as e:
        return JsonResponse({"error": str(e)}, status=502)
    return JsonResponse({"success": True, "data": {"featured_image": image}})

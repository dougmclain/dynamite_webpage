from django.urls import path
from . import views

app_name = "staff_portal"

urlpatterns = [
    path("login/", views.staff_login, name="login"),
    path("logout/", views.staff_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("posts/", views.post_list, name="post_list"),
    path("posts/create/", views.post_create, name="post_create"),
    path("posts/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("posts/<int:pk>/delete/", views.post_delete, name="post_delete"),
    path("api/generate-blog/", views.generate_blog_api, name="generate_blog_api"),
]

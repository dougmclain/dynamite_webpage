# In the site's urls.py:  path("pipeline/api/", include("content_pipeline.urls")),
from .api import urlpatterns  # noqa: F401

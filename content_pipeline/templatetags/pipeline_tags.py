"""{% load pipeline_tags %} … content="{{ post.featured_image.url|absolute_url:request }}"

Fixes the og:image bug on dynamitemanagement.com where the site domain was glued onto
Cloudinary URLs that were already absolute (https://dynamitemanagement.comhttps://res.cloudinary…).
"""
from django import template

register = template.Library()


@register.filter
def absolute_url(url, request=None):
    if not url:
        return ""
    url = str(url)
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return "https:" + url
    if request is not None:
        return request.build_absolute_uri(url)
    return url

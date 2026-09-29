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


_LEAD_JS = """<script>(function(){try{var k="lead_ft",s=window.sessionStorage,v=s.getItem(k);
if(!v){v=JSON.stringify({l:location.pathname+location.search,r:document.referrer||""});s.setItem(k,v);}
var ft=JSON.parse(v);document.addEventListener("submit",function(e){var f=e.target;
if(!f||!f.getAttribute||(f.getAttribute("method")||"").toLowerCase()!=="post")return;
[["lead_landing",ft.l],["lead_referrer",ft.r]].forEach(function(p){var i=f.querySelector('input[name="'+p[0]+'"]');
if(!i){i=document.createElement("input");i.type="hidden";i.name=p[0];f.appendChild(i);}i.value=String(p[1]||"").slice(0,500);});
},true);}catch(e){}})();</script>"""


@register.simple_tag
def lead_attribution_script():
    """First-touch landing page + referrer for lead tracking (see content_pipeline/leads.py)."""
    from django.utils.safestring import mark_safe
    return mark_safe(_LEAD_JS)

"""Writes drafts into each site's existing blog model, using FIELD_MAP."""
import json

from django.apps import apps
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from . import conf


def post_model():
    return apps.get_model(conf.get("POST_MODEL"))


def field_names(model):
    return {f.name for f in model._meta.get_fields()}


def _fm(key):
    return conf.get("FIELD_MAP").get(key)


def _has(model, key):
    name = _fm(key)
    return bool(name) and name in field_names(model)


def existing_posts(limit=200):
    """(title, url) for internal linking."""
    M = post_model()
    qs = M.objects.all()
    if _has(M, "status"):
        qs = qs.filter(**{_fm("status"): conf.get("STATUS_VALUES")["published"]})
    out = []
    for p in qs[:limit]:
        url = p.get_absolute_url() if hasattr(p, "get_absolute_url") else f"/blog/{getattr(p, _fm('slug'))}/"
        out.append((getattr(p, _fm("title")), conf.get("SITE_URL").rstrip("/") + url))
    return out


def _to_body(markdown_text):
    if conf.get("BODY_FORMAT") == "html":
        import markdown
        return markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "toc"])
    return markdown_text


def _faq_jsonld(faq):
    if not faq:
        return ""
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]},
        ensure_ascii=False)


def _clip(key, value):
    lim = conf.get("FIELD_LIMITS").get(key)
    return value[:lim] if (lim and value) else value


def _set_taxonomy(post, brief):
    M = post.__class__
    if brief.category_name and _has(M, "category"):
        Cat = apps.get_model(conf.get("CATEGORY_MODEL"))
        cat, _ = Cat.objects.get_or_create(slug=slugify(brief.category_name),
                                           defaults={"name": brief.category_name})
        setattr(post, _fm("category"), cat)
    return post


def _set_tags(post, brief):
    M = post.__class__
    if not (brief.tags and _has(M, "tags")):
        return
    Tag = apps.get_model(conf.get("TAG_MODEL"))
    objs = []
    for name in [t.strip() for t in brief.tags.split(",") if t.strip()]:
        t, _ = Tag.objects.get_or_create(slug=slugify(name), defaults={"name": name})
        objs.append(t)
    getattr(post, _fm("tags")).set(objs)


CREDIT_START, CREDIT_END = "<!-- cover-credit -->", "<!-- /cover-credit -->"


def set_credit(post, credit: str = "", page: str = ""):
    """Keeps one photo-credit line at the end of the post body (replaced whenever the cover changes).
    Pexels API guidelines ask for photographer credit + a link to Pexels."""
    import re
    body_field = conf.get("FIELD_MAP")["body"]
    body = re.sub(re.escape(CREDIT_START) + ".*?" + re.escape(CREDIT_END), "", getattr(post, body_field) or "",
                  flags=re.S).rstrip()
    if credit:
        if conf.get("BODY_FORMAT") == "html":
            line = (f'<p class="cover-credit"><small>Cover: <a href="{page}" rel="nofollow noopener" '
                    f'target="_blank">{credit}</a></small></p>')
        else:
            line = f"<small>Cover: [{credit}]({page})</small>"
        body = f"{body}\n\n{CREDIT_START}\n{line}\n{CREDIT_END}"
    setattr(post, body_field, body)


def save_cover(post, jpg: bytes, slug: str, alt: str, credit: str = "", page: str = ""):
    set_credit(post, credit, page)
    M = post.__class__
    if _has(M, "image"):
        getattr(post, _fm("image")).save(f"{slug}.jpg", ContentFile(jpg), save=False)
        # a model can have both; clear the static one so the uploaded image wins
        if _has(M, "image_static"):
            setattr(post, _fm("image_static"), "")
    elif _has(M, "image_static"):
        from django.core.files.storage import default_storage
        path = default_storage.save(f"blog/covers/{slug}.jpg", ContentFile(jpg))
        setattr(post, _fm("image_static"), default_storage.url(path))
    if _has(M, "image_alt"):
        setattr(post, _fm("image_alt"), alt[:255])


def upsert_draft(brief, jpg: bytes | None):
    """Create (or rewrite in place) the site's post as a DRAFT. Returns the post."""
    M = post_model()
    fm = conf.get("FIELD_MAP")
    post = None
    if brief.refresh_slug:
        post = M.objects.filter(**{fm["slug"]: brief.refresh_slug}).first()
    elif brief.post_id:
        post = M.objects.filter(pk=brief.post_id).first()
    new = post is None
    if new:
        post = M()
        setattr(post, fm["slug"], brief.post_slug)
    setattr(post, fm["title"], _clip("title", brief.draft_title))
    setattr(post, fm["body"], _to_body(brief.body))
    for key, val in (("excerpt", brief.excerpt), ("seo_title", brief.seo_title),
                     ("meta_description", brief.meta_description), ("meta_keywords", brief.meta_keywords),
                     ("structured_data", _faq_jsonld(brief.faq))):
        if _has(M, key) and val:
            setattr(post, fm[key], _clip(key, val))
    # a refreshed live post stays live; everything else is a draft until approved
    if _has(M, "status") and new:
        setattr(post, fm["status"], conf.get("STATUS_VALUES")["draft"])
    if _has(M, "author") and conf.get("AUTHOR_USERNAME"):
        from django.contrib.auth import get_user_model
        u = get_user_model().objects.filter(username=conf.get("AUTHOR_USERNAME")).first()
        if u:
            setattr(post, fm["author"], u)
    _set_taxonomy(post, brief)
    if jpg:
        save_cover(post, jpg, getattr(post, fm["slug"]), brief.cover_alt,
                   brief.cover_credit, brief.cover_source_page)
    post.save()
    _set_tags(post, brief)
    return post


def publish(brief):
    M = post_model()
    fm = conf.get("FIELD_MAP")
    post = M.objects.get(pk=brief.post_id)
    if _has(M, "status"):
        setattr(post, fm["status"], conf.get("STATUS_VALUES")["published"])
    if _has(M, "published_at"):
        setattr(post, fm["published_at"], brief.publish_at or timezone.now())
    post.save()
    return post

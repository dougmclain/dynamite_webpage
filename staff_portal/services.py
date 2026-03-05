import json
import os
import re
import uuid

import bleach
import requests
from django.conf import settings
from django.core.files.base import ContentFile


class BlogGenerationError(Exception):
    pass


ALLOWED_TAGS = [
    "h2", "h3", "h4", "p", "br", "strong", "em", "u", "a", "ul", "ol", "li",
    "blockquote", "pre", "code", "img", "table", "thead", "tbody", "tr", "th", "td",
    "hr", "span", "div",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title"],
    "span": ["style"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}


def sanitize_html(html_content):
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


def parse_ai_response(text):
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise BlogGenerationError("Could not parse AI response as JSON.")


def generate_blog_post(topic, tone, length, audience):
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise BlogGenerationError(
            "ANTHROPIC_API_KEY is not configured. Please set it in your environment variables."
        )

    try:
        import anthropic
    except ImportError:
        raise BlogGenerationError("The anthropic package is not installed.")

    audience_labels = {
        "hoa_board": "HOA board members",
        "property_managers": "property managers",
        "condo_owners": "condominium owners",
        "general": "general audience interested in property management",
    }
    audience_label = audience_labels.get(audience, audience)

    system_prompt = (
        "You are a professional blog writer for Dynamite Management, a company specializing in "
        "financial management for condominium and homeowner associations (HOAs). "
        "You write informative, well-structured blog posts about HOA/condo financial topics. "
        "Always return your response as valid JSON with no additional text outside the JSON."
    )

    user_prompt = f"""Write a blog post about: {topic}

Requirements:
- Tone: {tone}
- Target length: approximately {length} words
- Target audience: {audience_label}

Return ONLY a JSON object with these exact keys:
{{
    "title": "The blog post title",
    "content": "The full blog post content in HTML format using <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em> tags",
    "excerpt": "A 1-2 sentence summary (plain text, max 300 characters)",
    "meta_description": "SEO meta description (max 160 characters)",
    "meta_keywords": "comma-separated SEO keywords",
    "suggested_category": "One of: Financial Management, HOA Governance, Tax Planning, Reserve Funds, Property Management, Industry News",
    "suggested_tags": "comma-separated relevant tags"
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.AuthenticationError:
        raise BlogGenerationError("Invalid API key. Please check your ANTHROPIC_API_KEY.")
    except anthropic.APIError as e:
        raise BlogGenerationError(f"API error: {str(e)}")

    response_text = message.content[0].text
    result = parse_ai_response(response_text)

    # Sanitize HTML content
    if "content" in result:
        result["content"] = sanitize_html(result["content"])

    # Fetch a featured image from Pexels
    image_data = fetch_pexels_image(topic)
    if image_data:
        result["featured_image"] = image_data

    return result


def fetch_pexels_image(query):
    api_key = settings.PEXELS_API_KEY
    if not api_key:
        return None

    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("photos"):
            return None

        photo = data["photos"][0]
        image_url = photo["src"]["large"]

        # Download the image
        img_response = requests.get(image_url, timeout=15)
        img_response.raise_for_status()

        # Determine file extension
        content_type = img_response.headers.get("content-type", "image/jpeg")
        ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
        filename = f"blog_{uuid.uuid4().hex[:8]}.{ext}"

        # Save to media/blog/featured_images/
        save_dir = os.path.join(settings.MEDIA_ROOT, "blog", "featured_images")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        with open(save_path, "wb") as f:
            f.write(img_response.content)

        return {
            "filename": filename,
            "path": f"blog/featured_images/{filename}",
            "photographer": photo.get("photographer", ""),
            "url": photo.get("url", ""),
        }
    except Exception:
        return None

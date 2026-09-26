"""Thin wrapper around the Anthropic Messages API (streams, so long drafts don't time out)."""
import json
import os
import re

from . import conf


def _client():
    import anthropic  # pip install anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _run(content, system=None, max_tokens=None) -> tuple[str, int]:
    kwargs = dict(model=conf.get("MODEL"), max_tokens=max_tokens or conf.get("MAX_TOKENS"),
                  messages=[{"role": "user", "content": content}])
    if system:
        kwargs["system"] = system
    with _client().messages.stream(**kwargs) as stream:
        msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    used = (msg.usage.input_tokens or 0) + (msg.usage.output_tokens or 0)
    return text, used


def complete(system: str, user: str, max_tokens: int | None = None) -> tuple[str, int]:
    return _run(user, system=system, max_tokens=max_tokens)


def complete_with_images(prompt: str, images_b64: list[str], max_tokens: int = 500) -> tuple[str, int]:
    content = []
    for i, b in enumerate(images_b64):
        content.append({"type": "text", "text": f"Photo {i}:"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b}})
    content.append({"type": "text", "text": prompt})
    return _run(content, max_tokens=max_tokens)


def parse_json(text: str) -> dict:
    """Pull the JSON object out of a reply, tolerating ```json fences."""
    clean = re.sub(r"```(?:json)?", "", text).strip()
    start, end = clean.find("{"), clean.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object in Claude's reply")
    return json.loads(clean[start:end + 1])

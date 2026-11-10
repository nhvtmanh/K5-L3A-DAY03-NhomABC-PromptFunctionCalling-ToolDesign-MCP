from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or ("/" if netloc else "")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def deduplicate_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if items is None:
        items = []
    if not isinstance(items, list):
        return {
            "tool": "deduplicate",
            "error": "ValueError",
            "message": "items must be a list of objects",
        }

    unique_items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            return {
                "tool": "deduplicate",
                "error": "ValueError",
                "message": "each item must be an object",
            }

        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            unique_items.append(item)
            continue

        try:
            canonical_url = _canonical_url(url)
        except ValueError as exc:
            return {
                "tool": "deduplicate",
                "error": "ValueError",
                "message": f"Invalid URL: {exc}",
            }
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)
        unique_items.append(item)

    return {
        "tool": "deduplicate",
        "items": unique_items,
        "removed_count": len(items) - len(unique_items),
    }

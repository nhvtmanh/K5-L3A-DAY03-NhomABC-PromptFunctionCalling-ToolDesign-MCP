from __future__ import annotations

from tools import TOOL_FUNCTIONS


deduplicate = TOOL_FUNCTIONS["deduplicate"]


def test_deduplicate_keeps_first_item_for_canonical_duplicate_urls() -> None:
    first = {"title": "First", "url": "HTTPS://Example.com/research/#intro"}
    duplicate = {"title": "Duplicate", "url": "https://example.com/research"}
    other = {"title": "Other", "url": "https://example.com/other"}

    result = deduplicate(items=[first, duplicate, other])

    assert result["items"] == [first, other]
    assert result["removed_count"] == 1


def test_deduplicate_empty_or_missing_items_returns_empty_list() -> None:
    assert deduplicate()["items"] == []
    assert deduplicate(items=[])["removed_count"] == 0


def test_deduplicate_invalid_input_returns_error_dict() -> None:
    result = deduplicate(items=[{"url": "https://example.com"}, "not-an-item"])

    assert result["error"] == "ValueError"
    assert "each item must be an object" in result["message"]

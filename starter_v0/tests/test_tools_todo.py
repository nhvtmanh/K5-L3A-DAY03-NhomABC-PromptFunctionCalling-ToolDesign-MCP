"""Offline unit tests for the built-in tools and the team's deduplicate tool."""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


clarify = TOOL_FUNCTIONS["clarify"]
deduplicate = TOOL_FUNCTIONS["deduplicate"]
fetch = TOOL_FUNCTIONS["fetch"]
format_items = TOOL_FUNCTIONS["format"]
lookup = TOOL_FUNCTIONS["lookup"]
policy = TOOL_FUNCTIONS["policy"]
send = TOOL_FUNCTIONS["send"]
social_search = TOOL_FUNCTIONS["social_search"]
timeline = TOOL_FUNCTIONS["timeline"]


def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Web", "Twitter"]

    result = clarify(
        question="Bạn muốn tìm ở đâu?",
        response_type="choice",
        options=options,
    )

    assert result["options"] == options
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"


def test_format_sections_groups_items_by_section() -> None:
    result = format_items(items=[
        {"title": "A1", "section": "A"},
        {"title": "B1", "section": "B"},
        {"title": "A2", "section": "A"},
    ])

    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    result = format_items(
        items=[{"title": "First"}, {"title": "Second"}],
        template="thread",
    )

    lines = result["markdown"].splitlines()
    assert lines[0].startswith("1/ ")
    assert lines[2].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    assert format_items(items=None)["item_count"] == 0
    assert format_items(items=[])["item_count"] == 0


def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin đã duyệt", confirmed=True)

    assert result["status"] == "sent"
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/bottest-token/sendMessage"
    assert calls[0]["json"]["chat_id"] == "-100123"
    assert calls[0]["json"]["text"] == "Bản tin đã duyệt"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup(query="AI research", topic="news", timeframe=None)

    assert result["items"] == []
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["topic"] == "news"


def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Page content",
            "metadata": {
                "title": "Research",
                "sourceURL": "https://example.com/research",
            },
        },
    }))

    result = fetch("https://example.com/input")

    assert result["items"] == [{
        "title": "Research",
        "url": "https://example.com/research",
        "source": "example.com",
        "summary": "Page content",
    }]
    assert calls[0]["json"]["url"] == "https://example.com/input"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({
        "data": {"markdown": "x" * 4500, "metadata": {}},
    }))

    result = fetch("https://example.com")

    assert len(result["items"][0]["summary"]) == 4000


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    timeline_items = [{"screen_name": "sample", "text": "No id"}]
    timeline_items.extend(
        {
            "screen_name": "sample",
            "tweet_id": str(index),
            "text": f"Post {index}",
        }
        for index in range(6)
    )
    calls = fake_http(FakeResponse({"timeline": timeline_items}))

    result = timeline(screenname="sample", limit=3)

    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        f"https://x.com/sample/status/{index}" for index in range(3)
    ]
    assert calls[0]["params"] == {"screenname": "sample"}


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))

    result = social_search(query="OpenAI", search_type="Top", limit=2)

    assert result["items"] == []
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}


def test_policy_empty_query_returns_no_results() -> None:
    result = policy(query="   ")

    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy(query="customer data", policy_area="data_privacy")

    assert result["results"]
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy(query="citation", policy_area="source_citation", top_k=20)
    injection_results = [
        item for item in result["results"]
        if any("ignore the citation policy" in text.lower() for text in item["untrusted_text"])
    ]

    assert injection_results
    assert all("ignore the citation policy" not in item["facts"].lower() for item in injection_results)


def test_my_new_tool_happy_path_keeps_items_without_url_and_distinct_queries() -> None:
    no_url = {"title": "No URL"}
    first = {"title": "Query A", "url": "https://example.com/story?ref=a"}
    second = {"title": "Query B", "url": "https://example.com/story?ref=b"}

    result = deduplicate(items=[no_url, first, second])

    assert result["items"] == [no_url, first, second]
    assert result["removed_count"] == 0


def test_my_new_tool_bad_input_returns_error_dict() -> None:
    result = deduplicate(items={"url": "https://example.com"})

    assert result["error"] == "ValueError"
    assert "items must be a list" in result["message"]


def test_my_new_tool_malformed_url_returns_error_dict() -> None:
    result = deduplicate(items=[{"url": "http://[::1"}])

    assert result["error"] == "ValueError"
    assert "Invalid URL" in result["message"]

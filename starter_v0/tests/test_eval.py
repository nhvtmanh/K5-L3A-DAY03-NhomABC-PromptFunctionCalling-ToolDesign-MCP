from __future__ import annotations

from run_eval import evaluate_phase_b


def test_eval_compares_list_of_object_tool_arguments() -> None:
    case = {
        "failure_type": "wrong_tool",
        "expect": {
            "tool_calls": [
                {
                    "name": "deduplicate",
                    "args": {
                        "items": [
                            {"title": "First", "url": "https://example.com/a"},
                            {"title": "Second", "url": "https://example.com/b"},
                        ]
                    },
                }
            ]
        },
    }
    actual_calls = [
        {
            "name": "deduplicate",
            "args": {
                "items": [
                    {"title": "First", "url": "https://example.com/a"},
                    {"title": "Second", "url": "https://example.com/b"},
                ]
            },
        }
    ]

    result = evaluate_phase_b(case, actual_calls, text=None)

    assert result["passed"] is True
    assert result["routing_correct"] is True
    assert result["args_correct"] is True
    assert result["failures"] == []

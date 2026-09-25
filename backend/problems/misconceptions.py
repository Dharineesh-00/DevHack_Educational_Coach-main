"""Closed misconception taxonomies for supported problems."""

from __future__ import annotations

from problems.definitions import normalize_problem_id


MISCONCEPTIONS: dict[str, list[dict[str, str]]] = {
    "valid_parentheses": [
        {
            "id": "no-stack-structure",
            "description": "Doesn't use a stack/LIFO — e.g. counts opens vs closes, so '([)]' wrongly passes",
        },
        {
            "id": "bracket-type-mismatch",
            "description": "Uses a stack but doesn't check the popped bracket's type matches the closing bracket",
        },
        {
            "id": "unclosed-brackets-ignored",
            "description": "Never checks the stack is empty at the end — trailing unclosed opens wrongly pass",
        },
        {
            "id": "pop-empty-stack-crash",
            "description": "No guard popping/peeking an empty stack on a closing bracket — crashes or false-positives",
        },
        {
            "id": "push-pop-role-confusion",
            "description": "Inverted logic — pushes closing brackets instead of opening ones, or vice versa",
        },
        {
            "id": "non-bracket-char-handling",
            "description": "Mishandles characters that aren't brackets",
        },
        {
            "id": "off-by-one-index-error",
            "description": "Loop bounds/indexing bug skips or overruns the last character",
        },
        {
            "id": "other-unspecified",
            "description": "None of the above clearly applies",
        },
    ],
}


def get_misconceptions(problem_id: str) -> list[dict[str, str]]:
    """Look up misconceptions by normalized problem ID."""
    return MISCONCEPTIONS.get(normalize_problem_id(problem_id), [])
"""
Problem and test case definitions for deterministic DSA code evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TestCase:
    """Represents a single deterministic test case."""
    test_id: int
    args: list[Any]
    expected: Any


@dataclass(frozen=True)
class ProblemDefinition:
    """Represents a problem configuration for the test runner."""
    problem_id: str
    title: str
    entrypoint: str
    test_cases: list[TestCase]


# Phase 1 Test Cases
TEST_CASES: dict[str, list[dict[str, Any]]] = {
    "valid_parentheses": [
        {
            "test_id": 1,
            "args": ["()"],
            "expected": True,
        },
        {
            "test_id": 2,
            "args": ["()[]{}"],
            "expected": True,
        },
        {
            "test_id": 3,
            "args": ["(]"],
            "expected": False,
        },
        {
            "test_id": 4,
            "args": ["([)]"],
            "expected": False,
        },
        {
            "test_id": 5,
            "args": [""],
            "expected": True,
        },
        {
            "test_id": 6,
            "args": ["]"],
            "expected": False,
        },
    ]
}


PROBLEMS: dict[str, ProblemDefinition] = {
    "valid_parentheses": ProblemDefinition(
        problem_id="valid_parentheses",
        title="Valid Parentheses",
        entrypoint="is_valid",
        test_cases=[
            TestCase(
                test_id=tc["test_id"],
                args=tc["args"],
                expected=tc["expected"],
            )
            for tc in TEST_CASES["valid_parentheses"]
        ],
    ),
}


def normalize_problem_id(problem_id: str) -> str:
    """Normalize slugs like 'valid-parentheses' or 'valid_parentheses' to 'valid_parentheses'."""
    return problem_id.strip().lower().replace("-", "_")


def get_problem(problem_id: str) -> ProblemDefinition | None:
    """Look up a problem definition by slug or ID."""
    norm_id = normalize_problem_id(problem_id)
    return PROBLEMS.get(norm_id)

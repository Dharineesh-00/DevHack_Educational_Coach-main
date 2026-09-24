"""
Tests for Real Test-Case Execution for DSA Submissions.
Verifies deterministic harness, error handling, Piston integration, and /submit API response.
"""

import asyncio
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from main import app
from problems.definitions import get_problem
from services.piston_runner import PistonClient
from services.test_runner import (
    build_test_harness,
    evaluate_test_output,
    extract_harness_output,
    run_deterministic_tests,
)

CORRECT_SOLUTION = """
def is_valid(s: str) -> bool:
    stack = []
    mapping = {")": "(", "}": "{", "]": "["}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping:
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
        else:
            return False
    return not stack
"""

INCORRECT_SOLUTION = """
def is_valid(s: str) -> bool:
    # Naive solution: fails on order like "([)]" and "(]"
    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')
"""

SYNTAX_ERROR_SOLUTION = """
def is_valid(s: str) -> bool:
    if s
        return True
"""

RUNTIME_ERROR_INSIDE_FUNCTION = """
def is_valid(s: str) -> bool:
    # Deliberate runtime error inside function
    raise IndexError("Custom test failure")
"""

TOP_LEVEL_RUNTIME_ERROR = """
raise RuntimeError("Crash on import")

def is_valid(s: str) -> bool:
    return True
"""


@pytest.fixture
def piston_client():
    return PistonClient()


@pytest.fixture
def valid_parentheses_problem():
    problem = get_problem("valid-parentheses")
    assert problem is not None
    return problem


def test_correct_solution_all_6_pass(piston_client, valid_parentheses_problem):
    """1. Correct solution -> all 6 tests pass."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=CORRECT_SOLUTION,
            language="python",
        )
    )

    assert results.status == "passed"
    assert results.reason == "all_tests_passed"
    assert results.summary.total == 6
    assert results.summary.passed == 6
    assert results.summary.failed == 0
    assert len(results.tests) == 6

    # Verify each individual test passed
    for t in results.tests:
        assert t.passed is True
        assert t.error is None
        assert t.actual == t.expected


def test_incorrect_solution_fails_test_cases(piston_client, valid_parentheses_problem):
    """2. Incorrect solution -> at least one test fails (specifically '([)]' -> expected False)."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=INCORRECT_SOLUTION,
            language="python",
        )
    )

    assert results.status == "failed"
    assert results.reason == "test_failure"
    assert results.summary.failed >= 1
    assert results.summary.passed < results.summary.total

    # Test #4 is "([)]" -> expected False, but naive count returns True
    test4 = next(t for t in results.tests if t.test_id == 4)
    assert test4.input == "([)]"
    assert test4.expected is False
    assert test4.actual is True
    assert test4.passed is False


def test_runtime_error_inside_function(piston_client, valid_parentheses_problem):
    """3. Runtime error inside test function -> captured per test case, not crashing runner."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=RUNTIME_ERROR_INSIDE_FUNCTION,
            language="python",
        )
    )

    assert results.status == "failed"
    assert results.reason == "test_failure"
    assert results.summary.failed == 6
    assert results.summary.passed == 0
    for t in results.tests:
        assert t.passed is False
        assert "IndexError" in (t.error or "")


def test_top_level_runtime_error(piston_client, valid_parentheses_problem):
    """3b. Top level runtime crash -> reported as runtime_error."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=TOP_LEVEL_RUNTIME_ERROR,
            language="python",
        )
    )

    assert results.status == "failed"
    assert results.reason == "runtime_error"
    assert results.summary.failed == 6
    assert results.summary.passed == 0


def test_syntax_error_reported(piston_client, valid_parentheses_problem):
    """4. Syntax error -> correctly reported as compilation/syntax error."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=SYNTAX_ERROR_SOLUTION,
            language="python",
        )
    )

    assert results.status == "failed"
    assert results.reason == "syntax_error"
    assert results.summary.passed == 0
    assert results.summary.failed == 6


def test_empty_input_case(piston_client, valid_parentheses_problem):
    """5. Empty input case works ("" -> True)."""
    results = asyncio.run(
        run_deterministic_tests(
            piston_client=piston_client,
            problem=valid_parentheses_problem,
            code=CORRECT_SOLUTION,
            language="python",
        )
    )

    empty_test = next(t for t in results.tests if t.test_id == 5)
    assert empty_test.input == ""
    assert empty_test.expected is True
    assert empty_test.actual is True
    assert empty_test.passed is True


def test_api_submit_endpoint_preserves_contract_and_returns_test_results():
    """6. /submit returns test_results, execution, and all existing evaluation/tutor fields."""
    client = TestClient(app)

    response = client.post(
        "/submit",
        json={
            "language": "python",
            "code": CORRECT_SOLUTION,
            "user_id": "test_user_deterministic",
            "problem_id": "valid-parentheses",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structured test results
    assert "test_results" in data
    assert data["test_results"] is not None
    assert data["test_results"]["passed"] == 6
    assert data["test_results"]["total"] == 6
    assert data["test_results"]["status"] == "passed"
    assert data["test_results"]["reason"] == "all_tests_passed"
    assert len(data["test_results"]["tests"]) == 6

    # Verify execution details
    assert "execution" in data
    assert data["execution"] is not None
    assert data["execution"]["exit_code"] == 0

    # Verify existing fields are preserved
    assert "agent_logs" in data
    assert isinstance(data["agent_logs"], list)
    assert any("[TESTS]" in log for log in data["agent_logs"])
    assert any("[CRITIC]" in log for log in data["agent_logs"])
    assert any("[DEFENDER]" in log for log in data["agent_logs"])
    assert any("[JUDGE]" in log for log in data["agent_logs"])

    assert "tutor_response" in data
    assert len(data["tutor_response"]) > 0

    assert "misconception" in data
    assert "id" in data["misconception"]
    assert "confidence" in data["misconception"]
    assert "evidence_line" in data["misconception"]

    assert "trajectory" in data
    assert "recurrence_count" in data["trajectory"]
    assert "same_misconception_streak" in data["trajectory"]

    assert "stdout" in data
    assert "stderr" in data
    assert "exit_code" in data
    assert "language" in data

"""
Deterministic Test Runner and Harness for DSA submissions.
Executes code through the existing Piston client and evaluates expected vs actual outputs.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from pydantic import BaseModel, Field

from problems.definitions import ProblemDefinition
from services.piston_runner import PistonClient

logger = logging.getLogger(__name__)

DELIMITER_START = "<<<TEST_RESULTS_JSON>>>"
DELIMITER_END = "<<<TEST_RESULTS_JSON>>>"


# ---------------------------------------------------------------------------
# Structured Test Result Schemas
# ---------------------------------------------------------------------------

class TestCaseResult(BaseModel):
    test_id: int
    input: Any
    expected: Any
    actual: Any = None
    passed: bool
    error: str | None = None


class TestSummary(BaseModel):
    passed: int
    total: int
    failed: int


class ExecutionDetail(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int


class TestResults(BaseModel):
    problem_id: str
    status: str       # "passed" | "failed" | "error"
    reason: str       # "all_tests_passed" | "test_failure" | "syntax_error" | "runtime_error" | "timeout"
    passed: int
    total: int
    failed: int
    tests: list[TestCaseResult] = Field(default_factory=list)
    summary: TestSummary
    execution: ExecutionDetail


# ---------------------------------------------------------------------------
# Harness Generation
# ---------------------------------------------------------------------------

def build_test_harness(student_code: str, problem: ProblemDefinition) -> str:
    """
    Combine student code with the deterministic test harness script.
    """
    tests_payload = [
        {
            "test_id": tc.test_id,
            "args": tc.args,
            "expected": tc.expected,
        }
        for tc in problem.test_cases
    ]
    tests_json = json.dumps(tests_payload)
    fn_name = json.dumps(problem.entrypoint)

    harness_code = f"""
# ----------------- STUDENT CODE -----------------
{student_code}

# ----------------- DETERMINISTIC TEST HARNESS -----------------
import json as _json
import sys as _sys

def __dsa_test_runner():
    raw_tests = _json.loads({repr(tests_json)})
    fn_name = {fn_name}
    results = []

    fn = globals().get(fn_name)
    if fn is None or not callable(fn):
        for tc in raw_tests:
            inp = tc["args"][0] if len(tc["args"]) == 1 else tc["args"]
            results.append({{
                "test_id": tc["test_id"],
                "input": inp,
                "expected": tc["expected"],
                "actual": None,
                "passed": False,
                "error": f"Function '{{fn_name}}' is not defined",
            }})
    else:
        for tc in raw_tests:
            inp = tc["args"][0] if len(tc["args"]) == 1 else tc["args"]
            try:
                actual = fn(*tc["args"])
                if isinstance(tc["expected"], bool):
                    passed = isinstance(actual, bool) and actual == tc["expected"]
                else:
                    passed = bool(actual == tc["expected"])
                results.append({{
                    "test_id": tc["test_id"],
                    "input": inp,
                    "expected": tc["expected"],
                    "actual": actual,
                    "passed": passed,
                    "error": None,
                }})
            except Exception as exc:
                err_msg = f"{{type(exc).__name__}}: {{exc}}"
                results.append({{
                    "test_id": tc["test_id"],
                    "input": inp,
                    "expected": tc["expected"],
                    "actual": None,
                    "passed": False,
                    "error": err_msg,
                }})

    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    payload = {{
        "tests": results,
        "summary": {{
            "passed": passed_count,
            "total": total_count,
            "failed": total_count - passed_count,
        }},
    }}
    _sys.stdout.flush()
    print("{DELIMITER_START}" + _json.dumps(payload) + "{DELIMITER_END}")

if __name__ == "__main__":
    __dsa_test_runner()
"""
    return harness_code


# ---------------------------------------------------------------------------
# Output Parsing & Classification
# ---------------------------------------------------------------------------

def extract_harness_output(raw_stdout: str) -> tuple[dict | None, str]:
    """
    Extract the JSON payload emitted by the test harness and separate it
    from any stdout produced by the student's code.
    """
    pattern = rf"{re.escape(DELIMITER_START)}(.*?){re.escape(DELIMITER_END)}"
    match = re.search(pattern, raw_stdout, re.DOTALL)
    if not match:
        return None, raw_stdout

    json_str = match.group(1).strip()
    clean_stdout = (raw_stdout[:match.start()] + raw_stdout[match.end():]).strip()
    try:
        parsed = json.loads(json_str)
        return parsed, clean_stdout
    except json.JSONDecodeError:
        return None, raw_stdout


def evaluate_test_output(
    problem: ProblemDefinition,
    raw_stdout: str,
    raw_stderr: str,
    exit_code: int,
) -> TestResults:
    """
    Deterministically classify the execution result:
    - syntax_error
    - runtime_error
    - test_failure
    - all_tests_passed
    """
    total_cases = len(problem.test_cases)
    harness_data, clean_stdout = extract_harness_output(raw_stdout)

    # 1. Did the harness successfully run and produce parsed test data?
    if harness_data and isinstance(harness_data.get("tests"), list):
        test_items = [
            TestCaseResult(
                test_id=t["test_id"],
                input=t["input"],
                expected=t["expected"],
                actual=t.get("actual"),
                passed=bool(t.get("passed", False)),
                error=t.get("error"),
            )
            for t in harness_data["tests"]
        ]
        passed = sum(1 for t in test_items if t.passed)
        failed = total_cases - passed
        status = "passed" if (failed == 0 and passed == total_cases) else "failed"
        reason = "all_tests_passed" if status == "passed" else "test_failure"

        return TestResults(
            problem_id=problem.problem_id,
            status=status,
            reason=reason,
            passed=passed,
            total=total_cases,
            failed=failed,
            tests=test_items,
            summary=TestSummary(passed=passed, total=total_cases, failed=failed),
            execution=ExecutionDetail(
                success=(exit_code == 0 and status == "passed"),
                stdout=clean_stdout,
                stderr=raw_stderr,
                exit_code=exit_code,
            ),
        )

    # 2. No harness data output: execution failed before/during harness run
    is_syntax = (
        "SyntaxError" in raw_stderr
        or "IndentationError" in raw_stderr
        or "TabError" in raw_stderr
    )
    reason = "syntax_error" if is_syntax else "runtime_error"
    err_message = raw_stderr.strip() or ("Syntax error" if is_syntax else "Runtime error")

    failed_tests = [
        TestCaseResult(
            test_id=tc.test_id,
            input=tc.args[0] if len(tc.args) == 1 else tc.args,
            expected=tc.expected,
            actual=None,
            passed=False,
            error=err_message,
        )
        for tc in problem.test_cases
    ]

    return TestResults(
        problem_id=problem.problem_id,
        status="failed",
        reason=reason,
        passed=0,
        total=total_cases,
        failed=total_cases,
        tests=failed_tests,
        summary=TestSummary(passed=0, total=total_cases, failed=total_cases),
        execution=ExecutionDetail(
            success=False,
            stdout=clean_stdout,
            stderr=raw_stderr,
            exit_code=exit_code if exit_code != 0 else -1,
        ),
    )


# ---------------------------------------------------------------------------
# Test Runner Execution
# ---------------------------------------------------------------------------

async def run_deterministic_tests(
    piston_client: PistonClient,
    problem: ProblemDefinition,
    code: str,
    language: str = "python",
) -> TestResults:
    """
    Build the harness, invoke Piston, and parse deterministic results.
    """
    total_cases = len(problem.test_cases)
    harness_code = build_test_harness(student_code=code, problem=problem)

    try:
        piston_response = await piston_client.execute_code(language=language, code=harness_code)
        run_data = piston_response.get("run", {})
        stdout = run_data.get("stdout", "")
        stderr = run_data.get("stderr", "")
        exit_code = run_data.get("code", 0)

        # Check if Piston itself reported a timeout/signal
        signal = run_data.get("signal")
        if signal in ("SIGKILL", "SIGTERM") or "timed out" in stderr.lower():
            return TestResults(
                problem_id=problem.problem_id,
                status="failed",
                reason="timeout",
                passed=0,
                total=total_cases,
                failed=total_cases,
                tests=[
                    TestCaseResult(
                        test_id=tc.test_id,
                        input=tc.args[0] if len(tc.args) == 1 else tc.args,
                        expected=tc.expected,
                        actual=None,
                        passed=False,
                        error="Execution timed out",
                    )
                    for tc in problem.test_cases
                ],
                summary=TestSummary(passed=0, total=total_cases, failed=total_cases),
                execution=ExecutionDetail(
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                ),
            )

        return evaluate_test_output(
            problem=problem,
            raw_stdout=stdout,
            raw_stderr=stderr,
            exit_code=exit_code,
        )

    except Exception as exc:
        is_timeout = "timeout" in str(exc).lower() or type(exc).__name__ == "TimeoutException"
        reason = "timeout" if is_timeout else "runtime_error"
        err_msg = f"{type(exc).__name__}: {exc}"

        return TestResults(
            problem_id=problem.problem_id,
            status="failed",
            reason=reason,
            passed=0,
            total=total_cases,
            failed=total_cases,
            tests=[
                TestCaseResult(
                    test_id=tc.test_id,
                    input=tc.args[0] if len(tc.args) == 1 else tc.args,
                    expected=tc.expected,
                    actual=None,
                    passed=False,
                    error=err_msg,
                )
                for tc in problem.test_cases
            ],
            summary=TestSummary(passed=0, total=total_cases, failed=total_cases),
            execution=ExecutionDetail(
                success=False,
                stdout="",
                stderr=err_msg,
                exit_code=-1,
            ),
        )


def format_test_evidence(test_results: TestResults) -> str:
    """
    Format deterministic test results into structured evidence for the LLM panel.
    """
    lines = [
        f"PROBLEM: {test_results.problem_id}",
        f"TEST RESULT: {test_results.summary.passed}/{test_results.summary.total} passed",
        f"STATUS: {test_results.status.upper()} ({test_results.reason})",
    ]

    if test_results.reason in ("syntax_error", "runtime_error", "timeout"):
        err = test_results.execution.stderr.strip()
        if not err and test_results.tests and test_results.tests[0].error:
            err = test_results.tests[0].error
        lines.append(f"EXECUTION ERROR: {err}")
        return "\n".join(lines)

    failed_tests = [t for t in test_results.tests if not t.passed]
    if failed_tests:
        lines.append("FAILED TESTS:")
        for t in failed_tests:
            if t.error:
                lines.append(f"- Test #{t.test_id}: input = {t.input!r} -> Error: {t.error}")
            else:
                lines.append(f"- Test #{t.test_id}: input = {t.input!r} -> expected = {t.expected!r}, actual = {t.actual!r}")
    else:
        lines.append("All test cases passed successfully.")

    return "\n".join(lines)

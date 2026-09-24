"""
Orchestrator — the 'Good Cop / Bad Cop Interview Panel' pipeline.

Pipeline
--------
1. Execute the code via deterministic test harness on Piston.
2. Produce structured test-result evidence (expected vs actual, pass/fail).
3. Agent 1 – The Critic     : Ruthless Staff Engineer critiques code based on deterministic evidence.
4. Agent 2 – The Defender   : Empathetic DevRel coach counters the Critic.
5. Agent 3 – The Judge      : Lead Interviewer synthesises a Socratic hint.

Returns an :class:`OrchestrationResult` dataclass.
"""

from __future__ import annotations

import json as _json
import logging
import re as _re
import time
from collections import defaultdict
from dataclasses import dataclass

from db.base_repo import MetricsRepository
from db.mock_repo import MockMetricsRepository
from problems.definitions import get_problem
from services.llm_client import OpenRouterClient
from services.piston_runner import PistonClient
from services.test_runner import (
    TestResults,
    format_test_evidence,
    run_deterministic_tests,
)

logger = logging.getLogger(__name__)
_SEP = "=" * 60

# Simple in-memory failure tracker  { user_id: [timestamp, ...] }
_failure_log: dict[str, list[float]] = defaultdict(list)
_WINDOW = 300  # seconds (5 minutes)


def _record_failure(user_id: str) -> int:
    """Record a failed run and return how many failures in the last 5 min."""
    now = time.time()
    failures = _failure_log[user_id]
    failures.append(now)
    _failure_log[user_id] = [t for t in failures if now - t <= _WINDOW]
    return len(_failure_log[user_id])


def _vibe(failure_count: int) -> str:
    """Return a short frustration signal string for the VIBE log line."""
    if failure_count == 0:
        return "All good."
    if failure_count == 1:
        return "First failure. Stay calm, keep going."
    if failure_count <= 3:
        return f"Failed {failure_count} times in 5 min. Mild frustration."
    return f"Failed {failure_count} times in 5 min. High frustration."


# Shared singletons (instantiated once at import time)
_piston = PistonClient()
_ollama = OpenRouterClient()

# OpenRouter generation options for short, focused agent responses.
_FAST_OPTS: dict = {"max_tokens": 200, "temperature": 0.75}


@dataclass
class OrchestrationResult:
    """Holds every artefact produced by the debate pipeline."""

    # --- Piston execution ---
    language: str
    version: str
    stdout: str
    stderr: str
    execution_output: str  # combined stdout+stderr
    exit_code: int

    # --- Agent debate ---
    agent_logs: list[str]  # list[str]: one formatted line per panel member
    tutor_feedback: str    # Judge's final Socratic response

    # --- Misconception pipeline ---
    misconception_id: str
    misconception_confidence: float
    misconception_evidence_line: int
    recurrence_count: int
    same_misconception_streak: bool

    # --- Real test execution results ---
    test_results: TestResults | None = None


async def _safe_generate(prompt: str, options: dict | None = None, fallback: str = "") -> str:
    """Generate LLM response with graceful fallback on service failure."""
    try:
        reply = await _ollama.generate(prompt=prompt, options=options or _FAST_OPTS)
        clean = reply.strip()
        return clean if clean else fallback
    except Exception as exc:
        logger.warning("[orchestrator] LLM generation failed, using fallback: %s", exc)
        return fallback


async def run(
    code: str,
    language: str = "python",
    user_id: str = "anonymous",
    problem_id: str = "valid-parentheses",
    repo: MetricsRepository | None = None,
) -> OrchestrationResult:
    """
    Execute the full DSA analysis pipeline for a submitted code snippet.
    """
    if repo is None:
        repo = MockMetricsRepository()

    # ------------------------------------------------------------------
    # Step 1 — Deterministic Test Execution via Piston
    # ------------------------------------------------------------------
    problem = get_problem(problem_id)
    test_results: TestResults | None = None

    if problem is not None:
        test_results = await run_deterministic_tests(
            piston_client=_piston,
            problem=problem,
            code=code,
            language=language,
        )
        exec_language = language
        exec_version = "3.10.0"
        stdout = test_results.execution.stdout
        stderr = test_results.execution.stderr
        exit_code = test_results.execution.exit_code
        execution_output = (stderr.strip() or stdout.strip() or "")
    else:
        # Fallback to raw Piston execution if problem not in test registry
        piston_response = await _piston.execute_code(language=language, code=code)
        run_data = piston_response.get("run", {})
        exec_language = piston_response.get("language", language)
        exec_version = piston_response.get("version", "unknown")
        stdout = run_data.get("stdout", "")
        stderr = run_data.get("stderr", "")
        execution_output = run_data.get("output", "")
        exit_code = run_data.get("code", -1)

    logger.info(
        "\n%s\n[EXECUTION] Result: exit_code=%d\n"
        "             language=%s  version=%s\n"
        "             stdout  : %s\n"
        "             stderr  : %s\n%s",
        _SEP,
        exit_code,
        exec_language, exec_version,
        stdout.strip() or "(none)",
        stderr.strip() or "(none)",
        _SEP,
    )

    # Vibe check — track failures based on deterministic test results or exit code
    is_failed = (test_results.status != "passed") if test_results else (exit_code != 0)
    failure_count = _record_failure(user_id) if is_failed else 0
    logger.info("[AGENT: VIBE]  user_id=%s  |  %s", user_id, _vibe(failure_count))

    # Format deterministic test evidence
    problem_title = problem.title if problem else problem_id
    if test_results:
        evidence_str = format_test_evidence(test_results)
    else:
        evidence_str = f"Execution output: {execution_output}\nExit code: {exit_code}"

    # ------------------------------------------------------------------
    # Step 2 — Agent 1: The Critic (Ruthless Staff Engineer)
    # The LLM receives deterministic evidence and analyzes the flaw
    # ------------------------------------------------------------------
    logger.info("\n%s\n[AGENT: CRITIC] Reviewing submission with test evidence...", _SEP)

    critic_prompt = (
        f"You are a ruthless Staff Engineer interviewing a candidate for '{problem_title}'.\n"
        f"Candidate code:\n{code}\n\n"
        f"DETERMINISTIC TEST EVIDENCE:\n{evidence_str}\n\n"
        f"Instructions:\n"
        f"The test runner has ALREADY deterministically tested the code. Do not evaluate if tests passed.\n"
        f"In exactly 1 or 2 short sentences, critique their algorithmic flaw, logic bug, time/space complexity, or code quality based on the evidence.\n"
        f"Be harsh but technically accurate. Do not offer solutions."
    )

    if test_results and test_results.status == "passed":
        critic_fallback = "The solution passes all deterministic test cases, but evaluate whether your space complexity is truly minimal."
    elif test_results and test_results.reason in ("syntax_error", "runtime_error"):
        critic_fallback = f"The code failed with a {test_results.reason}: check your syntax and edge cases before running."
    elif test_results:
        critic_fallback = f"The code failed {test_results.summary.failed} of {test_results.summary.total} test cases; your bracket matching logic fails on mismatched pairs."
    else:
        critic_fallback = "Your implementation has structural flaws and improper handling of edge cases."

    critic_review = await _safe_generate(critic_prompt, options=_FAST_OPTS, fallback=critic_fallback)
    logger.info("\n[CRITIC]\n%s\n%s", critic_review, _SEP)

    # ------------------------------------------------------------------
    # Step 3 — Agent 2: The Defender (Empathetic DevRel Coach)
    # ------------------------------------------------------------------
    logger.info("\n%s\n[AGENT: DEFENDER] Countering the Critic...", _SEP)

    passed_info = f"{test_results.summary.passed}/{test_results.summary.total} tests passed." if test_results else ""
    defender_prompt = (
        f"You are an empathetic junior developer coach.\n"
        f"Problem: {problem_title}\n"
        f"{passed_info}\n"
        f"The harsh Staff Engineer just said: \"{critic_review}\".\n"
        f"Look at the student's code:\n{code}\n\n"
        f"In exactly 1 or 2 short sentences, defend the student.\n"
        f"Point out one good thing they did (such as approach, stack intuition, or clean naming).\n"
        f"Disagree with the Staff Engineer's harsh tone."
    )

    defender_fallback = "You have a solid conceptual foundation with the stack; debugging the mismatched edge cases will get this passing."
    defender_review = await _safe_generate(defender_prompt, options=_FAST_OPTS, fallback=defender_fallback)
    logger.info("\n[DEFENDER]\n%s\n%s", defender_review, _SEP)

    # ------------------------------------------------------------------
    # Step 4 — Agent 3: The Judge (Socratic Lead Interviewer)
    # ------------------------------------------------------------------
    logger.info("\n%s\n[AGENT: JUDGE] Synthesising debate...", _SEP)

    judge_prompt = (
        f"You are the Lead Interviewer.\n"
        f"Problem: {problem_title}\n"
        f"{passed_info}\n"
        f"The Critic said: \"{critic_review}\".\n"
        f"The Defender said: \"{defender_review}\".\n\n"
        f"Synthesize this debate. Write a friendly, 2-sentence response to the student.\n"
        f"Acknowledge the good (from the Defender), but gently push them to resolve the flaw using a Socratic question. NEVER write code for them."
    )

    if test_results and test_results.status == "passed":
        judge_fallback = "Great work getting all test cases to pass! How does your stack size scale in the worst case where all brackets are open?"
    else:
        judge_fallback = "Good start on utilizing a stack for bracket tracking. When you see a closing bracket, what condition must the top of the stack satisfy?"

    final_response = await _safe_generate(judge_prompt, options=_FAST_OPTS, fallback=judge_fallback)
    logger.info("\n[JUDGE]\n%s\n%s", final_response, _SEP)

    # ------------------------------------------------------------------
    # Step 5 — Extract structured misconception from Critic's review
    # ------------------------------------------------------------------
    misconception_prompt = (
        f"Given this code review: \"{critic_review}\", "
        f"respond with ONLY valid JSON (no markdown) in this exact shape: "
        f'{{"id": "<2-5-word-kebab-slug>", "confidence": <0.0-1.0>}}. '
        f"No other text."
    )
    raw_misc = await _safe_generate(
        misconception_prompt,
        options={"max_tokens": 40, "temperature": 0.2},
        fallback='{"id": "bracket-stack-ordering", "confidence": 0.7}',
    )
    try:
        misc_data = _json.loads(raw_misc)
        misconception_id: str = misc_data.get("id", "bracket-stack-ordering")
        misconception_confidence: float = float(misc_data.get("confidence", 0.7))
    except Exception:
        m = _re.search(r'"id"\s*:\s*"([^"]+)"', raw_misc)
        misconception_id = m.group(1) if m else "bracket-stack-ordering"
        misconception_confidence = 0.6

    evidence_line = next(
        (i + 1 for i, ln in enumerate(code.splitlines()) if ln.strip() and not ln.strip().startswith("#")),
        1,
    )

    recurrence_count = len(_failure_log.get(user_id, []))
    same_misconception_streak = recurrence_count >= 2

    # ------------------------------------------------------------------
    # Step 6 — Assemble agent logs + persist mastery signal
    # ------------------------------------------------------------------
    test_line = (
        f"[TESTS] {test_results.summary.passed}/{test_results.summary.total} passed ({test_results.reason})"
        if test_results
        else f"[EXECUTION] Exit code {exit_code}"
    )

    agent_logs: list[str] = [
        test_line,
        f"[CRITIC] {critic_review}",
        f"[DEFENDER] {defender_review}",
        f"[JUDGE] {final_response}",
    ]

    await repo.update_user_mastery(
        user_id=user_id,
        concept=misconception_id,
        score=50 if is_failed else 100,
    )

    return OrchestrationResult(
        language=exec_language,
        version=exec_version,
        stdout=stdout,
        stderr=stderr,
        execution_output=execution_output,
        exit_code=exit_code,
        agent_logs=agent_logs,
        tutor_feedback=final_response,
        misconception_id=misconception_id,
        misconception_confidence=misconception_confidence,
        misconception_evidence_line=evidence_line,
        recurrence_count=recurrence_count,
        same_misconception_streak=same_misconception_streak,
        test_results=test_results,
    )

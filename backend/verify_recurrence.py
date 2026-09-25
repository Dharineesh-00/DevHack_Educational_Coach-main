"""Standalone end-to-end recurrence check for the current orchestrator wiring."""

from __future__ import annotations

import asyncio

import orchestrator

BUGGY_CODE = """
def is_valid(s: str) -> bool:
    stack = []
    mapping = {")": "(", "}": "{", "]": "[",
    }
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
    return True
"""


class DeterministicLLM:
    """Keep this verification independent of live OpenRouter availability."""

    async def generate(self, prompt: str, **_: object) -> str:
        if "choose exactly ONE misconception" in prompt:
            return '{"id": "unclosed-brackets-ignored", "confidence": 0.99}'
        return "Deterministic verification response."


async def main() -> None:
    original_client = orchestrator._ollama
    orchestrator._ollama = DeterministicLLM()
    try:
        observed: list[int] = []
        for attempt in range(1, 4):
            result = await orchestrator.run(
                code=BUGGY_CODE,
                language="python",
                user_id="recurrence-verification-user",
                problem_id="valid-parentheses",
            )
            observed.append(result.recurrence_count)
            print(
                f"attempt={attempt} misconception_id={result.misconception_id} "
                f"confidence={result.misconception_confidence} "
                f"recurrence_count={result.recurrence_count}"
            )

        expected = [0, 1, 2]
        assert observed == expected, (
            f"Expected recurrence_count values {expected}, got {observed}"
        )
    finally:
        orchestrator._ollama = original_client


if __name__ == "__main__":
    asyncio.run(main())

"""Async client for a local Ollama server."""

from __future__ import annotations

import logging

import httpx

from services.llm_client import AllModelsFailedError

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:1.5b"
DEFAULT_TIMEOUT = 60.0


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server cannot be reached."""


class OllamaClient:
    """Async client wrapping Ollama's non-streaming generate endpoint."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str | None = None,
        format: str | None = None,
        options: dict | None = None,
    ) -> str:
        """Generate text using the local Ollama server."""
        request_options = dict(options or {})
        if "max_tokens" in request_options and "num_predict" not in request_options:
            request_options["num_predict"] = request_options.pop("max_tokens")
        else:
            request_options.pop("max_tokens", None)

        payload: dict[str, object] = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if format is not None:
            payload["format"] = format
        if request_options:
            payload["options"] = request_options

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.ConnectError as exc:
            message = (
                f"Could not connect to Ollama at {self.base_url}. "
                "Start it with 'ollama serve' and try again."
            )
            logger.error("[Ollama] %s", message)
            raise OllamaConnectionError(message) from exc
        except httpx.TimeoutException as exc:
            message = f"Ollama timed out after {self.timeout:g}s at {self.base_url}."
            logger.error("[Ollama] %s", message)
            raise OllamaConnectionError(message) from exc
        except httpx.HTTPStatusError:
            logger.exception("[Ollama] Generation request failed with an HTTP error")
            raise

        data = response.json()
        result = data.get("response")
        if not isinstance(result, str):
            raise RuntimeError("Ollama returned an invalid response without text.")
        return result


__all__ = ["AllModelsFailedError", "OllamaClient", "OllamaConnectionError"]

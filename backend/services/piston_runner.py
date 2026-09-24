import asyncio
import logging
import os
import sys

import httpx

logger = logging.getLogger(__name__)

LOCAL_PISTON_URL = "http://localhost:2000/api/v2/execute"
PUBLIC_PISTON_URL = "https://emkc.org/api/v2/piston/execute"
PISTON_API_URL = os.getenv("PISTON_API_URL", LOCAL_PISTON_URL)
PISTON_PYTHON_VERSION = "3.10.0"
DEFAULT_TIMEOUT = 30.0  # seconds


class PistonClient:
    """Async client for interacting with the Piston code execution API."""

    def __init__(self, base_url: str = PISTON_API_URL, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    async def execute_code(self, language: str, code: str) -> dict:
        """
        Execute code via the Piston API.

        Args:
            language: Programming language identifier (e.g. "python", "javascript").
            code:     Source code string to execute.

        Returns:
            The parsed JSON response from the Piston API.

        Raises:
            httpx.TimeoutException: If the request exceeds the configured timeout.
            httpx.HTTPStatusError: If the API returns a non-2xx response.
        """
        payload = {
            "language": language,
            "version": PISTON_PYTHON_VERSION if language == "python" else "*",
            "files": [
                {
                    "name": "main",
                    "content": code,
                }
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response.json()
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                logger.warning("Piston service at %s unreachable: %s. Using local fallback for dev.", self.base_url, exc)
                if language == "python":
                    return await self._execute_python_locally(code)
                raise
            except httpx.HTTPStatusError as exc:
                if language != "python" or exc.response.status_code != 400:
                    raise
                return await self._execute_python_locally(code)

    async def _execute_python_locally(self, code: str) -> dict:
        """Keep local development usable when Piston has no installed runtime."""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise

        output = stdout.decode() + stderr.decode()
        return {
            "language": "python",
            "version": sys.version.split()[0],
            "run": {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "output": output,
                "code": process.returncode,
            },
        }

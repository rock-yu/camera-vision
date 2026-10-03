from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

import httpx
import ollama


class VisionError(RuntimeError):
    """Base class for expected vision service failures."""


class VisionConnectionError(VisionError):
    """Raised when the local Ollama server cannot be reached."""


class VisionModelError(VisionError):
    """Raised when Ollama cannot use the configured model."""


class VisionResponseError(VisionError):
    """Raised when Ollama returns a response without a description."""


class VisionClient(Protocol):
    def describe(self, image: bytes, prompt: str) -> str: ...


class OllamaVisionClient:
    def __init__(self, model: str, host: str | None = None, timeout: float = 120.0) -> None:
        self._model = model
        if host:
            self._client = ollama.Client(host=host, timeout=timeout)
        else:
            self._client = ollama.Client(timeout=timeout)

    def describe(self, image: bytes, prompt: str) -> str:
        try:
            response = self._client.chat(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image],
                    }
                ],
            )
        except ollama.ResponseError as exc:
            if exc.status_code == 404:
                raise VisionModelError(
                    f"model '{self._model}' is unavailable; run 'ollama pull {self._model}'"
                ) from exc
            raise VisionModelError(f"Ollama rejected the request: {exc.error}") from exc
        except httpx.ConnectError as exc:
            raise VisionConnectionError(
                "cannot connect to Ollama; ensure the local server is running"
            ) from exc
        except httpx.TimeoutException as exc:
            raise VisionConnectionError("the Ollama request timed out") from exc
        except httpx.HTTPError as exc:
            raise VisionConnectionError(f"Ollama HTTP request failed: {exc}") from exc

        content = _response_content(response)
        if not content:
            raise VisionResponseError("Ollama returned an empty or malformed response")
        return content


def _response_content(response: Any) -> str:
    message = getattr(response, "message", None)
    if message is None and isinstance(response, Mapping):
        message = response.get("message")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, Mapping):
        content = message.get("content")

    return content.strip() if isinstance(content, str) else ""

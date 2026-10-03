from __future__ import annotations

from dataclasses import dataclass

import httpx
import ollama
import pytest

from camera_vision.vision import (
    OllamaVisionClient,
    VisionConnectionError,
    VisionModelError,
    VisionResponseError,
)


@dataclass
class Message:
    content: str


@dataclass
class Response:
    message: Message


class FakeOllamaClient:
    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.arguments: dict[str, object] | None = None

    def chat(self, **arguments: object) -> object:
        self.arguments = arguments
        if self.error is not None:
            raise self.error
        return self.response


def make_client(fake: FakeOllamaClient) -> OllamaVisionClient:
    client = OllamaVisionClient("llama3.2-vision")
    client._client = fake
    return client


def test_describe_sends_bytes_prompt_and_model() -> None:
    fake = FakeOllamaClient(Response(Message("  A bright room.  ")))
    client = make_client(fake)

    result = client.describe(b"jpeg-bytes", "Describe it.")

    assert result == "A bright room."
    assert fake.arguments == {
        "model": "llama3.2-vision",
        "messages": [
            {
                "role": "user",
                "content": "Describe it.",
                "images": [b"jpeg-bytes"],
            }
        ],
    }


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"message": {}},
        {"message": {"content": "  "}},
        Response(Message("")),
    ],
)
def test_malformed_response_is_rejected(response: object) -> None:
    client = make_client(FakeOllamaClient(response))

    with pytest.raises(VisionResponseError, match="empty or malformed"):
        client.describe(b"image", "prompt")


def test_missing_model_has_pull_guidance() -> None:
    error = ollama.ResponseError("model not found", status_code=404)
    client = make_client(FakeOllamaClient(error=error))

    with pytest.raises(VisionModelError, match=r"ollama pull llama3\.2-vision"):
        client.describe(b"image", "prompt")


def test_rejected_request_is_model_error() -> None:
    error = ollama.ResponseError("bad request", status_code=400)
    client = make_client(FakeOllamaClient(error=error))

    with pytest.raises(VisionModelError, match="rejected"):
        client.describe(b"image", "prompt")


def test_connection_error_is_actionable() -> None:
    request = httpx.Request("POST", "http://localhost:11434/api/chat")
    client = make_client(FakeOllamaClient(error=httpx.ConnectError("refused", request=request)))

    with pytest.raises(VisionConnectionError, match="ensure the local server is running"):
        client.describe(b"image", "prompt")


def test_timeout_is_actionable() -> None:
    request = httpx.Request("POST", "http://localhost:11434/api/chat")
    client = make_client(FakeOllamaClient(error=httpx.ReadTimeout("slow", request=request)))

    with pytest.raises(VisionConnectionError, match="timed out"):
        client.describe(b"image", "prompt")

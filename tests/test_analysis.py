from __future__ import annotations

import time
from threading import Event

from camera_vision.analysis import AnalysisController
from camera_vision.vision import VisionConnectionError


class BlockingClient:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.calls = 0

    def describe(self, image: bytes, prompt: str) -> str:
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=2)
        return f"{prompt}: {image.decode()}"


class FailingClient:
    def describe(self, image: bytes, prompt: str) -> str:
        raise VisionConnectionError("offline")


def wait_for_outcome(controller: AnalysisController) -> object:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        outcome = controller.poll()
        if outcome is not None:
            return outcome
        time.sleep(0.001)
    raise AssertionError("analysis did not finish")


def test_controller_allows_only_one_request() -> None:
    client = BlockingClient()
    controller = AnalysisController(client)
    try:
        assert controller.submit(b"first", "prompt") is True
        assert client.started.wait(timeout=1)
        assert controller.submit(b"second", "prompt") is False
        assert controller.busy is True

        client.release.set()
        outcome = wait_for_outcome(controller)

        assert outcome.description == "prompt: first"
        assert outcome.error is None
        assert controller.busy is False
        assert client.calls == 1
    finally:
        client.release.set()
        controller.close()


def test_controller_returns_expected_failure_and_recovers() -> None:
    controller = AnalysisController(FailingClient())
    try:
        assert controller.submit(b"image", "prompt") is True
        outcome = wait_for_outcome(controller)

        assert isinstance(outcome.error, VisionConnectionError)
        assert outcome.description is None
        assert controller.submit(b"later", "prompt") is True
    finally:
        controller.close()

from __future__ import annotations

from dataclasses import replace
from io import StringIO
from typing import Any, ClassVar

import numpy as np
import pytest

from camera_vision import app
from camera_vision.analysis import AnalysisOutcome
from camera_vision.config import OutputMode, parse_args
from camera_vision.output import Reporter


class FakeCapture:
    def __init__(self, opened: bool = True, frames: list[tuple[bool, Any]] | None = None) -> None:
        self.opened = opened
        self.frames = list(frames or [])
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def read(self) -> tuple[bool, Any]:
        if not self.frames:
            raise KeyboardInterrupt
        return self.frames.pop(0)

    def release(self) -> None:
        self.released = True


class FakeCV:
    def __init__(self, capture: FakeCapture, keys: list[int] | None = None) -> None:
        self.capture = capture
        self.keys = list(keys or [])
        self.destroyed = False
        self.preview_count = 0
        self.camera_index: int | None = None

    def VideoCapture(self, camera_index: int) -> FakeCapture:
        self.camera_index = camera_index
        return self.capture

    def imshow(self, title: str, frame: Any) -> None:
        self.preview_count += 1

    def waitKey(self, delay: int) -> int:
        return self.keys.pop(0) if self.keys else -1

    def destroyAllWindows(self) -> None:
        self.destroyed = True


class UnusedClient:
    def describe(self, image: bytes, prompt: str) -> str:
        raise AssertionError("client should not be called")


class FakeController:
    instances: ClassVar[list[FakeController]] = []
    seed_outcomes: ClassVar[list[AnalysisOutcome | None]] = []

    def __init__(self, client: object) -> None:
        self.busy = False
        self.submissions: list[tuple[bytes, str]] = []
        self.closed = False
        self.outcomes = list(self.seed_outcomes)
        self.instances.append(self)

    def submit(self, image: bytes, prompt: str) -> bool:
        if self.busy:
            return False
        self.submissions.append((image, prompt))
        self.busy = True
        return True

    def poll(self) -> AnalysisOutcome | None:
        if not self.outcomes:
            return None
        outcome = self.outcomes.pop(0)
        if outcome is not None:
            self.busy = False
        return outcome

    def close(self) -> None:
        self.closed = True


class FakeSpeech:
    def __init__(self) -> None:
        self.submissions: list[str] = []
        self.closed = False

    def submit(self, text: str) -> bool:
        self.submissions.append(text)
        return True

    def close(self) -> None:
        self.closed = True


def make_reporter() -> tuple[Reporter, StringIO, StringIO]:
    stdout = StringIO()
    stderr = StringIO()
    return Reporter(OutputMode.DESCRIPTION, stdout, stderr), stdout, stderr


def test_unavailable_camera_exits_and_releases() -> None:
    capture = FakeCapture(opened=False)
    cv = FakeCV(capture)
    reporter, stdout, stderr = make_reporter()

    result = app.run(parse_args(["--mode", "manual"]), UnusedClient(), reporter, cv=cv)

    assert result == 2
    assert capture.released is True
    assert stdout.getvalue() == ""
    assert "camera index 0" in stderr.getvalue()


def test_unavailable_camera_closes_speech() -> None:
    capture = FakeCapture(opened=False)
    cv = FakeCV(capture)
    speech = FakeSpeech()
    reporter, _, _ = make_reporter()

    result = app.run(
        parse_args(["--mode", "manual"]),
        UnusedClient(),
        reporter,
        cv=cv,
        speech=speech,
    )

    assert result == 2
    assert speech.closed is True


def test_quit_key_releases_camera_and_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame)])
    cv = FakeCV(capture, keys=[ord("q")])
    reporter, _, _ = make_reporter()
    monkeypatch.setattr(app, "AnalysisController", FakeController)

    result = app.run(parse_args(["--mode", "manual"]), UnusedClient(), reporter, cv=cv)

    assert result == 0
    assert capture.released is True
    assert cv.destroyed is True
    assert cv.preview_count == 1
    assert FakeController.instances[-1].closed is True


def test_frame_read_failure_is_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = FakeCapture(frames=[(False, None)])
    cv = FakeCV(capture)
    speech = FakeSpeech()
    reporter, _, stderr = make_reporter()
    monkeypatch.setattr(app, "AnalysisController", FakeController)

    result = app.run(
        parse_args(["--mode", "manual"]),
        UnusedClient(),
        reporter,
        cv=cv,
        speech=speech,
    )

    assert result == 3
    assert "failed to read a frame" in stderr.getvalue()
    assert capture.released is True
    assert speech.closed is True


def test_successful_description_is_submitted_to_speech(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame)])
    cv = FakeCV(capture, keys=[ord("q")])
    speech = FakeSpeech()
    reporter, stdout, _ = make_reporter()
    FakeController.seed_outcomes = [AnalysisOutcome(description="A person entered.")]
    monkeypatch.setattr(app, "AnalysisController", FakeController)
    try:
        result = app.run(
            parse_args(["--mode", "manual", "--output", "description"]),
            UnusedClient(),
            reporter,
            cv=cv,
            speech=speech,
        )
    finally:
        FakeController.seed_outcomes = []

    assert result == 0
    assert speech.submissions == ["A person entered."]
    assert speech.closed is True
    assert stdout.getvalue() == "A person entered.\n"


def test_failed_description_is_not_submitted_to_speech(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame)])
    cv = FakeCV(capture, keys=[ord("q")])
    speech = FakeSpeech()
    reporter, stdout, stderr = make_reporter()
    from camera_vision.vision import VisionConnectionError

    FakeController.seed_outcomes = [AnalysisOutcome(error=VisionConnectionError("Ollama offline"))]
    monkeypatch.setattr(app, "AnalysisController", FakeController)
    try:
        result = app.run(
            parse_args(["--mode", "manual", "--output", "description"]),
            UnusedClient(),
            reporter,
            cv=cv,
            speech=speech,
        )
    finally:
        FakeController.seed_outcomes = []

    assert result == 0
    assert speech.submissions == []
    assert stdout.getvalue() == ""
    assert "Ollama offline" in stderr.getvalue()


def test_manual_capture_submits_jpeg_and_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame), (True, frame)])
    cv = FakeCV(capture, keys=[ord(" "), ord("q")])
    reporter, _, _ = make_reporter()
    FakeController.instances.clear()
    monkeypatch.setattr(app, "AnalysisController", FakeController)

    result = app.run(
        replace(parse_args(["--mode", "manual"]), prompt="Describe hazards."),
        UnusedClient(),
        reporter,
        cv=cv,
    )

    controller = FakeController.instances[-1]
    assert result == 0
    assert len(controller.submissions) == 1
    image, prompt = controller.submissions[0]
    assert image.startswith(b"\xff\xd8")
    assert prompt == "Describe hazards."


def test_busy_controller_skips_capture_but_updates_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame), (True, frame)])
    cv = FakeCV(capture, keys=[ord(" "), ord("q")])
    reporter, _, _ = make_reporter()
    FakeController.instances.clear()
    monkeypatch.setattr(app, "AnalysisController", FakeController)

    app.run(parse_args(["--mode", "both"]), UnusedClient(), reporter, cv=cv, clock=lambda: 0.0)

    controller = FakeController.instances[-1]
    assert len(controller.submissions) == 1
    assert cv.preview_count == 2


def test_headless_interval_stops_cleanly_on_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    capture = FakeCapture(frames=[(True, frame)])
    cv = FakeCV(capture)
    speech = FakeSpeech()
    reporter, _, stderr = make_reporter()
    FakeController.instances.clear()
    monkeypatch.setattr(app, "AnalysisController", FakeController)
    config = parse_args(["--mode", "interval", "--no-preview", "--output", "description"])

    result = app.run(
        config,
        UnusedClient(),
        reporter,
        cv=cv,
        clock=lambda: 0.0,
        speech=speech,
    )

    assert result == 0
    assert "Interrupted; shutting down." in stderr.getvalue()
    assert capture.released is True
    assert cv.destroyed is False
    assert speech.closed is True

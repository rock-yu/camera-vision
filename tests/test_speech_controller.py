from __future__ import annotations

import time
from io import StringIO
from threading import Event, Lock

from camera_vision.config import OutputMode
from camera_vision.output import Reporter
from camera_vision.speech import SpeechPlaybackError
from camera_vision.speech_controller import SpeechController


class BlockingEngine:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.closed = False
        self.spoken: list[str] = []
        self._lock = Lock()

    def speak(self, text: str) -> None:
        with self._lock:
            self.spoken.append(text)
        self.started.set()
        self.release.wait(timeout=2)

    def close(self) -> None:
        self.closed = True


class RecoveringEngine:
    def __init__(self) -> None:
        self.first_failed = Event()
        self.second_spoken = Event()
        self.calls = 0
        self.closed = False

    def speak(self, text: str) -> None:
        self.calls += 1
        if self.calls == 1:
            self.first_failed.set()
            raise SpeechPlaybackError("speaker unavailable")
        self.second_spoken.set()

    def close(self) -> None:
        self.closed = True


def wait_until(predicate: object, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if callable(predicate) and predicate():
            return
        time.sleep(0.001)
    raise AssertionError("condition was not met")


def test_controller_finishes_active_and_keeps_only_newest_pending() -> None:
    engine = BlockingEngine()
    controller = SpeechController(engine, lambda _message: None)

    assert controller.submit("first") is True
    assert engine.started.wait(timeout=1)
    assert controller.submit("stale") is True
    assert controller.submit("newest") is True
    engine.release.set()
    wait_until(lambda: engine.spoken == ["first", "newest"])
    controller.close()

    assert engine.closed is True
    assert controller.submit("after close") is False


def test_controller_reports_failure_and_processes_later_text() -> None:
    engine = RecoveringEngine()
    errors: list[str] = []
    controller = SpeechController(engine, errors.append)

    assert controller.submit("first") is True
    assert engine.first_failed.wait(timeout=1)
    assert controller.submit("second") is True
    assert engine.second_spoken.wait(timeout=1)
    controller.close()

    assert errors == ["speaker unavailable"]
    assert engine.calls == 2
    assert engine.closed is True


def test_close_discards_pending_utterance() -> None:
    engine = BlockingEngine()
    controller = SpeechController(engine, lambda _message: None)

    controller.submit("active")
    assert engine.started.wait(timeout=1)
    controller.submit("pending")
    engine.release.set()
    controller.close()

    assert engine.spoken == ["active"]
    assert engine.closed is True


def test_speech_error_uses_stderr_without_polluting_description_stdout() -> None:
    engine = RecoveringEngine()
    stdout = StringIO()
    stderr = StringIO()
    reporter = Reporter(OutputMode.DESCRIPTION, stdout, stderr)
    controller = SpeechController(engine, reporter.error)

    reporter.description("A chair is visible.")
    controller.submit("A chair is visible.")
    assert engine.first_failed.wait(timeout=1)
    wait_until(lambda: "speaker unavailable" in stderr.getvalue())
    controller.close()

    assert stdout.getvalue() == "A chair is visible.\n"
    assert stderr.getvalue() == "Error: speaker unavailable\n"

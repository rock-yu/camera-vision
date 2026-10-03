from __future__ import annotations

from camera_vision import cli
from camera_vision.speech import SpeechInitializationError


class FakeEngine:
    def speak(self, text: str) -> None:
        return

    def close(self) -> None:
        return


class FakeController:
    def __init__(self, engine: FakeEngine, report_error: object) -> None:
        self.engine = engine
        self.report_error = report_error


def test_cli_initializes_speech_before_running_app(monkeypatch) -> None:
    engine = FakeEngine()
    events: list[str] = []

    def create_engine(config, report_status):
        events.append("speech")
        return engine

    def run_app(config, client, reporter, *, speech):
        events.append("app")
        assert isinstance(speech, FakeController)
        assert speech.engine is engine
        return 0

    monkeypatch.setattr(cli, "create_speech_engine", create_engine)
    monkeypatch.setattr(cli, "SpeechController", FakeController)
    monkeypatch.setattr(cli, "run", run_app)

    assert cli.main(["--speech"]) == 0
    assert events == ["speech", "app"]


def test_cli_reports_speech_initialization_failure(monkeypatch, capsys) -> None:
    app_called = False

    def create_engine(config, report_status):
        raise SpeechInitializationError("speech is unavailable")

    def run_app(*args, **kwargs):
        nonlocal app_called
        app_called = True
        return 0

    monkeypatch.setattr(cli, "create_speech_engine", create_engine)
    monkeypatch.setattr(cli, "run", run_app)

    assert cli.main(["--speech", "--speech-engine", "kokoro"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error: speech is unavailable" in captured.err
    assert app_called is False

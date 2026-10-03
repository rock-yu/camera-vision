from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from camera_vision.config import SpeechEngine, parse_args
from camera_vision.speech import (
    KokoroSpeechEngine,
    MacOSSpeechEngine,
    SpeechInitializationError,
    SpeechPlaybackError,
    SpeechSynthesisError,
    create_speech_engine,
)


class FakeKokoroModel:
    def __init__(
        self,
        error: Exception | None = None,
        voices: list[str] | None = None,
    ) -> None:
        self.error = error
        self.voices = voices or ["af_sarah", "af_heart"]
        self.calls: list[tuple[str, str, float]] = []

    def get_voices(self) -> list[str]:
        return self.voices

    def create(self, text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
        self.calls.append((text, voice, speed))
        if self.error is not None:
            raise self.error
        return np.array([0.0, 0.5], dtype=np.float32), 24_000


class FakePlayer:
    class PortAudioError(RuntimeError):
        pass

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[np.ndarray, int, bool]] = []
        self.stopped = False

    def play(self, samples: np.ndarray, rate: int, blocking: bool) -> None:
        self.calls.append((samples, rate, blocking))
        if self.error is not None:
            raise self.error

    def stop(self) -> None:
        self.stopped = True


class FakeEngine:
    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def close(self) -> None:
        return


def create_asset_files(tmp_path: Path) -> tuple[Path, Path]:
    model_path = tmp_path / "model.onnx"
    voices_path = tmp_path / "voices.bin"
    model_path.touch()
    voices_path.touch()
    return model_path, voices_path


def test_kokoro_uses_selected_voice_rate_and_blocking_playback(tmp_path: Path) -> None:
    model_path, voices_path = create_asset_files(tmp_path)
    model = FakeKokoroModel()
    player = FakePlayer()
    engine = KokoroSpeechEngine(
        model_path,
        voices_path,
        "af_heart",
        1.25,
        model_factory=lambda *_args: model,
        player=player,
    )

    engine.speak("A chair is visible.")
    engine.close()

    assert model.calls == [("A chair is visible.", "af_heart", 1.25)]
    assert player.calls[0][1:] == (24_000, True)
    assert player.stopped is True


@pytest.mark.parametrize("missing", ["model", "voices"])
def test_kokoro_requires_local_assets(tmp_path: Path, missing: str) -> None:
    model_path, voices_path = create_asset_files(tmp_path)
    (model_path if missing == "model" else voices_path).unlink()

    with pytest.raises(SpeechInitializationError, match=f"Kokoro {missing}"):
        KokoroSpeechEngine(
            model_path,
            voices_path,
            None,
            1.0,
            model_factory=lambda *_args: FakeKokoroModel(),
            player=FakePlayer(),
        )


def test_kokoro_reports_model_load_failure(tmp_path: Path) -> None:
    model_path, voices_path = create_asset_files(tmp_path)

    with pytest.raises(SpeechInitializationError, match="could not load"):
        KokoroSpeechEngine(
            model_path,
            voices_path,
            None,
            1.0,
            model_factory=lambda *_args: (_ for _ in ()).throw(RuntimeError("bad model")),
            player=FakePlayer(),
        )


def test_kokoro_rejects_unavailable_explicit_voice(tmp_path: Path) -> None:
    model_path, voices_path = create_asset_files(tmp_path)

    with pytest.raises(SpeechInitializationError, match="voice 'missing' is unavailable"):
        KokoroSpeechEngine(
            model_path,
            voices_path,
            "missing",
            1.0,
            model_factory=lambda *_args: FakeKokoroModel(),
            player=FakePlayer(),
        )


def test_kokoro_reports_synthesis_failure(tmp_path: Path) -> None:
    model_path, voices_path = create_asset_files(tmp_path)
    engine = KokoroSpeechEngine(
        model_path,
        voices_path,
        None,
        1.0,
        model_factory=lambda *_args: FakeKokoroModel(RuntimeError("bad text")),
        player=FakePlayer(),
    )

    with pytest.raises(SpeechSynthesisError, match="bad text"):
        engine.speak("Describe this.")


def test_kokoro_reports_playback_failure(tmp_path: Path) -> None:
    model_path, voices_path = create_asset_files(tmp_path)
    engine = KokoroSpeechEngine(
        model_path,
        voices_path,
        None,
        1.0,
        model_factory=lambda *_args: FakeKokoroModel(),
        player=FakePlayer(FakePlayer.PortAudioError("no device")),
    )

    with pytest.raises(SpeechPlaybackError, match="no device"):
        engine.speak("Describe this.")


def completed(
    args: list[str],
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_macos_speech_uses_argument_vector_voice_and_rate(tmp_path: Path) -> None:
    executable = tmp_path / "say"
    executable.touch()
    calls: list[list[str]] = []

    def runner(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[-2:] == ["-v", "?"]:
            return completed(command, stdout="Samantha            en_US\n")
        return completed(command)

    engine = MacOSSpeechEngine(
        "Samantha",
        1.25,
        executable=executable,
        runner=runner,
    )
    engine.speak("A person entered.")

    assert calls[-1] == [
        str(executable),
        "-r",
        "250",
        "-v",
        "Samantha",
        "A person entered.",
    ]


def test_macos_speech_rejects_missing_executable(tmp_path: Path) -> None:
    with pytest.raises(SpeechInitializationError, match="not found"):
        MacOSSpeechEngine(None, 1.0, executable=tmp_path / "missing")


def test_macos_speech_rejects_unavailable_voice(tmp_path: Path) -> None:
    executable = tmp_path / "say"
    executable.touch()

    with pytest.raises(SpeechInitializationError, match="unavailable"):
        MacOSSpeechEngine(
            "Missing",
            1.0,
            executable=executable,
            runner=lambda command, **_kwargs: completed(command, stdout="Samantha en_US\n"),
        )


def test_macos_speech_reports_nonzero_exit(tmp_path: Path) -> None:
    executable = tmp_path / "say"
    executable.touch()
    engine = MacOSSpeechEngine(
        None,
        1.0,
        executable=executable,
        runner=lambda command, **_kwargs: completed(command, 2, stderr="audio failed"),
    )

    with pytest.raises(SpeechPlaybackError, match="audio failed"):
        engine.speak("A person entered.")


def test_speech_disabled_creates_no_engine() -> None:
    config = parse_args([])

    assert create_speech_engine(config, lambda _message: None) is None


def test_explicit_kokoro_never_falls_back() -> None:
    config = parse_args(["--speech", "--speech-engine", "kokoro"])
    macos_called = False

    def kokoro_factory(*_args: Any) -> FakeEngine:
        raise SpeechInitializationError("missing assets")

    def macos_factory(*_args: Any, **_kwargs: Any) -> FakeEngine:
        nonlocal macos_called
        macos_called = True
        return FakeEngine()

    with pytest.raises(SpeechInitializationError, match="missing assets"):
        create_speech_engine(
            config,
            lambda _message: None,
            kokoro_factory=kokoro_factory,
            macos_factory=macos_factory,
        )

    assert macos_called is False


def test_auto_reports_and_uses_macos_fallback() -> None:
    config = parse_args(["--speech"])
    statuses: list[str] = []
    fallback = FakeEngine()

    engine = create_speech_engine(
        config,
        statuses.append,
        kokoro_factory=lambda *_args: (_ for _ in ()).throw(
            SpeechInitializationError("missing assets")
        ),
        macos_factory=lambda *_args, **_kwargs: fallback,
    )

    assert engine is fallback
    assert statuses == ["Kokoro unavailable (missing assets); using macOS system speech."]


def test_auto_without_supported_fallback_is_actionable() -> None:
    config = replace(parse_args(["--speech"]), speech_engine=SpeechEngine.AUTO)

    with pytest.raises(SpeechInitializationError, match="available only on macOS"):
        create_speech_engine(
            config,
            lambda _message: None,
            platform_name="linux",
            kokoro_factory=lambda *_args: (_ for _ in ()).throw(
                SpeechInitializationError("missing assets")
            ),
        )

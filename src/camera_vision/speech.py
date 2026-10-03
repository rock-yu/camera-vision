from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol

from camera_vision.config import AppConfig, SpeechEngine


class SpeechError(RuntimeError):
    """Base class for expected speech failures."""


class SpeechInitializationError(SpeechError):
    """Raised when a requested speech engine cannot start."""


class SpeechSynthesisError(SpeechError):
    """Raised when text cannot be converted to speech."""


class SpeechPlaybackError(SpeechError):
    """Raised when generated speech cannot be played."""


class SpeechEngineClient(Protocol):
    def speak(self, text: str) -> None: ...

    def close(self) -> None: ...


class KokoroSpeechEngine:
    def __init__(
        self,
        model_path: Path,
        voices_path: Path,
        voice: str | None,
        rate: float,
        *,
        model_factory: Callable[[str, str], Any] | None = None,
        player: Any | None = None,
    ) -> None:
        if not model_path.is_file():
            raise SpeechInitializationError(
                f"Kokoro model not found at '{model_path}'; download the local speech assets"
            )
        if not voices_path.is_file():
            raise SpeechInitializationError(
                f"Kokoro voices not found at '{voices_path}'; download the local speech assets"
            )

        try:
            if model_factory is None:
                model_factory = import_module("kokoro_onnx").Kokoro
            if player is None:
                player = import_module("sounddevice")
            self._model = model_factory(str(model_path), str(voices_path))
        except ImportError as exc:
            raise SpeechInitializationError(
                "Kokoro speech dependencies are unavailable; run 'uv sync --extra speech'"
            ) from exc
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise SpeechInitializationError(f"could not load Kokoro speech assets: {exc}") from exc

        self._player = player
        self._voice = voice or "af_sarah"
        self._rate = rate
        try:
            available_voices = self._model.get_voices()
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise SpeechInitializationError(f"could not read Kokoro voices: {exc}") from exc
        if self._voice not in available_voices:
            raise SpeechInitializationError(
                f"Kokoro voice '{self._voice}' is unavailable; choose one of: "
                + ", ".join(available_voices)
            )

    def speak(self, text: str) -> None:
        try:
            samples, sample_rate = self._model.create(
                text,
                voice=self._voice,
                speed=self._rate,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise SpeechSynthesisError(f"Kokoro synthesis failed: {exc}") from exc

        playback_errors = (
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
            getattr(self._player, "PortAudioError", RuntimeError),
        )
        try:
            self._player.play(samples, sample_rate, blocking=True)
        except playback_errors as exc:
            raise SpeechPlaybackError(f"Kokoro audio playback failed: {exc}") from exc

    def close(self) -> None:
        stop = getattr(self._player, "stop", None)
        if callable(stop):
            stop()


class MacOSSpeechEngine:
    def __init__(
        self,
        voice: str | None,
        rate: float,
        *,
        executable: Path = Path("/usr/bin/say"),
        platform_name: str = sys.platform,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if platform_name != "darwin":
            raise SpeechInitializationError("the macOS speech engine is available only on macOS")
        if not executable.is_file():
            raise SpeechInitializationError(f"macOS speech command not found at '{executable}'")

        self._executable = executable
        self._voice = voice
        self._words_per_minute = max(1, round(200 * rate))
        self._runner = runner

        if voice is not None:
            available = self._run([str(executable), "-v", "?"])
            if not any(line.startswith(voice + " ") for line in available.stdout.splitlines()):
                raise SpeechInitializationError(
                    f"macOS voice '{voice}' is unavailable; run 'say -v ?' to list voices"
                )

    def speak(self, text: str) -> None:
        command = [str(self._executable), "-r", str(self._words_per_minute)]
        if self._voice is not None:
            command.extend(["-v", self._voice])
        command.append(text)

        result = self._run(command)
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit status {result.returncode}"
            raise SpeechPlaybackError(f"macOS speech playback failed: {detail}")

    def close(self) -> None:
        return

    def _run(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise SpeechInitializationError(
                f"macOS speech command not found at '{self._executable}'"
            ) from exc
        except OSError as exc:
            raise SpeechPlaybackError(f"could not run macOS speech: {exc}") from exc


def create_speech_engine(
    config: AppConfig,
    report_status: Callable[[str], None],
    *,
    platform_name: str = sys.platform,
    kokoro_factory: Callable[..., SpeechEngineClient] = KokoroSpeechEngine,
    macos_factory: Callable[..., SpeechEngineClient] = MacOSSpeechEngine,
) -> SpeechEngineClient | None:
    if not config.speech:
        return None

    if config.speech_engine is SpeechEngine.KOKORO:
        return _create_kokoro(config, kokoro_factory)
    if config.speech_engine is SpeechEngine.MACOS:
        return macos_factory(
            config.speech_voice,
            config.speech_rate,
            platform_name=platform_name,
        )

    try:
        return _create_kokoro(config, kokoro_factory)
    except SpeechInitializationError as exc:
        if platform_name != "darwin":
            raise SpeechInitializationError(
                f"{exc}; automatic fallback is available only on macOS"
            ) from exc
        report_status(f"Kokoro unavailable ({exc}); using macOS system speech.")
        return macos_factory(
            None,
            config.speech_rate,
            platform_name=platform_name,
        )


def _create_kokoro(
    config: AppConfig,
    factory: Callable[..., SpeechEngineClient],
) -> SpeechEngineClient:
    return factory(
        config.speech_model_path,
        config.speech_voices_path,
        config.speech_voice,
        config.speech_rate,
    )

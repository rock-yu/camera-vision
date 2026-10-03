from __future__ import annotations

from pathlib import Path

import pytest

from camera_vision.config import CaptureMode, OutputMode, SpeechEngine, parse_args


def test_defaults() -> None:
    config = parse_args([])

    assert config.model == "llama3.2-vision"
    assert config.camera_index == 0
    assert config.capture_mode is CaptureMode.BOTH
    assert config.interval == 5.0
    assert config.preview is True
    assert config.output_mode is OutputMode.HUMAN
    assert config.timeout == 120.0
    assert config.speech is False
    assert config.speech_engine is SpeechEngine.AUTO
    assert config.speech_voice is None
    assert config.speech_rate == 1.0
    assert config.speech_model_path.name == "kokoro-v1.0.onnx"
    assert config.speech_voices_path.name == "voices-v1.0.bin"


def test_all_options() -> None:
    config = parse_args(
        [
            "--model",
            "moondream",
            "--host",
            "http://localhost:11434",
            "--camera-index",
            "2",
            "--prompt",
            "Find obstacles.",
            "--mode",
            "interval",
            "--interval",
            "12.5",
            "--no-preview",
            "--output",
            "description",
            "--timeout",
            "30",
            "--speech",
            "--speech-engine",
            "kokoro",
            "--speech-voice",
            "af_heart",
            "--speech-rate",
            "1.2",
            "--speech-model-path",
            "~/models/kokoro.onnx",
            "--speech-voices-path",
            "~/models/voices.bin",
        ]
    )

    assert config.model == "moondream"
    assert config.host == "http://localhost:11434"
    assert config.camera_index == 2
    assert config.prompt == "Find obstacles."
    assert config.capture_mode is CaptureMode.INTERVAL
    assert config.interval == 12.5
    assert config.preview is False
    assert config.output_mode is OutputMode.DESCRIPTION
    assert config.timeout == 30.0
    assert config.speech is True
    assert config.speech_engine is SpeechEngine.KOKORO
    assert config.speech_voice == "af_heart"
    assert config.speech_rate == 1.2
    assert config.speech_model_path == Path("~/models/kokoro.onnx").expanduser()
    assert config.speech_voices_path == Path("~/models/voices.bin").expanduser()


@pytest.mark.parametrize(
    "arguments",
    [
        ["--camera-index", "-1"],
        ["--interval", "0"],
        ["--timeout", "-1"],
        ["--speech-rate", "0"],
        ["--model", " "],
        ["--prompt", " "],
        ["--speech-voice", " "],
        ["--mode", "manual", "--no-preview"],
        ["--mode", "both", "--no-preview"],
    ],
)
def test_invalid_options_exit(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        parse_args(arguments)

    assert error.value.code == 2

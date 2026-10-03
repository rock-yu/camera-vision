from __future__ import annotations

import pytest

from camera_vision.config import CaptureMode, OutputMode, parse_args


def test_defaults() -> None:
    config = parse_args([])

    assert config.model == "llama3.2-vision"
    assert config.camera_index == 0
    assert config.capture_mode is CaptureMode.BOTH
    assert config.interval == 5.0
    assert config.preview is True
    assert config.output_mode is OutputMode.HUMAN
    assert config.timeout == 120.0


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


@pytest.mark.parametrize(
    "arguments",
    [
        ["--camera-index", "-1"],
        ["--interval", "0"],
        ["--timeout", "-1"],
        ["--model", " "],
        ["--prompt", " "],
        ["--mode", "manual", "--no-preview"],
        ["--mode", "both", "--no-preview"],
    ],
)
def test_invalid_options_exit(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        parse_args(arguments)

    assert error.value.code == 2

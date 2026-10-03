from __future__ import annotations

from collections.abc import Sequence

from camera_vision.app import run
from camera_vision.config import parse_args
from camera_vision.output import Reporter
from camera_vision.speech import SpeechInitializationError, create_speech_engine
from camera_vision.speech_controller import SpeechController
from camera_vision.vision import OllamaVisionClient


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    reporter = Reporter(config.output_mode)
    client = OllamaVisionClient(
        model=config.model,
        host=config.host,
        timeout=config.timeout,
    )
    try:
        speech_engine = create_speech_engine(config, reporter.status)
    except SpeechInitializationError as exc:
        reporter.error(str(exc))
        return 2

    speech = SpeechController(speech_engine, reporter.error) if speech_engine is not None else None
    return run(config, client, reporter, speech=speech)

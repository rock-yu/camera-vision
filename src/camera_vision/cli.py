from __future__ import annotations

from collections.abc import Sequence

from camera_vision.app import run
from camera_vision.config import parse_args
from camera_vision.output import Reporter
from camera_vision.vision import OllamaVisionClient


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)
    reporter = Reporter(config.output_mode)
    client = OllamaVisionClient(
        model=config.model,
        host=config.host,
        timeout=config.timeout,
    )
    return run(config, client, reporter)

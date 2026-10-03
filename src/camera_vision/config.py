from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

DEFAULT_PROMPT = "Describe what you see in this environment in detail."


class CaptureMode(StrEnum):
    MANUAL = "manual"
    INTERVAL = "interval"
    BOTH = "both"

    @property
    def supports_manual(self) -> bool:
        return self in {CaptureMode.MANUAL, CaptureMode.BOTH}

    @property
    def supports_interval(self) -> bool:
        return self in {CaptureMode.INTERVAL, CaptureMode.BOTH}


class OutputMode(StrEnum):
    HUMAN = "human"
    DESCRIPTION = "description"


@dataclass(frozen=True, slots=True)
class AppConfig:
    model: str
    host: str | None
    camera_index: int
    prompt: str
    capture_mode: CaptureMode
    interval: float
    preview: bool
    output_mode: OutputMode
    timeout: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="camera-vision",
        description="Describe webcam frames with a local Ollama vision model.",
    )
    parser.add_argument("--model", default="llama3.2-vision", help="Ollama vision model name.")
    parser.add_argument(
        "--host",
        default=os.environ.get("OLLAMA_HOST"),
        help="Ollama server URL. Defaults to OLLAMA_HOST or Ollama's local default.",
    )
    parser.add_argument("--camera-index", type=int, default=0, help="OpenCV camera index.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt sent with each frame.")
    parser.add_argument(
        "--mode",
        type=CaptureMode,
        choices=CaptureMode,
        default=CaptureMode.BOTH,
        help="Capture manually, on an interval, or both.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between automatic capture attempts.",
    )
    parser.add_argument(
        "--preview",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show the camera preview window.",
    )
    parser.add_argument(
        "--output",
        type=OutputMode,
        choices=OutputMode,
        default=OutputMode.HUMAN,
        help="'description' keeps stdout suitable for piping to another command.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Ollama request timeout in seconds.",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> AppConfig:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.camera_index < 0:
        parser.error("--camera-index must be zero or greater")
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not args.model.strip():
        parser.error("--model cannot be empty")
    if not args.prompt.strip():
        parser.error("--prompt cannot be empty")
    if args.mode.supports_manual and not args.preview:
        parser.error("manual capture requires --preview; use --mode interval with --no-preview")

    return AppConfig(
        model=args.model,
        host=args.host,
        camera_index=args.camera_index,
        prompt=args.prompt,
        capture_mode=args.mode,
        interval=args.interval,
        preview=args.preview,
        output_mode=args.output,
        timeout=args.timeout,
    )

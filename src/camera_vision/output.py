from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TextIO

from camera_vision.config import OutputMode


@dataclass(slots=True)
class Reporter:
    mode: OutputMode
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)

    def status(self, message: str) -> None:
        print(message, file=self.stderr, flush=True)

    def error(self, message: str) -> None:
        print(f"Error: {message}", file=self.stderr, flush=True)

    def description(self, description: str) -> None:
        if self.mode is OutputMode.HUMAN:
            print("\n--- Model description ---", file=self.stdout)
            print(description, file=self.stdout)
            print("-------------------------\n", file=self.stdout, flush=True)
            return

        print(" ".join(description.split()), file=self.stdout, flush=True)

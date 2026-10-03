from __future__ import annotations

import textwrap
from typing import Any

import cv2


class FrameEncodingError(RuntimeError):
    """Raised when OpenCV cannot encode a camera frame."""


def encode_jpeg(frame: Any, quality: int = 90) -> bytes:
    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    if not success:
        raise FrameEncodingError("OpenCV could not encode the captured frame as JPEG")
    return encoded.tobytes()


def add_preview_overlay(frame: Any, status: str, description: str) -> Any:
    height, width = frame.shape[:2]
    line_height = 24
    horizontal_padding = 12
    wrap_width = max(24, (width - horizontal_padding * 2) // 10)
    lines = [status]

    if description:
        wrapped = textwrap.wrap("Latest: " + " ".join(description.split()), width=wrap_width)
        lines.extend(wrapped[:5])

    panel_height = min(height, horizontal_padding * 2 + line_height * len(lines))
    cv2.rectangle(frame, (0, 0), (width, panel_height), (0, 0, 0), -1)

    for index, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (horizontal_padding, horizontal_padding + line_height * (index + 1) - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return frame

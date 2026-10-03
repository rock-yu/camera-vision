from __future__ import annotations

import cv2
import numpy as np
import pytest

from camera_vision import camera


def test_encode_jpeg_returns_image_bytes() -> None:
    frame = np.zeros((16, 16, 3), dtype=np.uint8)

    encoded = camera.encode_jpeg(frame)

    assert encoded.startswith(b"\xff\xd8")
    assert encoded.endswith(b"\xff\xd9")


def test_encode_jpeg_reports_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(camera.cv2, "imencode", lambda *_args, **_kwargs: (False, None))

    with pytest.raises(camera.FrameEncodingError, match="could not encode"):
        camera.encode_jpeg(object())


def test_preview_overlay_changes_a_copy_sized_frame() -> None:
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)

    result = camera.add_preview_overlay(
        frame.copy(),
        "Analyzing...",
        "A very long environmental description " * 20,
    )

    assert result.shape == frame.shape
    assert not np.array_equal(result, frame)
    assert result[0, 0].tolist() == [0, 0, 0]
    assert cv2.countNonZero(cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)) > 0

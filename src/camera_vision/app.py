from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import cv2

from camera_vision.analysis import AnalysisController
from camera_vision.camera import FrameEncodingError, add_preview_overlay, encode_jpeg
from camera_vision.config import AppConfig
from camera_vision.output import Reporter
from camera_vision.vision import VisionClient

WINDOW_TITLE = "Camera Vision"


def run(
    config: AppConfig,
    client: VisionClient,
    reporter: Reporter,
    *,
    cv: Any = cv2,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    capture = cv.VideoCapture(config.camera_index)
    if not capture.isOpened():
        reporter.error(
            f"could not open camera index {config.camera_index}; check camera permissions and index"
        )
        capture.release()
        return 2

    controller = AnalysisController(client)
    latest_description = ""
    status = "Ready"
    next_interval = clock()

    reporter.status(f"Camera {config.camera_index} opened; using model '{config.model}'.")
    if config.preview:
        controls = "Space: describe | " if config.capture_mode.supports_manual else ""
        reporter.status(f"{controls}Q or Esc: quit.")
    else:
        reporter.status("Press Ctrl-C to quit.")

    try:
        while True:
            frame_ok, frame = capture.read()
            if not frame_ok:
                reporter.error("failed to read a frame from the camera")
                return 3

            outcome = controller.poll()
            if outcome is not None:
                if outcome.error is not None:
                    reporter.error(str(outcome.error))
                    status = "Analysis failed; ready to retry"
                elif outcome.description is not None:
                    latest_description = outcome.description
                    reporter.description(outcome.description)
                    status = "Ready"

            key = -1
            if config.preview:
                preview_frame = add_preview_overlay(frame.copy(), status, latest_description)
                cv.imshow(WINDOW_TITLE, preview_frame)
                key = cv.waitKey(1) & 0xFF
                if key in {ord("q"), ord("Q"), 27}:
                    return 0

            now = clock()
            manual_requested = config.capture_mode.supports_manual and key == ord(" ")
            interval_requested = config.capture_mode.supports_interval and now >= next_interval
            if interval_requested:
                next_interval = now + config.interval

            if manual_requested or interval_requested:
                if controller.busy:
                    status = "Analyzing; capture skipped"
                    continue
                try:
                    image = encode_jpeg(frame)
                except FrameEncodingError as exc:
                    reporter.error(str(exc))
                    status = "Frame encoding failed; ready to retry"
                    continue

                controller.submit(image, config.prompt)
                status = f"Analyzing with {config.model}..."
    except KeyboardInterrupt:
        reporter.status("Interrupted; shutting down.")
        return 0
    finally:
        controller.close()
        capture.release()
        if config.preview:
            cv.destroyAllWindows()

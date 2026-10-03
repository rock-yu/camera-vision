from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

from camera_vision.vision import VisionClient, VisionError


@dataclass(frozen=True, slots=True)
class AnalysisOutcome:
    description: str | None = None
    error: VisionError | None = None


class AnalysisController:
    def __init__(self, client: VisionClient) -> None:
        self._client = client
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="camera-vision")
        self._future: Future[str] | None = None

    @property
    def busy(self) -> bool:
        return self._future is not None

    def submit(self, image: bytes, prompt: str) -> bool:
        if self.busy:
            return False
        self._future = self._executor.submit(self._client.describe, image, prompt)
        return True

    def poll(self) -> AnalysisOutcome | None:
        if self._future is None or not self._future.done():
            return None

        future = self._future
        self._future = None
        try:
            return AnalysisOutcome(description=future.result())
        except VisionError as exc:
            return AnalysisOutcome(error=exc)

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)

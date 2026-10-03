from __future__ import annotations

from collections.abc import Callable
from threading import Condition, Thread

from camera_vision.speech import SpeechEngineClient, SpeechError


class SpeechController:
    def __init__(
        self,
        engine: SpeechEngineClient,
        report_error: Callable[[str], None],
    ) -> None:
        self._engine = engine
        self._report_error = report_error
        self._condition = Condition()
        self._pending: str | None = None
        self._closed = False
        self._thread = Thread(target=self._run, name="camera-vision-speech", daemon=False)
        self._thread.start()

    def submit(self, text: str) -> bool:
        with self._condition:
            if self._closed:
                return False
            self._pending = text
            self._condition.notify()
            return True

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._pending = None
            self._condition.notify()

        self._thread.join()
        self._engine.close()

    def _run(self) -> None:
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._pending is not None or self._closed)
                if self._closed:
                    return
                text = self._pending
                self._pending = None

            if text is None:
                continue
            try:
                self._engine.speak(text)
            except SpeechError as exc:
                self._report_error(str(exc))

import time


class FPSMeter:
    def __init__(self) -> None:
        self._window_start = time.time()
        self._counter = 0
        self.current_fps = 0.0

    def tick(self) -> float:
        self._counter += 1
        now = time.time()
        elapsed = now - self._window_start
        if elapsed >= 1.0:
            self.current_fps = self._counter / elapsed
            self._counter = 0
            self._window_start = now
        return self.current_fps

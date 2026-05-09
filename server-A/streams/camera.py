import cv2
from typing import Optional


class CameraCapture:
    def __init__(self, source: str | int, width: int, height: int, fps: int) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera source: {self.source}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        if self._cap is None:
            raise RuntimeError("Camera is not open.")
        return self._cap.read()

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

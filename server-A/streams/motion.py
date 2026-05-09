import cv2
import numpy as np


class MOG2MotionDetector:
    def __init__(self, motion_area_threshold: int) -> None:
        self.motion_area_threshold = motion_area_threshold
        self._subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True,
        )

    def detect(self, frame_bgr: np.ndarray) -> tuple[bool, np.ndarray, int]:
        fg_mask = self._subtractor.apply(frame_bgr)
        _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.dilate(cleaned, kernel, iterations=2)

        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        for contour in contours:
            area = int(cv2.contourArea(contour))
            if area > max_area:
                max_area = area

        return max_area >= self.motion_area_threshold, cleaned, max_area

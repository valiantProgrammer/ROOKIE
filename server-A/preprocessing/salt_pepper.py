import cv2
import numpy as np


def reduce_salt_pepper(frame_bgr: np.ndarray) -> np.ndarray:
    # Median filtering is effective for impulse noise while preserving edges.
    return cv2.medianBlur(frame_bgr, 3)

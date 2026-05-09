import cv2
import numpy as np


def deblur_motion(frame_bgr: np.ndarray) -> np.ndarray:
    gaussian = cv2.GaussianBlur(frame_bgr, (0, 0), sigmaX=1.2)
    sharpened = cv2.addWeighted(frame_bgr, 1.6, gaussian, -0.6, 0)
    return cv2.bilateralFilter(sharpened, d=5, sigmaColor=40, sigmaSpace=40)

import cv2
import numpy as np


def correct_exposure(frame_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    mean_luma = float(np.mean(gray))

    if mean_luma < 70:
        gamma = 0.8
    elif mean_luma > 180:
        gamma = 1.2
    else:
        return frame_bgr

    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma *
                     255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(frame_bgr, table)

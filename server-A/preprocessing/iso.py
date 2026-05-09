import cv2
import numpy as np


def reduce_iso_noise(frame_bgr: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(
        frame_bgr,
        None,
        h=6,
        hColor=6,
        templateWindowSize=7,
        searchWindowSize=21,
    )

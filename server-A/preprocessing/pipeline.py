import cv2
import numpy as np

from preprocessing.exposure import correct_exposure
from preprocessing.iso import reduce_iso_noise
from preprocessing.salt_pepper import reduce_salt_pepper


def _apply_clahe(frame_bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    merged = cv2.merge((l, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def preprocess_frame(frame_bgr: np.ndarray) -> np.ndarray:
    frame = reduce_salt_pepper(frame_bgr)
    frame = correct_exposure(frame)
    frame = reduce_iso_noise(frame)
    frame = _apply_clahe(frame)
    return frame

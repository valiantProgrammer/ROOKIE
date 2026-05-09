import cv2
import numpy as np


def compress_frame(frame_bgr: np.ndarray, jpeg_quality: int) -> bytes:
    ok, encoded = cv2.imencode(
        ".jpg",
        frame_bgr,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)],
    )
    if not ok:
        raise RuntimeError("JPEG compression failed")
    return encoded.tobytes()

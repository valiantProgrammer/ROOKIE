import cv2
import numpy as np


def laplacian_blur_score(frame_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def fft_blur_score(frame_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    fft = np.fft.fftshift(np.fft.fft2(gray))
    magnitude = np.log(np.abs(fft) + 1.0)

    h, w = gray.shape
    cx, cy = w // 2, h // 2
    radius = 30
    low_band = magnitude[cy - radius : cy + radius, cx - radius : cx + radius]

    return float(np.mean(magnitude) - np.mean(low_band))


def sobel_sharpness(frame_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.mean(np.hypot(grad_x, grad_y)))


def analyze_blur(
    frame_bgr: np.ndarray,
    laplacian_threshold: float = 80.0,
    fft_threshold: float = 10.0,
    sobel_threshold: float = 12.0,
) -> dict[str, float | str | bool]:
    lap = laplacian_blur_score(frame_bgr)
    fft = fft_blur_score(frame_bgr)
    sobel = sobel_sharpness(frame_bgr)

    blurry = lap < laplacian_threshold or fft < fft_threshold or sobel < sobel_threshold

    if not blurry:
        blur_type = "Sharp"
    elif sobel < 8.0:
        blur_type = "Heavy Motion Blur"
    elif lap < 40.0:
        blur_type = "Strong Blur"
    else:
        blur_type = "Moderate Blur"

    return {
        "blurry": blurry,
        "blur_type": blur_type,
        "laplacian_score": lap,
        "fft_score": fft,
        "sobel_score": sobel,
    }


def is_blurry(frame_bgr: np.ndarray, laplacian_threshold: float = 80.0) -> bool:
    report = analyze_blur(frame_bgr, laplacian_threshold=laplacian_threshold)
    return bool(report["blurry"])

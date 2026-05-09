from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    camera_source: str | int = 0
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30
    max_queue_size: int = 5

    motion_resize_width: int = 640
    motion_resize_height: int = 360
    preprocess_width: int = 1280
    preprocess_height: int = 720

    motion_area_threshold: int = 1500
    motion_timeout_seconds: float = 2.5

    base_skip: int = 2
    medium_skip: int = 3
    high_skip: int = 5

    blur_check_interval: int = 5
    blur_laplacian_threshold: float = 80.0

    jpeg_quality: int = 70
    zmq_push_address: str = "tcp://*:5555"

    log_interval_seconds: float = 2.0


SETTINGS = Settings()

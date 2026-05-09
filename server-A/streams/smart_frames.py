class SmartFrameController:
    def __init__(self, base_skip: int, medium_skip: int, high_skip: int) -> None:
        self.base_skip = base_skip
        self.medium_skip = medium_skip
        self.high_skip = high_skip
        self.dynamic_skip = base_skip

    def update(self, capture_fps: float, queue_pressure: float) -> int:
        if capture_fps >= 24 and queue_pressure < 0.5:
            self.dynamic_skip = self.base_skip
        elif capture_fps >= 14 and queue_pressure < 0.8:
            self.dynamic_skip = self.medium_skip
        else:
            self.dynamic_skip = self.high_skip
        return self.dynamic_skip

    def should_process(self, frame_index: int) -> bool:
        skip = max(1, self.dynamic_skip)
        return frame_index % skip == 0

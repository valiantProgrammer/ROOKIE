import queue
import signal
import threading
import time
from typing import Any

import cv2

from config.settings import SETTINGS
from preprocessing.blur_detect import is_blurry
from preprocessing.motion_blur import deblur_motion
from preprocessing.pipeline import preprocess_frame
from streams.camera import CameraCapture
from streams.motion import MOG2MotionDetector
from streams.smart_frames import SmartFrameController
from utils.fps import FPSMeter
from utils.logger import get_logger
from utils.queues import make_queue, put_latest
from zmq.sender import ZMQFrameSender


logger = get_logger()
stop_event = threading.Event()


def capture_worker(camera: CameraCapture, raw_queue: queue.Queue):
    frame_id = 0
    capture_fps = FPSMeter()

    while not stop_event.is_set():
        ok, frame = camera.read()
        if not ok:
            logger.warning("Camera frame grab failed; retrying")
            time.sleep(0.01)
            continue

        frame_id += 1
        fps = capture_fps.tick()
        payload = {
            "frame_id": frame_id,
            "capture_ts": time.time(),
            "capture_fps": fps,
            "frame": frame,
        }
        put_latest(raw_queue, payload)


def motion_worker(
    raw_queue: queue.Queue,
    gated_queue: queue.Queue,
    controller: SmartFrameController,
    detector: MOG2MotionDetector,
):
    last_motion_ts = 0.0

    while not stop_event.is_set():
        try:
            item = raw_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        frame_id = item["frame_id"]
        capture_fps = float(item["capture_fps"])
        q_pressure = raw_queue.qsize() / max(1, raw_queue.maxsize)
        controller.update(capture_fps, q_pressure)

        if not controller.should_process(frame_id):
            continue

        frame = item["frame"]
        motion_frame = cv2.resize(
            frame,
            (SETTINGS.motion_resize_width, SETTINGS.motion_resize_height),
            interpolation=cv2.INTER_LINEAR,
        )

        motion_detected, _, area = detector.detect(motion_frame)
        if motion_detected:
            last_motion_ts = time.time()

        motion_active = (
            time.time() - last_motion_ts) < SETTINGS.motion_timeout_seconds
        if not motion_active:
            continue

        item["motion_area"] = area
        item["dynamic_skip"] = controller.dynamic_skip
        put_latest(gated_queue, item)


def preprocess_worker(gated_queue: queue.Queue, out_queue: queue.Queue, display_queue: queue.Queue):
    processed_counter = 0

    while not stop_event.is_set():
        try:
            item = gated_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        frame = item["frame"]
        processed = preprocess_frame(frame)
        processed_counter += 1

        if processed_counter % SETTINGS.blur_check_interval == 0:
            if is_blurry(processed, SETTINGS.blur_laplacian_threshold):
                processed = deblur_motion(processed)
                item["deblurred"] = True
            else:
                item["deblurred"] = False

        item["processed_frame"] = processed
        put_latest(out_queue, item)
        try:
            put_latest(display_queue, item)
        except Exception:
            pass


def display_worker(display_queue: queue.Queue):
    try:
        while not stop_event.is_set():
            try:
                item = display_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            frame = item.get("processed_frame") or item.get("frame")
            if frame is None:
                continue

            cv2.imshow("Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
                break
    finally:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def sender_worker(out_queue: queue.Queue, sender: ZMQFrameSender):
    sent_counter = 0
    log_clock = time.time()

    while not stop_event.is_set():
        try:
            item = out_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        meta: dict[str, Any] = {
            "frame_id": item["frame_id"],
            "capture_ts": item["capture_ts"],
            "motion_area": item.get("motion_area", 0),
            "skip": item.get("dynamic_skip", SETTINGS.base_skip),
            "deblurred": item.get("deblurred", False),
        }

        sent = sender.enqueue(item["processed_frame"], meta)
        if sent:
            sent_counter += 1

        if (time.time() - log_clock) >= SETTINGS.log_interval_seconds:
            logger.info(
                "out_q=%d zmq_q=%d sent=%d",
                out_queue.qsize(),
                sender.queue_size(),
                sent_counter,
            )
            log_clock = time.time()


def _build_threads(camera: CameraCapture, sender: ZMQFrameSender, display_queue: queue.Queue):
    raw_queue = make_queue(SETTINGS.max_queue_size)
    gated_queue = make_queue(SETTINGS.max_queue_size)
    out_queue = make_queue(SETTINGS.max_queue_size)

    controller = SmartFrameController(
        base_skip=SETTINGS.base_skip,
        medium_skip=SETTINGS.medium_skip,
        high_skip=SETTINGS.high_skip,
    )
    detector = MOG2MotionDetector(SETTINGS.motion_area_threshold)

    threads = [
        threading.Thread(target=capture_worker, args=(
            camera, raw_queue), name="capture", daemon=True),
        threading.Thread(
            target=motion_worker,
            args=(raw_queue, gated_queue, controller, detector),
            name="motion",
            daemon=True,
        ),
        threading.Thread(
            target=preprocess_worker,
            args=(gated_queue, out_queue, display_queue),
            name="preprocess",
            daemon=True,
        ),
        threading.Thread(
            target=sender_worker,
            args=(out_queue, sender),
            name="stream",
            daemon=True,
        ),
    ]

    # display thread shows the latest processed frames in a window
    threads.append(
        threading.Thread(
            target=display_worker,
            args=(display_queue,),
            name="display",
            daemon=True,
        )
    )

    return threads


def _install_signal_handlers() -> None:
    def _handle_stop(signum, _frame):
        logger.info("Signal %s received, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)


def main() -> None:
    _install_signal_handlers()

    camera = CameraCapture(
        source=SETTINGS.camera_source,
        width=SETTINGS.camera_width,
        height=SETTINGS.camera_height,
        fps=SETTINGS.camera_fps,
    )
    sender = None

    try:
        sender = ZMQFrameSender(
            bind_address=SETTINGS.zmq_push_address,
            jpeg_quality=SETTINGS.jpeg_quality,
            max_queue_size=SETTINGS.max_queue_size,
        )
    except Exception as exc:
        logger.error("Failed to initialize ZeroMQ sender: %s", exc)
        return

    try:
        camera.open()
        logger.info("Camera opened: source=%s", SETTINGS.camera_source)
        logger.info("ZMQ PUSH active at %s", SETTINGS.zmq_push_address)

        display_queue = make_queue(SETTINGS.max_queue_size)
        threads = _build_threads(camera, sender, display_queue)
        for thread in threads:
            thread.start()

        while not stop_event.is_set():
            time.sleep(0.25)

    except Exception as exc:
        logger.error("Failed to start preprocessing server: %s", exc)

    finally:
        stop_event.set()
        camera.release()
        if sender is not None:
            sender.close()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        logger.info("ROOKIE RTX 3050 preprocessing server stopped")


if __name__ == "__main__":
    main()

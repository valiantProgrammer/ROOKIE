import queue
import threading
import time
import sys
import os
from typing import Any
from pathlib import Path

from .compression import compress_frame


def _load_pyzmq():
    project_root = str(Path(__file__).resolve().parents[1])
    removed_entries: list[str] = []

    def should_remove(entry: str) -> bool:
        if entry == "":
            return True
        try:
            resolved_entry = str(Path(entry).resolve())
            return (
                resolved_entry == project_root
                or resolved_entry.startswith(project_root + os.sep)
            )
        except Exception:
            return False

    for entry in list(sys.path):
        if should_remove(entry):
            sys.path.remove(entry)
            removed_entries.append(entry)

    local_zmq = sys.modules.pop("zmq", None)
    try:
        import zmq as external_zmq  # type: ignore
    finally:
        for entry in reversed(removed_entries):
            sys.path.insert(0, entry)
        if local_zmq is not None:
            sys.modules["zmq"] = local_zmq

    return external_zmq


pyzmq = _load_pyzmq()


class ZMQFrameSender:
    def __init__(self, bind_address: str, jpeg_quality: int, max_queue_size: int) -> None:
        self.bind_address = bind_address
        self.jpeg_quality = jpeg_quality
        self._queue: queue.Queue[tuple[bytes, dict[str, Any]]] = queue.Queue(
            maxsize=max_queue_size)
        self._running = threading.Event()
        self._running.set()

        self._ctx = pyzmq.Context.instance()
        self._socket = self._ctx.socket(pyzmq.PUSH)
        self._socket.setsockopt(pyzmq.SNDHWM, max_queue_size)
        self._socket.bind(bind_address)

        self._worker = threading.Thread(
            target=self._send_loop, name="zmq-sender", daemon=True)
        self._worker.start()

    def enqueue(self, frame_bgr, metadata: dict[str, Any]) -> bool:
        payload = compress_frame(frame_bgr, self.jpeg_quality)
        msg = (payload, metadata)
        try:
            self._queue.put_nowait(msg)
            return True
        except queue.Full:
            return False

    def _send_loop(self) -> None:
        while self._running.is_set():
            try:
                payload, metadata = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            packet = {
                "ts": time.time(),
                "meta": metadata,
                "jpg": payload,
            }

            self._socket.send_pyobj(packet, flags=0)

    def queue_size(self) -> int:
        return self._queue.qsize()

    def close(self) -> None:
        self._running.clear()
        self._worker.join(timeout=1.0)
        self._socket.close(0)
        self._ctx.term()

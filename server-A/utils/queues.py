from queue import Full, Queue
from typing import TypeVar


T = TypeVar("T")


def make_queue(max_size: int) -> Queue:
    return Queue(maxsize=max_size)


def put_latest(q: Queue[T], item: T) -> bool:
    try:
        q.put_nowait(item)
        return True
    except Full:
        try:
            q.get_nowait()
        except Exception:
            return False
        try:
            q.put_nowait(item)
            return True
        except Full:
            return False

import logging
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Iterator, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_END = object()


class BackgroundStreamRunner:
    """
    Runs a stream to completion on its own thread and hands its items to
    the caller through a queue.

    A streaming response stops iterating as soon as the client goes away
    (another chat selected, tab closed), which would abandon the answer
    halfway. Here the producer keeps going whatever the consumer does, so
    the answer is still saved and shows up when the client comes back.
    """

    def __init__(self, max_workers: int):
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="answer",
        )

    def run(self, items: Iterator[T]) -> Iterator[T]:
        queue: Queue = Queue()

        def produce() -> None:
            try:
                for item in items:
                    queue.put(item)
            except Exception:
                logger.exception("Background stream failed")
            finally:
                queue.put(_END)

        self.executor.submit(produce)

        return self._consume(queue)

    @staticmethod
    def _consume(queue: Queue) -> Iterator[T]:
        while (item := queue.get()) is not _END:
            yield item

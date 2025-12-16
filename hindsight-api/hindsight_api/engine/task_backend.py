"""
Abstract task backend for running async tasks.

This provides an abstraction that can be adapted to different execution models:
- AsyncIO queue (default implementation)
- Pub/Sub architectures (future)
- Message brokers (future)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


class TaskBackend(ABC):
    """
    Abstract base class for task execution backends.

    Implementations must:
    1. Store/publish task events (as serializable dicts)
    2. Execute tasks through a provided executor callback

    The backend treats tasks as pure dictionaries that can be serialized
    and sent over the network. The executor (typically MemoryEngine.execute_task)
    receives the dict and routes it to the appropriate handler.
    """

    def __init__(self):
        """Initialize the task backend."""
        self._executor: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._initialized = False

    def set_executor(self, executor: Callable[[dict[str, Any]], Awaitable[None]]):
        """
        Set the executor callback for processing tasks.

        Args:
            executor: Async function that takes a task dict and executes it
        """
        self._executor = executor

    @abstractmethod
    async def initialize(self):
        """
        Initialize the backend (e.g., start workers, connect to broker).
        """
        pass

    @abstractmethod
    async def submit_task(self, task_dict: dict[str, Any]):
        """
        Submit a task for execution.

        Args:
            task_dict: Task as a dictionary (must be serializable)
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """
        Shutdown the backend gracefully (e.g., stop workers, close connections).
        """
        pass

    async def _execute_task(self, task_dict: dict[str, Any]):
        """
        Execute a task through the registered executor.

        Args:
            task_dict: Task dictionary to execute
        """
        if self._executor is None:
            task_type = task_dict.get("type", "unknown")
            logger.warning(f"No executor registered, skipping task {task_type}")
            return

        try:
            await self._executor(task_dict)
        except Exception as e:
            task_type = task_dict.get("type", "unknown")
            logger.error(f"Error executing task {task_type}: {e}")
            import traceback

            traceback.print_exc()


class AsyncIOQueueBackend(TaskBackend):
    """
    Task backend implementation using asyncio queues.

    This is the default implementation that uses in-process asyncio queues
    and a periodic consumer worker.
    """

    def __init__(self, batch_size: int = 100, batch_interval: float = 1.0):
        """
        Initialize AsyncIO queue backend.

        Args:
            batch_size: Maximum number of tasks to process in one batch
            batch_interval: Maximum time (seconds) to wait before processing batch
        """
        super().__init__()
        self._queue: asyncio.Queue | None = None
        self._worker_task: asyncio.Task | None = None
        self._shutdown_event: asyncio.Event | None = None
        self._batch_size = batch_size
        self._batch_interval = batch_interval

    async def initialize(self):
        """Initialize the queue and start the worker."""
        if self._initialized:
            return

        self._queue = asyncio.Queue()
        self._shutdown_event = asyncio.Event()
        self._worker_task = asyncio.create_task(self._worker())
        self._initialized = True
        logger.info("AsyncIOQueueBackend initialized")

    async def submit_task(self, task_dict: dict[str, Any]):
        """
        Submit a task by putting it in the queue.

        Args:
            task_dict: Task dictionary to execute
        """
        if not self._initialized:
            await self.initialize()

        await self._queue.put(task_dict)
        task_type = task_dict.get("type", "unknown")
        task_id = task_dict.get("id")

    async def wait_for_pending_tasks(self, timeout: float = 5.0):
        """
        Wait for all pending tasks in the queue to be processed.

        This is useful in tests to ensure background tasks complete before assertions.

        Args:
            timeout: Maximum time to wait in seconds
        """
        if not self._initialized or self._queue is None:
            return

        # Wait for queue to be empty and give worker time to process
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self._queue.empty():
                # Queue is empty, give worker a bit more time to finish any in-flight task
                await asyncio.sleep(0.3)
                # Check again - if still empty, we're done
                if self._queue.empty():
                    return
            else:
                # Queue not empty, wait a bit
                await asyncio.sleep(0.1)

    async def shutdown(self):
        """Shutdown the worker and drain the queue."""
        if not self._initialized:
            return

        logger.info("Shutting down AsyncIOQueueBackend...")

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel worker
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass  # Worker cancelled successfully

        self._initialized = False
        logger.info("AsyncIOQueueBackend shutdown complete")

    async def _worker(self):
        """
        Background worker that processes tasks in batches.

        Collects tasks for up to batch_interval seconds or batch_size items,
        then processes them.
        """
        while not self._shutdown_event.is_set():
            try:
                # Collect tasks for batching
                tasks = []
                deadline = asyncio.get_event_loop().time() + self._batch_interval

                while len(tasks) < self._batch_size and asyncio.get_event_loop().time() < deadline:
                    try:
                        remaining_time = max(0.1, deadline - asyncio.get_event_loop().time())
                        task_dict = await asyncio.wait_for(self._queue.get(), timeout=remaining_time)
                        tasks.append(task_dict)
                    except TimeoutError:
                        break

                # Process batch
                if tasks:
                    # Execute tasks concurrently
                    await asyncio.gather(
                        *[self._execute_task(task_dict) for task_dict in tasks], return_exceptions=True
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Backoff on error

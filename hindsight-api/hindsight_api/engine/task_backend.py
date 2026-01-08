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


class SyncTaskBackend(TaskBackend):
    """
    Synchronous task backend that executes tasks immediately.

    This is useful for embedded/CLI usage where we don't want background
    workers that prevent clean exit. Tasks are executed inline rather than
    being queued.
    """

    async def initialize(self):
        """No-op for sync backend."""
        self._initialized = True
        logger.debug("SyncTaskBackend initialized")

    async def submit_task(self, task_dict: dict[str, Any]):
        """
        Execute the task immediately (synchronously).

        Args:
            task_dict: Task dictionary to execute
        """
        if not self._initialized:
            await self.initialize()

        await self._execute_task(task_dict)

    async def shutdown(self):
        """No-op for sync backend."""
        self._initialized = False
        logger.debug("SyncTaskBackend shutdown")


class AsyncIOQueueBackend(TaskBackend):
    """
    Task backend implementation using asyncio queues.

    This is the default implementation that uses in-process asyncio queues
    and a periodic consumer worker.
    """

    def __init__(self, batch_size: int = 10, batch_interval: float = 1.0):
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
        self._in_flight_count = 0
        self._in_flight_lock = asyncio.Lock()

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

    async def wait_for_pending_tasks(self, timeout: float = 120.0):
        """
        Wait for all pending tasks in the queue and in-flight tasks to complete.

        This is useful in tests to ensure background tasks complete before assertions.

        Args:
            timeout: Maximum time to wait in seconds (default 120s for long-running tasks)
        """
        if not self._initialized or self._queue is None:
            return

        # Wait for queue to be empty AND no in-flight tasks
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            async with self._in_flight_lock:
                in_flight = self._in_flight_count

            if self._queue.empty() and in_flight == 0:
                # Queue is empty and no tasks in flight, we're done
                return

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

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

    async def _execute_task_with_tracking(self, task_dict: dict[str, Any]):
        """Execute a task and track its in-flight status."""
        async with self._in_flight_lock:
            self._in_flight_count += 1
        try:
            await self._execute_task(task_dict)
        finally:
            async with self._in_flight_lock:
                self._in_flight_count -= 1

    async def _execute_task_no_tracking(self, task_dict: dict[str, Any]):
        """Execute a task without in-flight tracking (tracking done at batch level)."""
        await self._execute_task(task_dict)

    def _get_queue_stats(self) -> tuple[int, dict[str, int]]:
        """Get current queue size and bank_id distribution."""
        queue_size = self._queue.qsize() if self._queue else 0
        bank_distribution: dict[str, int] = {}

        if queue_size > 0 and self._queue:
            # Peek at queue items without removing them
            # Note: This is a snapshot and may not be perfectly accurate due to concurrency
            try:
                # Access internal deque for logging purposes only
                items = list(self._queue._queue)  # type: ignore[attr-defined]
                for item in items:
                    bank_id = item.get("bank_id", "unknown")
                    bank_distribution[bank_id] = bank_distribution.get(bank_id, 0) + 1
            except Exception:
                pass  # Queue access failed, return empty distribution

        return queue_size, bank_distribution

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
                        # Track task as in-flight immediately when picked up from queue
                        # This prevents wait_for_pending_tasks from returning too early
                        async with self._in_flight_lock:
                            self._in_flight_count += 1
                        tasks.append(task_dict)
                    except TimeoutError:
                        break

                # Process batch
                if tasks:
                    # Log batch start with queue stats
                    queue_size, bank_distribution = self._get_queue_stats()

                    # Summarize batch by task type and bank
                    batch_summary: dict[str, dict[str, int]] = {}
                    for task_dict in tasks:
                        task_type = task_dict.get("type", "unknown")
                        bank_id = task_dict.get("bank_id", "unknown")
                        if task_type not in batch_summary:
                            batch_summary[task_type] = {}
                        batch_summary[task_type][bank_id] = batch_summary[task_type].get(bank_id, 0) + 1

                    # Build log message
                    batch_parts = []
                    for task_type, banks in sorted(batch_summary.items()):
                        bank_str = ", ".join(f"{b}:{c}" for b, c in sorted(banks.items()))
                        batch_parts.append(f"{task_type}[{bank_str}]")
                    batch_str = ", ".join(batch_parts)

                    if queue_size > 0:
                        pending_str = ", ".join(f"{k}:{v}" for k, v in sorted(bank_distribution.items()))
                        logger.info(
                            f"Processing {len(tasks)} tasks: {batch_str} (pending={queue_size} [{pending_str}])"
                        )
                    else:
                        logger.info(f"Processing {len(tasks)} tasks: {batch_str}")

                    # Execute tasks concurrently (in_flight already tracked when picked up)
                    await asyncio.gather(
                        *[self._execute_task_no_tracking(task_dict) for task_dict in tasks], return_exceptions=True
                    )

                    # Decrement in_flight count after all tasks complete
                    async with self._in_flight_lock:
                        self._in_flight_count -= len(tasks)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Backoff on error

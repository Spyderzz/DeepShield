"""Phase 19.3 — in-memory async job queue.

Backed by FastAPI BackgroundTasks for single-worker deployments; the API
surface matches what a future Celery/Redis migration would expose, so
callers don't need to change when we swap the transport.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from loguru import logger


@dataclass
class Job:
    id: str
    stage: str = "queued"
    progress: int = 0  # 0..100
    status: str = "queued"  # queued | running | done | error
    result: Any | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class _JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job(id=uuid.uuid4().hex)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return
            for k, v in fields.items():
                setattr(j, k, v)
            j.updated_at = time.time()

    def prune(self, ttl_seconds: int = 3600) -> None:
        cutoff = time.time() - ttl_seconds
        with self._lock:
            dead = [jid for jid, j in self._jobs.items() if j.updated_at < cutoff]
            for jid in dead:
                self._jobs.pop(jid, None)


registry = _JobRegistry()


def run_job(job_id: str, stages: list[str], fn: Callable[[Callable[[str, int], None]], Any]) -> None:
    """Wrap a callable so it advances stage/progress through `registry`.

    `fn` receives a `progress(stage, pct)` updater it can call.
    """
    def progress(stage: str, pct: int) -> None:
        registry.update(job_id, stage=stage, progress=max(0, min(100, int(pct))), status="running")

    registry.update(job_id, status="running", stage=stages[0] if stages else "running", progress=1)
    try:
        result = fn(progress)
        registry.update(job_id, status="done", stage="done", progress=100, result=result)
    except Exception as e:  # noqa: BLE001
        logger.exception(f"Job {job_id} failed")
        registry.update(job_id, status="error", error=str(e), progress=100)

"""Job State Service for Tracking Asynchronous Processing Operations (Phase 5).

Manages job lifecycle records, stage progress tracking, and temporary result storage
with primary Redis backing and in-memory fallback for deterministic testing and resilience.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import redis

try:
    from app.core.config import settings
    from app.core.logging import logger
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logging import logger


class JobNotFoundError(Exception):
    """Raised when an operation references an unknown or expired job ID."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Analysis job '{job_id}' not found.")


class JobQueueUnavailableError(Exception):
    """Raised when Celery broker or Redis connection is unreachable."""

    def __init__(self, message: str = "The asynchronous task queue is currently unavailable.") -> None:
        super().__init__(message)


class JobStateService:
    """Service orchestrating temporary job state persistence across Redis and memory."""

    JOB_KEY_PREFIX = "kollamo:job:"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours temporary persistence (Section 75)

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_url: Optional[str] = None,
        use_memory_fallback: bool = True,
    ) -> None:
        self._redis = redis_client
        self._redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        self._use_memory_fallback = use_memory_fallback
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._redis_connected: Optional[bool] = None

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Returns active Redis client if accessible, or None."""
        if self._redis is not None:
            return self._redis

        if self._redis_connected is False:
            return None

        try:
            client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            client.ping()
            self._redis = client
            self._redis_connected = True
            logger.info(f"Connected to Redis job state backend at {self._redis_url}")
            return self._redis
        except Exception as exc:
            self._redis_connected = False
            logger.debug(f"Redis not available ({exc}); using in-memory job state store.")
            return None

    def create_job(self, job_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initializes a new job record with status QUEUED."""
        now_iso = datetime.now(timezone.utc).isoformat()
        job_record: Dict[str, Any] = {
            "job_id": job_id,
            "status": "QUEUED",
            "progress": {
                "stage": "QUEUED",
                "completed": 0,
                "total": None,
                "percentage": None,
            },
            "result": None,
            "error": None,
            "created_at": now_iso,
            "updated_at": now_iso,
            "request_data": request_data,
        }

        # Save to memory store first for immediate local availability
        self._memory_store[job_id] = job_record

        # Persist to Redis if available
        r = self._get_redis_client()
        if r is not None:
            try:
                r.set(
                    f"{self.JOB_KEY_PREFIX}{job_id}",
                    json.dumps(job_record),
                    ex=self.DEFAULT_TTL_SECONDS,
                )
            except Exception as exc:
                logger.warning(f"Failed to persist job {job_id} to Redis: {exc}")

        return job_record

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates fields of an existing job record."""
        current = self.get_job(job_id)
        if not current:
            # If not found, create base structure
            current = {
                "job_id": job_id,
                "status": status or "PROCESSING",
                "progress": progress,
                "result": result,
                "error": error,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            if status is not None:
                current["status"] = status
            if progress is not None:
                current["progress"] = progress
            if result is not None:
                current["result"] = result
            if error is not None:
                current["error"] = error
            current["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._memory_store[job_id] = current

        r = self._get_redis_client()
        if r is not None:
            try:
                r.set(
                    f"{self.JOB_KEY_PREFIX}{job_id}",
                    json.dumps(current),
                    ex=self.DEFAULT_TTL_SECONDS,
                )
            except Exception as exc:
                logger.warning(f"Failed to update job {job_id} in Redis: {exc}")

        return current

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves job state from Redis or in-memory store."""
        r = self._get_redis_client()
        if r is not None:
            try:
                data = r.get(f"{self.JOB_KEY_PREFIX}{job_id}")
                if data:
                    parsed = json.loads(data)
                    self._memory_store[job_id] = parsed
                    return parsed
            except Exception as exc:
                logger.debug(f"Redis get failed for {job_id}: {exc}")

        return self._memory_store.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        """Removes a job record from memory and Redis."""
        removed_memory = self._memory_store.pop(job_id, None) is not None
        removed_redis = False

        r = self._get_redis_client()
        if r is not None:
            try:
                removed_redis = bool(r.delete(f"{self.JOB_KEY_PREFIX}{job_id}"))
            except Exception:
                pass

        return removed_memory or removed_redis

    def clear(self) -> None:
        """Clears memory store (used for tests)."""
        self._memory_store.clear()


_job_service_instance: Optional[JobStateService] = None


def get_job_state_service() -> JobStateService:
    """Dependency injection provider for JobStateService singleton."""
    global _job_service_instance
    if _job_service_instance is None:
        _job_service_instance = JobStateService()
    return _job_service_instance


def set_job_state_service(service: Optional[JobStateService]) -> None:
    """Sets or resets the singleton instance (used for tests)."""
    global _job_service_instance
    _job_service_instance = service

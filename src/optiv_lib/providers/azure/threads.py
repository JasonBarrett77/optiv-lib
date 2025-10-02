# src/optiv_lib/providers/azure/objects/threads.py
from __future__ import annotations

import random
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, Sequence, TypeVar

from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError

T = TypeVar("T")
R = TypeVar("R")

# ----------------------------
# Global concurrency controls
# ----------------------------
_GLOBAL_MAX_WORKERS = 32
_GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=_GLOBAL_MAX_WORKERS)
_GLOBAL_SEMAPHORE = threading.Semaphore(_GLOBAL_MAX_WORKERS)


def _default_retry_if(exc: BaseException) -> bool:
    if isinstance(exc, (ServiceRequestError, ServiceResponseError)):
        return True
    if isinstance(exc, HttpResponseError):
        return getattr(exc, "status_code", None) in (408, 429, 502, 503, 504)
    return False


def _retry_after_seconds(exc: HttpResponseError, fallback: float) -> float:
    try:
        headers = getattr(exc, "response", None).headers  # type: ignore[attr-defined]
        if headers:
            ra = headers.get("Retry-After")
            if ra is not None:
                return max(fallback, float(ra))
            ra_ms = headers.get("Retry-After-Ms")
            if ra_ms is not None:
                return max(fallback, float(ra_ms) / 1000.0)
    except Exception:
        pass
    return fallback


def _retry_call(func: Callable[[T], R], arg: T, *, retries: int, base_delay: float, backoff: float, max_delay: float, retry_if: Callable[[BaseException], bool], ) -> R:
    attempt = 0
    delay = max(0.0, base_delay)

    while True:
        _GLOBAL_SEMAPHORE.acquire()
        try:
            return func(arg)
        except BaseException as exc:
            attempt += 1
            if attempt > retries or not retry_if(exc):
                raise
            sleep_for = delay
            if isinstance(exc, HttpResponseError) and getattr(exc, "status_code", None) in (408, 429, 502, 503, 504):
                sleep_for = _retry_after_seconds(exc, fallback=delay)
            # jitter: +/-25% to avoid synchronized retries
            jitter = random.uniform(-0.25 * sleep_for, 0.25 * sleep_for)
            time.sleep(max(0.0, min(max_delay, sleep_for + jitter)))
            delay = min(max_delay, delay * max(1.0, backoff))
        finally:
            _GLOBAL_SEMAPHORE.release()


def _submit_with_retry(func: Callable[[T], R], arg: T, *, retries: int, base_delay: float, backoff: float, max_delay: float, retry_if: Callable[[BaseException], bool], ) -> Future[
    R]:
    return _GLOBAL_EXECUTOR.submit(_retry_call, func, arg, retries=retries, base_delay=base_delay, backoff=backoff, max_delay=max_delay, retry_if=retry_if, )


def thread_map(func: Callable[[T], R], items: Sequence[T], max_workers: int | None = None,  # retained for API compat; global 32-cap enforced
        ignore_errors: bool = True, *, retries: int = 2, base_delay: float = 0.5, backoff: float = 2.0, max_delay: float = 8.0,
        retry_if: Callable[[BaseException], bool] | None = None, ) -> list[R]:
    if not items:
        return []
    predicate = retry_if or _default_retry_if
    futures = [_submit_with_retry(func, it, retries=retries, base_delay=base_delay, backoff=backoff, max_delay=max_delay, retry_if=predicate, ) for it in items]
    results: list[R] = []
    for fut in as_completed(futures):
        if ignore_errors:
            try:
                results.append(fut.result())
            except BaseException:
                pass
        else:
            results.append(fut.result())
    return results


def thread_map_flat(func: Callable[[T], Iterable[R]], items: Sequence[T], max_workers: int | None = None, ignore_errors: bool = True, *, retries: int = 2, base_delay: float = 0.5,
        backoff: float = 2.0, max_delay: float = 8.0, retry_if: Callable[[BaseException], bool] | None = None, ) -> list[R]:
    chunks = thread_map(func, items, max_workers=max_workers, ignore_errors=ignore_errors, retries=retries, base_delay=base_delay, backoff=backoff, max_delay=max_delay,
        retry_if=retry_if, )
    out: list[R] = []
    for c in chunks:
        if c is None:
            continue
        out.extend(c)
    return out


def shutdown_threads(wait: bool = True) -> None:
    """Gracefully shut down the global executor."""
    _GLOBAL_EXECUTOR.shutdown(wait=wait, cancel_futures=not wait)

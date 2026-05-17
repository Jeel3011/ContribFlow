"""
Shared thread pool executor for all FastAPI routes.
Prevents spinning up a new executor per route call.
"""
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="contribflow"
)


def get_executor() -> ThreadPoolExecutor:
    """Get the shared thread pool executor."""
    return _executor

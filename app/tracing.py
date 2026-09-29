from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any


class _DisabledClient:
    """No-op adapter used when credentials are intentionally absent."""

    def update_current_span(self, **kwargs: Any) -> None:
        return None

    def update_current_generation(self, **kwargs: Any) -> None:
        return None

    @contextmanager
    def start_as_current_observation(self, **kwargs: Any):
        yield self

try:
    from langfuse import get_client, observe, propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield


def get_langfuse_client():
    if not tracing_enabled():
        return _DisabledClient()
    return get_client()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )

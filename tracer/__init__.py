"""
Centralized Trace management of ``sys.settrace``.
"""

from tracer.tracer import (ALL_EVENTS, EVENT2SHORT, clear_hooks,
                           null_trace_hook, remove_hook)
from tracer.version import __version__

__all__ = [
    "ALL_EVENTS",
    "EVENT2SHORT",
    "clear_hooks",
    "null_trace_hook",
    "remove_hook",
    "__version__"
    ]

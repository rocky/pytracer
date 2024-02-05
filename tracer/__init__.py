"""
Centralized Trace management of ``sys.settrace``.
"""

from tracer.tracer import clear_hooks, null_trace_hook, remove_hook

__all__ = ["clear_hooks", "null_trace_hook", "remove_hook"]

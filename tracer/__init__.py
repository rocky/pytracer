"""
Centralized Trace management of ``sys.monitor`` and ``sys.settrace``a.
"""

from tracer.tracefilter import (
    get_code_object,
    get_module_object,
    TraceFilter,
)

from tracer.tracer import (
    DEFAULT_ADD_HOOK_OPTS,
    HOOKS,
    add_hook,
    clear_hooks,
    clear_hooks_and_stop,
    find_hook,
    is_started,
    null_trace_hook,
    option_set,
    remove_hook,
    size,
    start,
    stop,
)

from tracer.sys_monitoring import (
    ALL_EVENT_NAMES,
    ALL_EVENTS,
    EVENT2SHORT,
    MONITOR_HOOKS,
    PytraceException,
    add_trace_callbacks,
    find_hook_by_name,
    find_hook_by_id,
    msize,
    mstart,
    mstop,
)
from tracer.version import __version__

__all__ = [
    "ALL_EVENT_NAMES",
    "ALL_EVENTS",
    "DEFAULT_ADD_HOOK_OPTS",
    "EVENT2SHORT",
    "HOOKS",
    "MONITOR_HOOKS",
    "PytraceException",
    "TraceFilter",
    "__version__",
    "add_hook",
    "add_trace_callbacks",
    "clear_hooks",
    "clear_hooks_and_stop",
    "find_hook",
    "find_hook_by_name",
    "find_hook_by_id",
    "get_code_object",
    "get_module_object",
    "is_started",
    "msize",
    "mstart",
    "mstop",
    "null_trace_hook",
    "option_set",
    "remove_hook",
    "size",
    "start",
    "stop",
]

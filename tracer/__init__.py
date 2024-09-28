"""
Centralized Trace management of ``sys.settrace``.
"""

from xdis.namedtuple24 import namedtuple

from tracefilter import (
    get_code_object,
    get_module_object,
)

from tracer import (
    ALL_EVENT_NAMES,
    ALL_EVENTS,
    DEFAULT_ADD_HOOK_OPTS,
    EVENT2SHORT,
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
from version import __version__

__all__ = [
    "ALL_EVENT_NAMES",
    "ALL_EVENTS",
    "DEFAULT_ADD_HOOK_OPTS",
    "EVENT2SHORT",
    "HOOKS",
    "__version__",
    "add_hook",
    "clear_hooks",
    "clear_hooks_and_stop",
    "find_hook",
    "get_code_object",
    "get_module_object",
    "is_started",
    "namedtuple",
    "null_trace_hook",
    "option_set",
    "remove_hook",
    "size",
    "start",
    "stop",
]

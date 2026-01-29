"""Unit tests for Tracer.trace"""

import sys
from types import CodeType
from typing import Any, NamedTuple

import tracer
import tracer.tracefilter as tracefilter
from tracer.sys_monitoring import (
    add_trace_callbacks,
    TOOL_ID_RANGE,
    free_tool_id,
    stop,
)

E = sys.monitoring.events

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.tracefilter, tracer.sys_monitoring])

class Entry(NamedTuple):
    event: str
    code_str: str
    arg: Any


def code_short(code: CodeType) -> str:
    import os.path as osp

    return f"{code.co_name} in {osp.basename(code.co_filename)}"


def line_event_callback(code, line_number):
    """A line event callback trace function"""

    if ignore_filter.is_excluded(code):
        return sys.monitoring.DISABLE

    entry = Entry("line", code_short(code), line_number)
    global trace_lines
    trace_lines += (entry,)


def call_event_callback(code, instruction_offset, callable_obj, args):
    """A call event callback trace function"""

    if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
        return sys.monitoring.DISABLE

    entry = Entry("call", code_short(code), (instruction_offset, callable_obj))
    global trace_lines
    trace_lines += (entry,)


def setup_function():
    global trace_lines
    global ignore_tracefilter
    trace_lines = []
    ignore_tracefilter = tracefilter.TraceFilter([tracer.sys_monitoring])
    for tool_id in TOOL_ID_RANGE:
        if tracer.size() == 0:
            break
        free_tool_id(tool_id)
    assert tracer.size() == 0
    return


def test_basic_start_stop():
    """Test that trace hook is triggering event callbacks without filtering."""

    callback_hooks = {
        E.CALL: call_event_callback,
        E.LINE: line_event_callback,
    }

    def foo(*args):
        print(f"foo called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    hook_name = "trace_basic_start_stop"
    add_trace_callbacks(hook_name, callback_hooks)
    eval("1+2")
    foo()
    stop(hook_name)

#     # for entry in trace_lines:
#     # print entry.event, entry.filename, entry.lineno, entry.name

#     assert len(trace_lines) >= 5, "Should have captured some trace output"
#     for i, right in [
#         (
#             -1,
#             (
#                 "return",
#                 "squares",
#             ),
#         ),
#         (
#             -2,
#             (
#                 "line",
#                 "squares",
#             ),
#         ),
#     ]:
#         assert right == (trace_lines[i].event, trace_lines[i].name)
#     return


# def test_trace_filtering():
#     """Test that trace hook is triggering event callbacks with filtering."""

#     # We need globalness because tracing uses this, although we don't use it
#     # in this function.
#     global ignore_filter
#     ignore_filter = tracefilter.TraceFilter()

#     tracefilter.TraceFilter()
#     tracer.clear_hooks_and_stop()
#     assert (
#         tracer.add_hook(
#             my_trace_dispatch, {"start": True, "event_set": frozenset(("call",))}
#         )
#         == 1
#     )

#     def foo():
#         return

#     foo()
#     tracer.stop()

#     #  for entry in trace_lines:
#     #    print entry.event, entry.filename, entry.lineno, entry.name
#     assert len(trace_lines) >= 2, "Should have captured some trace output"
#     for i, right in [
#         (
#             -1,
#             (
#                 "call",
#                 "stop",
#             ),
#         ),
#         (
#             -2,
#             (
#                 "call",
#                 "foo",
#             ),
#         ),
#     ]:
#         assert trace_lines[i].event, trace_lines[i].name == right
#     return

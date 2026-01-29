"""Unit tests for Tracer.trace"""

import sys
from types import CodeType
from typing import Any, NamedTuple

import pytest

import tracer
import tracer.tracefilter as tracefilter
from tracer.sys_monitoring import (
    MAX_TOOL_IDS,
    TOOL_ID_RANGE,
    PytraceException,
    check_tool_id,
    find_hook_by_id,
    find_hook_by_name,
    free_tool_id,
    register_tool_by_name,
)

E = sys.monitoring.events

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.tracefilter, tracer.sys_monitoring])

hook_name = "test_monitor_trace"


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


def method_trace_dispatch(frame, event, arg):
    """A method-based trace hook"""
    return method_trace_dispatch


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


def test_event2short_sanity():
    t = sorted(tracer.EVENT2SHORT.keys())
    assert tracer.ALL_EVENT_NAMES == tuple(
        t
    ), "EVENT2SHORT.keys() should match ALL_EVENT_NAMES"
    return


def test_check_tool_id():
    """Test size, free_tool_id, Basic sanity and status testing."""
    for tool_id in (-1, MAX_TOOL_IDS):
        with pytest.raises(PytraceException):
            check_tool_id(tool_id)

def test_find_hook_fns_size():
    tool_id1 = register_tool_by_name("test_find_hook_fns1")
    tool_id2 = register_tool_by_name("test_find_hook_fns2")
    assert find_hook_by_id(tool_id1) == "test_find_hook_fns1"
    assert find_hook_by_id(tool_id2) == "test_find_hook_fns2"
    assert find_hook_by_name("test_find_hook_fns2") == tool_id2



def test_register_tool_by_name_and_size():
    for tool_id in TOOL_ID_RANGE:
        tool_name = f"pytest_register_too_by_name_{tool_id}"
        register_tool_by_name(tool_name, can_change_tool_id=False)
        assert (
            tracer.size() == tool_id + 1
        ), f"size() should note {tool_id + 1} tool(s) registered"

    # We now have a full list of HOOKS.

    # See that we get an error when trying to add a new one.
    with pytest.raises(PytraceException):
        register_tool_by_name("Should not be able to add", can_change_tool_id=True)

    # Reregistering with the same name id with the same id.
    register_tool_by_name(tool_name, can_change_tool_id=False)
    register_tool_by_name(tool_name, can_change_tool_id=True)

    # Registering a previously_used name under a different id, but
    # not allowing a tool_id change.
    tool_name = "pytest_register_tool_by_name_0"
    with pytest.raises(PytraceException):
        register_tool_by_name(tool_name, tool_id=3, can_change_tool_id=False)

    # Registering a previously_used name, allowing a tool_id change.
    tool_name = "pytest_register_tool_by_name_0"
    with pytest.raises(PytraceException):
        register_tool_by_name(tool_name, tool_id=4, can_change_tool_id=False)

    # We should still have a full list of HOOKS
    assert tracer.size() == MAX_TOOL_IDS
    return


def test_free_tool_id():
    """Test free_tool_id()"""
    with pytest.raises(PytraceException):
        free_tool_id(20)
    for tool_id in TOOL_ID_RANGE:
        assert tracer.sys_monitoring.TOOL_NAME[tool_id] is None
        assert tracer.sys_monitoring.HOOKS[tool_id] is None
        if (sys.monitoring.get_tool(tool_id)) is not None:
            with pytest.raises(PytraceException):
                free_tool_id(tool_id)
        else:
            tool_name = f"test_free_tool_id_{tool_id}"
            register_tool_by_name(tool_name, tool_id, can_change_tool_id=False)
            free_tool_id(tool_id)



# # FIXME: reinstate after cleaning pytracer more
# def test_trace():
#     """Test that trace hook is triggering event callbacks without filtering."""
#     tracer.clear_hooks_and_stop()
#     assert tracer.add_hook(my_trace_dispatch, {"start": True, "backlevel": 1}) == 1

#     def squares():
#         j = 1
#         for _ in range(5):
#             j += j + 2
#             pass
#         return

#     squares()
#     tracer.stop()

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

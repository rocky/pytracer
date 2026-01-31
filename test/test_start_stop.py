"""Unit tests for Tracer.trace"""

# codecs is imported because codecs.reset it is weirldy getting line traced into.
import codecs
import os
import sys
from types import CodeType
from typing import Any, List, NamedTuple

import tracer
import tracer.tracefilter as tracefilter
from tracer.sys_monitoring import (
    add_trace_callbacks,
    TOOL_ID_RANGE,
    free_tool_id,
    start,
    stop,
)

E = sys.monitoring.events

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.tracefilter, tracer.sys_monitoring, codecs.IncrementalDecoder.reset])


class Entry(NamedTuple):
    event: str
    code_str: str
    arg: Any


def assert_check_lines(tag: str, got: list, expected: List[List[str, str]]):
    if os.environ.get("DEBUG"):
        from pprint import pp

        pp(got)

    print(f"test {tag}")
    got_length = len(got)
    for i, expected_entry in enumerate(expected):
        if i < got_length:
            got_entry = got[i]
            got_check = [got_entry.event, got_entry.code_str]
            if expected_entry != got_check:
                print(f"Trace line: {got_entry}")
            assert (
                expected_entry == got_check
            ), f"Mismatch at at {i}. Expected {expected_entry}; got {got_check}"
        else:
            assert False, f"Extra entries expected at {i}\n: expected_entry"
    expected_length = len(expected)
    if got_length > expected_length:
        print(f"Extra entry starting at {got_length}:\n {got[expected_length]}")

    assert (
        got_length == expected_length
    ), "Extra entries traced {got_length} vs. {expected_length}"
    return


def code_short(code: CodeType) -> str:
    import os.path as osp

    return f"{code.co_name} in {osp.basename(code.co_filename)}"


def line_event_callback(code, line_number):
    """A line event callback trace function"""

    # FIXME: why are we tracing into codecs.IncrementalDecoder.reset?
    if  str(code).find("reset") > 0:
        return

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
        print(f"test function foo() called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    global trace_lines
    hook_name = "trace_basic_start_stop"
    print("\n")
    add_trace_callbacks(hook_name, callback_hooks)
    eval("1+2")
    foo()
    stop(hook_name)
    assert_check_lines(
        "test 1",
        trace_lines,
        [
            ["line", "test_basic_start_stop in test_start_stop.py"],  # eval("1+2")
            ["call", "test_basic_start_stop in test_start_stop.py"],  # eval()
            ["line", "<module> in <string>"],  # 1+2)
            ["line", "test_basic_start_stop in test_start_stop.py"],  # foo()
            ["call", "test_basic_start_stop in test_start_stop.py"],  # foo()
            ["line", "foo in test_start_stop.py"],  # foo: ... print()
            ["call", "foo in test_start_stop.py"],  # print()
            ["line", "test_basic_start_stop in test_start_stop.py"],  # stop()
        ],
    )

    # Do a start after we've done the stop.
    # All setup was in place.

    trace_lines = []
    start(hook_name)
    bar()
    stop(hook_name)
    # from pprint import pp
    # pp(trace_lines)

    assert_check_lines(
        "test 2",
        trace_lines,
        [
            ["line", "test_basic_start_stop in test_start_stop.py"],  # module: bar()
            ["call", "test_basic_start_stop in test_start_stop.py"],  # module: bar()
            ["line", "bar in test_start_stop.py"], # foo("foo")
            ["call", "bar in test_start_stop.py"], # foo()
            ["line", "foo in test_start_stop.py"], # print(f"test function ... "))
            ["call", "foo in test_start_stop.py"], # print(...)
            ["line", "bar in test_start_stop.py"], # foo("bar")
            ["call", "bar in test_start_stop.py"], # foo("bar")
            ["line", "foo in test_start_stop.py"], # print(f"test_function...")
            ["call", "foo in test_start_stop.py"], # print()
            ["line", "test_basic_start_stop in test_start_stop.py"] # stop(),
        ],
    )


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

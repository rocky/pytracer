"""Unit tests for Tracer.trace"""

# codecs is imported because codecs.reset it is weirldy getting line traced into.
import codecs
import os
import sys
from types import CodeType
from typing import List

import tracer
import tracer.tracefilter as tracefilter
from tracer.stepping import StepGranularity, StepType, start_local
from tracer.sys_monitoring import TOOL_ID_RANGE, free_tool_id, mstart, mstop
from tracer.tracefilter import TraceFilter

E = sys.monitoring.events

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.tracefilter, tracer.sys_monitoring, codecs.IncrementalDecoder.reset])


def assert_check_lines(tag: str, got: list, expected: List[List[str]]):
    if os.environ.get("DEBUG"):
        from pprint import pp

        pp(got)

    print(f"test {tag}")
    assert got == expected


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

    entry = ["line", code_short(code)]
    trace_lines.append(entry)


def call_event_callback(code, instruction_offset, callable_obj, args):
    """A call event callback trace function"""

    if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
        return sys.monitoring.DISABLE

    entry = ["call", code_short(code)]
    trace_lines.append(entry)


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


def test_basic_mstart_mstop():
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

    sysmon_tool_name = "trace_basic_mstart_mstop"
    print("\n")
    tool_id, events_mask = mstart(sysmon_tool_name, tool_id=1)
    ignore_filter = TraceFilter([sys.monitoring, mstop])
    start_local(
        sysmon_tool_name,
        callback_hooks,
        events_mask=E.LINE,
        step_type=StepType.STEP_INTO,
        step_granularity=StepGranularity.LINE_NUMBER,
        ignore_filter=ignore_filter,
    )
    eval("1+2")
    foo()
    mstop(sysmon_tool_name)
    sys.monitoring.set_events(tool_id, 0)

    global trace_lines
    assert_check_lines(
        "test 1",
        trace_lines,
        [
            ["line", "test_basic_mstart_mstop in test_start_stop.py"],  # eval("1+2")
            ["call", "test_basic_mstart_mstop in test_start_stop.py"],  # eval()
            ["line", "test_basic_mstart_mstop in test_start_stop.py"],  # foo()
            ["call", "test_basic_mstart_mstop in test_start_stop.py"],  # foo()
            ['line', 'test_basic_mstart_mstop in test_start_stop.py']
        ],
    )

    # Do a mstart after we've done the mstop.
    # All setup was in place.

    # trace_lines = []
    # mstart(sysmon_tool_name)
    # bar()
    # mstop(sysmon_tool_name)
    # # from pprint import pp
    # # pp(trace_lines)

    # assert_check_lines(
    #     "test 2",
    #     trace_lines,
    #     [
    #         ["line", "test_basic_mstart_mstop in test_start_stop.py"],  # module: bar()
    #         ["call", "test_basic_mstart_mstop in test_start_stop.py"],  # module: bar()
    #         ["line", "bar in test_start_stop.py"], # foo("foo")
    #         ["call", "bar in test_start_stop.py"], # foo()
    #         ["line", "foo in test_start_stop.py"], # print(f"test function ... "))
    #         ["call", "foo in test_start_stop.py"], # print(...)
    #         ["line", "bar in test_start_stop.py"], # foo("bar")
    #         ["call", "bar in test_start_stop.py"], # foo("bar")
    #         ["line", "foo in test_start_stop.py"], # print(f"test_function...")
    #         ["call", "foo in test_start_stop.py"], # print()
    #         ["line", "test_basic_mstart_mstop in test_start_stop.py"] # mstop(),
    #     ],
    # )


# def test_trace_filtering():
#     """Test that trace hook is triggering event callbacks with filtering."""

#     # We need globalness because tracing uses this, although we don't use it
#     # in this function.
#     global ignore_filter
#     ignore_filter = tracefilter.TraceFilter()

#     tracefilter.TraceFilter()
#     tracer.clear_hooks_and_mstop()
#     assert (
#         tracer.add_hook(
#             my_trace_dispatch, {"mstart": True, "event_set": frozenset(("call",))}
#         )
#         == 1
#     )

#     def foo():
#         return

#     foo()
#     tracer.mstop()

#     #  for entry in trace_lines:
#     #    print entry.event, entry.filename, entry.lineno, entry.name
#     assert len(trace_lines) >= 2, "Should have captured some trace output"
#     for i, right in [
#         (
#             -1,
#             (
#                 "call",
#                 "mstop",
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

"""Unit tests for Tracer.trace"""

from typing import Any, NamedTuple

import pytest
import tracer
import tracer.tracefilter as tracefilter

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.stop])


class Entry(NamedTuple):
    frame: Any
    event: str
    arg: Any
    filename: str
    lineno: int
    name: str


def my_trace_dispatch(frame, event, arg):
    """A pure-function trace hook"""
    global trace_lines
    if ignore_filter.is_excluded(frame):
        return None
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    name = frame.f_code.co_name
    entry = Entry(frame, event, arg, filename, lineno, name)
    trace_lines += (entry,)
    return my_trace_dispatch


def method_trace_dispatch(frame, event, arg):
    """A method-based trace hook"""
    return method_trace_dispatch


def setup_function():
    global trace_lines
    global ignore_tracefilter
    trace_lines = []
    ignore_tracefilter = tracefilter.TraceFilter()
    return


def test_event2short_sanity():
    t = sorted(tracer.EVENT2SHORT.keys())
    assert tracer.ALL_EVENT_NAMES == tuple(
        t
    ), "EVENT2SHORT.keys() should match ALL_EVENT_NAMES"
    return


def test_option_set():
    assert tracer.option_set({"opt": True}, "opt", {"opt": False})
    assert tracer.option_set(None, "opt", {"opt": True})
    assert not tracer.option_set(
        {"opt": True}, "notthere", {"opt": True, "notthere": False}
    )
    assert tracer.option_set({"opt": True}, "notthere", {}) is None
    return


def test_basic():
    """Basic sanity and status testing."""
    tracer.HOOKS = []
    assert tracer.size() == 0
    assert not tracer.is_started()
    tracer.start()
    assert tracer.is_started()

    tracer.stop()
    assert not tracer.is_started()
    assert tracer.add_hook(my_trace_dispatch, {"backlevel": 1}) == 1
    assert len(trace_lines) == 0

    tracer.start()
    assert len(trace_lines) == 0
    assert tracer.is_started()
    tracer.remove_hook(my_trace_dispatch, stop_if_empty=True) == 0
    assert not tracer.is_started()
    assert tracer.add_hook(my_trace_dispatch, {"start": True, "backlevel": 1}) == 1
    assert tracer.is_started()
    tracer.clear_hooks_and_stop()
    return


def test_errors():
    """Test various error conditions."""
    # 5 is not a function
    with pytest.raises(TypeError):
        tracer.add_hook(5)

    # test_errors has the wrong number of args
    with pytest.raises(TypeError):
        tracer.add_hook(test_errors)

    def wrong_fn_args(a, b):
        return (a, b)

    with pytest.raises(TypeError):
        tracer.add_hook(wrong_fn_args)

    tracer.clear_hooks
    assert tracer.add_hook(method_trace_dispatch) == 1
    return


# FIXME: reinstate after cleaning pytracer more
def test_trace():
    """Test that trace hook is triggering event callbacks without filtering."""
    tracer.clear_hooks_and_stop()
    assert tracer.add_hook(my_trace_dispatch, {"start": True, "backlevel": 1}) == 1

    def squares():
        j = 1
        for _ in range(5):
            j += j + 2
            pass
        return

    squares()
    tracer.stop()

    # for entry in trace_lines:
    # print entry.event, entry.filename, entry.lineno, entry.name

    assert len(trace_lines) >= 5, "Should have captured some trace output"
    for i, right in [
        (
            -1,
            (
                "return",
                "squares",
            ),
        ),
        (
            -2,
            (
                "line",
                "squares",
            ),
        ),
    ]:
        assert right == (trace_lines[i].event, trace_lines[i].name)
    return


def test_trace_filtering():
    """Test that trace hook is triggering event callbacks with filtering."""

    # We need globalness because tracing uses this, although we don't use it
    # in this function.
    global ignore_filter
    ignore_filter = tracefilter.TraceFilter()

    tracefilter.TraceFilter()
    tracer.clear_hooks_and_stop()
    assert (
        tracer.add_hook(
            my_trace_dispatch, {"start": True, "event_set": frozenset(("call",))}
        )
        == 1
    )

    def foo():
        return

    foo()
    tracer.stop()

    #  for entry in trace_lines:
    #    print entry.event, entry.filename, entry.lineno, entry.name
    assert len(trace_lines) >= 2, "Should have captured some trace output"
    for i, right in [
        (
            -1,
            (
                "call",
                "stop",
            ),
        ),
        (
            -2,
            (
                "call",
                "foo",
            ),
        ),
    ]:
        assert trace_lines[i].event, trace_lines[i].name == right
    return

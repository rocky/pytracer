#!/usr/bin/env python
# -*- Python -*-
"""Unit test for Tracer's add-hook"""

import tracer
from tracer.tracefilter import TraceFilter


trace_lines = []
ignore_filter = TraceFilter([tracer.stop])

def trace_dispatch1(frame, event, arg):
    return trace_dispatch1

def trace_dispatch2(frame, event, arg):
    return trace_dispatch2

def trace_dispatch3(frame, event, arg):
    return trace_dispatch3

def setup_function():
    global ignore_tracefilter
    ignore_tracefilter = TraceFilter()
    return


def test_add_hook():
    """Basic sanity and status testing."""
    assert tracer.size() == 0
    assert tracer.add_hook(trace_dispatch1) == 1
    assert tracer.add_hook(trace_dispatch2) == 2
    assert trace_dispatch1 == tracer.HOOKS[0][0]
    assert trace_dispatch2 == tracer.HOOKS[1][0]
    assert tracer.add_hook(trace_dispatch3, {'position': 0})
    assert trace_dispatch3 == tracer.HOOKS[0][0]
    assert trace_dispatch1 == tracer.HOOKS[1][0]
    assert trace_dispatch2 == tracer.HOOKS[2][0]
    return

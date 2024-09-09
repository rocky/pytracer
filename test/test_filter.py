#!/usr/bin/env python
# -*- Python -*-
"""Unit test for TracerFilter"""

import inspect
from tracer.tracefilter import TraceFilter, add_to_set

trace_lines = []

def test_basic():
    filter = TraceFilter([test_basic])
    assert filter.is_included(test_basic), "Check that we can find a filter"
    assert not filter.is_included(trace_lines), "Check that we can pass bogus items"
    assert filter.is_included(inspect.currentframe()), "Check that we can find a filter using a frame"

    # TODO: check we can find filter using:
    #  code, or module
    # add module and check exclude of functions in that

    assert not filter.is_included(add_to_set)
    filter.remove_include(test_basic)
    assert not filter.is_included(test_basic), "Check filter is removed properly"
    return

#!/usr/bin/env python
# -*- Python -*-
"""Unit test for TracerFilter"""

import inspect
from tracer.tracefilter import TraceFilter, add_to_code_set

trace_lines = []

def test_basic():
    filter = TraceFilter([test_basic])
    assert filter.is_excluded(test_basic), "Check that we can find a filter"
    assert not filter.is_excluded(trace_lines), "Check that we can pass bogus items"
    current_frame = inspect.currentframe()
    assert filter.is_excluded(current_frame), "Check that we can find a filter using a frame"

    # TODO: check we can find filter using:
    #  code, or module
    # add module and check exclude of functions in that

    assert filter.remove(test_basic), "Removing a code object that is in set"
    assert not filter.remove(test_basic), "Removing a code object is no longer in set"
    assert not filter.remove(add_to_code_set)
    assert not filter.is_excluded(add_to_code_set), "Check filter is removed properly again"
    return

#!/usr/bin/env python
# -*- Python -*-
"Unit test for Tracer's add-hook"
import operator, os, sys, unittest

top_builddir = os.path.join(os.path.dirname(__file__), '..', 'tracer')
if top_builddir[-1] != os.path.sep:
    top_builddir += os.path.sep
sys.path.insert(0, top_builddir)

import tracer, tracefilter

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.stop])

def trace_dispatch1(frame, event, arg):
    return trace_dispatch1

def trace_dispatch2(frame, event, arg):
    return trace_dispatch2

def trace_dispatch3(frame, event, arg):
    return trace_dispatch3

class TestTraceAddHook(unittest.TestCase):

    def setUp(self):
        global ignore_filter
        trace_lines = []
        ignore_tracefilter = tracefilter.TraceFilter()
        return

    def test_add_hook(self):
        """Basic sanity and status testing."""
        self.assertEqual(0, tracer.size())
        self.assertEqual(1, tracer.add_hook(trace_dispatch1))
        self.assertEqual(2, tracer.add_hook(trace_dispatch2))
        self.assertEqual(trace_dispatch1, tracer.HOOKS[0][0])
        self.assertEqual(trace_dispatch2, tracer.HOOKS[1][0])
        self.assertEqual(3, tracer.add_hook(trace_dispatch3,
                                            {'position': 0}))
        self.assertEqual(trace_dispatch3, tracer.HOOKS[0][0])
        self.assertEqual(trace_dispatch1, tracer.HOOKS[1][0])
        self.assertEqual(trace_dispatch2, tracer.HOOKS[2][0])
        return

if __name__ == '__main__':
    unittest.main()

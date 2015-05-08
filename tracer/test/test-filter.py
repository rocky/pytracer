#!/usr/bin/env python
# -*- Python -*-
"Unit test for Tracer"
import inspect, operator, os, sys, unittest

top_builddir = os.path.join(os.path.dirname(__file__), '..', 'tracer')
if top_builddir[-1] != os.path.sep:
    top_builddir += os.path.sep
sys.path.insert(0, top_builddir)

from tracefilter import *

trace_lines = []

class TestFilter(unittest.TestCase):

    def test_basic(self):
        filter = TraceFilter([add_to_set])
        self.assertFalse(filter.is_included(to_f_code))
        self.assertTrue(filter.is_included(add_to_set))
        self.assertFalse(filter.is_included(inspect.currentframe()))
        filter.remove_include(add_to_set)
        self.assertFalse(filter.is_included(add_to_set))
        return

if __name__ == '__main__':
    unittest.main()

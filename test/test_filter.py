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

# Something to use for testing
def five():
    return 5

def six():
    return 6

class TestFilter(unittest.TestCase):

    def test_basic(self):
        filter = TraceFilter([five])
        self.assertFalse(filter.is_excluded(six))
        self.assertTrue(filter.is_excluded(five))
        self.assertFalse(filter.is_excluded(inspect.currentframe()))
        filter.remove(self.test_basic)
        self.assertFalse(filter.is_excluded(self.test_basic))
        return

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
# -*- Python -*-
"Unit test for Tracer"
import operator, os, sys, unittest

top_builddir = os.path.join(os.path.dirname(__file__), '..', 'tracer')
if top_builddir[-1] != os.path.sep:
    top_builddir += os.path.sep
sys.path.insert(0, top_builddir)

import tracer, tracefilter

trace_lines = []
ignore_filter = tracefilter.TraceFilter([tracer.stop])

class TestRemove(unittest.TestCase):

    def test_remove(self):
        self.assertEquals(None, tracer.remove_hook(tracer.null_trace_hook))
        tracer.clear_hooks()
        self.assertEquals(None, tracer.remove_hook(tracer.null_trace_hook))
        return

if __name__ == '__main__':
    unittest.main()

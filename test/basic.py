#!/usr/bin/env python
# -*- Python -*-
"Unit test for Tracer"
import os, sys, unittest

# For now we assume we run this program in this directory.
top_builddir = ".."
if top_builddir[-1] != os.path.sep:
    top_builddir += os.path.sep
sys.path.insert(0, top_builddir)

import tracer

trace_lines = []
def trace_dispatch(frame, event, arg):
    global trace_lines
    trace_lines += ((frame, event, arg),)
    return

class TestTracer(unittest.TestCase):
    global trace_lines

    def setUp(self):
        trace_lines = []
        return

    def test_basic(self):
        self.assertEqual(0, tracer.size())
        self.assertEqual(False, tracer.isstarted())
        tracer.start()
        self.assertEqual(True, tracer.isstarted())

        tracer.stop()
        self.assertEqual(False, tracer.isstarted())
        self.assertEqual(1, tracer.add_hook(trace_dispatch))
        self.assertEqual(0, len(trace_lines))

        tracer.start()
        x=1
        self.assertEqual(0, len(trace_lines))
        self.assertEqual(True, tracer.isstarted())
        self.assertEqual(0, 
                         tracer.remove_hook(trace_dispatch, 
                                            stop_if_empty=True))
        self.assertEqual(False, tracer.isstarted())
        self.assertEqual(1, tracer.add_hook(trace_dispatch,
                                            issue_start=True))
        self.assertEqual(True, tracer.isstarted())
        tracer.clear_hooks_and_stop()
        return

    def test_errors(self):
        """Test various errors conditions."""
        # Don't know why assertRaises fails...
        # self.assertRaises(TypeError, tracer.add_hook(5))
        try:
            tracer.add_hook(5)
        except TypeError:
            self.assertTrue(True)
        else:
            self.assertFalse(True, "Can't use int as a trace function")
            
        # Don't know why assertRaises fails...
        # self.assertRaises(TypeError, tracer.add_hook(self.test_errors))
        try:
            tracer.add_hook(self.test_errors)
        except TypeError:
            self.assertTrue(True)
        else:
            self.assertFalse(True, 
                             "self.test_errors is a method, not a function")

        def wrong_fn_args(a, b): pass
        try:
            tracer.add_hook(wrong_fn_args)
        except TypeError:
            self.assertTrue(True)
        else:
            self.assertFalse(True, "Wrong number of args")
        return


if __name__ == '__main__':
    unittest.main()

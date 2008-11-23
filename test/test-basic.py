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

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        return
    def __str__(self):
        state = ["%s=%r" % (attribute, value)
                 for (attribute, value) in self.__dict__.items()]
        return '\n'.join(state)

trace_lines = []
def my_trace_dispatch(frame, event, arg):
    global trace_lines
    filename = frame.f_code.co_filename
    lineno   = frame.f_lineno
    name     = frame.f_code.co_name
    entry    = Bunch(frame=frame, event=event, arg=arg, filename=filename,
                     lineno=lineno, name=name)
    trace_lines += (entry,)
    return

class TestTracer(unittest.TestCase):
    global trace_lines

    def setUp(self):
        trace_lines = []
        return

    def test_basic(self):
        """Basic sanity and status testing."""
        self.assertEqual(0, tracer.size())
        self.assertEqual(False, tracer.is_started())
        tracer.start()
        self.assertEqual(True, tracer.is_started())

        tracer.stop()
        self.assertEqual(False, tracer.is_started())
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch))
        self.assertEqual(0, len(trace_lines))

        tracer.start()
        self.assertEqual(0, len(trace_lines))
        self.assertEqual(True, tracer.is_started())
        self.assertEqual(0, 
                         tracer.remove_hook(my_trace_dispatch, 
                                            stop_if_empty=True))
        self.assertEqual(False, tracer.is_started())
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch,
                                            do_start=True))
        self.assertEqual(True, tracer.is_started())
        tracer.clear_hooks_and_stop()
        return

    def test_errors(self):
        """Test various error conditions."""
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

    def test_trace(self):
        """Test that trace hook is triggering event callbacks.(No filtering.)"""
        tracer.clear_hooks_and_stop()
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch, do_start=True))
        def foo(): pass
        foo()
        tracer.stop()
        global trace_lines
#       import pprint
#       for entry in trace_lines: 
#           print entry.event, entry.filename, entry.lineno, entry.name
        self.assertTrue(len(trace_lines) >= 5,
                        'Should have captured some trace output')
        for i, right in [(-1, ('line',   'stop',)),
                         (-2, ('call',   'stop',)),
                         (-3, ('return', 'foo', )),
                         (-4, ('line',   'foo', )),
                         (-5, ('call',   'foo', ))
                         ]:
            self.assertEqual(right, 
                             (trace_lines[i].event, trace_lines[i].name,))
        return

    def test_trace_filtering(self):
        """Test that trace hook is triggering event callbacks with filtering."""
        tracer.clear_hooks_and_stop()
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch, do_start=True,
                                            event_set=frozenset(('call',))))
        def foo(): pass
        foo()
        tracer.stop()
        global trace_lines
#       import pprint
#       for entry in trace_lines: 
#           print entry.event, entry.filename, entry.lineno, entry.name
        self.assertTrue(len(trace_lines) >= 2,
                        'Should have captured some trace output')
        for i, right in [(-1, ('call',   'stop',)),
                         (-2, ('call',   'foo', ))
                         ]:
            self.assertEqual(right, 
                             (trace_lines[i].event, trace_lines[i].name,))
        return

if __name__ == '__main__':
    unittest.main()

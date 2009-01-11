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

def my_trace_dispatch(frame, event, arg):
    """A pure-function trace hook"""
    global trace_lines
    if ignore_filter.is_included(frame): 
        return None
    Entry    = tracer.superTuple('line_entry', 'frame', 'event', 'arg', 'filename',
                                 'lineno', 'name')
    filename = frame.f_code.co_filename
    lineno   = frame.f_lineno
    name     = frame.f_code.co_name
    entry    = Entry(frame, event, arg, filename, lineno, name)
    trace_lines += (entry,)
    return my_trace_dispatch

class TestTracer(unittest.TestCase):

    def method_trace_dispatch(self, frame, event, arg):
        """A method-based trace hook"""
        return method_trace_dispatch

    def setUp(self):
        global ignore_filter
        trace_lines = []
        ignore_tracefilter = tracefilter.TraceFilter()
        return

    def test_event2short_sanity(self):
        t = tracer.EVENT2SHORT.keys()
        t.sort()
        self.assertEqual(tracer.ALL_EVENT_NAMES, tuple(t), 
                         "EVENT2SHORT.keys() should match ALL_EVENT_NAMES")
        return

    def test_option_set(self):
        self.assertTrue(tracer.option_set({'opt': True}, 'opt', 
                                          {'opt': False}))
        self.assertTrue(tracer.option_set(None, 'opt', {'opt': True}))
        self.assertFalse(tracer.option_set({'opt': True}, 'notthere', 
                                           {'opt': True, 'notthere': False}))
        self.assertEqual(None, tracer.option_set({'opt': True}, 'notthere', 
                                                 {}))
        return

    def test_basic(self):
        """Basic sanity and status testing."""
        self.assertEqual(0, tracer.size())
        self.assertEqual(False, tracer.is_started())
        tracer.start()
        self.assertEqual(True, tracer.is_started())

        tracer.stop()
        self.assertEqual(False, tracer.is_started())
        self.assertEqual(1, 
                         tracer.add_hook(my_trace_dispatch,
                                         {'backlevel': 1}))
        self.assertEqual(0, len(trace_lines))

        tracer.start()
        self.assertEqual(0, len(trace_lines))
        self.assertEqual(True, tracer.is_started())
        self.assertEqual(0, 
                         tracer.remove_hook(my_trace_dispatch, 
                                            stop_if_empty=True))
        self.assertEqual(False, tracer.is_started())
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch,
                                            {'start': True,
                                             'backlevel': 1}))
        self.assertEqual(True, tracer.is_started())
        tracer.clear_hooks_and_stop()
        return

    def test_errors(self):
        """Test various error conditions."""
        # 5 is not a function
        self.assertRaises(TypeError, tracer.add_hook, *(5,))
            
        # test_errors has the wrong number of args
        self.assertRaises(TypeError, tracer.add_hook, *(self.test_errors,))

        def wrong_fn_args(a, b): pass
        self.assertRaises(TypeError, tracer.add_hook, *(wrong_fn_args,))

        tracer.clear_hooks
        self.assertEqual(1, tracer.add_hook(self.method_trace_dispatch))
        return

    # FIXME: reinstate after cleaning pytracer more
    def test_trace(self):
        """Test that trace hook is triggering event callbacks.(No filtering.)"""
        tracer.clear_hooks_and_stop()
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch, 
                                            {'start': True,
                                             'backlevel': 1}))
        def squares(): 
            j = 1
            for i in range(5): 
                j += j + 2
                pass
            return
        squares()
        tracer.stop()
        global trace_lines
        import pprint
#         for entry in trace_lines: 
#            print entry.event, entry.filename, entry.lineno, entry.name
        self.assertTrue(len(trace_lines) >= 5,
                        'Should have captured some trace output')
        for i, right in [(-1, ('return', 'squares',)),
                         (-2, ('line',   'squares',))]:
            self.assertEqual(right, 
                             (trace_lines[i].event, trace_lines[i].name,))
        return

    def test_trace_filtering(self):
        """Test that trace hook is triggering event callbacks with filtering."""
        global ignore_filter
        ignore_filter = tracefilter.TraceFilter()
        tracer.clear_hooks_and_stop()
        self.assertEqual(1, tracer.add_hook(my_trace_dispatch, 
                                            {'start': True,
                                             'event_set': frozenset(('call',))}))
        def foo(): pass
        foo()
        tracer.stop()
        global trace_lines
        import pprint
#         for entry in trace_lines: 
#             print entry.event, entry.filename, entry.lineno, entry.name
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

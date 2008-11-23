"""Centralized Trace management around sys.settrace. We allow several 
sets of trace events to get registered and unregistered and allow tracing
to be turned on and off temporarily without losing the trace functions.
"""

import sys, inspect, types, thread

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        return
    def __str__(self):
        state = ["%s=%r" % (attribute, value)
                 for (attribute, value) in self.__dict__.items()]
        return '\n'.join(state)

hooks         = []    # List of Bunch(trace_fn, event_set)
                      # We run trace_fn if the event is in event_set.
started_state = False # True if we are tracing. 
                      # FIXME: in 2.6 we can use sys.gettrace

ALL_EVENTS    = frozenset(('c_call', 'c_exception', 'c_return', 'call', 
                           'exception', 'line', 'return',))

def _check_event_set(event_set):
    """Check EVENT_SET for validity. Raise TypeError if not valid"""
    global ALL_EVENTS
    if event_set is not None and not event_set.issubset(ALL_EVENTS):
        raise TypeError
    return 

def _find_hook(trace_fn):
    """Find TRACE_FN in hooks, and return the index of it.
    return None is not found."""
    global hooks
    try:
        i = [tuple.trace_fn for tuple in hooks].index(trace_fn)
    except ValueError:
        return None
    return i

def _tracer_func(frame, event, arg):
    """The internal function set by sys.settrace which runs
    all of the user-registered trace hook functions."""
    global hooks
    for hook in hooks:
        if hook.event_set is None or event in hook.event_set:
            hook.trace_fn(frame, event, arg)
    # From sys.settrace info: The local trace function
    # should return a reference to itself (or to another function
    # for further tracing in that scope), or None to turn off
    # tracing in that scope. 
    return _tracer_func
    
def add_hook(trace_fn, to_front=False, do_start=False, event_set=None):
    """Add TRACE_FN to the list of callback functions that get run
    when tracing is turned on. The number of hook functions
    registered is returned. 

    A check is made on TRACE_FN to make sure it is a function
    which takes 3 parameters.

    If TO_FRONT is given, the hook will be made at the front of the 
    list of hooks; otherwise it will be added at the end.

    EVENT_SET if given and not None, is a list of events that trace_fn will
    get run on. None indicates all possible events. If this parameter is
    given, it is checked for validity.
    """
    global hooks

    # Parameter checking:
    if not inspect.isfunction(trace_fn):
        raise TypeError
    try:
        if 3 != trace_fn.func_code.co_argcount: 
            raise TypeError
    except:
        raise TypeError
    _check_event_set(event_set)
            
    position = to_front and 0 or -1
    hooks[position:position] = [Bunch(trace_fn=trace_fn, event_set=event_set)]
    if do_start: start()
    return len(hooks)
    
def clear_hooks():
    """Clear all trace hooks"""
    global hooks
    hooks = []
    return

def clear_hooks_and_stop():
    """Clear all trace hooks and stop tracing"""
    global started_state
    if started_state: stop()
    clear_hooks()
    return

def size():
    global hooks
    return len(hooks)

def is_started():
    """Return true if tracing has been started. Until we assume Python 2.6
    or better, keeping track is done by internal tracking. Thus calls to 
    sys.settrace outside of Tracer won't be detected :-(
    """
    global started_state
    return started_state

def remove_hook(trace_fn, stop_if_empty=False):
    """Remove TRACE_FN from list of callback functions run when
    tracing is turned on. If TRACE_FN is not in the list of
    callback functions, None is ruturned. On successful
    removal, the number of callback functions remaining is
    returned."""
    global hooks
    i = _find_hook(trace_fn)
    if i is not None:
        del hooks[i]
        if 0 == len(hooks) and stop_if_empty:
            stop()
            return 0
        return len(hooks)
    raise LookupError
    
# FIXME: in 2.6, there is the possibility for chaining 
# existing hooks by using sys.gettrace().
def start(trace_fn=None):
    """Start using all previously-registered trace hooks. If trace_fn
    is not None, we'll search for that and add it if it's not already
    added."""
    if sys.settrace(_tracer_func) is None:
        global started_state, hooks
        started_state = True
        return len(hooks)
    raise NotImplementedError

def stop():
    """Stop all trace hooks"""
    if sys.settrace(None) is None:
        global hooks, started_state
        started_state = False
        return len(hooks)
    raise NotImplementedError

# Demo it
if __name__=='__main__':
    import inspect
    def my_trace_dispatch(frame, event, arg):
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        print "%s - %s:%d" % (event, filename, lineno),
        if arg: 
            print arg
        else:
            print

        # print "event: %s frame %s arg %s\n" % [event, frame, arg]
        return my_trace_dispatch
    def foo(): print "foo"

    print "** Tracing started before start(): %s" % is_started()

    start() # tracer.start() outside of this file

    print "** Tracing started after start(): %s" % is_started()
    add_hook(my_trace_dispatch) # tracer.add_hook(...) outside
    eval("1+2")
    stop()
    y=5
    start()
    foo()
    z=5
    remove_hook(my_trace_dispatch, stop_if_empty=True)
    print "** Tracing started: %s" % is_started()

    print "** Tracing only 'call' now..."
    add_hook(my_trace_dispatch, do_start=True,
             event_set=frozenset(('call',)))
    foo()
    stop()
    exit(0)

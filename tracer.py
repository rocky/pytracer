"""Centralized Trace management around sys.settrace. We allow several 
sets of trace events to get registered and unregistered and allow tracing
to be turned on and off temporarily without losing the trace functions.
"""

import sys, inspect, types, thread


hook_fns      = []    # List of hook functions to run
started_state = False # True if we are tracing. 
                      # FIXME: in 2.6 we can use sys.gettrace

def __find_hook(trace_fn):
    """Find TRACE_FN in hook_fns, and return the index of it.
    return None is not found."""
    global hook_fns
    try:
        i = hook_fns.index(trace_fn)
    except ValueError:
        return None
    return i

def __tracer_func(frame, event, arg):
    """The internal function set by sys.settrace which runs
    all of the user-registered trace hook functions."""
    global hook_fns
    for hook_fn in hook_fns:
        hook_fn(frame, event, arg)
    # From sys.settrace info: The local trace function
    # should return a reference to itself (or to another function
    # for further tracing in that scope), or None to turn off
    # tracing in that scope. 
    return __tracer_func
    
def add_hook(trace_fn, to_front=False, issue_start=False):
    """Add TRACE_FN to the list of callback functions that get run
    when tracing is turned on. The number of hook functions
    registered is returned. 

    A check is made on TRACE_FN to make sure it is a function
    which takes 3 parameters.

    If TO_FRONT is given, the hook will be made at the front of the 
    list of hooks; otherwise it will be added at the end."""
    global hook_fns
    if not inspect.isfunction(trace_fn):
        raise TypeError
    try:
        if 3 != trace_fn.func_code.co_argcount: 
            raise TypeError
    except:
            raise TypeError
    position = 0
    if to_front: position = -1
    hook_fns[position:position] = [trace_fn]
    if issue_start: start()
    return len(hook_fns)
    
def clear_hooks():
    """Clear all trace hooks"""
    global hook_fns
    hook_fns = []

def clear_hooks_and_stop():
    """Clear all trace hooks"""
    global hook_fns, started_state
    if started_state: stop()
    clear_hooks()

def size():
    global hook_fns
    return len(hook_fns)

def isstarted():
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
    global hook_fns
    i = __find_hook(trace_fn)
    if i is not None:
        del hook_fns[i]
        if 0 == len(hook_fns) and stop_if_empty:
            stop()
            return 0
        return len(hook_fns)
    raise LookupError
    
# FIXME: in 2.6, there is the possibility for chaining 
# existing hooks by using sys.gettrace().
def start(hook_fn=None):
    """Start using all previously-registered trace hooks. If hook_fn
    is not None, we'll search for that and add it if it's not already
    added."""
    if sys.settrace(__tracer_func) is None:
        global hook_fns, started_state
        started_state = True
        return len(hook_fns)
    raise NotImplementedError

def stop():
    """Stop all trace hooks"""
    if sys.settrace(None) is None:
        global hook_fns, started_state
        started_state = False
        return len(hook_fns)
    raise NotImplementedError

# Demo it
if __name__=='__main__':
    import inspect
    def trace_dispatch(frame, event, arg):
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        print "%s - %s:%d" % (event, filename, lineno),
        if arg: 
            print arg
        else:
            print

        # print "event: %s frame %s arg %s\n" % [event, frame, arg]
        return trace_dispatch
    def foo(): print "foo"

    print "Tracing started: %s" % isstarted()

    start() # tracer.start() outside of this file

    print "Tracing started: %s" % isstarted()
    add_hook(trace_dispatch) # tracer.add_hook(...) outside
    eval("1+2")
    stop()
    y=5
    start()
    foo()
    z=5
    remove_hook(trace_dispatch, stop_if_empty=True)
    print "Tracing started: %s" % isstarted()
    exit(0)



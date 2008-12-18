"""Centralized Trace management around sys.settrace. We allow several 
sets of trace events to get registered and unregistered and allow tracing
to be turned on and off temporarily without losing the trace functions.
"""

import operator, sys, inspect, threading

# Python Cookbook Recipe 6.7
def superTuple(typename, *attribute_names):
    " create and return a subclass of `tuple', with named attributes "
    # make the subclass with appropriate __new__ and __repr__ specials
    nargs = len(attribute_names)
    class supertup(tuple):
        __slots__ = ()   # save memory, we don't need a per-instance dict
        def __new__(cls, *args):
            if len(args) !=nargs:
                raise TypeError, '%s takes exactly %d arguments (%d given)' % (
                    typename, nargs, len(args))
            return tuple.__new__(cls, args)
        def __repr__(self):
            return '%s(%s)' % (typename, ', '.join(map(repr, self)))
    # add a few key touches to our subclass of `tuple'
    for index, attr_name in enumerate(attribute_names):
        setattr(supertup, attr_name, property(operator.itemgetter(index)))
    supertup.__name__ = typename
    return supertup

Trace_entry = superTuple('Trace_entry', 'trace_fn', 'event_set')

HOOKS         = []    # List of Bunch(trace_fn, event_set)
                      # We run trace_fn if the event is in event_set.
STARTED_STATE = False # True if we are tracing. 
                      # FIXME: in 2.6 we can use sys.gettrace

ALL_EVENTS    = frozenset(('c_call', 'c_exception', 'c_return', 'call', 
                           'exception', 'line', 'return',))

def _null_trace_hook(frame, event, arg): pass

def _check_event_set(event_set):
    " check `event_set' for validity. Raise TypeError if not valid "
    if event_set is not None and not event_set.issubset(ALL_EVENTS):
        raise TypeError, 'event set is neither None nor a subset of ALL_EVENTS'
    return 

def _find_hook(trace_fn):
    """Find `trace_fn' in `hooks', and return the index of it.
    return None is not found."""
    try:
        i = [entry.trace_fn for entry in HOOKS].index(trace_fn)
    except ValueError:
        return None
    return i

def _option_set(options, value, default_opts):
    if value in options:
        return options[value]
    elif value in default_opts:
        return default_opts[value]
    else:
        return None
    pass

def _tracer_func(frame, event, arg):
    """The internal function set by sys.settrace which runs
    all of the user-registered trace hook functions."""
    global HOOKS

    # sys.settrace's semantics provide that a if trace hook returns
    # None, it should turn off tracing for that frame. We will
    # approximate that: if *all* trace hooks request ignore, then we
    # will reset the trace flag in the frame. We could do better
    # at the expense and overhead by saving more info and checking
    # more on each event.
    event_triggered  = False
    keep_trace       = False

    # Go over all registered hooks
    for hook in HOOKS:
        if hook.event_set is None or event in hook.event_set:
            keep_trace      = keep_trace or hook.trace_fn(frame, event, arg)
            event_triggered = True
            pass
        pass
    # print "event_seen %s, keep_trace %s" % (event_triggered, keep_trace,)
    if event_triggered and not keep_trace:
        # INVESTIGATE: I don't know why, but returning None doesn't
        # nuke the trace for this funcition.  So we'll instead set it
        # to a no-op trace hook.
        frame.f_trace = _null_trace_hook
        return None
        
    # From sys.settrace info: The local trace function
    # should return a reference to itself (or to another function
    # for further tracing in that scope), or None to turn off
    # tracing in that scope. 
    return _tracer_func


DEFAULT_ADD_HOOK_OPTS = {
    'front': False, 
    'start': False, 
    'event_set': ALL_EVENTS, 
    'ignore_me': False
    }

def add_hook(trace_fn, options=DEFAULT_ADD_HOOK_OPTS):
    """Add `trace_fn' to the list of callback functions that get run
    when tracing is turned on. The number of hook functions
    registered is returned. 

    A check is made on `trace_fn' to make sure it is a function
    which takes 3 parameters.

    If `to_front' is given, the hook will be made at the front of the 
    list of hooks; otherwise it will be added at the end.

    `event_set' if given and not None, is a list of events that trace_fn will
    get run on. None indicates all possible events. If this parameter is
    given, it is checked for validity.
    """

    global STARTED_STATE
    if STARTED_STATE:
        # Set to not trace this routine.
        frame = inspect.currentframe()
        frame.f_trace = _null_trace_hook
        pass

    # Parameter checking:
    if not inspect.isfunction(trace_fn):
        raise TypeError, "trace_fn should be something isfunction() blesses"
    try:
        if 3 != trace_fn.func_code.co_argcount: 
            raise TypeError, (
                'trace fn should take exactly 3 arguments (%d given)' % (
                        trace_fn.func_code.co_argcount))
    except:
        raise TypeError

    event_set = _option_set(options, 'event_set', DEFAULT_ADD_HOOK_OPTS)
    _check_event_set(event_set)

    position = _option_set(options, 'front', DEFAULT_ADD_HOOK_OPTS)

    # We set start_option via a function call *before* updating HOOKS
    # so we don't trigger a call after tracing this function is in
    # effect.
    do_start = _option_set(options, 'start', DEFAULT_ADD_HOOK_OPTS)
    
    if not _option_set(options, 'ignore_me', DEFAULT_ADD_HOOK_OPTS):
        # Set to trace calling this routine.
        frame = inspect.currentframe().f_back
        frame.f_trace = _tracer_func
        pass

    # If the global tracer hook has been registered, the below will
    # trigger the hook to get called after the assignment.
    # That's why we set the hook for this frame to ignore tracing.
    HOOKS[position:position] = [Trace_entry(trace_fn, event_set)]

    if do_start: start()
    return len(HOOKS)
    
def clear_hooks():
    ' clear all trace hooks '
    global HOOKS
    HOOKS = []
    return

def clear_hooks_and_stop():
    ' clear all trace hooks and stop tracing '
    global STARTED_STATE
    if STARTED_STATE: stop()
    clear_hooks()
    return

def size():
    ' return the number of trace hooks installed, an integer. '
    global HOOKS
    return len(HOOKS)

def is_started():
    """Return true if tracing has been started. Until we assume Python 2.6
    or better, keeping track is done by internal tracking. Thus calls to 
    sys.settrace outside of Tracer won't be detected :-(
    """
    global STARTED_STATE
    return STARTED_STATE

def remove_hook(trace_fn, stop_if_empty=False):
    """Remove `trace_fn' from list of callback functions run when
    tracing is turned on. If `trace_fn' is not in the list of
    callback functions, None is ruturned. On successful
    removal, the number of callback functions remaining is
    returned."""
    global HOOKS
    i = _find_hook(trace_fn)
    if i is not None:
        del HOOKS[i]
        if 0 == len(HOOKS) and stop_if_empty:
            stop()
            return 0
        return len(HOOKS)
    raise LookupError
    
# FIXME: in 2.6, there is the possibility for chaining 
# existing hooks by using sys.gettrace().
# FIXME: change to use options
def start(trace_fn=None, to_front=False, event_set=None,
          include_threads=True):
    """Start using all previously-registered trace hooks. If `trace_fn'
    is not None, we'll search for that and add it if it's not already
    added."""
    if trace_fn is not None: add_hook(trace_fn, to_front, event_set)
    if include_threads:
        threading.settrace(_tracer_func)
    if sys.settrace(_tracer_func) is None:
        global STARTED_STATE, HOOKS
        STARTED_STATE = True
        return len(HOOKS)
    if trace_fn is not None: remove_hook(trace_fn)
    raise NotImplementedError, "sys.settrace() doesn't seem to be implemented"

def stop():
    """Stop all trace hooks"""
    if sys.settrace(None) is None:
        global HOOKS, STARTED_STATE
        STARTED_STATE = False
        return len(HOOKS)
    raise NotImplementedError, "sys.settrace() doesn't seem to be implemented"

# Demo it
if __name__ == '__main__':
    trace_count = 25

    def my_trace_dispatch(frame, event, arg):
        global trace_count
        'A sample trace function'
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        print "%s - %s:%d" % (event, filename, lineno),
        if arg: 
            print arg
        else:
            print
            pass

        # print "event: %s frame %s arg %s\n" % [event, frame, arg]
        if trace_count > 0:
            trace_count -= 1
            return my_trace_dispatch
        else:
            print "Max trace count reached - turning off tracing"
            return None
        return

    def foo(): print "foo"

    print "** Tracing started before start(): %s" % is_started()

    start() # tracer.start() outside of this file

    print "** Tracing started after start(): %s" % is_started()
    add_hook(my_trace_dispatch) # tracer.add_hook(...) outside
    eval("1+2")
    stop()
    y = 5
    start()
    foo()
    z = 5
    for i in range(10):
        print i
    trace_count = 25
    remove_hook(my_trace_dispatch, stop_if_empty=True)
    print "** Tracing started: %s" % is_started()

    print "** Tracing only 'call' now..."
    add_hook(my_trace_dispatch, 
             {'start': True, 'event_set': frozenset(('call',))})
    foo()
    stop()
    exit(0)

"""Centralized Trace management around sys.settrace. We allow several
sets of trace events to get registered and unregistered. We allow
certain functions to be registered to be not traced. We allow tracing
to be turned on and off temporarily without losing the trace
functions.
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

Trace_entry = superTuple('Trace_entry', 'trace_fn', 'event_set',
                         'ignore_frame')

HOOKS         = []    # List of Bunch(trace_fn, event_set)
                      # We run trace_fn if the event is in event_set.
STARTED_STATE = False # True if we are tracing. 
                      # FIXME: in 2.6 we can use sys.gettrace

ALL_EVENTS    = frozenset(('c_call', 'c_exception', 'c_return', 'call', 
                           'exception', 'line', 'return',))

def null_trace_hook(frame, event, arg): 
    """ A trace hook that doesn't do anything. Can use this to "turn off"
    tracing by setting frame.f_trace. Setting sys.settrace(None) sometimes
    doesn't work...
    """
    pass

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

    # Go over all registered hooks
    for hook in HOOKS:
        if hook.ignore_frame == frame: continue
        if hook.event_set is None or event in hook.event_set:
            if not hook.trace_fn(frame, event, arg):
                # sys.settrace's semantics provide that a if trace
                # hook returns None or False, it should turn off
                # tracing for that frame.
                hook = Trace_entry(hook.trace_fn, hook.event_set,
                                   frame)
            pass
        pass
    # print "event_seen %s, keep_trace %s" % (event_triggered, keep_trace,)
        
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
        frame.f_trace = null_trace_hook
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

    option_set = lambda key: _option_set(options, key, DEFAULT_ADD_HOOK_OPTS)
    event_set = option_set( 'event_set')
    _check_event_set(event_set)

    position = option_set('front')

    # We set start_option via a function call *before* updating HOOKS
    # so we don't trigger a call after tracing this function is in
    # effect.
    do_start = option_set('start')
    
    frame = inspect.currentframe().f_back
    if option_set('ignore_me'):
        ignore_frame = frame
    else:
        ignore_frame = None
        pass

    # Set to trace calling this routine.
    frame.f_trace = _tracer_func

    # If the global tracer hook has been registered, the below will
    # trigger the hook to get called after the assignment.
    # That's why we set the hook for this frame to ignore tracing.
    HOOKS[position:position] = [Trace_entry(trace_fn, event_set,
                                            ignore_frame)]

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

DEFAULT_START_OPTS = {
    'trace_fn':  None, 
    'add_hook_opts': DEFAULT_ADD_HOOK_OPTS,
    'include_threads': False
    }
    
def start(options = DEFAULT_START_OPTS):
    """Start using all previously-registered trace hooks. If `trace_fn'
    is not None, we'll search for that and add it, if it's not already
    added."""
    option_set = lambda key: _option_set(options, key, DEFAULT_START_OPTS)
    trace_fn = option_set('trace_fn')
    if trace_fn is not None: 
        add_hook(trace_fn, option_set('add_hook_opts'))
        pass

    if option_set('include_threads'):
        threading.settrace(_tracer_func)
        pass

    # FIXME: in 2.6, there is the possibility for chaining 
    # existing hooks by using sys.gettrace().

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

    import tracefilter
    ignore_filter = tracefilter.TraceFilter([_find_hook, stop, remove_hook])
    def my_trace_dispatch(frame, event, arg):
        global trace_count, ignore_filter
        'A sample trace function'
        if ignore_filter.is_included(frame): return
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        print "%s - %s:%d" % (event, filename, lineno),
        if arg: 
            print "arg", arg
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

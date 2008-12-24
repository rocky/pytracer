"""Centralized Trace management around sys.settrace. We allow several
sets of trace events to get registered and unregistered. We allow
certain functions to be registered to be not traced. We allow tracing
to be turned on and off temporarily without losing the trace
functions.
"""

import operator, sys, inspect, threading, types

# Python Cookbook Recipe 6.7. In Python 2.6 use collections.namedtuple
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
                         'ignore_frameid')

HOOKS         = []    # List of Bunch(trace_fn, event_set)
                      # We run trace_fn if the event is in event_set.
STARTED_STATE = False # True if we are tracing. 
                      # FIXME: in 2.6 we can use sys.gettrace

ALL_EVENT_NAMES   = ('c_call', 'c_exception', 'c_return', 'call', 
                     'exception', 'line', 'return',)
ALL_EVENTS    = frozenset(ALL_EVENT_NAMES)

TRACE_SUSPEND = False

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

def find_hook(trace_fn):
    """Find `trace_fn' in `hooks', and return the index of it.
    return None is not found."""
    try:
        i = [entry.trace_fn for entry in HOOKS].index(trace_fn)
    except ValueError:
        return None
    return i

def option_set(options, value, default_options):
    if not options:
        if value in default_options:
            return default_options[value]
        pass
    elif value in options:
        return options[value]
    elif value in default_options:
        return default_options[value]
    return None

def _tracer_func(frame, event, arg):
    """The internal function set by sys.settrace which runs
    all of the user-registered trace hook functions."""

    global TRACE_SUSPEND, HOOKS
    if TRACE_SUSPEND: return _tracer_func

    # Go over all registered hooks
    for i in range(len(HOOKS)):
        hook = HOOKS[i]
        if hook.ignore_frameid == id(frame): continue
        if hook.event_set is None or event in hook.event_set:
            if not hook.trace_fn(frame, event, arg):
                # sys.settrace's semantics provide that a if trace
                # hook returns None or False, it should turn off
                # tracing for that frame.
                HOOKS[i] = Trace_entry(hook.trace_fn, hook.event_set,
                                       id(frame))
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
    'backlevel': 0
    }

def add_hook(trace_fn, options=None):
    """Add `trace_fn' to the list of callback functions that get run
    when tracing is turned on. The number of hook functions
    registered is returned. 

    A check is made on `trace_fn' to make sure it is a function
    which takes 3 parameters: a frame, an event, and an arg or which
    sometimes arg is None.

    If `to_front' is given, the hook will be made at the front of the 
    list of hooks; otherwise it will be added at the end.

    `options' is a hash having potential keys: 'front', 'start',
    'event_set', and 'backlevel'. 

    If the event_set option-key is included, it should be is an event
    set that trace_fn will get run on. Use set() or frozenset() to
    create this set. ALL_EVENT_NAMES is a tuple contain a list of
    the event names. ALL_EVENTS is a frozenset of these.

    'to_front' adds the hook the the front of the list; the default is
    the back of the list. 

    'start' is a boolean which indicates the hooks should be started
    if they aren't already. 

    'backlevel' an integer indicates that the calling should continue
    backwards in return call frames and is the number of levels to
    skip ignore. 0 means that the caller of add_hook() is traced as
    well as a all new frames the caller subsequently calls. 1 means
    that all the caller of add_hook() is ignored but prior parent
    frames are traced, and None means that no previous parent frames
    should be traced.
    """

    # Parameter checking:
    if inspect.ismethod(trace_fn):
        argcount = 4
    elif inspect.isfunction(trace_fn):
        argcount = 3        
    else:
        raise TypeError, (
            "trace_fn should be something isfunction() or ismethod() blesses")
    try:
        if argcount != trace_fn.func_code.co_argcount: 
            raise TypeError, (
                'trace fn should take exactly %d arguments (takes %d)' % (
                        argcount, trace_fn.func_code.co_argcount,))
    except:
        raise TypeError

    get_option = lambda key: option_set(options, key, DEFAULT_ADD_HOOK_OPTS)
    event_set = get_option( 'event_set')
    _check_event_set(event_set)

    position = get_option('front')

    # Setup so we don't trace into this routine. 
    ignore_frame = inspect.currentframe()

    # Should we trace frames below the one that we issued this 
    # call? 
    backlevel = get_option('backlevel')
    if backlevel is not None:
        if types.IntType != type(backlevel):
            raise TypeError, (
                'backlevel should be an integer type, is %s' % (
                    backlevel))
        frame = ignore_frame
        while frame and backlevel >= 0:
            backlevel -= 1
            frame = frame.f_back
            pass
        
        # Set to trace all frames below this
        while frame:
            frame.f_trace = _tracer_func
            frame = frame.f_back
            pass
        
        pass
    # If the global tracer hook has been registered, the below will
    # trigger the hook to get called after the assignment.
    # That's why we set the hook for this frame to ignore tracing.
    HOOKS[position:position] = [Trace_entry(trace_fn, event_set, 
                                            ignore_frame)]
    
    if get_option('start'): start()
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
    i = find_hook(trace_fn)
    if i is not None:
        del HOOKS[i]
        if 0 == len(HOOKS) and stop_if_empty:
            stop()
            return 0
        return len(HOOKS)
    return None

DEFAULT_START_OPTS = {
    'trace_fn':  None, 
    'add_hook_opts': DEFAULT_ADD_HOOK_OPTS,
    'include_threads': False
    }
    
def start(options = None):
    """Start using all previously-registered trace hooks. If `trace_fn'
    is not None, we'll search for that and add it, if it's not already
    added."""
    get_option = lambda key: option_set(options, key, DEFAULT_START_OPTS)
    trace_fn = get_option('trace_fn')
    if trace_fn is not None: 
        add_hook(trace_fn, get_option('add_hook_opts'))
        pass

    if get_option('include_threads'):
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
    trace_count = 10

    import tracefilter
    ignore_filter = tracefilter.TraceFilter([find_hook, stop, remove_hook])
    def my_trace_dispatch(frame, event, arg):
        global trace_count, ignore_filter
        'A sample trace function'
        if ignore_filter.is_included(frame): return None
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
        pass

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
    for i in range(6):
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



A more flexible interface to _sys.settrace()_ allowing, chained trace hooks, prioritiziation of hooks, or filtering out functions to ignore for a specific hook.

I use this in rewrites of the stock Python debugger, [trepan2](http://code.google.com/p/pydbgr) and [trepan3k](http://code.google.com/p/python3-trepan).

# Description #

This module extends _sys.settrace()_ to allow more than a single global trace hook and set its invocation priority. In addition, you can set to filter out calls to a particular function or ignore particular events for a given hook.

# Module tracer #

## add\_hook ##

` def add_hook(trace_fn, options=None): `

Add _trace\_fn_ to the list of callback functions that get run when
tracing is turned on. The number of hook functions registered is
returned.

A check is made on _trace\_fn_ to make sure it is a function which
takes 3 parameters: a _frame_, an _event_, and an argument which sometimes
has the value _None_.

_options_ is a dictionary having potential keys: _position_, _start_,
_event\_set_, and _backlevel_.

If the _event\_set_ option-key is included, it should be is an event set
that _trace\_fn()_ will get run on. Use _set()_ or _frozenset()_ to create this
set. _ALL\_EVENT\_NAMES_ is a tuple contain a list of the event
names. _ALL\_EVENTS_ is a frozenset of these.

_position_ is the index of where the hook should be place in the list,
so 0 is first and -1 _after_ is last item; the default is the very
back of the list (-1). -2 is _after_ the next to last item.

_start_ is a boolean which indicates the hooks should be started if
they aren't already.

_backlevel_ an integer indicates that the calling should continue
backwards in return call frames and is the number of levels to skip
ignore. 0 means that the caller of _add\_hook()_ is traced as well as all
new frames the caller subsequently calls. 1 means that all the caller
of _add\_hook()_ is ignored but prior parent frames are traced, and None
means that no previous parent frames should be traced.

## remove\_hook ##
` remove_hook(trace_fn, stop_if_empty=False): `

Remove _trace\_fn_ from list of callback functions run when
tracing is turned on. If _trace\_fn_ is not in the list of
callback functions, _None_ is returned. On successful
removal, the number of callback functions remaining is
returned.

## clear\_hooks ##

` clear_hooks(): `

Clear all trace hooks.

## null\_trace\_hook ##

` def null_trace_hook(frame, event, arg): `

A trace hook that doesn't do anything. Can use this to turn off
tracing by setting _frame.f\_trace_. Setting _sys.settrace(None)_ sometimes
doesn't work.

## size ##

` def size(): `

Returns the number of trace hooks installed, an integer.

## is\_started ##

` def is_started(): `

Returns _True_if tracing has been started. Until we assume Python 2.6
or better, keeping track is done by internal tracking. Thus calls to
sys.settrace outside of Tracer won't be detected


## start ##

`def start(options = None):`

Start using all previously-registered trace hooks. If
_options[trace\_fn](trace_fn.md)_ is not _None_, we'll search for that trace
function and add it, if it's not already added.

## stop ##

`def stop()`

Stop all trace hooks.

# Class Tracefilter #

A class that can be used to test whether certain frames or functions should be skipped/included in tracing.

## methods ##

**NOTE: "include" should be called "exclude" and I will probably change the names in the future.**

```
  def __init__(self, include_fns=[], continue_return_frame=None):
  
  def add_include(self, frame_or_fn):
      """Remove 'frame_or_fn' from the list of functions to include"""
  
  def clear_include(self):
  
  def is_included(self, frame_or_fn):
      """Return True if 'frame_or_fn' is in the list of functions to include"""
  
  def remove_include(self, frame_or_fn):
      """Remove 'frame_or_fn' from the list of functions to include"""
```

## functions ##

```
    def add_to_set(frame_or_fn, f_set):
        """Add 'frame_or_fn' to the list of functions to include"""
    
    def fs2set(frames_or_fns):
        """Given a list of frame or function objects, turn it into a set which
        can be used in an include set."""
    
    def to_f_code(f):
```
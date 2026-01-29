# -*- coding: utf-8 -*-
#   Copyright (C) 2026 Rocky Bernstein <rocky@gnu.org>
#   based on code I wrote going back to 2008
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Centralized Trace management around sys.monitoring. We allow several
sets of trace events to get registered and unregistered. We allow
certain functions to be registered to be not traced. We allow tracing
to be turned on and off temporarily without losing the trace
functions.

This module has been revised to use Python 3.12's sys.monitoring
API. It assumes the presence of the following functions on
sys.monitoring:

- set_monitor(func) -> returns previous monitor (or None)
- Passing None to set_monitor disables monitoring.

For threading support it assumes threading.setmonitor(func) exists and
behaves analogous to threading.settrace.

"""

import inspect
import sys

from types import CodeType
from typing import Any, Callable, Dict, Optional, Set

E = sys.monitoring.events

# The maximum number of sys.monitoring tool IDs is 6 (range 0 to 5)
MAX_TOOL_IDS = 6
TOOL_ID_RANGE = range(MAX_TOOL_IDS)

# A mapping of tool ids (a number) to tool names (as string)

# We run trace_func if the event is in event_set.
STARTED_STATE: Dict[int, bool] = {}

# NOTE: This file now uses sys.monitoring (Python 3.12+) instead of sys.settrace.

ALL_EVENT_NAMES = (
    "branch",
    "branch_left",
    "branch_right",
    "c_call",
    "c_exception",
    "c_return",
    "call",
    "exception",
    "instruction",
    "jump",
    "line",
    "raise",
    "resume",
    "return",
    "start",
    "yield",
)

# If you want short strings for the above event names
EVENT2SHORT = {
    "branch": "><",
    "branch_left": ".>",
    "branch_right": "<.",
    "c_call": "C>",
    "c_exception": "C!",
    "c_return": "C<",
    "call": "->",
    "exception": "!!",
    "jump": "/\\",
    "line": "--",
    "instruction": "..",
    "raise": "||",
    "resume": "ok",
    "return": "<-",
    "start": "|-",
    "yield": "-|",
}

ALL_EVENTS = frozenset(ALL_EVENT_NAMES)

class FixedList:
    """
    A class fixed-length list.
    """
    def __init__(self, initial_value: Optional[Any], size: int):
        self._data = [initial_value] * size

    def __getitem__(self, index: int):
        return self._data[index]

    def __setitem__(self, index: int, value: Optional[Dict[int, Callable]]):
        self._data[index] = value

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr(self._data)

    def index(self, start: int) -> int:
        """Return first index of value.

        Raises ValueError if the value is not present.
        """
        return self._data.index(start)


# A list of the registered hooks keyed by sys.monitoring.events.
HOOKS = FixedList(None, MAX_TOOL_IDS)

# A list of tool names
TOOL_NAME = FixedList(None, MAX_TOOL_IDS)

debug = False  # Setting true

# Build a lookup table from sys.monitoring.events
# This filters for constants starting with PY_ or specific event names like LINE
event2string: Dict[int, str] = {}
eventname2int: Dict[str, int] = {}

for attr in dir(E):
    if not attr.startswith("_"):
        val = getattr(E, attr)
        # Standard names are like PY_START; we convert them to "start"
        # Some names like LINE or JUMP don't have the PY_ prefix
        name = attr.lower()
        if name.startswith("py_"):
            name = name[3:]
        event2string[val] = name
        eventname2int[name] = val


class PytraceException(Exception):
    def __init__(self, mess: str):
        self.mess = mess

    def __str__(self):
        return self.messr

def check_tool_id(tool_id: int):
    if tool_id not in TOOL_ID_RANGE:
        raise PytraceException(f"tool id {tool_id} is not in {range(MAX_TOOL_IDS)}")

def null_trace_hook(*args, **kwargs):
    """A trace hook that doesn't do anything. Can use this to "turn off"
    tracing by setting frame.f_trace. Setting sys.settrace(None) sometimes
    doesn't work...
    """
    pass


def find_hook_by_name(tool_name: str) -> Optional[int]:
    """Find tool id when given a tool name or return None if it is not found."""
    try:
        return TOOL_NAME.index(tool_name)
    except ValueError:
        return None


def find_hook_by_id(tool_id: int) -> Optional[str]:
    """Find tool name given a tool id and return that, or
    return None if it is not found."""
    check_tool_id(tool_id)
    try:
        return TOOL_NAME[tool_id]
    except IndexError:
        return None


def add_trace_callbacks(
    tool_name: str, trace_callbacks: Dict[int, CodeType], options=None
) -> Optional[int]:
    """For each event and callback function in `trace_callbacks`,
    register that event under `tool_name`.

    A check is made on each trace function trace_callbacks to make
    sure it is a function.
    """

    if (tool_id := find_hook_by_name(tool_name)) is None:
        for i, tool_name_entry in enumerate(TOOL_NAME):
            if tool_name_entry is None and sys.monitoring.get_tool(i) is None:
                tool_id = i
                break
        else:
            print(f"all {MAX_TOOL_IDS} hooks are in use")
            return None

        # FIXME check for TOOL_NAME all full.
        TOOL_NAME[tool_id] = tool_name
        if (old_tool := sys.monitoring.get_tool(i)) is None:
            sys.monitoring.use_tool_id(tool_id, tool_name)
        else:
            if trace_callbacks is not None and old_tool != tool_name:
                print("Not adding a trace_callback where it already appeared")
                return None
            pass

    else:
        if not sys.monitoring.get_tool(tool_id):
            sys.monitoring.use_tool_id(tool_id, tool_name)

    HOOKS[tool_id] = trace_callbacks
    register_events(tool_id, trace_callbacks)
    return tool_id


def size() -> int:
    """Returns a count of the number of trace monitoring hooks installed through
    our mechanism. This is an integer in TOOL_ID_RANGE."""
    return sum(1 for item in TOOL_NAME if item is not None)

# FIXME allow either a name or id
def is_started(tool_id: int) -> bool:
    """Returns _True_ if monitoring has been started for `hook_id`."""
    check_tool_id(tool_id)
    HOOKS[tool_id] is not None


def free_tool_id(tool_id):
    """Remove hooks in tool_id the from list of callback functions run
    when monitoring is turned on. We only remove those hooks that are associated
    with our callbacks.
    """
    check_tool_id(tool_id)
    registered_tool_name = sys.monitoring.get_tool(tool_id)
    if registered_tool_name is not None:
        if registered_tool_name != TOOL_NAME[tool_id]:
            raise PytraceException(f"tool name {tool_id} is registered under name {registered_tool_name} not {TOOL_NAME[tool_id]}")

        sys.monitoring.free_tool_id(tool_id)

    HOOKS[tool_id] = None
    TOOL_NAME[tool_id] = None
    return

# FIXME add optional event mask
def register_events(tool_id: int, trace_callbacks: Dict[int, Callable]) -> int:
    check_tool_id(tool_id)
    events = 0
    sys.monitoring.set_events(tool_id, events)
    for event_id, trace_callback_func in trace_callbacks.items():
        # Parameter checking:
        if not (
            inspect.ismethod(trace_callback_func)
            or inspect.isfunction(trace_callback_func)
        ):
            print("trace_func should be something isfunction() or ismethod() blesses")

        events |= event_id
        old_callback = sys.monitoring.register_callback(
            tool_id, event_id, trace_callback_func
        )
        if old_callback is not None and old_callback != trace_callback_func:
            print(
                f"Warning smashed old_callback {old_callback} in tool_id {tool_id}, event id {event_id}"
            )
    sys.monitoring.set_events(tool_id, events)
    return events


def register_tool_by_name(
    tool_name: str, tool_id: Optional[int] = None, can_change_tool_id: bool = True
) -> int:
    """
    Register `tool_name` in sys.monitoring and return the tool_id it is
    registered under.

    If tool_id is not given we will find a free tool_id
    number or raise an error if there are no more free slots.

    If tool_id is given, it should have either been a previously unused
    slot, or it should have been registered under the same name.

    Note that pdb uses tool_id 0. So a debugger like trepan3k that
    wants to co-exist with pdb suggest a number other than 0.

    In any event the tool_id used (which will be the same as tool_id coming
    in if that was not None is returned when there is no error.
    """
    # import pdb; pdb.set_trace()

    if tool_id is not None:
        check_tool_id(tool_id)

        registered_tool_name = sys.monitoring.get_tool(tool_id)
        # See if tool_id has been sys.monitor registered. If so, does
        # it have the name we expect?
        if registered_tool_name is not None and registered_tool_name != tool_name:
            # Not the tool name we expect, but if we can change it, do so.
            if can_change_tool_id:
                sys.monitoring.clear_tool_id(tool_id)
                sys.monitoring.use_tool_id(tool_id, tool_name)
            else:
                raise PytraceException(
                    f"tool id {tool_id} is registered already under {registered_tool_name}, "
                    + f"so it cannot be used as {tool_name}. tool_id is not specified as changable."
                )

    elif (registered_tool_id := find_hook_by_name(tool_name)) is None:
        # tool_id was not registered. Find a free tool_id slot.
        for i, tool_name_entry in enumerate(TOOL_NAME):
            if tool_name_entry is None and sys.monitoring.get_tool(i) is None:
                tool_id = i
                break
        else:
            raise PytraceException(f"all {MAX_TOOL_IDS} hooks are in use")

        TOOL_NAME[tool_id] = tool_name
        sys.monitoring.use_tool_id(tool_id, tool_name)
    elif tool_id is None:
        tool_id = registered_tool_id
    else:
        if registered_tool_id != tool_id:
            if can_change_tool_id:
                tool_id = registered_tool_id
            else:
                raise PytraceException(
                    f"tool id {tool_name} was registered already under {registered_tool_id}, "
                    + f"so it cannot be used with id {tool_id}. tool_id is not specified as changable."
                )

    # We have resolved tool_id to a previous free slot and have
    # registered that tool_id. So all we have to do is record that
    # slot for our use, under the given tool_name in TOOL_NAME,
    # if that hasn't been done before.

    if TOOL_NAME[tool_id] is None:
        TOOL_NAME[tool_id] = tool_name
    elif TOOL_NAME[tool_id] != tool_name:
        raise PytraceException(
            f"tool id {tool_id} is associated in Pytracer {registered_tool_name}, "
            + f"so it cannot be used as {tool_name}"
        )

    return tool_id


def start(
    tool_name: str,
    trace_callbacks: Optional[Dict[int, CodeType]] = None,
    tool_id: Optional[int] = None,
    events_set: Optional[Set[str]] = None
) -> Optional[int]:
    """Start using any previously-registered trace hooks. If
    `options[trace_func]_ is not None, we'll search for that and add it, if it's
    not already added.
    """

    if trace_callbacks is None:
        tool_id = register_tool_by_name(tool_name, tool_id)
        if HOOKS[tool_id]:
            # This is not the first start. So set
            # sys.monitoring to track these events that
            # we have callbacks for.
            register_events(tool_id, HOOKS[tool_id])
        return tool_id
    return add_trace_callbacks(tool_name, trace_callbacks)


# Think about: we could return the uncleared event names in addition to the
# event set. And/or a the list found and cleared.
def stop(
    tool_name: str, events_set: Optional[Set[str]] = None, free_tool_id: bool = False
) -> Optional[int]:
    """Stop or unregister callback hooks in `tool_name` for events
    `events`. If events is None, then all events found under tool_name
    are removed. And if the event wasn't set previously, it is tacitly
    ignored.

    Note, the event set is given as a set of strings, not an encoded
    event bitmask.  The strings used are not checked for validity, so
    when an event name is and invalid name, that has no effect, and
    no warning is given.

    The new event mask in effect is returned encoded as a bitmask. If
    None is returned, then tool_name was not found.

    If free_tool_id is False, HOOKS[tool_id] will still hold the
    dictionary of callback functions which can be enabled again later without
    needed to specify this dictoinary.

    Set free_tool_id to True, when clearing all events, and when you
    will no longer need any tracing, or will do tool setup should you
    need trace at a later point. This allows execution to continue at
    full speed, and clears and frees tool_id which allows another
    monitor to use the tool id number.

    When free_tool_id is True, the event_set should be cover the entire
    events set registered; or "events_set" should be None (which means
    the same thing). Otherwise the free_tool_id parameter is ingored.

    """

    if (tool_id := find_hook_by_name(tool_name)) is None:
        return None

    if events_set is None:
        events_set = ALL_EVENT_NAMES

    # We have a tool id
    trace_callbacks = HOOKS[tool_id]

    # Build up a new list of events from
    # scratch. We set the new event mask if
    # it was *already* in trace_callback_func and it
    # was *not* noted to be removed from events_set.
    new_event_mask = 0

    for event_id, trace_callback_func in trace_callbacks.items():
        if event2string.get(event_id) not in events_set:
            new_event_mask |= event_id

    # print(f"events to clear {new_event_mask}")  # debug
    sys.monitoring.set_events(tool_id, new_event_mask)
    return new_event_mask


# Demo it
if __name__ == "__main__":

    t = list(EVENT2SHORT.keys())
    t.sort()
    print("EVENT2SHORT.keys() == ALL_EVENT_NAMES: %s" % (tuple(t) == ALL_EVENT_NAMES))
    trace_count = 100000
    hook_name = "pytrace-test"

    import importlib
    import tracefilter

    ignore_filter = tracefilter.TraceFilter(
        [
            add_trace_callbacks,
            check_tool_id,
            find_hook_by_name,
            importlib._bootstrap,
            is_started,
            register_events,
            free_tool_id,
            start,
            stop,
            sys.monitoring.set_events,
        ]
    )

    def code_short(code: CodeType) -> str:
        import os.path as osp

        return f"{code.co_name} in {osp.basename(code.co_filename)}"

    def line_event_callback(code, line_number):
        """A line event callback trace function"""

        if ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(f"line event: code: {code_short(code)}, line: {line_number}")

        global trace_count
        if trace_count > 0:
            trace_count -= 1
        else:
            print("Max line trace count reached - turning off monitoring")
            stop(hook_name, E.LINE)
            return sys.monitoring.DISABLE
        return sys.monitoring.DISABLE

    def call_event_callback(code, instruction_offset, callable_obj, args):
        """A call event callback trace function"""
        if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(
            f"call event: code: {code_short(code)}, offset: *{instruction_offset} call: {callable_obj}"
        )

        if args == sys.monitoring.MISSING:
            print("call event: no call arguments")
        else:
            print(f"call event: args: {args}")

        # print "event: %s frame %s arg %s\n" % [event, frame, arg]
        global trace_count
        if trace_count > 0:
            trace_count -= 1
        else:
            print("Max call trace count reached - turning off monitoring")
            # TODO: DISABLE HERE
            return sys.monitoring.DISABLE
        return sys.monitoring.DISABLE

    def foo(*args):
        print(f"foo called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    print(f"** Monitoring started before start(): {is_started(1)}")
    tool_id = start(hook_name, tool_id=1)
    print(f"tool_id is {tool_id}")

    callback_hooks = {
        E.CALL: call_event_callback,
        E.LINE: line_event_callback,
    }

    add_trace_callbacks(hook_name, callback_hooks)
    eval("1+2")
    foo()

    stop(hook_name)
    print(f"** Monitoring state after stopped: {is_started(tool_id)}")
    y = 5
    start(hook_name)
    bar()
    z = 5
    for i in range(6):
        print(i)
    trace_count = 25
    free_tool_id(tool_id)
    print(f"** Monitoring started: {is_started(tool_id)}")

    # After adding event parameter to start()
    # print("** Monitoring only 'call' now...")
    tool_id = start(tool_name=hook_name, trace_callbacks=callback_hooks)
    foo()
    bar()
    stop(tool_id)

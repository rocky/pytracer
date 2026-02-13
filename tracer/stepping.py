"""
Debugger-like "step into", "step over" and "finish" support.
"""

import sys
from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Dict, Optional, Tuple, Union

import tracer.sys_monitoring as sys_monitoring
from tracer.sys_monitoring import mstart

E = sys.monitoring.events

# Events that are not allowed in sys.monitoring.set_local_events
GLOBAL_EVENTS = E.C_RAISE | E.C_RETURN | E.PY_UNWIND | E.RAISE
STEP_INTO_TRACKING = E.CALL | E.PY_START | E.PY_RETURN


class StepType(Enum):
    NO_STEPPING = "no stepping"
    STEP_INTO = "step into"
    STEP_OUT = "step out"
    STEP_OVER = "step over"


class StepGranularity(Enum):
    INSTRUCTION = "instruction"
    LINE_NUMBER = "line number"
    # Is there stuff like "RESUME" or at "safe" points


class BreakpointTag(Enum):
    LINE_NUMBER = "line number"
    LINE_NUMBER_OFFSET = "line number and offset"
    CODE_OFFSET = "instruction offset"


@dataclass
class LineNumberValue:
    tag: BreakpointTag = BreakpointTag.LINE_NUMBER
    line_number: int = -1


@dataclass
class LineNumberOffsetValue:
    tag: BreakpointTag = BreakpointTag.LINE_NUMBER_OFFSET
    line_number: int = -1
    code_offset: int = -1


@dataclass
class CodeOffsetValue:
    tag: BreakpointTag = BreakpointTag.CODE_OFFSET
    code_offset: int = -1


# The "Union" structure
Location = Union[LineNumberValue, LineNumberOffsetValue, CodeOffsetValue]


@dataclass
class FrameInfo:
    step_type: StepType = StepType.NO_STEPPING
    step_granularity: Optional[StepGranularity] = None
    local_events_mask: int = 0
    calls_to: Optional[FrameType] = None


FRAME_TRACKING: Dict[FrameType, FrameInfo] = {}


@dataclass
class CodeInfo:
    breakpoints = []
    last_frame: Optional[FrameType] = None


# We store breakpoints per tool id and code.
CODE_TRACKING: Dict[Tuple[int, CodeType], CodeInfo] = {}

# Event mask that should be use to callback on
# finish or return from function, method or module.
# Note: we cannot include global events, specifically
# those in GLOBAL_EVENTS since that is illegal for set_local_events().
STEP_OUT_EVENTS = E.PY_YIELD | E.PY_RETURN

# Event mask that should be use to callback on
# line stepping. This should
STEP_OVER_EVENTS = STEP_OUT_EVENTS

# trace status can be:
#  * "step over" stepping which is
#    local event stepping can be any combination of local events, and
#    possible global events "exception handled", "raise", "reraise", "throw".
#    The most common event is LINE,
#    but INSTRUCTION may be useful.  Breakpoints at certain places will use either
#    filter on line or INSTRUCTION events.
#
#  * "step into" stepping which is local stepping and global events.
#
#  * "finish "stepping which is local return and yield, and global PY_UNWIND
#  * "continue"


def set_breakpoint(tool_id: int, location: Location):
    # event_bitmask = sys.montoring.get_events(tool_id)
    return


def set_step_into(
    tool_id: int, frame: FrameType, granularity: StepGranularity, events_mask: int
):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It always adds a CALL event to the.
    local events to be tracked.
    """

    # Clear global events that are illegal for `set_local_events()`.
    events_mask &= ~GLOBAL_EVENTS

    combined_events_mask = (STEP_OUT_EVENTS | events_mask) | E.CALL | E.PY_START

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_INTO,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    code = frame.f_code
    sys.monitoring.set_local_events(tool_id, code, combined_events_mask)


def set_step_over(
    tool_id: int, frame: FrameType, step_granularity: StepGranularity, events_mask: int
):
    """
    Set local callback for a `step over` in `code`.
    `events_mask` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It should *not* contain CALL.
    This will be masked out.
    """
    # Clear global events that are illegal for `set_local_events()`.
    events_mask &= ~GLOBAL_EVENTS

    combined_events_mask = (STEP_OUT_EVENTS | events_mask) & ~(E.CALL | E.PY_START)

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_OVER,
        step_granularity=None,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    code = frame.f_code
    sys.monitoring.set_local_events(tool_id, code, combined_events_mask)


def set_step_out(tool_id: int, frame: FrameType):

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.

    code = frame.f_code
    local_events_mask = sys.monitoring.get_local_events(tool_id, code)
    combined_events_mask = (STEP_OUT_EVENTS | local_events_mask) & ~E.CALL

    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_OUT,
        step_granularity=None,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    sys.monitoring.set_local_events(STEP_OUT_EVENTS, code)


def code_short(code: CodeType) -> str:
    import os.path as osp

    return f"{code.co_name} in {osp.basename(code.co_filename)}"


# ignore_filter = tracefilter.TraceFilter([sys_monitoring, sys.monitoring])


def line_event_callback(tool_id: int, code: CodeType, line_number: int) -> object:
    """A line event callback trace function"""

    # if ignore_filter.is_excluded(code):
    #    return sys.monitoring.DISABLE

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:

    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # Below: 0 is us; 1 is our closure lambda, and 2 is the user code.
    frame = sys._getframe(2)
    if frame.f_code != code:
        print("Woah -- code vs frame code mismatch in line event")

    # print(f"XXX FRAME: f_trace: {frame.f_trace}, f_trace_lines: {frame.f_trace_lines}, f_trace_opcodes: {frame.f_trace_opcodes}")

    frame_info = FRAME_TRACKING.get(frame, None)
    if frame_info is not None:
        if (step_type := frame_info.step_type) is None:
            print(f"XXX This should not happen - first time for {frame}")
        else:
            print(
                f"\nLINE: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) {step_type} {frame_info.step_granularity} code:"
                f"\n\t{code_short(code)}, line: {line_number}"
            )

    ### end code inside hook.

    return local_event_handler_return(tool_id, code, events_mask)


def local_event_handler_return(
    tool_id: int, code: CodeType, events_mask: int
) -> object:
    """A line event callback trace function"""
    sys.monitoring.set_local_events(tool_id, code, events_mask)
    return


def call_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
    callable_obj: CodeType,
    args,
) -> object:
    """A CALL event callback trace function"""

    if (ignore_filter := sys_monitoring.MONITOR_FILTERS[tool_id]) is not None:
        if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
            return

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:
    # * events_mask
    # * frame
    # * step_type

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # Below: 0 is us; 1 is our closure lambda, and 2 is the user code.
    frame = sys._getframe(2)
    if frame.f_code != code:
        print("Woah -- code vs frame code mismatch in line event")

    frame_info = FRAME_TRACKING.get(frame)
    if frame_info is None:
        print(f"Woah -- frame in FRAME_TRACKING is not set:\n{FRAME_TRACKING}\nleaving...")
        return

    step_type = frame_info.step_type

    step_granularity = frame_info.step_granularity

    print(
        (
            f"\n{event.upper()}: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) {step_type} {step_granularity} code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset}"
        )
    )

    ### end code inside hook. events_mask, frame and step_type should be set.

    if hasattr(callable_obj, "__code__") and isinstance(
        callable_obj.__code__, CodeType
    ):
        return call_event_handler_return(
            tool_id, callable_obj.__code__, events_mask, step_type
        )


def call_event_handler_return(
    tool_id: int, code: CodeType, events_mask: int, step_type: StepType
) -> object:
    """Returning from a call event handler. We assume events_mask does not have
    any events that are not local events.
    """
    if step_type == StepType.STEP_INTO:
        # Propagate local tracking into code object to be called and it step type.
        # FIXME: it would be better to attach it to the particular *frame*
        # that will be called.
        sys.monitoring.set_local_events(tool_id, code, events_mask)

    return


def exception_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
    exception: BaseException,
):
    """An event callback trace function for RAISE, RERAISE, EXCEPTION_HANDLED, PY_UNWIND,
    PY_THROW, and STOP_ITERATION."""

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:
    # * events_mask
    # * frame

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    print(
        f"\n{event.upper()}: tool_id: {tool_id} code: {bin(events_mask)}\n\t"
        f"{code_short(code)}, offset: *{instruction_offset}\n\treturn value: {exception}"
    )

    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code == code:
            break
        frame = frame.f_back
    else:
        print("Woah! did not find frame")
        return

    ### end code inside hook; `frame` should be set.

    return leave_event_handler_return(tool_id, frame)


def goto_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
    destination_offset: int,
) -> object:
    """A JUMP or BRANCH (LEFT, RIGHT)event callback trace function"""

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set `events_mask`.

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # # Below: 0 is us; 1 is our closure lambda, and 2 is the user code.
    # frame = sys._getframe(2)
    # print(f"XXX FRAME: f_trace: {frame.f_trace}, f_trace_lines: {frame.f_trace_lines}, f_trace_opcodes: {frame.f_trace_opcodes}")

    print(
        (
            f"\n{event.upper()}: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset} to *{destination_offset}"
        )
    )

    ### end code inside hook; `events_mask` should be set.

    return local_event_handler_return(tool_id, code, events_mask)


def instruction_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
) -> object:
    """A call event callback trace function"""

    if (ignore_filter := sys_monitoring.MONITOR_FILTERS[tool_id]) is not None:
        if ignore_filter.is_excluded(code):
            return

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set `events_mask`.

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # # Below: 0 is us; 1 is our closure lambda, and 2 is the user code.
    # frame = sys._getframe(2)
    # print(f"XXX FRAME: f_trace: {frame.f_trace}, f_trace_lines: {frame.f_trace_lines}, f_trace_opcodes: {frame.f_trace_opcodes}")

    print(
        (
            f"\n{event.upper()}: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset}"
        )
    )

    ### end code inside hook; `events_mask` should be set.

    return local_event_handler_return(tool_id, code, events_mask)


def leave_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
    return_value: object,
):
    """A Return and Yield event callback trace function"""

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:
    # * events_mask
    # * frame

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    print(
        f"\n{event.upper()}: tool_id: {tool_id} code: {bin(events_mask)}\n\t"
        f"{code_short(code)}, offset: *{instruction_offset}\n\treturn value: {return_value}"
    )

    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code == code:
            break
        frame = frame.f_back
    else:
        print("Woah! did not find frame")
        return

    ### end code inside hook; `frame` should be set.

    if event != "yield":
        return leave_event_handler_return(tool_id, frame)
    # Do we want to do something special for yield?


def leave_event_handler_return(tool_id: int, frame: FrameType) -> object:
    """Returning from a RETURN, YIELD event handler. Note PY_UNWIND can
    skip over RETURN and YIELD events that might otherwise occur.
    """
    # Remove Set local events based on step type and breakpoints.
    if frame in FRAME_TRACKING:
        # print("WOOT - Deleting frame")
        del FRAME_TRACKING[frame]

        code = frame.f_code
        code_info = CODE_TRACKING.get((tool_id, code))
        if code_info is not None:
            # FIXME: do we have to worry about other threads?
            if len(code_info.breakpoints) == 0:
                # Remove any local events
                sys.monitoring.set_local_events(tool_id, code, 0)
            # else:
            # FIXME: What should we do here for breakpoints?
            # # Do we need to remove this from CODE_TRACKING?
            # del CODE_TRACKING[tool_id, code]

    return


def start_event_callback(
    tool_id: int,
    code: CodeType,
    instruction_offset: int,
) -> object:
    """A PY_START event callback trace function"""

    if (ignore_filter := sys_monitoring.MONITOR_FILTERS[tool_id]) is not None:
        if ignore_filter.is_excluded(code):
            return

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:
    # * events_mask
    # * frame
    # * step_type

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # Below: 0 is us; 1 is our closure lambda, and 2 is the user code.
    frame = sys._getframe(2)
    if frame.f_code != code:
        print("Woah -- code vs frame code mismatch in line event")

    parent_frame = frame.f_back
    step_type = StepType.NO_STEPPING
    step_granularity = StepGranularity.LINE_NUMBER
    if parent_frame is None:
        print("Woah -- parent frame is None.")

    else:
        parent_frame_info = FRAME_TRACKING.get(parent_frame)
        if parent_frame_info is None:
            print(f"Woah -- parent frame {parent_frame} in FRAME_TRACKING is not set:\n{FRAME_TRACKING}\nleaving...")
        else:
            step_type = parent_frame_info.step_type

            # Right now we don't allow debugger events or breakpoints on START.
            # If we do someday, adjust the below
            if step_type not in (StepType.STEP_INTO, StepType.NO_STEPPING):
                print(
                    f"Expecting -- 'step into' or 'not stepping' in parent; is {parent_frame_info.step_type}"
                )
                return

            # Note in the parent frame's frame_info a call to us. This assists
            # in finding stale frames: frames that were were not removed from
            # our tables on a RETURN or YIELD event, possibly because an
            # exception skipped over them.
            parent_frame_info.calls_to = frame

            step_granularity = parent_frame_info.step_granularity

    step_granularity_mask = (
        E.INSTRUCTION if step_granularity == StepGranularity.INSTRUCTION else E.LINE
    )
    local_events_mask = events_mask | step_granularity_mask

    FRAME_TRACKING[frame] = FrameInfo(
        step_type, step_granularity, local_events_mask, None
    )

    if step_type == StepType.NO_STEPPING:
        return

    print(
        (
            f"\nSTART: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) {step_type} code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset}"
        )
    )

    ### end code inside hook. events_mask, frame and step_type should be set.

    return local_event_handler_return(tool_id, code, events_mask)


def set_callback_hooks_for_toolid(tool_id: int) -> dict:
    """
    Augments callback handlers to include the tool-id name and event name.
    We often need to add the event name since callback handlers are shared
    across similar kinds of events, like E.BRANCH_LEFT and E.BRANCH_RIGHT.

    Only local callbacks are set.
    """
    return {
        E.BRANCH_LEFT: (
            lambda code, instruction_offset, destination_offset: goto_event_callback(
                tool_id, "branch left", code, instruction_offset, destination_offset
            )
        ),
        E.BRANCH_RIGHT: (
            lambda code, instruction_offset, destination_offset: goto_event_callback(
                tool_id, "branch right", code, instruction_offset, destination_offset
            )
        ),
        E.CALL: (
            lambda code, instruction_offset, callable_obj, args: call_event_callback(
                tool_id, "call", code, instruction_offset, callable_obj, args
            )
        ),
        E.INSTRUCTION: (
            lambda code, instruction_offset: instruction_event_callback(
                tool_id, "instruction", code, instruction_offset
            )
        ),
        E.JUMP: (
            lambda code, instruction_offset, destination_offset: goto_event_callback(
                tool_id, "jump", code, instruction_offset, destination_offset
            )
        ),
        E.LINE: (
            lambda code, line_number: line_event_callback(tool_id, code, line_number)
        ),
        E.PY_RETURN: lambda code, instruction_offset, retval: leave_event_callback(
            tool_id, "return", code, instruction_offset, retval
        ),
        E.PY_START: lambda code, instruction_offset: start_event_callback(
            tool_id, code, instruction_offset
        ),
        # This is a global event
        # E.PY_UNWIND: lambda code, instruction_offset, retval: exception_event_callback(
        #     tool_id, "yield", code, instruction_offset, retval
        # ),
        E.PY_YIELD: lambda code, instruction_offset, retval: leave_event_callback(
            tool_id, "yield", code, instruction_offset, retval
        ),
        E.STOP_ITERATION: lambda code, instruction_offset, retval: exception_event_callback(
            tool_id, "stop iteration", code, instruction_offset, retval
        ),
    }


def start_local(
    tool_name: str,
    trace_callbacks: Optional[Dict[int, CodeType]] = None,
    tool_id: Optional[int] = None,
    frame: Optional[FrameType] = None,
    events_mask: Optional[int] = None,
    step_type: StepType = StepType.NO_STEPPING,
    step_granularity: Optional[StepGranularity] = None,
    ignore_filter: Optional[CodeType] = None,
) -> Tuple[int, int]:
    """Start local event tracing. If trace_callbacks is None, we will
    search for that and add it, if it's not already added.  If
    `events_mask` is None, the default, then no events are set.
    `ignore_filter` lists code objects and modules that should be ignored.
    """
    if frame is None:
        frame = sys._getframe(1)

    code = frame.f_code

    if events_mask is None:
        events_mask = 0

    if step_type == StepType.STEP_INTO:
        step_mask_granularity = (
            E.INSTRUCTION if step_granularity == StepGranularity.INSTRUCTION else E.LINE
        )
        events_mask |= (STEP_INTO_TRACKING | step_mask_granularity)

    FRAME_TRACKING[frame] = FrameInfo(
        step_type=step_type, step_granularity=step_granularity, calls_to=None
    )

    tool_id, event_mask = mstart(
        tool_name=tool_name,
        trace_callbacks=trace_callbacks,
        tool_id=tool_id,
        events_mask=events_mask,
        is_global=False,
        code=code,
        ignore_filter=ignore_filter,
    )
    return tool_id, event_mask


# Demo it
if __name__ == "__main__":

    import tracefilter
    # import sys_monitoring
    from sys_monitoring import mstop

    ignore_filter = tracefilter.TraceFilter([sys.monitoring, sys_monitoring])

    tool_name = "tracer.stepping"

    def foo(*args):
        print(
            f"\tinside foo: local {sys.monitoring.get_local_events(tool_id, bar.__code__)}"
        )
        print(f"\tinside foo: foo all (global) {sys.monitoring.get_events(tool_id)}")
        print(f"\tinside foo: called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    tool_id, events_mask = mstart(tool_name, tool_id=1)
    callback_hooks = set_callback_hooks_for_toolid(tool_id)

    print(f"tool_id is {tool_id}, events_mask is {events_mask}")

    print("\nUSING START_LOCAL with LINE EVENTS and step over")
    print("=" * 50)
    start_local(
        tool_name,
        callback_hooks,
        tool_id,
        events_mask=E.LINE,
        step_type=StepType.STEP_OVER,
        step_granularity=StepGranularity.LINE_NUMBER,
        ignore_filter=ignore_filter,
    )
    x = 1
    bar()
    mstop(tool_name)

    # Do this again using start_local
    print("\nUSING START_LOCAL LINE EVENTS and step into")
    print("=" * 50)

    start_local(
        tool_name,
        callback_hooks,
        tool_id,
        events_mask=E.LINE,
        step_type=StepType.STEP_INTO,
        step_granularity=StepGranularity.LINE_NUMBER,
        ignore_filter=ignore_filter,
    )
    x = 2
    bar()
    mstop(tool_name)

    print("\nUSING START_LOCAL WITH INSTRUCTION only")
    print("=" * 50)
    start_local(
        tool_name,
        callback_hooks,
        tool_id,
        events_mask=E.INSTRUCTION,
        step_type=StepType.STEP_INTO,
        step_granularity=StepGranularity.INSTRUCTION,
        ignore_filter=ignore_filter,
    )
    bar()
    mstop(tool_name)

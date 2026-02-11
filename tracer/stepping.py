"""
Debugger-like "step into", "step over" and "finish" support.
"""

import sys
from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Dict, List, Tuple, Union

E = sys.monitoring.events

# Events that are not allowed in sys.monitoring.set_local_events
GLOBAL_EVENTS = E.C_RAISE | E.C_RETURN | E.PY_UNWIND | E.RAISE


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

# Maps thread_id, tool_id, code to a list of breakpoint locations.
CODE_TRACKING: Dict[Tuple[int, int, CodeType], List[Location]] = {}


FRAME_TRACKING: Dict[FrameType, StepType] = {}

# CODE2EVENTS: Dict[(int, int, CodeType), ]

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


def set_step_into(tool_id: int, frame: FrameType, event_set: int):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It always adds a CALL event to the.
    local events to be tracked.
    """

    # Clear global events that are illegal for `set_local_events()`.
    event_set &= ~GLOBAL_EVENTS

    combined_event_set = (STEP_OUT_EVENTS | event_set) | E.CALL

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = StepType.STEP_INTO

    code = frame.f_code
    sys.monitoring.set_local_events(tool_id, code, combined_event_set)


def set_step_over(tool_id: int, frame: FrameType, event_set: int):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It should *not* contain CALL.
    This will be masked out.
    """
    # Clear global events that are illegal for `set_local_events()`.
    event_set &= ~GLOBAL_EVENTS

    combined_event_set = (STEP_OUT_EVENTS | event_set) & ~E.CALL

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = StepType.STEP_OVER

    code = frame.f_code
    sys.monitoring.set_local_events(tool_id, code, combined_event_set)


def set_step_out(tool_id: int, frame: FrameType):

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = StepType.STEP_OUT

    code = frame.f_code
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

    # Below: 0 is us; 1 is our lambda, and 2 is the user code.
    frame = sys._getframe(2)
    if frame.f_code != code:
        print("Woah -- code vs frame code mismatch in line event")

    # print(f"XXX FRAME: f_trace: {frame.f_trace}, f_trace_lines: {frame.f_trace_lines}, f_trace_opcodes: {frame.f_trace_opcodes}")

    if (step_type := FRAME_TRACKING.get(frame, None)) is None:
        # print(f"XXX first time for {frame}")
        step_type = StepType.STEP_OVER
        if (prev_frame := frame.f_back) is not None:
            step_type = FRAME_TRACKING.get(prev_frame, StepType.STEP_OVER)
            FRAME_TRACKING[frame] = step_type
        else:
            print("Can't find frame")

    print(
        f"\nLINE: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) {step_type} code:"
        f"\n\t{code_short(code)}, line: {line_number}"
    )

    ### end code inside hook.

    return line_event_handler_return(tool_id, code, events_mask)


def line_event_handler_return(tool_id: int, code: CodeType, events_mask: int) -> object:
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
    """A call event callback trace function"""
    # if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
    #     return sys.monitoring.DISABLE

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set:
    # * events_mask
    # * frame
    # * step_type

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # Below: 0 is us; 1 is our lambda, and 2 is the user code.
    frame = sys._getframe(2)
    if frame.f_code != code:
        print("Woah -- code vs frame code mismatch in line event")

    step_type = FRAME_TRACKING.get(frame, StepType.STEP_OVER)

    print(
        (
            f"\n{event.upper()}: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) {step_type} code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset} call: {callable_obj}, args: {args}"
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


def instruction_event_callback(
    tool_id: int,
    event: str,
    code: CodeType,
    instruction_offset: int,
) -> object:
    """A call event callback trace function"""

    ### This is the code that gets run inside the hook, e.g. a debugger REPL.
    ### The code inside the hook should set `events_mask`.

    # For testing, we don't want to change events_mask. Just note it.
    events_mask = sys.monitoring.get_local_events(tool_id, code)

    # # Below: 0 is us; 1 is our lambda, and 2 is the user code.
    # frame = sys._getframe(2)
    # print(f"XXX FRAME: f_trace: {frame.f_trace}, f_trace_lines: {frame.f_trace_lines}, f_trace_opcodes: {frame.f_trace_opcodes}")

    print(
        (
            f"\n{event.upper()}: tool id: {tool_id}, {bin(events_mask)} ({events_mask}) code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset}"
        )
    )

    ### end code inside hook; `events_mask` should be set.

    return instruction_event_handler_return(tool_id, code, events_mask)


def instruction_event_handler_return(
    tool_id: int, code: CodeType, events_mask: int
) -> object:
    """Returning from a call event trace function"""
    # Set local events based on step type and breakpoints.
    sys.monitoring.set_local_events(tool_id, code, events_mask)
    return


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

    return leave_event_handler_return(tool_id, frame)


def leave_event_handler_return(tool_id: int, frame: FrameType) -> object:
    """Returning from a RETURN, YIELD, or PY_UNWIND event handler"""
    # Remove Set local events based on step type and breakpoints.
    if frame in FRAME_TRACKING:
        # print("WOOT - Deleting frame")
        del FRAME_TRACKING[frame]

        code = frame.f_code
        # TODO: Check we have breakpoints in code,
        have_breakpoints = True
        if have_breakpoints:
            sys.monitoring.set_local_events(tool_id, code, 0)
    #
    return


def set_callback_hooks_for_toolid(tool_id: int) -> dict:
    return {
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
        E.LINE: (
            lambda code, line_number: line_event_callback(tool_id, code, line_number)
        ),
        E.PY_RETURN: lambda code, instruction_offset, retval: leave_event_callback(
            tool_id, "return", code, instruction_offset, retval
        ),
        E.PY_UNWIND: lambda code, instruction_offset, retval: exception_event_callback(
            tool_id, "yield", code, instruction_offset, retval
        ),
        E.PY_YIELD: lambda code, instruction_offset, retval: leave_event_callback(
            tool_id, "yield", code, instruction_offset, retval
        ),
        E.STOP_ITERATION: lambda code, instruction_offset, retval: exception_event_callback(
            tool_id, "stop iteration", code, instruction_offset, retval
        ),
    }


# Demo it
if __name__ == "__main__":

    import tracefilter
    # import sys_monitoring
    from sys_monitoring import mstart, mstop, start_local

    ignore_filter = tracefilter.TraceFilter([sys.monitoring])

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

    print("\nUSING START_LOCAL with LINE EVENTS, default step over")
    print("=" * 50)
    start_local(
        tool_name,
        callback_hooks,
        tool_id,
        code=bar.__code__,
        events_set=E.LINE,
        ignore_filter=ignore_filter,
    )
    x = 1
    bar()
    mstop(tool_name)

    # Do this again using start_local
    print("\nUSING START_LOCAL (all events)")
    print("=" * 50)

    start_local(tool_name, code=bar.__code__)
    bar()
    mstop(tool_name)

    # Do this again start with inc
    print("\nUSING START_LOCAL WITH INSTRUCTION only")
    print("=" * 50)
    start_local(tool_name, code=bar.__code__, events_set=E.INSTRUCTION)
    bar()
    mstop(tool_name)

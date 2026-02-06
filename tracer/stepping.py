"""
Debugger-like "step into", "step over" and "finish" support.
"""

import sys
from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Dict, List, Tuple, Union

E = sys.monitoring.events

LOCAL_EVENTS = (
    E.PY_START
    | E.BRANCH_LEFT
    | E.BRANCH_RIGHT
    | E.CALL
    | E.INSTRUCTION
    | E.JUMP
    | E.LINE
    | E.PY_RESUME
    | E.PY_RETURN
    | E.PY_YIELD
    | E.STOP_ITERATION
)


class StepType(Enum):
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


@dataclass
class FrameTracking:
    """
    Information about the current frame with regards to monitoring.
    We use this to support "step in", "step over" and "step out".
    """

    # event_mask is gets set into this mask for this frame.  The
    # caller should factor in whether there are breakpoints in the
    # code.  If there are breakpoints, events will change depending on
    # whether the breakpoint location is on a line, or an instruction.
    # Also, frame status figure into the local mask: whether we are
    # stepping, in, over, or out.
    local_event_mask: int

    # status: "in", "over" or, "out"
    status: StepType

    # Should we include breakpoints and test here?


FRAME_TRACKING: Dict[FrameType, FrameTracking] = {}

# CODE2EVENTS: Dict[(int, int, CodeType), ]

# Event mask that should be use to callback on
# finish or return from function, method or module.
STEP_OUT_EVENTS = E.PY_YIELD | E.PY_RETURN | E.RAISE | E.C_RETURN | E.PY_UNWIND

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


def set_step_into(tool_id: int, code: CodeType, event_set: int):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It always adds a CALL event to the.
    local events to be tracked.
    """
    combined_event_set = (STEP_OUT_EVENTS | event_set) | E.CALL
    sys.monitoring.set_local_events(tool_id, code, combined_event_set)


def set_step_over(tool_id: int, code: CodeType, event_set: int):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It should *not* contain CALL.
    This will be masked out.
    """
    combined_event_set = (STEP_OUT_EVENTS | event_set) & ~E.CALL
    sys.monitoring.set_local_events(tool_id, code, combined_event_set)


def set_step_out(tool_id: int, code: CodeType):
    # event_bitmask = sys.montoring.get_events(tool_id)
    sys.monitoring.set_local_events(STEP_OUT_EVENTS, code)

def code_short(code: CodeType) -> str:
    import os.path as osp

    return f"{code.co_name} in {osp.basename(code.co_filename)}"

# ignore_filter = tracefilter.TraceFilter([sys_monitoring, sys.monitoring])

def line_event_callback(tool_id: int, code: CodeType, line_number: int) -> object:
    """A line event callback trace function"""

    # if ignore_filter.is_excluded(code):
    #    return sys.monitoring.DISABLE

    print(f"\nEVENT: line, code:\n\t{code_short(code)}, line: {line_number}")
    return line_event_handler_return(
        code, StepType.STEP_INTO, StepGranularity.LINE_NUMBER
    )

def line_event_handler_return(
    code: CodeType, step_type: StepType, granularity: StepGranularity
) -> object:
    """A line event callback trace function"""
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

    print(
        (
            f"\nEVENT: {event}, tool id: {tool_id}, code:\n\t"
            f"{code_short(code)}, offset: *{instruction_offset} call: {callable_obj}"
        )
    )
    return call_event_handler_return(code, StepType.STEP_INTO)
    return

def call_event_handler_return(code: CodeType, step_type: StepType) -> object:
    """Returning from a call event handler"""
    # Set local events based on step type and breakpoints.
    return

def leave_event_callback(
        tool_id: int, event: str, code: CodeType, instruction_offset: int, retval: object
):
    """A Return and Yield event callback trace function"""
    print(
        f"\nEVENT: {event}, tool_id: {tool_id} code:\n\t"
        f"{code_short(code)}, offset: *{instruction_offset}\nreturn value: {retval}"
    )
    return leave_event_handler_return(
        code, StepType.STEP_INTO, StepGranularity.LINE_NUMBER
    )

def leave_event_handler_return(
    code: CodeType, step_type: StepType, granularity: StepGranularity.LINE_NUMBER
) -> object:
    """Returning from a return or yield event handler"""
    # Set local events based on step type and breakpoints.
    return

callback_hooks = {
    E.CALL: (
        lambda code, instruction_offset, callable_obj, args: call_event_callback(
            tool_id, "call", code, instruction_offset, callable_obj, args
        )
    ),
    E.LINE: (
        lambda code, line_number: line_event_callback(
            tool_id, code, line_number
        )
    ),
    E.PY_RETURN: lambda code, instruction_offset, retval: leave_event_callback(
        tool_id, "return", code, instruction_offset, retval
    ),
    E.PY_YIELD: lambda code, instruction_offset, retval: leave_event_callback(
        tool_id, "yield", code, instruction_offset, retval
    ),
}



# Demo it
if __name__ == "__main__":

    # import tracefilter
    # import sys_monitoring
    from sys_monitoring import mstart, start_local, mstop

    hook_name = "tracer.stepping"

    def foo(*args):
        print(
            f"XXX2 foo local {sys.monitoring.get_local_events(tool_id, bar.__code__)}"
        )
        print(f"XXX3 foo all (global) {sys.monitoring.get_events(tool_id)}")
        print(f"foo called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    tool_id, events_mask = mstart(hook_name, tool_id=1)
    print(f"tool_id is {tool_id}, events_mask is {events_mask}")


    start_local(hook_name, callback_hooks, E.LINE, code=bar.__code__)
    x = 1
    bar()
    mstop(hook_name)
    print("=" * 40)
    # mstart(hook_name)
    # bar()
    # mstop(hook_name)
    # print("=" * 40)

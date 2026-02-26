"""
Debugger-like "step into", "step over" and "finish" support.
"""

import sys
from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Callable, Dict, Optional, Tuple

from tracer.sys_monitoring import EVENT2STR, E, mstart

# Events that are not allowed in sys.monitoring.set_local_events
GLOBAL_EVENTS = E.C_RAISE | E.C_RETURN | E.PY_UNWIND | E.RAISE
STEP_INTO_TRACKING = E.CALL | E.PY_START | E.PY_RETURN

# Mask to use for "step out". Use with & ^(INSTRUCTION_LIKE_EVENTS)
INSTRUCTION_LIKE_EVENTS = (
    E.LINE | E.INSTRUCTION | E.JUMP | E.BRANCH_LEFT | E.BRANCH_RIGHT | E.STOP_ITERATION
)


class StepType(Enum):
    NO_STEPPING = "no stepping"
    STEP_INTO = "step into"
    STEP_OUT = "step out"
    STEP_OVER = "step over"


class StepGranularity(Enum):
    INSTRUCTION = "instruction"
    LINE_NUMBER = "line number"
    # Is there stuff like "RESUME" or at "safe" points


@dataclass
class FrameInfo:
    step_type: StepType = StepType.NO_STEPPING
    step_granularity: Optional[StepGranularity] = None
    local_events_mask: int = 0
    calls_to: Optional[FrameType | CodeType] = None


FRAME_TRACKING: Dict[FrameType, FrameInfo] = {}


# Event mask that should be use to callback on
# finish or return from function, method or module.
# Note: we cannot include global events, specifically
# those in GLOBAL_EVENTS since that is illegal for set_local_events().
STEP_OUT_EVENTS = E.PY_YIELD | E.PY_RETURN

# Event mask that should be use to callback on
# line stepping. This should
STEP_OVER_EVENTS = STEP_OUT_EVENTS


def clear_stale_frames(tool_id: int, frame: FrameInfo):
    while frame is not None:
        frame_info = FRAME_TRACKING.get(frame)
        if frame_info is None:
            return
        calls_to_frame = frame_info.calls_to
        if calls_to_frame is None:
            return
        code = calls_to_frame.f_code
        # FIXME: reinstate the above. code_info is somehow come out as a code type.
        # if (((code_info := CODE_TRACKING.get(tool_id, code)) is None) or
        #     len(code_info.breakpoints) == 0):
        #     print("XXX3")
        #     events_mask = sys.monitoring.get_local_events(tool_id, code)
        #     events_mask &= ~(INSTRUCTION_LIKE_EVENTS)
        #     sys.monitoring.set_local_events(tool_id, code, events_mask)
        events_mask = sys.monitoring.get_local_events(tool_id, code)
        events_mask &= ~(INSTRUCTION_LIKE_EVENTS)
        events_mask &= ~E.LINE
        sys.monitoring.set_local_events(tool_id, code, events_mask)
        del FRAME_TRACKING[frame]
        frame = calls_to_frame


def refresh_code_mask(tool_id: int, frame: FrameInfo) -> Tuple[int, int]:
    """Refresh the local_events_mask recording in sys.montoring for
    the code object found in `frame` to the value found via FrameInfo.

    Why do we need to do this?

    If the code in `frame`  was involved in a recursive call or another thread,
    it is possible that the local events for that code got changed.
    So be sure to set the local event mask back to what it was,
    saved in FRAME_TRACKING at the time of the call.
    """
    code = frame.f_code
    new_events_mask = events_mask = sys.monitoring.get_local_events(tool_id, code)

    if (
        frame_info := FRAME_TRACKING.get(frame)
    ) and events_mask != frame_info.local_events_mask:
        print(
            f"WOOT local events mask changed from {bin(events_mask)} ({events_mask})"
            f" to {bin(frame_info.local_events_mask)} ({frame_info.local_events_mask})"
        )
        sys.monitoring.set_local_events(
            tool_id, frame.f_code, frame_info.local_events_mask
        )
        new_events_mask = frame_info.local_events_mask

    return events_mask, new_events_mask


def code_short(code: CodeType) -> str:
    import os.path as osp

    return f"{code.co_name} in {osp.basename(code.co_filename)}"


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


def set_step_into(
    tool_id: int,
    frame: FrameType,
    granularity: StepGranularity,
    events_mask: int,
    callbacks: Dict[int, Callable],
):
    """
    Set local callback for a `step over` in `code`.
    `event_set` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It always adds a CALL event to the.
    local events to be tracked.
    """

    # Clear global events that are illegal for `set_local_events()`.
    # Note that all "~" operations should be done before any "|" operations.
    events_mask &= ~GLOBAL_EVENTS

    combined_events_mask = STEP_OUT_EVENTS | events_mask | E.CALL | E.PY_START


    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_INTO,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    code = frame.f_code

    sync_callbacks_with_mask(
        code, tool_id, combined_events_mask, callbacks
    )


def set_step_out(tool_id: int, frame: FrameType, callbacks: Dict[int, Callable]):
    """
    Set local callback for a `step out`.
    `events_mask` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It should *not* contain CALL.
    This will be masked out.
    """

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.

    code = frame.f_code

    # Note that all "~" operations should be done before any "|" operations.
    events_mask = sys.monitoring.get_local_events(tool_id, code) & ~(
        INSTRUCTION_LIKE_EVENTS
    )

    # THINK ABOUT: Do we really care about PY_START? Clear it anyway.
    # TODO: If we can be sure there is not stale code (stale frames) that were
    # skipped over by execptions, we don't need to trace into E.CALL to check for this.

    combined_events_mask = STEP_OUT_EVENTS | events_mask | E.CALL | E.PY_START

    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_OUT,
        step_granularity=None,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    code = frame.f_code

    sync_callbacks_with_mask(
        code, tool_id, combined_events_mask, callbacks
    )


def set_step_over(
    tool_id: int,
    frame: FrameType,
    granularity: StepGranularity,
    events_mask: int,
    callbacks: Dict[int, Callable],
):
    """
    Set local callback for a `step over`.
    `events_mask` should have an event mask for local events line or
    various local instruction-type events (INSTRUCTION, JUMP, BRANCH_LEVEL,
    BRANCH_RIGHT, or STOP_ITERATION). It should *not* contain CALL.
    This will be masked out.
    """

    # Clear global events that are illegal for `set_local_events()`.
    # Note that all "~" operations should be done before any "|" operations.
    events_mask &= ~GLOBAL_EVENTS

    combined_events_mask = STEP_OUT_EVENTS | events_mask | E.PY_START

    # Note step out is desired in FRAME_TRACKING so it can be
    # detected in the return portion of the callback handlers.
    FRAME_TRACKING[frame] = FrameInfo(
        step_type=StepType.STEP_OVER,
        step_granularity=None,
        local_events_mask=combined_events_mask,
        calls_to=None,
    )

    code = frame.f_code

    sync_callbacks_with_mask(
        code, tool_id, combined_events_mask, callbacks
    )


def start_local(
    tool_name: str,
    trace_callbacks: Optional[Dict[int, CodeType]] = None,
    tool_id: Optional[int] = None,
    frame: Optional[FrameType] = None,
    code: Optional[CodeType] = None,
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

    if code is None:
        code = frame.f_code

    if events_mask is None:
        events_mask = 0

    if step_type == StepType.STEP_INTO:
        step_mask_granularity = (
            E.INSTRUCTION if step_granularity == StepGranularity.INSTRUCTION else E.LINE
        )
        events_mask |= STEP_INTO_TRACKING | step_mask_granularity

    FRAME_TRACKING[frame] = FrameInfo(
        step_type=step_type,
        step_granularity=step_granularity,
        local_events_mask=events_mask,
        calls_to=None,
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


def sync_callbacks_with_mask(
    code: CodeType,
    tool_id: int,
    events_mask: int,
    callbacks: Dict[int, Callable],
):
    for event in (
        E.BRANCH_LEFT,
        E.BRANCH_RIGHT,
        E.CALL,
        E.INSTRUCTION,
        E.JUMP,
        E.LINE,
        E.STOP_ITERATION,
    ):
        if event & events_mask == 0:
            old_callback = sys.monitoring.register_callback(tool_id, event, None)
            if old_callback is not None:
                print(f"Cleared event {EVENT2STR[event]} with {old_callback}")
                pass
            pass
        elif (callback := callbacks.get(event)) is not None:
            # print(f"XXX registering event {EVENT2STR[event]} ({event}) with {callback}")
            old_callback = sys.monitoring.register_callback(tool_id, event, callback)
            if old_callback is not None and old_callback != callback:
                print(f"Woah - smashed event {EVENT2STR[event]} ({event}) {old_callback} with {callback}")
            pass
        else:
            print(f"Woah - should have found a callback for {EVENT2STR[event]}; clearing event")
            events_mask &= ~event

    sys.monitoring.set_local_events(tool_id, code, events_mask)

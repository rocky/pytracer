"""
The simplest of examples: stepping for line and instruction events for a single
basic block.
"""

import sys

from tracer.breakpoint import (Breakpoint, LineNumberValue, clear_breakpoint,
                               set_breakpoint)
from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_continue,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter

tool_name = "01-breakpoint_one-basic-block"
tool_id, events_mask = mstart(tool_name, tool_id=1)
assert tool_id is not None
callback_hooks = set_callback_hooks_for_toolid(tool_id)

brpkt = None
def stepping_one_basic_block(arg: int, tool_id: int, line_increment: int) -> int:
    # Be mindful of how adding/removing lines below changes
    # the breakpoint location
    global brkpt
    frame = sys._getframe(0)
    location = LineNumberValue(line_number=frame.f_lineno + line_increment)
    brkpt = Breakpoint(location, frame.f_code)
    set_breakpoint(tool_id, brkpt)
    set_step_continue(tool_id, frame, callback_hooks)
    print(f"XXX: breakpoint set at {location.line_number}")
    x = arg  # frame + 6
    y = x + arg # frame + 7
    return y


ignore_filter = TraceFilter([sys.monitoring, mstop])

# First step lines
print("BREAKPOINT FOR LINE EVENTS")
print("=" * 40)
start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)

# Should hit breakpoint set in function
stepping_one_basic_block(101, tool_id, 6)

# Clear the breakpoint set in the last call
print(f"XXX: breakpoint at {brkpt.location.line_number} clearned")
clear_breakpoint(tool_id, brkpt)

# Should hit breakpoint set in the function
# but not the one we just cleared.
stepping_one_basic_block(102, tool_id, 7)

# Should not find new breakpoint. But the one from the
# previous call should be hit.
stepping_one_basic_block(103, tool_id, 0)
mstop(tool_name)

# # Next, step instructions
# print("=" * 40)
# print("INSTRUCTION EVENTS ONLY")
# print("=" * 40)

# start_local(
#     tool_name,
#     callback_hooks,
#     events_mask=E.INSTRUCTION,
#     step_type=StepType.STEP_OVER,
#     step_granularity=StepGranularity.INSTRUCTION,
#     ignore_filter=ignore_filter,
# )
# stepping_one_basic_block(
#     2, granularity=StepGranularity.INSTRUCTION, events_mask=E.INSTRUCTION
# )
# mstop(tool_name)

# # Finally, step both instructions and lines

# print("=" * 40)
# print("INSTRUCTION AND LINE EVENTS")
# print("=" * 40)


# start_local(
#     tool_name,
#     callback_hooks,
#     events_mask=E.INSTRUCTION | E.LINE,
#     step_type=StepType.STEP_OVER,
#     step_granularity=StepGranularity.INSTRUCTION,
#     ignore_filter=ignore_filter,
# )
# stepping_one_basic_block(
#     3,
#     granularity=StepType.STEP_OVER,
#     events_mask=E.INSTRUCTION | E.LINE,
# )
# mstop(tool_name)

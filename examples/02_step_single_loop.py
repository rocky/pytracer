"""
Stepping for line and instruction events of a simple loop.
"""

import sys

from tracer.stepping import (StepGranularity, StepType,
                             set_callback_hooks_for_toolid, set_step_into,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop


def stepping_simple_loop(
    arg: int, events_mask: int, granularity: StepGranularity
) -> int:
    set_step_into(
        tool_id,
        frame=sys._getframe(0),
        granularity=granularity,
        events_mask=events_mask,
    )
    x = arg
    for i in range(2):
        x += arg
    return x


tool_name = "02-stepping-single-loop"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE,
    step_type=StepType.STEP_INTO,
)
stepping_simple_loop(1, E.LINE, StepGranularity.INSTRUCTION)
mstop(tool_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name, callback_hooks, events_mask=E.INSTRUCTION, step_type=StepType.STEP_INTO
)
stepping_simple_loop(1, E.INSTRUCTION | E.JUMP, StepGranularity.INSTRUCTION)
mstop(tool_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION | E.LINE | E.JUMP,
)
stepping_simple_loop(1, E.INSTRUCTION | E.LINE | E.JUMP, StepGranularity.INSTRUCTION)
mstop(tool_name)

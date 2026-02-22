"""
Stepping for line and instruction events of a simple loop.
"""

import sys

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_into,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def stepping_iter_loop(arg: int, events_mask: int, granularity: StepGranularity) -> int:
    set_step_into(
        tool_id, sys._getframe(0), granularity=granularity, events_mask=events_mask
    )
    x = arg
    for i in iter(range(2)):
        x += i
    return x


tool_name = "02-stepping-single-loop"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_into])

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE,
    step_type=StepType.STEP_INTO,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
stepping_iter_loop(1, E.LINE, StepGranularity.LINE_NUMBER)
mstop(tool_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION,
    step_type=StepType.STEP_INTO,
    step_granularity=StepGranularity.INSTRUCTION,
    ignore_filter=ignore_filter,
)
stepping_iter_loop(1, E.INSTRUCTION, StepGranularity.INSTRUCTION)
mstop(tool_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION | E.LINE,
    step_type=StepType.STEP_INTO,
    ignore_filter=ignore_filter,
)
stepping_iter_loop(1, E.INSTRUCTION | E.LINE, StepGranularity.INSTRUCTION)
mstop(tool_name)

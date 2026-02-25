"""
The simplest of examples: stepping for line and instruction events for a single
basic block.
"""

import sys

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_into,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter

tool_name = "00-stepping-one-basic-block"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

def stepping_one_basic_block(
    arg: int, granularity: StepGranularity, events_mask: int
) -> int:
    set_step_into(
        tool_id,
        frame=sys._getframe(0),
        granularity=granularity,
        events_mask=events_mask,
        callbacks=callback_hooks,
    )
    x = arg
    y = x + arg
    return y


ignore_filter = TraceFilter([sys.monitoring, mstop])


# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
stepping_one_basic_block(1, granularity=StepGranularity.LINE_NUMBER, events_mask=E.LINE)
mstop(tool_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.INSTRUCTION,
    ignore_filter=ignore_filter,
)
stepping_one_basic_block(
    2, granularity=StepGranularity.INSTRUCTION, events_mask=E.INSTRUCTION
)
mstop(tool_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION | E.LINE,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.INSTRUCTION,
    ignore_filter=ignore_filter,
)
stepping_one_basic_block(
    3,
    granularity=StepType.STEP_OVER,
    events_mask=E.INSTRUCTION | E.LINE,
)
mstop(tool_name)

"""
"Step out" for simple try/except block.
"""

import sys

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_out,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def step_try_except(arg: list, granularity: StepGranularity, events_mask: int) -> int:
    set_step_out(tool_id, sys._getframe(0))
    try:
        arg[1] += 1
    except Exception:
        return 5
    return 2


tool_name = "stepping-try-except"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_out])

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
step_try_except([], granularity=StepGranularity.LINE_NUMBER, events_mask=E.LINE)
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
step_try_except([], granularity=StepGranularity.INSTRUCTION, events_mask=E.INSTRUCTION)
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
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
step_try_except(
    [],
    granularity=StepGranularity.INSTRUCTION,
    events_mask=E.LINE | E.INSTRUCTION,
)
mstop(tool_name)

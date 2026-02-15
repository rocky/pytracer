"""
Stepping for line and instruction events basic block raising an exception,
and index error.
"""
import sys

from tracer.stepping import (StepGranularity, StepType,
                             set_callback_hooks_for_toolid, set_step_out,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def stepping_index_error(arg: list, event_mask: int) -> int:
    set_step_out(tool_id, sys._getframe(0), event_mask)
    y = arg[1]
    return y


tool_name = "stepping-into-index-error"
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
try:
    stepping_index_error([], E.LINE)
except Exception:
    pass
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
try:
    stepping_index_error([], E.INSTRUCTION | E.PY_RETURN)
except Exception:
    pass
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
    step_granularity=StepGranularity.INSTRUCTION,
    ignore_filter=ignore_filter,
)
try:
    stepping_index_error([], E.INSTRUCTION | E.LINE | E.PY_RETURN)
except Exception:
    pass
mstop(tool_name)

"""
Stepping for simple try/except block.
"""
import sys

from tracer.stepping import (StepGranularity, StepType,
                             set_callback_hooks_for_toolid, set_step_into,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop


def step_try_except(arg: list, event_mask: int) -> int:
    set_step_into(tool_id, sys._getframe(0), event_mask)
    try:
        arg[1] += 1
    except Exception:
        return 5
    return 2


tool_name = "stepping-try-except"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    code=step_try_except.__code__,
    events_mask=E.LINE,
)
step_try_except([], E.LINE)
mstop(tool_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION,
)
step_try_except([], E.INSTRUCTION)
mstop(tool_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    tool_name,
    callback_hooks,
    events_mask=E.INSTRUCTION | E.LINE,
)
step_try_except([], E.INSTRUCTION | E.LINE)
mstop(tool_name)

"""
Stepping for simple try/except block.
"""
import sys

from tracer.stepping import set_callback_hooks_for_toolid, set_step_into
from tracer.sys_monitoring import E, mstart, mstop, start_local


def stepping_try_except(arg: list, event_mask: int) -> int:
    set_step_into(tool_id, sys._getframe(0), event_mask)
    try:
        arg[1] += 1
    except Exception:
        return 5
    return 2


hook_name = "stepping-try-except"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_try_except.__code__,
    events_set=E.LINE,
)
stepping_try_except([], E.LINE)
mstop(hook_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_try_except.__code__,
    events_set=E.INSTRUCTION,
)
stepping_try_except([], E.INSTRUCTION)
mstop(hook_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    hook_name,
    callback_hooks,
    code=stepping_try_except.__code__,
    events_set=E.INSTRUCTION | E.LINE,
)
stepping_try_except([], E.INSTRUCTION | E.LINE)
mstop(hook_name)

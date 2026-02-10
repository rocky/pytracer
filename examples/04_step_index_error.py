"""
Stepping for line and instruction events basic block raising an exception,
and index error.
"""
import sys

from tracer.stepping import set_callback_hooks_for_toolid, set_step_into
from tracer.sys_monitoring import E, mstart, mstop, start_local


def stepping_index_error(arg: list, event_mask: int) -> int:
    set_step_into(tool_id, sys._getframe(0), event_mask)
    y = arg[1]
    return y


hook_name = "stepping-into-index-error"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_index_error.__code__,
    events_set=E.LINE,
)
try:
    stepping_index_error([], E.LINE)
except Exception:
    pass
mstop(hook_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_index_error.__code__,
    events_set=E.INSTRUCTION,
)
try:
    stepping_index_error([], E.INSTRUCTION)
except Exception:
    pass
mstop(hook_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    hook_name,
    callback_hooks,
    code=stepping_index_error.__code__,
    events_set=E.INSTRUCTION | E.LINE,
)
try:
    stepping_index_error([], E.INSTRUCTION | E.LINE)
except Exception:
    pass
mstop(hook_name)

"""
Stepping for line and instruction events of a simple loop.
"""
import sys

from tracer.stepping import set_callback_hooks_for_toolid, set_step_into
from tracer.sys_monitoring import E, mstart, mstop, start_local


def stepping_iter_loop(arg: int, event_mask: int) -> int:
    set_step_into(tool_id, sys._getframe(0), event_mask)
    x = arg
    for i in iter(range(2)):
        x += i
    return x


hook_name = "02-stepping-single-loop"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_iter_loop.__code__,
    events_set=E.LINE | E.STOP_ITERATION,
)
stepping_iter_loop(1, E.LINE | E.STOP_ITERATION)
mstop(hook_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_iter_loop.__code__,
    events_set=E.INSTRUCTION,
)
stepping_iter_loop(1, E.INSTRUCTION | E.STOP_ITERATION)
mstop(hook_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    hook_name,
    callback_hooks,
    code=stepping_iter_loop.__code__,
    events_set=E.INSTRUCTION | E.LINE,
)
stepping_iter_loop(1, E.INSTRUCTION | E.LINE)
mstop(hook_name)

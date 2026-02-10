"""
Stepping for line and instruction events of a simple loop.
"""

from tracer.stepping import set_callback_hooks_for_toolid, set_step_into
from tracer.sys_monitoring import E, mstart, mstop, start_local


def stepping_simple_loop(arg: int, event_mask: int) -> int:
    set_step_into(tool_id, stepping_simple_loop.__code__, event_mask)
    x = arg
    for i in range(2):
        x += arg
    return x


hook_name = "stepping-one-basic-block"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_simple_loop.__code__,
    events_set=E.LINE,
)
stepping_simple_loop(1, E.LINE)
mstop(hook_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_simple_loop.__code__,
    events_set=E.INSTRUCTION,
)
stepping_simple_loop(1, E.INSTRUCTION)
mstop(hook_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    hook_name,
    callback_hooks,
    code=stepping_simple_loop.__code__,
    events_set=E.INSTRUCTION | E.LINE,
)
stepping_simple_loop(1, E.INSTRUCTION | E.LINE)
mstop(hook_name)

"""
The simplest of examples: stepping for line and instruction events for a single
basic block.
"""

from tracer.stepping import set_callback_hooks_for_toolid, set_step_into
from tracer.sys_monitoring import E, mstart, mstop, start_local


def stepping_one_basic_block(arg: int, event_mask: int) -> int:
    set_step_into(tool_id, stepping_one_basic_block.__code__, event_mask)
    x = arg
    y = x + arg
    return y


hook_name = "stepping-one-basic-block"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First step lines
print("LINE EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_one_basic_block.__code__,
    events_set=E.LINE,
)
stepping_one_basic_block(1, E.LINE)
mstop(hook_name)

# Next, step instructions
print("=" * 40)
print("INSTRUCTION EVENTS ONLY")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=stepping_one_basic_block.__code__,
    events_set=E.INSTRUCTION,
)
stepping_one_basic_block(1, E.INSTRUCTION)
mstop(hook_name)

# Finally, step both instructions and lines

print("=" * 40)
print("INSTRUCTION AND LINE EVENTS")
print("=" * 40)


start_local(
    hook_name,
    callback_hooks,
    code=stepping_one_basic_block.__code__,
    events_set=E.INSTRUCTION | E.LINE,
)
stepping_one_basic_block(1, E.INSTRUCTION | E.LINE)
mstop(hook_name)

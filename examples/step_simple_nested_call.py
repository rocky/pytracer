"""
Stepping for a somple nested call.
"""

from typing import Callable

from tracer.stepping import (set_callback_hooks_for_toolid, set_step_into,
                             set_step_over)
from tracer.sys_monitoring import E, mstart, mstop, start_local


def nested_function(x: list) -> list:
    return x


def stepping_simple_nested_call(step_fn: Callable) -> int:
    step_fn()
    x = nested_function([1, 2, 3])
    return x


hook_name = "stepping-simple-nested-call"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First, step try step into
print("STEP INTO NESTED FUNCTION")
print("=" * 40)

step_fn = lambda: set_step_into(
    tool_id, stepping_simple_nested_call.__code__, E.LINE
)  # noqa

start_local(
    hook_name,
    callback_hooks,
    code=stepping_simple_nested_call.__code__,
    events_set=E.LINE,
)
stepping_simple_nested_call(step_fn)
mstop(hook_name)

# Next, try step over
print("=" * 40)
print("STEP OVER NESTED FUNCTION")
print("=" * 40)

step_fn = lambda: set_step_over(
    tool_id, stepping_simple_nested_call.__code__, E.LINE
)  # noqa

start_local(
    hook_name,
    callback_hooks,
    code=stepping_simple_nested_call.__code__,
    events_set=E.LINE,
)
stepping_simple_nested_call(step_fn)
mstop(hook_name)

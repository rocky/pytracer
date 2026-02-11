"""
Stepping with a call which raises an exception
"""
import sys

from tracer.stepping import (set_callback_hooks_for_toolid, set_step_into,
                             set_step_over)
from tracer.sys_monitoring import E, mstart, mstop, start_local


def nested_function(x: list) -> list:
    # Raises an IndexError
    return x[100]


def step_into_simple_nested_call(x: list) -> int:
    set_step_into(tool_id, sys._getframe(0), E.LINE | E.PY_RETURN | E.PY_UNWIND)
    try:
        x = nested_function([1, 2, 3])
    except IndexError:
        pass
    try:
        return nested_function([4, 5, 6])
    except IndexError:
        return x


def step_over_simple_nested_call(x: list) -> int:
    set_step_over(tool_id, sys._getframe(0), E.LINE | E.PY_RETURN)
    try:
        x = nested_function([7, 8, 9])
    except IndexError:
        pass
    try:
        return nested_function([10, 11, 12])
    except IndexError:
        return x


hook_name = "10-step-call-raising-exception"
tool_id, events_mask = mstart(hook_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First, step try step into
print("STEP INTO NESTED FUNCTION")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=step_into_simple_nested_call.__code__,
    events_set=E.CALL | E.LINE | E.PY_RETURN
)
step_into_simple_nested_call(5)
mstop(hook_name)

# Next, try step over
print("=" * 40)
print("STEP OVER NESTED FUNCTION")
print("=" * 40)

start_local(
    hook_name,
    callback_hooks,
    code=step_over_simple_nested_call.__code__,
    events_set=E.LINE,
)
step_over_simple_nested_call(6)
mstop(hook_name)

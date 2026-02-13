"""
Stepping for a simple nested call involving a generator
"""
import sys

from tracer.stepping import (StepGranularity, StepType,
                             set_callback_hooks_for_toolid, set_step_into,
                             set_step_over, start_local)
from tracer.sys_monitoring import E, mstart, mstop


def nested_function() -> int:
    yield 1
    yield 2


def step_into_simple_nested_call(x: int) -> int:
    set_step_into(tool_id, sys._getframe(0), E.LINE | E.PY_RETURN | E.PY_YIELD)
    for i in nested_function():
        x += i
    return x

def step_over_simple_nested_call(x: list) -> int:
    set_step_over(tool_id, sys._getframe(0), E.LINE | E.PY_RETURN | E.PY_YIELD)
    for i in nested_function():
        x += i
    return x


tool_name = "09-step-simple-generator"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)

# First, step try step into
print("STEP INTO NESTED FUNCTION")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.CALL | E.LINE | E.PY_RETURN | E.PY_YIELD
)
step_into_simple_nested_call(5)
mstop(tool_name)

# Next, try step over
print("=" * 40)
print("STEP OVER NESTED FUNCTION")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE,
)
step_over_simple_nested_call(6)
mstop(tool_name)

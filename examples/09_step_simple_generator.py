"""
Stepping for a simple nested call involving a generator
"""

import sys

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_into,
                             set_step_over, start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def nested_function() -> int:
    yield 1
    x = 1
    yield x


def step_into_simple_nested_call(x: int) -> int:
    set_step_into(tool_id, sys._getframe(0), StepGranularity.LINE_NUMBER, E.LINE)
    for i in nested_function():
        x += i
    return x


def step_over_simple_nested_call(x: list) -> int:
    set_step_over(tool_id, sys._getframe(0), StepGranularity.LINE_NUMBER, E.LINE)
    for i in nested_function():
        x += i
    return x


tool_name = "09-step-simple-generator"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_into, set_step_over])

# First, step try step into
print("STEP INTO NESTED FUNCTION")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_INTO,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
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
    events_mask=E.LINE | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
step_over_simple_nested_call(6)
mstop(tool_name)

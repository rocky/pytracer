"""
Stepping with a call which raises an exception
"""

import sys

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_into,
                             set_step_over, start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def double_nested_function(x: list) -> list:
    # Raises an IndexError
    return x[100]


def nested_function(x: list) -> list:
    return double_nested_function(x)


tool_name = "12-double-call-with-exception"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_into, set_step_over])


def step_into_nested_call(x: list) -> int:
    set_step_into(
        tool_id,
        sys._getframe(0),
        StepGranularity.LINE_NUMBER,
        E.LINE,
        callbacks=callback_hooks,
    )
    try:
        return nested_function([1, 2, 3])
    except IndexError:
        return 4


def step_over_nested_call(x: list) -> int:
    set_step_over(
        tool_id,
        sys._getframe(0),
        StepGranularity.LINE_NUMBER,
        E.LINE,
        callbacks=callback_hooks,
    )
    try:
        return nested_function([7, 8, 9])
    except IndexError:
        return 5


# First, step try step into
print("STEP INTO NESTED FUNCTION")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE | E.CALL | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_INTO,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
step_into_nested_call([1, 2, 3])
mstop(tool_name)

# Next, try step over
print("=" * 40)
print("STEP OVER NESTED FUNCTION")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE | E.CALL | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
step_over_nested_call([4, 5, 6])
mstop(tool_name)

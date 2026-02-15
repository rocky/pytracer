"""
Trace stepping over a long import.
"""
import sys
import timeit

from tracer.stepping import (StepGranularity, StepType,
                             set_callback_hooks_for_toolid, set_step_into,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def step_over_long_import():
    set_step_into(tool_id, sys._getframe(0), StepGranularity.LINE_NUMBER, E.LINE)
    import mathics
    print(len(dir(mathics)))


tool_name = "12-step-into-long_import"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_into])

# First, step try step into
print("STEP INTO LONG IMPORT")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE | E.CALL | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_INTO,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
execution_time=timeit.timeit(step_over_long_import, number=1)
mstop(tool_name)
print(f"Execution time: {execution_time} seconds")

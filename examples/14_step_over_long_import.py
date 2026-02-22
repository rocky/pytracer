"""
Trace stepping over a long import.
"""

import sys
import timeit

from tracer.callbacks import set_callback_hooks_for_toolid
from tracer.stepping import (StepGranularity, StepType, set_step_over,
                             start_local)
from tracer.sys_monitoring import E, mstart, mstop
from tracer.tracefilter import TraceFilter


def step_over_long_import():
    set_step_over(tool_id, sys._getframe(0), StepGranularity.LINE_NUMBER, E.LINE)
    import numpy as n

    print(len(dir(n)))


tool_name = "14-step-over-long_import"
tool_id, events_mask = mstart(tool_name, tool_id=1)
callback_hooks = set_callback_hooks_for_toolid(tool_id)
ignore_filter = TraceFilter([sys.monitoring, mstop, set_step_over])

# First, step try step into
print("STEP OVER LONG IMPORT")
print("=" * 40)

start_local(
    tool_name,
    callback_hooks,
    events_mask=E.LINE | E.CALL | E.PY_RETURN | E.PY_START,
    step_type=StepType.STEP_OVER,
    step_granularity=StepGranularity.LINE_NUMBER,
    ignore_filter=ignore_filter,
)
execution_time = timeit.timeit(step_over_long_import, number=1)
mstop(tool_name)
print(f"Execution time: {execution_time} seconds")

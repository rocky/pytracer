"""
Debugger-like "step into", "step over" and "finish" support.
"""
import sys
from types import CodeType

E = sys.monitoring.events

LOCAL_EVENTS = (
    E.PY_START |
    E.PY_RESUME |
    E.PY_RETURN |
    E.PY_YIELD |
    E.CALL |
    E.LINE |
    E.INSTRUCTION |
    E.JUMP |
    E.BRANCH_LEFT |
    E.BRANCH_RIGHT |
    E.STOP_ITERATION
)

# Event mask that should be use to callback on
# finish or return from function, method or module.
FINISH_EVENTS = E.PY_YIELD | E.PY_RETURN | E.RAISE | E.C_RETURN | E.PY_UNWIND

# Event mask that should be use to callback on
# line stepping.
STEP_OVER_EVENTS = E.LINE | FINISH_EVENTS

# Event mask that should be use to callback on
# "step into" line stepping.
STEP_INTO_EVENTS = STEP_OVER_EVENTS | E.CALL | E.PY_RESUME | E.PY_THROW

DISABLE_ALL_EVENTS = 0

def set_step_into(tool_id: int):
    # event_bitmask = sys.montoring.get_events(tool_id)
    return


def set_step_over(tool_id: int, code: CodeType):
    sys.monitoring.set_local_events(STEP_OVER_EVENTS, code)


def set_finish_mask(tool_id: int, code: CodeType):
    # event_bitmask = sys.montoring.get_events(tool_id)
    sys.monitoring.set_local_events(FINISH_EVENTS, code)


# Demo it
if __name__ == "__main__":

    import tracefilter
    import sys_monitoring
    from sys_monitoring import start, stop

    hook_name = "tracer.stepping"

    def code_short(code: CodeType) -> str:
        import os.path as osp

        return f"{code.co_name} in {osp.basename(code.co_filename)}"

    ignore_filter = tracefilter.TraceFilter([sys_monitoring, sys.monitoring])

    def line_event_callback(code, line_number):
        """A line event callback trace function"""

        if ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(f"line event: code: {code_short(code)}, line: {line_number}")

    def call_event_callback(code, instruction_offset, callable_obj, args):
        """A call event callback trace function"""
        if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(
            f"call event: code: {code_short(code)}, offset: *{instruction_offset} call: {callable_obj}"
        )
        return sys.monitoring.DISABLE

    def foo(*args):
        print(f"XXX2 foo local {sys.monitoring.get_local_events(tool_id, bar.__code__)}")
        print(f"XXX3 foo all (global) {sys.monitoring.get_events(tool_id)}")
        print(f"foo called with {args}")

    def bar():
        print(f"XXX0 bar local {sys.monitoring.get_local_events(tool_id, bar.__code__)}")
        print(f"XXX1 bar all (global) {sys.monitoring.get_events(tool_id)}")
        foo("foo")
        foo("bar")

    tool_id = start(hook_name, tool_id=1)
    print(f"tool_id is {tool_id}")

    callback_hooks = {
        E.CALL: call_event_callback,
        E.LINE: line_event_callback,
    }

    start(hook_name, callback_hooks, STEP_INTO_EVENTS)
    bar()
    stop(hook_name)
    print("=" * 40)
    start(hook_name)
    sys.monitoring.set_local_events(tool_id, bar.__code__, DISABLE_ALL_EVENTS)
    bar()
    stop(hook_name)
    print("=" * 40)

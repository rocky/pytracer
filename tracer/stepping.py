"""
Debugger-like "step into", "step over" and "finish" support.
"""

import sys
from collections import namedtuple
from types import CodeType
from typing import Dict, Tuple

E = sys.monitoring.events

LOCAL_EVENTS = (
    E.PY_START
    | E.PY_RESUME
    | E.PY_RETURN
    | E.PY_YIELD
    | E.CALL
    | E.LINE
    | E.INSTRUCTION
    | E.JUMP
    | E.BRANCH_LEFT
    | E.BRANCH_RIGHT
    | E.STOP_ITERATION
)

# For a given code object and thread id and tool_id, have a place to store
# event masks that dictate what events we should be stopping on.
# The "status" field specifies on entry to a callback function, what
# level of callback is desired. This can be step, into, step over, or finish.
CodeMasks = namedtuple("CodeMasks", "local_events_mask global_events_mask status breakpoints")

# thread_id, tool_id, code
CODE2EVENTS: Dict[Tuple[int, int, CodeType], CodeMasks] = {}

# CODE2EVENTS: Dict[(int, int, CodeType), ]

# Event mask that should be use to callback on
# finish or return from function, method or module.
FINISH_EVENTS = E.PY_YIELD | E.PY_RETURN | E.RAISE | E.C_RETURN | E.PY_UNWIND

# Event mask that should be use to callback on
# line stepping.
STEP_OVER_EVENTS = E.LINE | FINISH_EVENTS

# Event mask that should be use to callback on
# "step into" line stepping.
STEP_INTO_EVENTS = STEP_OVER_EVENTS | E.CALL | E.PY_RESUME | E.PY_THROW

# trace status can be:
#  * "step over" stepping which is
#    local event stepping can be any combination of local events, and
#    possible global events "exception handled", "raise", "reraise", "throw".
#    The most common event is LINE,
#    but INSTRUCTION may be useful.  Breakpoints at certain places will use either
#    filter on line or INSTRUCTION events.
#
#  * "step into" stepping which is local stepping and global events.
#
#  * "finish "stepping which is local return and yield, and global PY_UNWIND
#  * "continue"


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
    from sys_monitoring import start, start_local, stop

    hook_name = "tracer.stepping"

    def code_short(code: CodeType) -> str:
        import os.path as osp

        return f"{code.co_name} in {osp.basename(code.co_filename)}"

    ignore_filter = tracefilter.TraceFilter([sys_monitoring, sys.monitoring])

    def line_event_callback(code: CodeType, line_number: int) -> object:
        """A line event callback trace function"""

        if ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(f"line event: code: {code_short(code)}, line: {line_number}")

    def call_event_callback(
        code: CodeType, instruction_offset: int, callable_obj: CodeType, args
    ) -> object:
        """A call event callback trace function"""
        if ignore_filter.is_excluded(callable_obj) or ignore_filter.is_excluded(code):
            return sys.monitoring.DISABLE

        print(
            f"call event: code: {code_short(code)}, offset: *{instruction_offset} call: {callable_obj}"
        )
        return

    def return_yield_event_callback(
        event: str, code: CodeType, instruction_offset: int, retval: object
    ):
        """A Return and Yield event callback trace function"""
        print(
            f"event: {event}, code: {code_short(code)}, offset: *{instruction_offset}\nreturn value: {retval}"
        )
        return

    def foo(*args):
        print(
            f"XXX2 foo local {sys.monitoring.get_local_events(tool_id, bar.__code__)}"
        )
        print(f"XXX3 foo all (global) {sys.monitoring.get_events(tool_id)}")
        print(f"foo called with {args}")

    def bar():
        foo("foo")
        foo("bar")

    tool_id, events_mask = start(hook_name, tool_id=1)
    print(f"tool_id is {tool_id}, events_mask is {events_mask}")

    callback_hooks = {
        E.CALL: call_event_callback,
        E.LINE: line_event_callback,
        E.PY_RETURN: lambda code, instruction_offset, retval: return_yield_event_callback(
            "return", code, instruction_offset, retval
        ),
        E.PY_YIELD: lambda code, instruction_offset, retval: return_yield_event_callback(
            "yield", code, instruction_offset, retval
        ),
    }

    start_local(hook_name, callback_hooks, STEP_INTO_EVENTS, code=bar.__code__)
    bar()

    stop(hook_name)
    print("=" * 40)
    start(hook_name)
    bar()
    stop(hook_name)
    print("=" * 40)

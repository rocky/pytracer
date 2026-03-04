# -*- coding: utf-8 -*-
#   Copyright (C) 2026 Rocky Bernstein <rocky@gnu.org>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Breakpoint structures and routines.
"""
import sys
from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Dict, List, Optional, Tuple, Union

E = sys.monitoring.events

class BreakpointTag(Enum):
    LINE_NUMBER = "line number"
    LINE_NUMBER_OFFSET = "line number and offset"
    CODE_OFFSET = "instruction offset"


@dataclass
class LineNumberValue:
    tag: BreakpointTag = BreakpointTag.LINE_NUMBER
    line_number: int = -1


@dataclass
class LineNumberOffsetValue:
    tag: BreakpointTag = BreakpointTag.LINE_NUMBER_OFFSET
    line_number: int = -1
    code_offset: int = -1


@dataclass
class CodeOffsetValue:
    tag: BreakpointTag = BreakpointTag.CODE_OFFSET
    code_offset: int = -1


# The "Union" structure
# Location = Union[LineNumberValue, LineNumberOffsetValue, CodeOffsetValue]


@dataclass
class Breakpoint:
    location: Union[LineNumberValue, LineNumberOffsetValue, CodeOffsetValue]
    code: CodeType


class CodeInfo:
    def __init__(self, breakpoints, last_frame: Optional[FrameType] = None):
        self.breakpoints: List[Breakpoint] = breakpoints
        self.last_frame: Optional[FrameType] = last_frame


# We store breakpoints per tool id and code.
CODE_TRACKING: Dict[Tuple[int, CodeType], CodeInfo] = {}


def clear_breakpoint(tool_id: int, breakpoint: Breakpoint) -> Tuple[int, List[Breakpoint]]:
    location = breakpoint.location
    code = breakpoint.code
    code_key = (tool_id, code)
    if code_key in CODE_TRACKING:
        code_info = CODE_TRACKING.get((tool_id, code), CodeInfo([], None))

        # Remove breakpoint
        breakpoints = code_info.breakpoints
        if breakpoint in breakpoints:
            breakpoints.remove(breakpoint)
        no_breakpoints = len(code_info.breakpoints) == 0
    else:
        no_breakpoints = True
        breakpoints = []

    events = sys.monitoring.get_local_events(tool_id, code)
    if no_breakpoints:
        if events == 0:
            # Nothing to do
            return 0, []

        if isinstance(location, LineNumberValue):
            combined_events = events & ~E.LINE
        elif isinstance(location, LineNumberOffsetValue):
            combined_events = events & ~(E.LINE | E.INSTRUCTION)
            pass
        elif isinstance(location, CodeOffsetValue):
            combined_events = events & ~E.INSTRUCTION
            pass

        sys.monitoring.set_local_events(tool_id, code, combined_events)

    return combined_events, breakpoints

def set_breakpoint(tool_id: int, bp: Breakpoint) -> Tuple[int, CodeInfo]:
    location = bp.location
    code = bp.code
    events = sys.monitoring.get_local_events(tool_id, code)
    if isinstance(location, LineNumberValue):
        combined_events = events | E.LINE
    elif isinstance(location, LineNumberOffsetValue):
        combined_events = events | E.LINE | E.INSTRUCTION
        pass
    elif isinstance(location, CodeOffsetValue):
        combined_events = events | E.INSTRUCTION
        pass

    sys.monitoring.set_local_events(tool_id, code, combined_events)
    code_info = CODE_TRACKING.get((tool_id, code), CodeInfo([], None))
    if bp not in code_info.breakpoints:
        code_info.breakpoints.append(bp)
        CODE_TRACKING[(tool_id, code)] = code_info
    return combined_events, code_info

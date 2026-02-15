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

from dataclasses import dataclass
from enum import Enum
from types import CodeType, FrameType
from typing import Dict, Optional, Tuple, Union


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
Location = Union[LineNumberValue, LineNumberOffsetValue, CodeOffsetValue]


@dataclass
class CodeInfo:
    breakpoints = []
    last_frame: Optional[FrameType] = None


# We store breakpoints per tool id and code.
CODE_TRACKING: Dict[Tuple[int, CodeType], CodeInfo] = {}

def set_breakpoint(tool_id: int, location: Location):
    # TO BE COMPLETED...
    # event_bitmask = sys.montoring.get_events(tool_id)
    return

#   Copyright (C) 2008-2009, 2013, 2024 Rocky Bernstein <rocky@gnu.org>
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
"""Filter out trace events based on the event's frame or a function code."""

from types import CodeType
from typing import Any, Iterable, Optional
import inspect


def add_to_set(object: Any, code_set: set) -> bool:
    """Add `frame_or_fn' to the list of functions to include"""
    try:
        code = get_code_object(object)
        code_set.add(code)
        return True
    except Exception:
        return False


def objects2set(objects: Iterable) -> set:
    """Given a list of frame or function objects, turn it into a set which
    can be used in an include set.
    """
    code_set = set()
    for object in objects:
        add_to_set(object, code_set)
        pass
    return code_set


def get_code_object(object: Any) -> Optional[CodeType]:
    """
      Try to find a Python code object in ``object`` and if we
      find it, return the code object. If we can't find, return
      None.
    """
    code = None
    if inspect.ismethod(object):
        object = object.__func__

    for attr in ("__code__", "gi_code", "ag_code", "cr_code"):
        if hasattr(object, attr):
            code = getattr(object, attr)
            break
        pass
    else:
        t = inspect.getmembers(object, inspect.iscode)
        if len(t) > 0:
            return t[0][1]
        return None
    return code if isinstance(code, CodeType) else None


class TraceFilter:
    """A class that can be used to test whether
    certain frames, functions, classes, or modules should be skipped/included in tracing.
    """

    def __init__(self, include_items=[], include_modules=set()):
        self.include_f_codes = objects2set(include_items)
        self.exclude_modules = include_modules
        return

    def is_included(self, frame_or_fn_or_module) -> bool:
        """Return True if `frame_or_fn' is in the list of functions to include"""

        try:
            return get_code_object(frame_or_fn_or_module) in self.include_f_codes
        except Exception:
            return False

    def clear_include(self):
        self.include_f_codes = set()
        return

    def add_include(self, frame_or_fn):
        """Remove `frame_or_fn' from the list of functions to include"""
        try:
            return add_to_set(frame_or_fn, self.include_f_codes)
        except Exception:
            return False

    def remove_include(self, frame_or_fn_or_module) -> bool:
        """Remove `frame_or_fn' from the list of functions to include"""
        try:
            self.include_f_codes.remove(get_code_object(frame_or_fn_or_module))
            return True
        except Exception:
            return False


# Demo it
if __name__ == "__main__":
    filter = TraceFilter([add_to_set])
    curframe = inspect.currentframe()
    f_code = get_code_object(curframe)
    print("Created filter for 'add_to_set'")
    print(filter.include_f_codes)
    print("filter includes 'add_to_set'?: %s" % filter.is_included(add_to_set))
    print("Current frame includes 'add_to_set'?? %s" % filter.is_included(curframe))
    print("filter includes get_code_object?: %s" % filter.is_included(get_code_object))
    print("Removing filter for 'add_to_set'.")
    filter.remove_include(add_to_set)
    print("filter includes 'add_to_set'?: %s" % filter.is_included(add_to_set))
    filter.clear_include()
    pass

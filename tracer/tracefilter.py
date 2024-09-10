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

import inspect
from types import CodeType, ModuleType
from typing import Any, Iterable, Optional, Set


def add_to_code_set(object: Any, code_set: Set[CodeType]) -> bool:
    """Add `object` to the list of functions to include.
    Returns True if a code object was added."""
    try:
        code = get_code_object(object)
        if code is not None:
            code_set.add(code)
            return True
    except Exception:
        pass
    return False


def get_code_object(object: Any) -> Optional[CodeType]:
    """
    Try to find a Python code object in ``object`` and if we
    find it, return the code object. If we can't find, return
    None.
    """
    code = None

    # The code to pick out a code object comes from code in dis.dis
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

    def __init__(self, exclude_items: Iterable=list()):
        self.clear()
        for item in exclude_items:
            self.add(item)
        return

    def is_excluded(self, object) -> bool:
        """Return True if `object', a frame or function, is in the
        list of functions to exclude"""

        if object is ModuleType:
            return object in self.excluded_modules
        code_object = get_code_object(object)
        if code_object is None:
            return False
        return code_object in self.excluded_code_objects

    def clear(self):
        self.excluded_code_objects: Set[CodeType] = set()
        self.excluded_modules: Set[ModuleType] = set()
        return

    def add(self, object: Any) -> bool:
        """Remove `frame_or_fn' from the list of functions to include"""
        if object is ModuleType:
            self.excluded_modules.add(object)
            return True
        return add_to_code_set(object, self.excluded_code_objects)

    def remove(self, object: Any) -> bool:
        """Remove `object' from the list of functions to include.
        Return True if an object was removed or False otherwise.
        """
        if object is ModuleType:
            self.excluded_modules.remove(object)
            return True
        code_object = get_code_object(object)
        if code_object is None or code_object not in self.excluded_code_objects:
            return False
        self.excluded_code_objects.remove(code_object)
        return True


# Demo it
if __name__ == "__main__":
    filter = TraceFilter([add_to_code_set])
    curframe = inspect.currentframe()
    f_code = get_code_object(curframe)
    print("Created filter for 'add_to_set'")
    print(filter.excluded_code_objects)
    print(f"filter excludes add_to_set(): {filter.is_excluded(add_to_code_set)}")
    print(f"Current frame now excludes add_to_set(): {filter.is_excluded(curframe)}")
    print(f"filter excludes get_code_object?: {filter.is_excluded(get_code_object)}")
    print("Removing filter for add_to_set()")
    filter.remove(add_to_code_set)
    print(f"filter excludes now add_to_set(): {filter.is_excluded(add_to_code_set)}")
    filter.clear()
    pass

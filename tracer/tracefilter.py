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
import os
import sys
from types import CodeType, ModuleType


def add_to_code_set(object, code_set):
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


def get_code_object(object):
    """
    Try to find a Python code object in ``object`` and if we
    find it, return the code object. If we can't find, return
    None.
    """
    code = None

    # The code to pick out a code object comes from code in dis.dis
    if inspect.ismethod(object):
        object = object.func_code

    for attr in ("func_code", "f_code", "__code__", "gi_code", "ag_code", "cr_code"):
        if hasattr(object, attr):
            code = getattr(object, attr)
            break
        pass
    else:
        t = inspect.getmembers(object, inspect.iscode)
        if len(t) > 0:
            return t[0][1]
        return None
    if isinstance(code, CodeType):
        return code
    else:
        return None


def get_module_object(object):
    """Given a module name, frame, or code object, return the
    module that his object belongs to, or None if we
    can't find the module.
    """
    if isinstance(object, ModuleType):
        return object

    module_path = None
    module_name = None

    if isinstance(object, CodeType):
        module_path = object.co_filename
    elif hasattr(object, "__module__"):
        module_name = object.__module__

    if isinstance(module_path, str):
        if os.path.exists(module_path):
            # from sys.modules, pick out those modules whose filename is "module_path".
            modules = [
                module
                for module in sys.modules.values()
                if hasattr(module, "__file__") and module.__file__ == module_path
            ]
            if len(modules):
                # There is at least one matching module. (They all
                # should be the same.)
                return modules[0]

    if module_name is not None:
        return sys.modules.get(module_name)
    else:
        return sys.modules.get(module_name)


class TraceFilter:
    """A class that can be used to test whether
    certain frames, functions, classes, or modules should be skipped/included in tracing.
    """

    def __init__(self, exclude_items=list()):
        self.clear()
        for item in exclude_items:
            self.add(item)
        return

    def is_excluded(self, object):
        """Return True if `object', a frame or function, is in the
        list of functions to exclude"""

        if isinstance(object, ModuleType):
            return object in self.excluded_modules
        code_object = get_code_object(object)
        if code_object is None:
            return False
        if code_object in self.excluded_code_objects:
            return True

        module_object = get_module_object(code_object)
        if module_object is None:
            return False

        return module_object in self.excluded_modules

    def clear(self):
        self.excluded_code_objects = set()
        self.excluded_modules = set()
        return

    def add(self, object):
        """Remove `frame_or_fn' from the list of functions to include"""
        if isinstance(object, ModuleType):
            self.excluded_modules.add(object)
            return True
        if inspect.isclass(object):
            module_object = get_module_object(object)
            if isinstance(module_object, ModuleType):
                self.excluded_modules.add(module_object)
                return True
            else:
                return False
        return add_to_code_set(object, self.excluded_code_objects)

    def remove(self, object):
        """Remove `object' from the list of functions to include.
        Return True if an object was removed or False otherwise.
        """
        if isinstance(object, ModuleType):
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
    print("filter excludes add_to_set(): %s" % filter.is_excluded(add_to_code_set))
    print("Current frame now excludes add_to_set(): %s" % filter.is_excluded(curframe))
    print("filter excludes get_code_object?: %s" % filter.is_excluded(get_code_object))
    print("Removing filter for add_to_set()")
    filter.remove(add_to_code_set)
    print("filter excludes now add_to_set(): %s" % filter.is_excluded(add_to_code_set))
    filter.clear()
    assert len(filter.excluded_modules) == 0
    print(get_module_object(add_to_code_set))
    pass

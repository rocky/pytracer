#   Copyright (C) 2008-2009, 2013 Rocky Bernstein <rocky@gnu.org>
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

def add_to_set(frame_or_fn, f_set):
    """Add `frame_or_fn' to the list of functions to include"""
    try:
        f_code = to_f_code(frame_or_fn)
        f_set.add(f_code)
        return True
    except:
        return False
    pass

def fs2set(frames_or_fns):
    """Given a list of frame or function objects, turn it into a set which
    can be used in an include set.
    """
    f_code_set = set()
    for f in frames_or_fns:
        add_to_set(f, f_code_set)
        pass
    return f_code_set

def to_f_code(f):
    if hasattr(f, 'func_code'):
        return f.func_code
    elif hasattr(f, '__code__'):
        return f.__code__
    else:
        t = inspect.getmembers(f, inspect.iscode)
        if len(t) > 0: return t[0][1]
        return None

class TraceFilter:
    """A class that can be used to test whether
    certain frames or functions should be skipped/included in tracing.
    """
    def __init__(self, include_fns = [], continue_return_frame = None):
        self.include_f_codes = fs2set(include_fns)
        return

    def is_included(self, frame_or_fn):
        """Return True if `frame_or_fn' is in the list of functions to include"""
        try:
            return to_f_code(frame_or_fn) in self.include_f_codes
        except:
            return False
        pass

    def clear_include(self):
        self.include_f_codes = set()
        return

    def add_include(self, frame_or_fn):
        """Remove `frame_or_fn' from the list of functions to include"""
        try:
            return add_to_set(frame_or_fn, self.include_f_codes)
        except:
            return False
        pass

    def remove_include(self, frame_or_fn):
        """Remove `frame_or_fn' from the list of functions to include"""
        try:
            self.include_f_codes.remove(to_f_code(frame_or_fn))
            return True
        except:
            return False
        pass


# Demo it
if __name__ == '__main__':
    filter = TraceFilter([add_to_set])
    curframe = inspect.currentframe()
    f_code = to_f_code(curframe)
    print("Created filter for 'add_to_set'")
    print(filter.include_f_codes)
    print("filter includes 'add_to_set'?: %s" % filter.is_included(add_to_set))
    print("Current frame includes 'add_to_set'?? %s" %
          filter.is_included(curframe))
    print("filter includes to_f_code?: %s" % filter.is_included(to_f_code))
    print("Removing filter for 'add_to_set'.")
    filter.remove_include(add_to_set)
    print("filter includes 'add_to_set'?: %s" % filter.is_included(add_to_set))
    filter.clear_include()
    pass

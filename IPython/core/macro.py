"""Support for interactive macros in IPython"""

from __future__ import annotations

# *****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************

import re

coding_declaration = re.compile(r"#\s*coding[:=]\s*([-\w.]+)")


class Macro:
    """Simple class to store the value of macros as strings.

    Macro is just a callable that executes a string of IPython
    input when called.
    """

    def __init__(self, code: str):
        """store the macro value, as a single string which can be executed"""
        lines = [
            line for line in code.splitlines() if not coding_declaration.match(line)
        ]
        code = "\n".join(lines)
        self.value = code + "\n"

    def __str__(self):
        return self.value

    def __repr__(self):
        return "IPython.macro.Macro(%s)" % repr(self.value)

    def __getstate__(self):
        """needed for safe pickling via %store"""
        return {"value": self.value}

    def __setstate__(self, state):
        self.value = state["value"]

    def __add__(self, other: Macro | str) -> Macro:
        if isinstance(other, Macro):
            return Macro(self.value + other.value)
        elif isinstance(other, str):
            return Macro(self.value + other)
        raise TypeError(
            f"unsupported operand type(s) for +: 'Macro' and {type(other).__name__!r}"
        )

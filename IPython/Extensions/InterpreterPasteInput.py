# -*- coding: utf-8 -*-
"""Modified input prompt for entering text with >>> or ... at the start.

We define a special input line filter to allow typing lines which begin with
'>>> ' or '... '. These two strings, if present at the start of the input
line, are stripped. This allows for direct pasting of code from examples such
as those available in the standard Python tutorial.

Normally pasting such code is one chunk is impossible because of the
extraneous >>> and ..., requiring one to do a line by line paste with careful
removal of those characters. This module allows pasting that kind of
multi-line examples in one pass.

Here is an 'screenshot' of a section of the tutorial pasted into IPython with
this feature enabled:

In [1]: >>> def fib2(n): # return Fibonacci series up to n
   ...: ...     '''Return a list containing the Fibonacci series up to n.'''
   ...: ...     result = []
   ...: ...     a, b = 0, 1
   ...: ...     while b < n:
   ...: ...         result.append(b)    # see below
   ...: ...         a, b = b, a+b
   ...: ...     return result
   ...:

In [2]: fib2(10)
Out[2]: [1, 1, 2, 3, 5, 8]

The >>> and ... are stripped from the input so that the python interpreter
only sees the real part of the code.

All other input is processed normally.

Notes
=====

* You can even paste code that has extra initial spaces, such as is common in
doctests:

In [3]:     >>> a = ['Mary', 'had', 'a', 'little', 'lamb']

In [4]:     >>> for i in range(len(a)):
   ...:         ...     print i, a[i]
   ...:     ...
0 Mary
1 had
2 a
3 little
4 lamb
"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# This file is an example of how to modify IPython's line-processing behavior
# without touching the internal code. We'll define an alternate pre-processing
# stage which allows a special form of input (which is invalid Python syntax)
# for certain quantities, rewrites a line of proper Python in those cases, and
# then passes it off to IPython's normal processor for further work.

# With this kind of customization, IPython can be adapted for many
# special-purpose scenarios providing alternate input syntaxes.

# This file can be imported like a regular module.

# IPython has a prefilter() function that analyzes each input line. We redefine
# it here to first pre-process certain forms of input

# The prototype of any alternate prefilter must be like this one (the name
# doesn't matter):
# - line is a string containing the user input line.
# - continuation is a parameter which tells us if we are processing a first
# line of user input or the second or higher of a multi-line statement.

import re

from IPython.iplib import InteractiveShell

PROMPT_RE = re.compile(r'(^[ \t]*>>> |^[ \t]*\.\.\. )')

def prefilter_paste(self,line,continuation):
    """Alternate prefilter for input of pasted code from an interpreter.
    """
    if not line:
        return ''
    m = PROMPT_RE.match(line)
    if m:
        # In the end, always call the default IPython _prefilter() function.
        # Note that self must be passed explicitly, b/c we're calling the
        # unbound class method (since this method will overwrite the instance
        # prefilter())
        return self._prefilter(line[len(m.group(0)):],continuation)
    elif line.strip() == '...':
        return self._prefilter('',continuation)
    elif line.isspace():
        # This allows us to recognize multiple input prompts separated by blank
        # lines and pasted in a single chunk, very common when pasting doctests
        # or long tutorial passages.
        return ''
    else:
        return self._prefilter(line,continuation)

def activate_prefilter():
    """Rebind the input-pasting filter to be the new IPython prefilter"""
    InteractiveShell.prefilter = prefilter_paste

def deactivate_prefilter():
    """Reset the filter."""
    InteractiveShell.prefilter = InteractiveShell._prefilter

# Just a heads up at the console
activate_prefilter()
print '*** Pasting of code with ">>>" or "..." has been enabled.'

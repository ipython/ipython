# encoding: utf-8
"""Generic utilities for use by IPython's various subsystems.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2006  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Stdlib imports
#---------------------------------------------------------------------------

import os
import sys

#---------------------------------------------------------------------------
# Other IPython utilities
#---------------------------------------------------------------------------


#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------

def extractVars(*names,**kw):
    """Extract a set of variables by name from another frame.

    :Parameters:
      - `*names`: strings
        One or more variable names which will be extracted from the caller's
    frame.

    :Keywords:
      - `depth`: integer (0)
        How many frames in the stack to walk when looking for your variables.


    Examples:

        In [2]: def func(x):
           ...:     y = 1
           ...:     print extractVars('x','y')
           ...:

        In [3]: func('hello')
        {'y': 1, 'x': 'hello'}
    """

    depth = kw.get('depth',0)
    
    callerNS = sys._getframe(depth+1).f_locals
    return dict((k,callerNS[k]) for k in names)
    

def extractVarsAbove(*names):
    """Extract a set of variables by name from another frame.

    Similar to extractVars(), but with a specified depth of 1, so that names
    are exctracted exactly from above the caller.

    This is simply a convenience function so that the very common case (for us)
    of skipping exactly 1 frame doesn't have to construct a special dict for
    keyword passing."""

    callerNS = sys._getframe(2).f_locals
    return dict((k,callerNS[k]) for k in names)

def shexp(s):
    """Expand $VARS and ~names in a string, like a shell

    :Examples:
    
       In [2]: os.environ['FOO']='test'

       In [3]: shexp('variable FOO is $FOO')
       Out[3]: 'variable FOO is test'
    """
    return os.path.expandvars(os.path.expanduser(s))
    

def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input.

    :Examples:

        In [7]: list_strings('A single string')
        Out[7]: ['A single string']

        In [8]: list_strings(['A single string in a list'])
        Out[8]: ['A single string in a list']

        In [9]: list_strings(['A','list','of','strings'])
        Out[9]: ['A', 'list', 'of', 'strings']
    """

    if isinstance(arg,basestring): return [arg]
    else: return arg

def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'.

    :Examples:

        In [16]: marquee('A test',40)
        Out[16]: '**************** A test ****************'

        In [17]: marquee('A test',40,'-')
        Out[17]: '---------------- A test ----------------'

        In [18]: marquee('A test',40,' ')
        Out[18]: '                 A test                 '

    """
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)/len(mark)/2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)



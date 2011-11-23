# encoding: utf-8
"""
Utilities for working with stack frames.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

@py3compat.doctest_refactor_print
def extract_vars(*names,**kw):
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
           ...:     print extract_vars('x','y')
           ...:

        In [3]: func('hello')
        {'y': 1, 'x': 'hello'}
    """

    depth = kw.get('depth',0)
    
    callerNS = sys._getframe(depth+1).f_locals
    return dict((k,callerNS[k]) for k in names)


def extract_vars_above(*names):
    """Extract a set of variables by name from another frame.

    Similar to extractVars(), but with a specified depth of 1, so that names
    are exctracted exactly from above the caller.

    This is simply a convenience function so that the very common case (for us)
    of skipping exactly 1 frame doesn't have to construct a special dict for
    keyword passing."""

    callerNS = sys._getframe(2).f_locals
    return dict((k,callerNS[k]) for k in names)


def debugx(expr,pre_msg=''):
    """Print the value of an expression from the caller's frame.

    Takes an expression, evaluates it in the caller's frame and prints both
    the given expression and the resulting value (as well as a debug mark
    indicating the name of the calling function.  The input must be of a form
    suitable for eval().

    An optional message can be passed, which will be prepended to the printed
    expr->value pair."""

    cf = sys._getframe(1)
    print '[DBG:%s] %s%s -> %r' % (cf.f_code.co_name,pre_msg,expr,
                                   eval(expr,cf.f_globals,cf.f_locals))


# deactivate it by uncommenting the following line, which makes it a no-op
#def debugx(expr,pre_msg=''): pass


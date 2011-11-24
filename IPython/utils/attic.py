# encoding: utf-8
"""
Older utilities that are not being used.

WARNING: IF YOU NEED TO USE ONE OF THESE FUNCTIONS, PLEASE FIRST MOVE IT
TO ANOTHER APPROPRIATE MODULE IN IPython.utils.
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
import warnings

from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


def mutex_opts(dict,ex_op):
    """Check for presence of mutually exclusive keys in a dict.

    Call: mutex_opts(dict,[[op1a,op1b],[op2a,op2b]...]"""
    for op1,op2 in ex_op:
        if op1 in dict and op2 in dict:
            raise ValueError,'\n*** ERROR in Arguments *** '\
                  'Options '+op1+' and '+op2+' are mutually exclusive.'


class EvalDict:
    """
    Emulate a dict which evaluates its contents in the caller's frame.

    Usage:
    >>> number = 19

    >>> text = "python"

    >>> print "%(text.capitalize())s %(number/9.0).1f rules!" % EvalDict()
    Python 2.1 rules!
    """

    # This version is due to sismex01@hebmex.com on c.l.py, and is basically a
    # modified (shorter) version of:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66018 by
    # Skip Montanaro (skip@pobox.com).

    def __getitem__(self, name):
        frame = sys._getframe(1)
        return eval(name, frame.f_globals, frame.f_locals)

EvalString = EvalDict  # for backwards compatibility


def all_belong(candidates,checklist):
    """Check whether a list of items ALL appear in a given list of options.

    Returns a single 1 or 0 value."""

    return 1-(0 in [x in checklist for x in candidates])


def belong(candidates,checklist):
    """Check whether a list of items appear in a given list of options.

    Returns a list of 1 and 0, one for each candidate given."""

    return [x in checklist for x in candidates]


def with_obj(object, **args):
    """Set multiple attributes for an object, similar to Pascal's with.

    Example:
    with_obj(jim,
             born = 1960,
             haircolour = 'Brown',
             eyecolour = 'Green')

    Credit: Greg Ewing, in
    http://mail.python.org/pipermail/python-list/2001-May/040703.html.

    NOTE: up until IPython 0.7.2, this was called simply 'with', but 'with'
    has become a keyword for Python 2.5, so we had to rename it."""

    object.__dict__.update(args)


def map_method(method,object_list,*argseq,**kw):
    """map_method(method,object_list,*args,**kw) -> list

    Return a list of the results of applying the methods to the items of the
    argument sequence(s).  If more than one sequence is given, the method is
    called with an argument list consisting of the corresponding item of each
    sequence. All sequences must be of the same length.

    Keyword arguments are passed verbatim to all objects called.

    This is Python code, so it's not nearly as fast as the builtin map()."""

    out_list = []
    idx = 0
    for object in object_list:
        try:
            handler = getattr(object, method)
        except AttributeError:
            out_list.append(None)
        else:
            if argseq:
                args = map(lambda lst:lst[idx],argseq)
                #print 'ob',object,'hand',handler,'ar',args # dbg
                out_list.append(handler(args,**kw))
            else:
                out_list.append(handler(**kw))
        idx += 1
    return out_list


def import_fail_info(mod_name,fns=None):
    """Inform load failure for a module."""

    if fns == None:
        warn("Loading of %s failed.\n" % (mod_name,))
    else:
        warn("Loading of %s from %s failed.\n" % (fns,mod_name))


class NotGiven: pass

def popkey(dct,key,default=NotGiven):
    """Return dct[key] and delete dct[key].

    If default is given, return it if dct[key] doesn't exist, otherwise raise
    KeyError.  """

    try:
        val = dct[key]
    except KeyError:
        if default is NotGiven:
            raise
        else:
            return default
    else:
        del dct[key]
        return val


def wrap_deprecated(func, suggest = '<nothing>'):
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s, use %s instead" %
                      ( func.__name__, suggest),
                      category=DeprecationWarning,
                      stacklevel = 2)
        return func(*args, **kwargs)
    return newFunc



# encoding: utf-8

"""Utilities to enable code objects to be pickled.

Any process that import this module will be able to pickle code objects.  This
includes the func_code attribute of any function.  Once unpickled, new
functions can be built using new.function(code, globals()).  Eventually
we need to automate all of this so that functions themselves can be pickled.

Reference: A. Tremols, P Cogolo, "Python Cookbook," p 302-305
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import types
try:
    import copyreg  # Py 3
except ImportError:
    import copy_reg as copyreg  # Py 2

def code_ctor(*args):
    return types.CodeType(*args)

def reduce_code(co):
    args =  [co.co_argcount, co.co_nlocals, co.co_stacksize,
            co.co_flags, co.co_code, co.co_consts, co.co_names,
            co.co_varnames, co.co_filename, co.co_name, co.co_firstlineno,
            co.co_lnotab, co.co_freevars, co.co_cellvars]
    if sys.version_info[0] >= 3:
        args.insert(1, co.co_kwonlyargcount)
    return code_ctor, tuple(args)

copyreg.pickle(types.CodeType, reduce_code)
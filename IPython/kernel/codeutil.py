# encoding: utf-8

"""Utilities to enable code objects to be pickled.

Any process that import this module will be able to pickle code objects.  This
includes the func_code attribute of any function.  Once unpickled, new 
functions can be built using new.function(code, globals()).  Eventually
we need to automate all of this so that functions themselves can be pickled.

Reference: A. Tremols, P Cogolo, "Python Cookbook," p 302-305
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import new, types, copy_reg

def code_ctor(*args):
    return new.code(*args)
    
def reduce_code(co):
    if co.co_freevars or co.co_cellvars:
        raise ValueError("Sorry, cannot pickle code objects with closures")
    return code_ctor, (co.co_argcount, co.co_nlocals, co.co_stacksize,
        co.co_flags, co.co_code, co.co_consts, co.co_names,
        co.co_varnames, co.co_filename, co.co_name, co.co_firstlineno,
        co.co_lnotab)

copy_reg.pickle(types.CodeType, reduce_code)
# encoding: utf-8

"""This file contains unittests for the interpreter.py module."""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team                           
#                                                                             
#  Distributed under the terms of the BSD License.  The full license is in    
#  the file COPYING, distributed as part of this software.                    
#-----------------------------------------------------------------------------
                                                                              
#-----------------------------------------------------------------------------
# Imports                                                                     
#-----------------------------------------------------------------------------

from IPython.kernel.core.interpreter import Interpreter

def test_unicode():
    """ Test unicode handling with the interpreter.
    """
    i = Interpreter()
    i.execute_python(u'print "ù"')
    i.execute_python('print "ù"')


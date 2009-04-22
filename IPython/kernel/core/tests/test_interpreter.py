# encoding: utf-8

"""This file contains unittests for the interpreter.py module."""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team                           
#                                                                             
#  Distributed under the terms of the BSD License.  The full license is in    
#  the file COPYING, distributed as part of this software.                    
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports                                                                     
#-----------------------------------------------------------------------------

import unittest
from IPython.kernel.core.interpreter import Interpreter

#-----------------------------------------------------------------------------
# Tests 
#-----------------------------------------------------------------------------

# Tell nose to skip this module
__test__ = {}

class TestInterpreter(unittest.TestCase):

    def test_unicode(self):
        """ Test unicode handling with the interpreter."""
        i = Interpreter()
        i.execute_python(u'print "ù"')
        i.execute_python('print "ù"')

    def test_ticket266993(self):
        """ Test for ticket 266993."""
        i = Interpreter()
        i.execute('str("""a\nb""")')

    def test_ticket364347(self):
        """Test for ticket 364347."""
        i = Interpreter()
        i.split_commands('str("a\\nb")')

    def test_split_commands(self):
        """ Test that commands are indeed individually split."""
        i = Interpreter()
        test_atoms = [('(1\n + 1)', ),
                      ('1', '1', ),
                      ]
        for atoms in test_atoms:
            atoms = [atom.rstrip() + '\n' for atom in atoms]
            self.assertEquals(i.split_commands(''.join(atoms)),atoms)

    def test_long_lines(self):
        """ Test for spurious syntax error created by the interpreter."""
        test_strings = [u'( 1 +\n 1\n )\n\n',
                        u'(1 \n + 1\n )\n\n',
                       ]
        i = Interpreter()
        for s in test_strings:
            i.execute(s)


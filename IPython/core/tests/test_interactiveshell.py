"""Tests for the key interactiveshell module.

Historically the main classes in interactiveshell have been under-tested.  This
module should grow as many single-method tests as possible to trap many of the
recurring bugs we seem to encounter with high-level interaction.

Authors
-------
* Fernando Perez
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import unittest
from StringIO import StringIO

from IPython.testing import decorators as dec
from IPython.utils import io

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class InteractiveShellTestCase(unittest.TestCase):
    def test_naked_string_cells(self):
        """Test that cells with only naked strings are fully executed"""
        ip = get_ipython()
        # First, single-line inputs
        ip.run_cell('"a"\n')
        self.assertEquals(ip.user_ns['_'], 'a')
        # And also multi-line cells
        ip.run_cell('"""a\nb"""\n')
        self.assertEquals(ip.user_ns['_'], 'a\nb')

    def test_run_empty_cell(self):
        """Just make sure we don't get a horrible error with a blank
        cell of input. Yes, I did overlook that."""
        ip = get_ipython()
        old_xc = ip.execution_count
        ip.run_cell('')
        self.assertEquals(ip.execution_count, old_xc)

    def test_run_cell_multiline(self):
        """Multi-block, multi-line cells must execute correctly.
        """
        ip = get_ipython()
        src = '\n'.join(["x=1",
                         "y=2",
                         "if 1:",
                         "    x += 1",
                         "    y += 1",])
        ip.run_cell(src)
        self.assertEquals(ip.user_ns['x'], 2)
        self.assertEquals(ip.user_ns['y'], 3)

    def test_multiline_string_cells(self):
        "Code sprinkled with multiline strings should execute (GH-306)"
        ip = get_ipython()
        ip.run_cell('tmp=0')
        self.assertEquals(ip.user_ns['tmp'], 0)
        ip.run_cell('tmp=1;"""a\nb"""\n')
        self.assertEquals(ip.user_ns['tmp'], 1)

    def test_dont_cache_with_semicolon(self):
        "Ending a line with semicolon should not cache the returned object (GH-307)"
        ip = get_ipython()
        oldlen = len(ip.user_ns['Out'])
        a = ip.run_cell('1;', store_history=True)
        newlen = len(ip.user_ns['Out'])
        self.assertEquals(oldlen, newlen)
        #also test the default caching behavior
        ip.run_cell('1', store_history=True)
        newlen = len(ip.user_ns['Out'])
        self.assertEquals(oldlen+1, newlen)

    def test_In_variable(self):
        "Verify that In variable grows with user input (GH-284)"
        ip = get_ipython()
        oldlen = len(ip.user_ns['In'])
        ip.run_cell('1;', store_history=True)
        newlen = len(ip.user_ns['In'])
        self.assertEquals(oldlen+1, newlen)
        self.assertEquals(ip.user_ns['In'][-1],'1;')
        
    def test_magic_names_in_string(self):
        ip = get_ipython()
        ip.run_cell('a = """\n%exit\n"""')
        self.assertEquals(ip.user_ns['a'], '\n%exit\n')
    
    def test_alias_crash(self):
        """Errors in prefilter can't crash IPython"""
        ip = get_ipython()
        ip.run_cell('%alias parts echo first %s second %s')
        # capture stderr:
        save_err = io.stderr
        io.stderr = StringIO()
        ip.run_cell('parts 1')
        err = io.stderr.getvalue()
        io.stderr = save_err
        self.assertEquals(err.split(':')[0], 'ERROR')
    
    def test_trailing_newline(self):
        """test that running !(command) does not raise a SyntaxError"""
        ip = get_ipython()
        ip.run_cell('!(true)\n', False)
        ip.run_cell('!(true)\n\n\n', False)
    
    def test_gh_597(self):
        """Pretty-printing lists of objects with non-ascii reprs may cause
        problems."""
        class Spam(object):
          def __repr__(self):
            return "\xe9"*50
        import IPython.core.formatters
        f = IPython.core.formatters.PlainTextFormatter()
        f([Spam(),Spam()])
    
    def test_future_flags(self):
        """Check that future flags are used for parsing code (gh-777)"""
        ip = get_ipython()
        ip.run_cell('from __future__ import print_function')
        try:
            ip.run_cell('prfunc_return_val = print(1,2, sep=" ")')
            assert 'prfunc_return_val' in ip.user_ns
        finally:
            # Reset compiler flags so we don't mess up other tests.
            ip.compile.reset_compiler_flags()

    def test_future_unicode(self):
        """Check that unicode_literals is imported from __future__ (gh #786)"""
        ip = get_ipython()
        try:
            ip.run_cell(u'byte_str = "a"')
            assert isinstance(ip.user_ns['byte_str'], str) # string literals are byte strings by default
            ip.run_cell('from __future__ import unicode_literals')
            ip.run_cell(u'unicode_str = "a"')
            assert isinstance(ip.user_ns['unicode_str'], unicode) # strings literals are now unicode
        finally:
            # Reset compiler flags so we don't mess up other tests.
            ip.compile.reset_compiler_flags()

    def test_bad_custom_tb(self):
        """Check that InteractiveShell is protected from bad custom exception handlers"""
        ip = get_ipython()
        from IPython.utils import io
        save_stderr = io.stderr
        try:
            # capture stderr
            io.stderr = StringIO()
            ip.set_custom_exc((IOError,), lambda etype,value,tb: 1/0)
            self.assertEquals(ip.custom_exceptions, (IOError,))
            ip.run_cell(u'raise IOError("foo")')
            self.assertEquals(ip.custom_exceptions, ())
            self.assertTrue("Custom TB Handler failed" in io.stderr.getvalue())
        finally:
            io.stderr = save_stderr

    def test_bad_custom_tb_return(self):
        """Check that InteractiveShell is protected from bad return types in custom exception handlers"""
        ip = get_ipython()
        from IPython.utils import io
        save_stderr = io.stderr
        try:
            # capture stderr
            io.stderr = StringIO()
            ip.set_custom_exc((NameError,),lambda etype,value,tb, tb_offset=None: 1)
            self.assertEquals(ip.custom_exceptions, (NameError,))
            ip.run_cell(u'a=abracadabra')
            self.assertEquals(ip.custom_exceptions, ())
            self.assertTrue("Custom TB Handler failed" in io.stderr.getvalue())
        finally:
            io.stderr = save_stderr



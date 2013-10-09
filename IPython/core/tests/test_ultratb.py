# encoding: utf-8
"""Tests for IPython.core.ultratb
"""
import io
import os.path
import unittest

from IPython.testing import tools as tt
from IPython.testing.decorators import onlyif_unicode_paths
from IPython.utils.syspathcontext import prepended_to_syspath
from IPython.utils.tempdir import TemporaryDirectory

ip = get_ipython()

file_1 = """1
2
3
def f():
  1/0
"""

file_2 = """def f():
  1/0
"""

class ChangedPyFileTest(unittest.TestCase):
    def test_changing_py_file(self):
        """Traceback produced if the line where the error occurred is missing?
        
        https://github.com/ipython/ipython/issues/1456
        """
        with TemporaryDirectory() as td:
            fname = os.path.join(td, "foo.py")
            with open(fname, "w") as f:
                f.write(file_1)
            
            with prepended_to_syspath(td):
                ip.run_cell("import foo")
            
            with tt.AssertPrints("ZeroDivisionError"):
                ip.run_cell("foo.f()")
            
            # Make the file shorter, so the line of the error is missing.
            with open(fname, "w") as f:
                f.write(file_2)
            
            # For some reason, this was failing on the *second* call after
            # changing the file, so we call f() twice.
            with tt.AssertNotPrints("Internal Python error", channel='stderr'):
                with tt.AssertPrints("ZeroDivisionError"):
                    ip.run_cell("foo.f()")
                with tt.AssertPrints("ZeroDivisionError"):
                    ip.run_cell("foo.f()")

iso_8859_5_file = u'''# coding: iso-8859-5

def fail():
    """дбИЖ"""
    1/0     # дбИЖ
'''

class NonAsciiTest(unittest.TestCase):
    @onlyif_unicode_paths
    def test_nonascii_path(self):
        # Non-ascii directory name as well.
        with TemporaryDirectory(suffix=u'é') as td:
            fname = os.path.join(td, u"fooé.py")
            with open(fname, "w") as f:
                f.write(file_1)
            
            with prepended_to_syspath(td):
                ip.run_cell("import foo")
            
            with tt.AssertPrints("ZeroDivisionError"):
                ip.run_cell("foo.f()")
    
    def test_iso8859_5(self):
        with TemporaryDirectory() as td:
            fname = os.path.join(td, 'dfghjkl.py')

            with io.open(fname, 'w', encoding='iso-8859-5') as f:
                f.write(iso_8859_5_file)
            
            with prepended_to_syspath(td):
                ip.run_cell("from dfghjkl import fail")
            
            with tt.AssertPrints("ZeroDivisionError"):
                with tt.AssertPrints(u'дбИЖ', suppress=False):
                    ip.run_cell('fail()')

indentationerror_file = """if True:
zoon()
"""

class IndentationErrorTest(unittest.TestCase):
    def test_indentationerror_shows_line(self):
        # See issue gh-2398
        with tt.AssertPrints("IndentationError"):
            with tt.AssertPrints("zoon()", suppress=False):
                ip.run_cell(indentationerror_file)
        
        with TemporaryDirectory() as td:
            fname = os.path.join(td, "foo.py")
            with open(fname, "w") as f:
                f.write(indentationerror_file)
            
            with tt.AssertPrints("IndentationError"):
                with tt.AssertPrints("zoon()", suppress=False):
                    ip.magic('run %s' % fname)

se_file_1 = """1
2
7/
"""

se_file_2 = """7/
"""

class SyntaxErrorTest(unittest.TestCase):
    def test_syntaxerror_without_lineno(self):
        with tt.AssertNotPrints("TypeError"):
            with tt.AssertPrints("line unknown"):
                ip.run_cell("raise SyntaxError()")

    def test_changing_py_file(self):
        with TemporaryDirectory() as td:
            fname = os.path.join(td, "foo.py")
            with open(fname, 'w') as f:
                f.write(se_file_1)

            with tt.AssertPrints(["7/", "SyntaxError"]):
                ip.magic("run " + fname)

            # Modify the file
            with open(fname, 'w') as f:
                f.write(se_file_2)

            # The SyntaxError should point to the correct line
            with tt.AssertPrints(["7/", "SyntaxError"]):
                ip.magic("run " + fname)

    def test_non_syntaxerror(self):
        # SyntaxTB may be called with an error other than a SyntaxError
        # See e.g. gh-4361
        try:
            raise ValueError('QWERTY')
        except ValueError:
            with tt.AssertPrints('QWERTY'):
                ip.showsyntaxerror()

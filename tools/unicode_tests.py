# coding: utf-8
"""These tests have to be run separately from the main test suite (iptest),
because that sets the default encoding to utf-8, and it cannot be changed after
the interpreter is up and running. The default encoding in a Python 2.x 
environment is ASCII."""
import unittest, sys

from IPython.core import compilerop

assert sys.getdefaultencoding() == "ascii"

class CompileropTest(unittest.TestCase):
    def test_accept_unicode(self):
        cp = compilerop.CachingCompiler()
        cp(u"t = 'žćčšđ'", "single")

if __name__ == "__main__":
    unittest.main()

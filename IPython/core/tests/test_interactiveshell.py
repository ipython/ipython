# -*- coding: utf-8 -*-
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
import ast
import os
import shutil
import sys
import tempfile
import unittest
from os.path import join
from StringIO import StringIO

# third-party
import nose.tools as nt

# Our own
from IPython.testing.decorators import skipif
from IPython.testing import tools as tt
from IPython.utils import io

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
# This is used by every single test, no point repeating it ad nauseam
ip = get_ipython()

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

class InteractiveShellTestCase(unittest.TestCase):
    def test_naked_string_cells(self):
        """Test that cells with only naked strings are fully executed"""
        # First, single-line inputs
        ip.run_cell('"a"\n')
        self.assertEqual(ip.user_ns['_'], 'a')
        # And also multi-line cells
        ip.run_cell('"""a\nb"""\n')
        self.assertEqual(ip.user_ns['_'], 'a\nb')

    def test_run_empty_cell(self):
        """Just make sure we don't get a horrible error with a blank
        cell of input. Yes, I did overlook that."""
        old_xc = ip.execution_count
        ip.run_cell('')
        self.assertEqual(ip.execution_count, old_xc)

    def test_run_cell_multiline(self):
        """Multi-block, multi-line cells must execute correctly.
        """
        src = '\n'.join(["x=1",
                         "y=2",
                         "if 1:",
                         "    x += 1",
                         "    y += 1",])
        ip.run_cell(src)
        self.assertEqual(ip.user_ns['x'], 2)
        self.assertEqual(ip.user_ns['y'], 3)

    def test_multiline_string_cells(self):
        "Code sprinkled with multiline strings should execute (GH-306)"
        ip.run_cell('tmp=0')
        self.assertEqual(ip.user_ns['tmp'], 0)
        ip.run_cell('tmp=1;"""a\nb"""\n')
        self.assertEqual(ip.user_ns['tmp'], 1)

    def test_dont_cache_with_semicolon(self):
        "Ending a line with semicolon should not cache the returned object (GH-307)"
        oldlen = len(ip.user_ns['Out'])
        a = ip.run_cell('1;', store_history=True)
        newlen = len(ip.user_ns['Out'])
        self.assertEqual(oldlen, newlen)
        #also test the default caching behavior
        ip.run_cell('1', store_history=True)
        newlen = len(ip.user_ns['Out'])
        self.assertEqual(oldlen+1, newlen)

    def test_In_variable(self):
        "Verify that In variable grows with user input (GH-284)"
        oldlen = len(ip.user_ns['In'])
        ip.run_cell('1;', store_history=True)
        newlen = len(ip.user_ns['In'])
        self.assertEqual(oldlen+1, newlen)
        self.assertEqual(ip.user_ns['In'][-1],'1;')
        
    def test_magic_names_in_string(self):
        ip.run_cell('a = """\n%exit\n"""')
        self.assertEqual(ip.user_ns['a'], '\n%exit\n')
    
    def test_alias_crash(self):
        """Errors in prefilter can't crash IPython"""
        ip.run_cell('%alias parts echo first %s second %s')
        # capture stderr:
        save_err = io.stderr
        io.stderr = StringIO()
        ip.run_cell('parts 1')
        err = io.stderr.getvalue()
        io.stderr = save_err
        self.assertEqual(err.split(':')[0], 'ERROR')
    
    def test_trailing_newline(self):
        """test that running !(command) does not raise a SyntaxError"""
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
        ip.run_cell('from __future__ import print_function')
        try:
            ip.run_cell('prfunc_return_val = print(1,2, sep=" ")')
            assert 'prfunc_return_val' in ip.user_ns
        finally:
            # Reset compiler flags so we don't mess up other tests.
            ip.compile.reset_compiler_flags()

    def test_future_unicode(self):
        """Check that unicode_literals is imported from __future__ (gh #786)"""
        try:
            ip.run_cell(u'byte_str = "a"')
            assert isinstance(ip.user_ns['byte_str'], str) # string literals are byte strings by default
            ip.run_cell('from __future__ import unicode_literals')
            ip.run_cell(u'unicode_str = "a"')
            assert isinstance(ip.user_ns['unicode_str'], unicode) # strings literals are now unicode
        finally:
            # Reset compiler flags so we don't mess up other tests.
            ip.compile.reset_compiler_flags()
    
    def test_can_pickle(self):
        "Can we pickle objects defined interactively (GH-29)"
        ip = get_ipython()
        ip.reset()
        ip.run_cell(("class Mylist(list):\n"
                     "    def __init__(self,x=[]):\n"
                     "        list.__init__(self,x)"))
        ip.run_cell("w=Mylist([1,2,3])")
        
        from cPickle import dumps
        
        # We need to swap in our main module - this is only necessary
        # inside the test framework, because IPython puts the interactive module
        # in place (but the test framework undoes this).
        _main = sys.modules['__main__']
        sys.modules['__main__'] = ip.user_module
        try:
            res = dumps(ip.user_ns["w"])
        finally:
            sys.modules['__main__'] = _main
        self.assertTrue(isinstance(res, bytes))
        
    def test_global_ns(self):
        "Code in functions must be able to access variables outside them."
        ip = get_ipython()
        ip.run_cell("a = 10")
        ip.run_cell(("def f(x):\n"
                     "    return x + a"))
        ip.run_cell("b = f(12)")
        self.assertEqual(ip.user_ns["b"], 22)

    def test_bad_custom_tb(self):
        """Check that InteractiveShell is protected from bad custom exception handlers"""
        from IPython.utils import io
        save_stderr = io.stderr
        try:
            # capture stderr
            io.stderr = StringIO()
            ip.set_custom_exc((IOError,), lambda etype,value,tb: 1/0)
            self.assertEqual(ip.custom_exceptions, (IOError,))
            ip.run_cell(u'raise IOError("foo")')
            self.assertEqual(ip.custom_exceptions, ())
            self.assertTrue("Custom TB Handler failed" in io.stderr.getvalue())
        finally:
            io.stderr = save_stderr

    def test_bad_custom_tb_return(self):
        """Check that InteractiveShell is protected from bad return types in custom exception handlers"""
        from IPython.utils import io
        save_stderr = io.stderr
        try:
            # capture stderr
            io.stderr = StringIO()
            ip.set_custom_exc((NameError,),lambda etype,value,tb, tb_offset=None: 1)
            self.assertEqual(ip.custom_exceptions, (NameError,))
            ip.run_cell(u'a=abracadabra')
            self.assertEqual(ip.custom_exceptions, ())
            self.assertTrue("Custom TB Handler failed" in io.stderr.getvalue())
        finally:
            io.stderr = save_stderr

    def test_drop_by_id(self):
        myvars = {"a":object(), "b":object(), "c": object()}
        ip.push(myvars, interactive=False)
        for name in myvars:
            assert name in ip.user_ns, name
            assert name in ip.user_ns_hidden, name
        ip.user_ns['b'] = 12
        ip.drop_by_id(myvars)
        for name in ["a", "c"]:
            assert name not in ip.user_ns, name
            assert name not in ip.user_ns_hidden, name
        assert ip.user_ns['b'] == 12
        ip.reset()

    def test_var_expand(self):
        ip.user_ns['f'] = u'Ca\xf1o'
        self.assertEqual(ip.var_expand(u'echo $f'), u'echo Ca\xf1o')
        self.assertEqual(ip.var_expand(u'echo {f}'), u'echo Ca\xf1o')
        self.assertEqual(ip.var_expand(u'echo {f[:-1]}'), u'echo Ca\xf1')
        self.assertEqual(ip.var_expand(u'echo {1*2}'), u'echo 2')

        ip.user_ns['f'] = b'Ca\xc3\xb1o'
        # This should not raise any exception:
        ip.var_expand(u'echo $f')
    
    def test_var_expand_local(self):
        """Test local variable expansion in !system and %magic calls"""
        # !system
        ip.run_cell('def test():\n'
                    '    lvar = "ttt"\n'
                    '    ret = !echo {lvar}\n'
                    '    return ret[0]\n')
        res = ip.user_ns['test']()
        nt.assert_in('ttt', res)
        
        # %magic
        ip.run_cell('def makemacro():\n'
                    '    macroname = "macro_var_expand_locals"\n'
                    '    %macro {macroname} codestr\n')
        ip.user_ns['codestr'] = "str(12)"
        ip.run_cell('makemacro()')
        nt.assert_in('macro_var_expand_locals', ip.user_ns)
    
    def test_bad_var_expand(self):
        """var_expand on invalid formats shouldn't raise"""
        # SyntaxError
        self.assertEqual(ip.var_expand(u"{'a':5}"), u"{'a':5}")
        # NameError
        self.assertEqual(ip.var_expand(u"{asdf}"), u"{asdf}")
        # ZeroDivisionError
        self.assertEqual(ip.var_expand(u"{1/0}"), u"{1/0}")
    
    def test_silent_nopostexec(self):
        """run_cell(silent=True) doesn't invoke post-exec funcs"""
        d = dict(called=False)
        def set_called():
            d['called'] = True
        
        ip.register_post_execute(set_called)
        ip.run_cell("1", silent=True)
        self.assertFalse(d['called'])
        # double-check that non-silent exec did what we expected
        # silent to avoid
        ip.run_cell("1")
        self.assertTrue(d['called'])
        # remove post-exec
        ip._post_execute.pop(set_called)
    
    def test_silent_noadvance(self):
        """run_cell(silent=True) doesn't advance execution_count"""
        ec = ip.execution_count
        # silent should force store_history=False
        ip.run_cell("1", store_history=True, silent=True)
        
        self.assertEqual(ec, ip.execution_count)
        # double-check that non-silent exec did what we expected
        # silent to avoid
        ip.run_cell("1", store_history=True)
        self.assertEqual(ec+1, ip.execution_count)
    
    def test_silent_nodisplayhook(self):
        """run_cell(silent=True) doesn't trigger displayhook"""
        d = dict(called=False)
        
        trap = ip.display_trap
        save_hook = trap.hook
        
        def failing_hook(*args, **kwargs):
            d['called'] = True
        
        try:
            trap.hook = failing_hook
            ip.run_cell("1", silent=True)
            self.assertFalse(d['called'])
            # double-check that non-silent exec did what we expected
            # silent to avoid
            ip.run_cell("1")
            self.assertTrue(d['called'])
        finally:
            trap.hook = save_hook

    @skipif(sys.version_info[0] >= 3, "softspace removed in py3")
    def test_print_softspace(self):
        """Verify that softspace is handled correctly when executing multiple
        statements.

        In [1]: print 1; print 2
        1
        2

        In [2]: print 1,; print 2
        1 2
        """
        
    def test_ofind_line_magic(self):
        from IPython.core.magic import register_line_magic
        
        @register_line_magic
        def lmagic(line):
            "A line magic"

        # Get info on line magic
        lfind = ip._ofind('lmagic')
        info = dict(found=True, isalias=False, ismagic=True,
                    namespace = 'IPython internal', obj= lmagic.__wrapped__,
                    parent = None)
        nt.assert_equal(lfind, info)
        
    def test_ofind_cell_magic(self):
        from IPython.core.magic import register_cell_magic
        
        @register_cell_magic
        def cmagic(line, cell):
            "A cell magic"

        # Get info on cell magic
        find = ip._ofind('cmagic')
        info = dict(found=True, isalias=False, ismagic=True,
                    namespace = 'IPython internal', obj= cmagic.__wrapped__,
                    parent = None)
        nt.assert_equal(find, info)
    
    def test_custom_exception(self):
        called = []
        def my_handler(shell, etype, value, tb, tb_offset=None):
            called.append(etype)
            shell.showtraceback((etype, value, tb), tb_offset=tb_offset)
        
        ip.set_custom_exc((ValueError,), my_handler)
        try:
            ip.run_cell("raise ValueError('test')")
            # Check that this was called, and only once.
            self.assertEqual(called, [ValueError])
        finally:
            # Reset the custom exception hook
            ip.set_custom_exc((), None)


class TestSafeExecfileNonAsciiPath(unittest.TestCase):

    def setUp(self):
        self.BASETESTDIR = tempfile.mkdtemp()
        self.TESTDIR = join(self.BASETESTDIR, u"åäö")
        os.mkdir(self.TESTDIR)
        with open(join(self.TESTDIR, u"åäötestscript.py"), "w") as sfile:
            sfile.write("pass\n")
        self.oldpath = os.getcwdu()
        os.chdir(self.TESTDIR)
        self.fname = u"åäötestscript.py"

    def tearDown(self):
        os.chdir(self.oldpath)
        shutil.rmtree(self.BASETESTDIR)

    def test_1(self):
        """Test safe_execfile with non-ascii path
        """
        ip.safe_execfile(self.fname, {}, raise_exceptions=True)


class TestSystemRaw(unittest.TestCase):
    def test_1(self):
        """Test system_raw with non-ascii cmd
        """
        cmd = ur'''python -c "'åäö'"   '''
        ip.system_raw(cmd)

class TestModules(unittest.TestCase, tt.TempFileMixin):
    def test_extraneous_loads(self):
        """Test we're not loading modules on startup that we shouldn't.
        """
        self.mktmp("import sys\n"
                   "print('numpy' in sys.modules)\n"
                   "print('IPython.parallel' in sys.modules)\n"
                   "print('IPython.zmq' in sys.modules)\n"
                   )
        out = "False\nFalse\nFalse\n"
        tt.ipexec_validate(self.fname, out)

class Negator(ast.NodeTransformer):
    """Negates all number literals in an AST."""
    def visit_Num(self, node):
        node.n = -node.n
        return node

class TestAstTransform(unittest.TestCase):
    def setUp(self):
        self.negator = Negator()
        ip.ast_transformers.append(self.negator)
    
    def tearDown(self):
        ip.ast_transformers.remove(self.negator)
    
    def test_run_cell(self):
        with tt.AssertPrints('-34'):
            ip.run_cell('print (12 + 22)')
        
        # A named reference to a number shouldn't be transformed.
        ip.user_ns['n'] = 55
        with tt.AssertNotPrints('-55'):
            ip.run_cell('print (n)')
    
    def test_timeit(self):
        called = set()
        def f(x):
            called.add(x)
        ip.push({'f':f})
        
        with tt.AssertPrints("best of "):
            ip.run_line_magic("timeit", "-n1 f(1)")
        self.assertEqual(called, set([-1]))
        called.clear()
        
        with tt.AssertPrints("best of "):
            ip.run_cell_magic("timeit", "-n1 f(2)", "f(3)")
        self.assertEqual(called, set([-2, -3]))
    
    def test_time(self):
        called = []
        def f(x):
            called.append(x)
        ip.push({'f':f})
        
        # Test with an expression
        with tt.AssertPrints("CPU times"):
            ip.run_line_magic("time", "f(5+9)")
        self.assertEqual(called, [-14])
        called[:] = []
        
        # Test with a statement (different code path)
        with tt.AssertPrints("CPU times"):
            ip.run_line_magic("time", "a = f(-3 + -2)")
        self.assertEqual(called, [5])
    
    def test_macro(self):
        ip.push({'a':10})
        # The AST transformation makes this do a+=-1
        ip.define_macro("amacro", "a+=1\nprint(a)")
        
        with tt.AssertPrints("9"):
            ip.run_cell("amacro")
        with tt.AssertPrints("8"):
            ip.run_cell("amacro")

class IntegerWrapper(ast.NodeTransformer):
    """Wraps all integers in a call to Integer()"""
    def visit_Num(self, node):
        if isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='Integer', ctx=ast.Load()),
                            args=[node], keywords=[])

class TestAstTransform2(unittest.TestCase):
    def setUp(self):
        self.intwrapper = IntegerWrapper()
        ip.ast_transformers.append(self.intwrapper)
        
        self.calls = []
        def Integer(*args):
            self.calls.append(args)
            return args
        ip.push({"Integer": Integer})
    
    def tearDown(self):
        ip.ast_transformers.remove(self.intwrapper)
        del ip.user_ns['Integer']
    
    def test_run_cell(self):
        ip.run_cell("n = 2")
        self.assertEqual(self.calls, [(2,)])
    
    def test_timeit(self):
        called = set()
        def f(x):
            called.add(x)
        ip.push({'f':f})
        
        with tt.AssertPrints("best of "):
            ip.run_line_magic("timeit", "-n1 f(1)")
        self.assertEqual(called, set([(1,)]))
        called.clear()
        
        with tt.AssertPrints("best of "):
            ip.run_cell_magic("timeit", "-n1 f(2)", "f(3)")
        self.assertEqual(called, set([(2,), (3,)]))

class ErrorTransformer(ast.NodeTransformer):
    """Throws an error when it sees a number."""
    def visit_Num(self):
        raise ValueError("test")

class TestAstTransformError(unittest.TestCase):
    def test_unregistering(self):
        err_transformer = ErrorTransformer()
        ip.ast_transformers.append(err_transformer)
        
        with tt.AssertPrints("unregister", channel='stderr'):
            ip.run_cell("1 + 2")
        
        # This should have been removed.
        nt.assert_not_in(err_transformer, ip.ast_transformers)

def test__IPYTHON__():
    # This shouldn't raise a NameError, that's all
    __IPYTHON__

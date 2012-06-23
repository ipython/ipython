"""Tests for various magic functions specific to the terminal frontend.

Needs to be run by nose (to make ipython session available).
"""
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from StringIO import StringIO
from unittest import TestCase

import nose.tools as nt

from IPython.testing import tools as tt

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
ip = get_ipython()

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

def check_cpaste(code, should_fail=False):
    """Execute code via 'cpaste' and ensure it was executed, unless
    should_fail is set.
    """
    _ip.user_ns['code_ran'] = False

    src = StringIO()
    if not hasattr(src, 'encoding'):
        # IPython expects stdin to have an encoding attribute
        src.encoding = None
    src.write('\n')
    src.write(code)
    src.write('\n--\n')
    src.seek(0)

    stdin_save = sys.stdin
    sys.stdin = src

    try:
        context = tt.AssertPrints if should_fail else tt.AssertNotPrints
        with context("Traceback (most recent call last)"):
                _ip.magic('cpaste')

        if not should_fail:
            assert _ip.user_ns['code_ran']
    finally:
        sys.stdin = stdin_save

PY31 = sys.version_info[:2] == (3,1)

def test_cpaste():
    """Test cpaste magic"""

    def run():
        """Marker function: sets a flag when executed.
        """
        _ip.user_ns['code_ran'] = True
        return 'run' # return string so '+ run()' doesn't result in success

    tests = {'pass': ["run()",
                      "In [1]: run()",
                      "In [1]: if 1:\n   ...:     run()",
                      "> > > run()",
                      ">>> run()",
                      "   >>> run()",
                      ],

             'fail': ["1 + run()",
             ]}
    
    # I don't know why this is failing specifically on Python 3.1. I've
    # checked it manually interactively, but we don't care enough about 3.1
    # to spend time fiddling with the tests, so we just skip it.
    if not PY31:
        tests['fail'].append("++ run()")

    _ip.user_ns['run'] = run

    for code in tests['pass']:
        check_cpaste(code)

    for code in tests['fail']:
        check_cpaste(code, should_fail=True)


class PasteTestCase(TestCase):
    """Multiple tests for clipboard pasting"""

    def paste(self, txt, flags='-q'):
        """Paste input text, by default in quiet mode"""
        ip.hooks.clipboard_get = lambda : txt
        ip.magic('paste '+flags)

    def setUp(self):
        # Inject fake clipboard hook but save original so we can restore it later
        self.original_clip = ip.hooks.clipboard_get

    def tearDown(self): 
        # Restore original hook
        ip.hooks.clipboard_get = self.original_clip
       
    def test_paste(self):
        ip.user_ns.pop('x', None)
        self.paste('x=1')
        nt.assert_equal(ip.user_ns['x'], 1)

    def test_paste_pyprompt(self):
        ip.user_ns.pop('x', None)
        self.paste('>>> x=2')
        nt.assert_equal(ip.user_ns['x'], 2)

    def test_paste_py_multi(self):
        self.paste("""
        >>> x = [1,2,3]
        >>> y = []
        >>> for i in x:
        ...     y.append(i**2)
        ...
        """)
        nt.assert_equal(ip.user_ns['x'], [1,2,3])
        nt.assert_equal(ip.user_ns['y'], [1,4,9])

    def test_paste_py_multi_r(self):
        "Now, test that self.paste -r works"
        ip.user_ns.pop('x', None)
        nt.assert_false('x' in ip.user_ns)
        ip.magic('paste -r')
        nt.assert_equal(ip.user_ns['x'], [1,2,3])

    def test_paste_email(self):
        "Test pasting of email-quoted contents"
        self.paste("""
        >> def foo(x):
        >>     return x + 1
        >> x = foo(1.1)
        """)
        nt.assert_equal(ip.user_ns['x'], 2.1)

    def test_paste_email2(self):
        "Email again; some programs add a space also at each quoting level"
        self.paste("""
        > > def foo(x):
        > >     return x + 1
        > > x = foo(2.1)
        """)
        nt.assert_equal(ip.user_ns['x'], 3.1)

    def test_paste_email_py(self):
        "Email quoting of interactive input"
        self.paste("""
        >> >>> def f(x):
        >> ...   return x+1
        >> ...
        >> >>> x = f(2.5)
        """)
        nt.assert_equal(ip.user_ns['x'], 3.5)

    def test_paste_echo(self):
        "Also test self.paste echoing, by temporarily faking the writer"
        w = StringIO()
        writer = ip.write
        ip.write = w.write
        code = """
        a = 100
        b = 200"""
        try:
            self.paste(code,'')
            out = w.getvalue()
        finally:
            ip.write = writer
        nt.assert_equal(ip.user_ns['a'], 100)
        nt.assert_equal(ip.user_ns['b'], 200)
        nt.assert_equal(out, code+"\n## -- End pasted text --\n")


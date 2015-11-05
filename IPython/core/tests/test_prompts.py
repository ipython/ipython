# -*- coding: utf-8
"""Tests for prompt generation."""

import unittest

import os

from IPython.testing import tools as tt, decorators as dec
from IPython.core.prompts import PromptManager, LazyEvaluate, _invisible_characters
from IPython.testing.globalipapp import get_ipython
from IPython.utils.tempdir import TemporaryWorkingDirectory
from IPython.utils import py3compat
from IPython.utils.py3compat import unicode_type

ip = get_ipython()


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.pm = PromptManager(shell=ip, config=ip.config)
    
    def test_multiline_prompt(self):
        self.pm.in_template = "[In]\n>>>"
        self.pm.render('in')
        self.assertEqual(self.pm.width, 3)
        self.assertEqual(self.pm.txtwidth, 3)
        
        self.pm.in_template = '[In]\n'
        self.pm.render('in')
        self.assertEqual(self.pm.width, 0)
        self.assertEqual(self.pm.txtwidth, 0)
    
    def test_translate_abbreviations(self):
        def do_translate(template):
            self.pm.in_template = template
            return self.pm.templates['in']
        
        pairs = [(r'%n>', '{color.number}{count}{color.prompt}>'),
                 (r'\T', '{time}'),
                 (r'\n', '\n')
                ]
    
        tt.check_pairs(do_translate, pairs)
    
    def test_user_ns(self):
        self.pm.color_scheme = 'NoColor'
        ip.ex("foo='bar'")
        self.pm.in_template = "In [{foo}]"
        prompt = self.pm.render('in')
        self.assertEqual(prompt, u'In [bar]')

    def test_builtins(self):
        self.pm.color_scheme = 'NoColor'
        self.pm.in_template = "In [{int}]"
        prompt = self.pm.render('in')
        self.assertEqual(prompt, u"In [%r]" % int)

    def test_undefined(self):
        self.pm.color_scheme = 'NoColor'
        self.pm.in_template = "In [{foo_dne}]"
        prompt = self.pm.render('in')
        self.assertEqual(prompt, u"In [<ERROR: 'foo_dne' not found>]")

    def test_render(self):
        self.pm.in_template = r'\#>'
        self.assertEqual(self.pm.render('in',color=False), '%d>' % ip.execution_count)
    
    @dec.onlyif_unicode_paths
    def test_render_unicode_cwd(self):
        with TemporaryWorkingDirectory(u'ünicødé'):
            self.pm.in_template = r'\w [\#]'
            p = self.pm.render('in', color=False)
            self.assertEqual(p, u"%s [%i]" % (py3compat.getcwd(), ip.execution_count))
    
    def test_lazy_eval_unicode(self):
        u = u'ünicødé'
        lz = LazyEvaluate(lambda : u)
        # str(lz) would fail
        self.assertEqual(unicode_type(lz), u)
        self.assertEqual(format(lz), u)
    
    def test_lazy_eval_nonascii_bytes(self):
        u = u'ünicødé'
        b = u.encode('utf8')
        lz = LazyEvaluate(lambda : b)
        # unicode(lz) would fail
        self.assertEqual(str(lz), str(b))
        self.assertEqual(format(lz), str(b))
    
    def test_lazy_eval_float(self):
        f = 0.503
        lz = LazyEvaluate(lambda : f)
        
        self.assertEqual(str(lz), str(f))
        self.assertEqual(unicode_type(lz), unicode_type(f))
        self.assertEqual(format(lz), str(f))
        self.assertEqual(format(lz, '.1'), '0.5')
    
    @dec.skip_win32
    def test_cwd_x(self):
        self.pm.in_template = r"\X0"
        save = py3compat.getcwd()
        os.chdir(os.path.expanduser('~'))
        p = self.pm.render('in', color=False)
        try:
            self.assertEqual(p, '~')
        finally:
            os.chdir(save)

    def test_invisible_chars(self):
        self.assertEqual(_invisible_characters('abc'), 0)
        self.assertEqual(_invisible_characters('\001\033[1;37m\002'), 9)
        # Sequences must be between \001 and \002 to be counted
        self.assertEqual(_invisible_characters('\033[1;37m'), 0)
        # Test custom escape sequences
        self.assertEqual(_invisible_characters('\001\033]133;A\a\002'), 10)

    def test_width(self):
        default_in = '\x01\x1b]133;A\x07\x02In [1]: \x01\x1b]133;B\x07\x02'
        self.pm.in_template = default_in
        self.pm.render('in')
        self.assertEqual(self.pm.width, 8)
        self.assertEqual(self.pm.txtwidth, 8)

        # Test custom escape sequences
        self.pm.in_template = '\001\033]133;A\a\002' + default_in + '\001\033]133;B\a\002'
        self.pm.render('in')
        self.assertEqual(self.pm.width, 8)
        self.assertEqual(self.pm.txtwidth, 8)

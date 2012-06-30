# -*- coding: utf-8
"""Tests for prompt generation."""

import unittest

import os
import nose.tools as nt

from IPython.testing import tools as tt, decorators as dec
from IPython.core.prompts import PromptManager, LazyEvaluate
from IPython.testing.globalipapp import get_ipython
from IPython.utils import py3compat
from IPython.utils.tempdir import TemporaryDirectory

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
        self.assertEquals(prompt, u'In [bar]')

    def test_builtins(self):
        self.pm.color_scheme = 'NoColor'
        self.pm.in_template = "In [{int}]"
        prompt = self.pm.render('in')
        self.assertEquals(prompt, u"In [%r]" % int)

    def test_undefined(self):
        self.pm.color_scheme = 'NoColor'
        self.pm.in_template = "In [{foo_dne}]"
        prompt = self.pm.render('in')
        self.assertEquals(prompt, u"In [<ERROR: 'foo_dne' not found>]")

    def test_render(self):
        self.pm.in_template = r'\#>'
        self.assertEqual(self.pm.render('in',color=False), '%d>' % ip.execution_count)
    
    def test_render_unicode_cwd(self):
        save = os.getcwdu()
        with TemporaryDirectory(u'ünicødé') as td:
            os.chdir(td)
            self.pm.in_template = r'\w [\#]'
            p = self.pm.render('in', color=False)
            self.assertEquals(p, u"%s [%i]" % (os.getcwdu(), ip.execution_count))
        os.chdir(save)
    
    def test_lazy_eval_unicode(self):
        u = u'ünicødé'
        lz = LazyEvaluate(lambda : u)
        # str(lz) would fail
        self.assertEquals(unicode(lz), u)
        self.assertEquals(format(lz), u)
    
    def test_lazy_eval_nonascii_bytes(self):
        u = u'ünicødé'
        b = u.encode('utf8')
        lz = LazyEvaluate(lambda : b)
        # unicode(lz) would fail
        self.assertEquals(str(lz), str(b))
        self.assertEquals(format(lz), str(b))
    
    def test_lazy_eval_float(self):
        f = 0.503
        lz = LazyEvaluate(lambda : f)
        
        self.assertEquals(str(lz), str(f))
        self.assertEquals(unicode(lz), unicode(f))
        self.assertEquals(format(lz), str(f))
        self.assertEquals(format(lz, '.1'), '0.5')
    
    @dec.skip_win32
    def test_cwd_x(self):
        self.pm.in_template = r"\X0"
        save = os.getcwdu()
        os.chdir(os.path.expanduser('~'))
        p = self.pm.render('in', color=False)
        try:
            self.assertEquals(p, '~')
        finally:
            os.chdir(save)
    

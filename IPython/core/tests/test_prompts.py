"""Tests for prompt generation."""

import unittest

import nose.tools as nt

from IPython.testing import tools as tt, decorators as dec
from IPython.core.prompts import PromptManager
from IPython.testing.globalipapp import get_ipython

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

"""
Module with tests for ansi filters
"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.utils.coloransi import TermColors

from ...tests.base import TestsBase
from ..ansi import strip_ansi, ansi2html, ansi2latex


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestAnsi(TestsBase):
    """Contains test functions for ansi.py"""

    def test_strip_ansi(self):
        """strip_ansi test"""
        correct_outputs = {
            '%s%s%s' % (TermColors.Green, TermColors.White, TermColors.Red)  : '',
            'hello%s' % TermColors.Blue: 'hello',
            'he%s%sllo' % (TermColors.Yellow, TermColors.Cyan) : 'hello',
            '%shello' % TermColors.Blue : 'hello',
            '{0}h{0}e{0}l{0}l{0}o{0}'.format(TermColors.Red) : 'hello',
            'hel%slo' % TermColors.Green : 'hello',
            'hello' : 'hello'}

        for inval, outval in correct_outputs.items():
            self._try_strip_ansi(inval, outval)


    def _try_strip_ansi(self, inval, outval):
        self.assertEqual(outval, strip_ansi(inval))


    def test_ansi2html(self):
        """ansi2html test"""
        correct_outputs = {
            '%s' % (TermColors.Red)  : '<span class="ansired"></span>',
            'hello%s' % TermColors.Blue: 'hello<span class="ansiblue"></span>',
            'he%s%sllo' % (TermColors.Green, TermColors.Cyan) : 'he<span class="ansigreen"></span><span class="ansicyan">llo</span>',
            '%shello' % TermColors.Yellow : '<span class="ansiyellow">hello</span>',
            '{0}h{0}e{0}l{0}l{0}o{0}'.format(TermColors.White) : '<span class="ansigrey">h</span><span class="ansigrey">e</span><span class="ansigrey">l</span><span class="ansigrey">l</span><span class="ansigrey">o</span><span class="ansigrey"></span>',
            'hel%slo' % TermColors.Green : 'hel<span class="ansigreen">lo</span>',
            'hello' : 'hello'}

        for inval, outval in correct_outputs.items():
            self._try_ansi2html(inval, outval)


    def _try_ansi2html(self, inval, outval):
        self.fuzzy_compare(outval, ansi2html(inval))


    def test_ansi2latex(self):
        """ansi2latex test"""
        correct_outputs = {
            '%s' % (TermColors.Red)  : r'{\color{red}}',
            'hello%s' % TermColors.Blue: r'hello{\color{blue}}',
            'he%s%sllo' % (TermColors.Green, TermColors.Cyan) : r'he{\color{green}}{\color{cyan}llo}',
            '%shello' % TermColors.Yellow : r'\textbf{\color{yellow}hello}',
            '{0}h{0}e{0}l{0}l{0}o{0}'.format(TermColors.White) : r'\textbf{\color{white}h}\textbf{\color{white}e}\textbf{\color{white}l}\textbf{\color{white}l}\textbf{\color{white}o}\textbf{\color{white}}',
            'hel%slo' % TermColors.Green : r'hel{\color{green}lo}',
            'hello' : 'hello',
            u'hello\x1b[34mthere\x1b[mworld' : u'hello{\\color{blue}there}world',
            u'hello\x1b[mthere': u'hellothere',
            u'hello\x1b[01;34mthere' : u"hello\\textbf{\\color{lightblue}there}",
            u'hello\x1b[001;34mthere' : u"hello\\textbf{\\color{lightblue}there}"
            }

        for inval, outval in correct_outputs.items():
            self._try_ansi2latex(inval, outval)


    def _try_ansi2latex(self, inval, outval):
        self.fuzzy_compare(outval, ansi2latex(inval), case_sensitive=True)

"""
Module with tests for Strings
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


from ...tests.base import TestsBase
from ..strings import *


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestStrings(TestsBase):

    def test_wrap_text(self):
        """
        wrap_text test
        """
        test_text = """
        Tush! never tell me; I take it much unkindly
        That thou, Iago, who hast had my purse
        As if the strings were thine, shouldst know of this.
        """
        for length in [30,5,1]:
            yield self._confirm_wrap_text, test_text, length
    
    def _confirm_wrap_text(self, text, length):
        for line in wrap_text(text, length).split('\n'):
            assert len(line) <= length

    def test_html2text(self):
        """
        html2text test
        """
        #TODO: More tests
        assert html2text('<name>joe</name>') == 'joe'
        

    def test_add_anchor(self):
        """
        add_anchor test
        """
        #TODO: More tests
        self.fuzzy_compare(add_anchor('<b>Hello World!</b>'), '<b id="Hello-World!">Hello World!<a class="anchor-link" href="#Hello-World!">&#182;</a></b>')

        
    def test_strip_dollars(self):
        """
        strip_dollars test
        """
        tests = [
            ('', ''), 
            ('$$', ''), 
            ('$H$', 'H'), 
            ('$He', 'He'), 
            ('H$el', 'H$el'), 
            ('Hell$', 'Hell'),
            ('Hello', 'Hello'),
            ('W$o$rld', 'W$o$rld')]
        for test in tests:
            yield self._try_strip_dollars, test[0], test[1]


    def _try_strip_dollars(self, test, result):
        assert strip_dollars(test) == result


    def test_strip_files_prefix(self):
        """
        strip_files_prefix test
        """
        tests = [
            ('', ''), 
            ('/files', '/files'), 
            ('test="/files"', 'test="/files"'), 
            ('My files are in `files/`', 'My files are in `files/`'),
            ('<a href="files/test.html">files/test.html</a>', '<a href="test.html">files/test.html</a>')]
        for test in tests:
            yield self._try_files_prefix, test[0], test[1]


    def _try_files_prefix(self, test, result):
        assert strip_files_prefix(test) == result
        

    def test_comment_lines(self):
        """
        comment_lines test
        """
        for line in comment_lines('hello\nworld\n!').split('\n'):
            assert line.startswith('# ')
        for line in comment_lines('hello\nworld\n!', 'beep').split('\n'):
            assert line.startswith('beep')
        

    def test_get_lines(self):
        """
        get_lines test
        """
        text = "hello\nworld\n!"
        assert get_lines(text, start=1) == "world\n!"
        assert get_lines(text, end=2) == "hello\nworld"
        assert get_lines(text, start=2, end=5) == "!"
        assert get_lines(text, start=-2) == "world\n!"
        

    def test_ipython2python(self):
        """
        ipython2python test
        """
        #TODO: More tests
        results = ipython2python(u'%%pylab\nprint("Hello-World")')
        self.fuzzy_compare(results, u"get_ipython().run_cell_magic(u'pylab', u'', u'print(\"Hello-World\")')", 
            ignore_spaces=True, ignore_newlines=True)

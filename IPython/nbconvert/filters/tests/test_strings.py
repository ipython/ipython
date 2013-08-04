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
import os

from IPython.testing import decorators as dec
from ...tests.base import TestsBase
from ..strings import (wrap_text, html2text, add_anchor, strip_dollars, 
    strip_files_prefix, get_lines, comment_lines, ipython2python, posix_path,
)


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestStrings(TestsBase):

    def test_wrap_text(self):
        """wrap_text test"""
        test_text = """
        Tush! never tell me; I take it much unkindly
        That thou, Iago, who hast had my purse
        As if the strings were thine, shouldst know of this.
        """
        for length in [30,5,1]:
            yield self._confirm_wrap_text(test_text, length)
    

    def _confirm_wrap_text(self, text, length):
        for line in wrap_text(text, length).split('\n'):
            assert len(line) <= length


    def test_html2text(self):
        """html2text test"""
        #TODO: More tests
        self.assertEqual(html2text('<name>joe</name>'), 'joe')
        

    def test_add_anchor(self):
        """add_anchor test"""
        #TODO: More tests
        results = add_anchor('<b>Hello World!</b>')
        assert 'Hello World!' in results
        assert 'id="' in results
        assert 'class="anchor-link"' in results
        assert '<b' in results
        assert '</b>' in results

        
    def test_strip_dollars(self):
        """strip_dollars test"""
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
            yield self._try_strip_dollars(test[0], test[1])


    def _try_strip_dollars(self, test, result):
        self.assertEqual(strip_dollars(test), result)


    def test_strip_files_prefix(self):
        """strip_files_prefix test"""
        tests = [
            ('', ''), 
            ('/files', '/files'), 
            ('test="/files"', 'test="/files"'), 
            ('My files are in `files/`', 'My files are in `files/`'),
            ('<a href="files/test.html">files/test.html</a>', '<a href="test.html">files/test.html</a>')]
        for test in tests:
            yield self._try_files_prefix(test[0], test[1])


    def _try_files_prefix(self, test, result):
        self.assertEqual(strip_files_prefix(test), result)
        

    def test_comment_lines(self):
        """comment_lines test"""
        for line in comment_lines('hello\nworld\n!').split('\n'):
            assert line.startswith('# ')
        for line in comment_lines('hello\nworld\n!', 'beep').split('\n'):
            assert line.startswith('beep')
        

    def test_get_lines(self):
        """get_lines test"""
        text = "hello\nworld\n!"
        self.assertEqual(get_lines(text, start=1), "world\n!")
        self.assertEqual(get_lines(text, end=2), "hello\nworld")
        self.assertEqual(get_lines(text, start=2, end=5), "!")
        self.assertEqual(get_lines(text, start=-2), "world\n!")
        

    def test_ipython2python(self):
        """ipython2python test"""
        #TODO: More tests
        results = ipython2python(u'%%pylab\nprint("Hello-World")').replace("u'", "'")
        self.fuzzy_compare(results, u"get_ipython().run_cell_magic('pylab', '', 'print(\"Hello-World\")')", 
            ignore_spaces=True, ignore_newlines=True)
    
    def test_posix_path(self):
        path_list = ['foo', 'bar']
        expected = '/'.join(path_list)
        native = os.path.join(*path_list)
        filtered = posix_path(native)
        self.assertEqual(filtered, expected)

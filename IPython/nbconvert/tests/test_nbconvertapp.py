# -*- coding: utf-8 -*- 
"""Test NbConvertApp"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import glob
import sys

from .base import TestsBase

import IPython.testing.tools as tt
from IPython.testing import decorators as dec

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestNbConvertApp(TestsBase):
    """Collection of NbConvertApp tests"""


    def test_notebook_help(self):
        """Will help show if no notebooks are specified?"""
        with self.create_temp_cwd():
            out, err = self.call('nbconvert --log-level 0', ignore_return_code=True)
            self.assertIn("see '--help-all'", out)
    
    def test_help_output(self):
        """ipython nbconvert --help-all works"""
        tt.help_all_output_test('nbconvert')

    def test_glob(self):
        """
        Do search patterns work for notebook names?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            self.call('nbconvert --to python *.ipynb --log-level 0')
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_glob_subdir(self):
        """
        Do search patterns work for subdirectory notebook names?
        """
        with self.create_temp_cwd():
            self.copy_files_to(['notebook*.ipynb'], 'subdir/')
            self.call('nbconvert --to python --log-level 0 ' + 
                      os.path.join('subdir', '*.ipynb'))
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_explicit(self):
        """
        Do explicit notebook names work?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            self.call('nbconvert --log-level 0 --to python notebook2')
            assert not os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    @dec.onlyif_cmds_exist('pdflatex')
    @dec.onlyif_cmds_exist('pandoc')
    def test_filename_spaces(self):
        """
        Generate PDFs with graphics if notebooks have spaces in the name?
        """
        with self.create_temp_cwd(['notebook2.ipynb']):
            os.rename('notebook2.ipynb', 'notebook with spaces.ipynb')
            self.call('nbconvert --log-level 0 --to latex '
                            '"notebook with spaces" --post PDF '
                            '--PDFPostProcessor.verbose=True')
            assert os.path.isfile('notebook with spaces.tex')
            assert os.path.isdir('notebook with spaces_files')
            assert os.path.isfile('notebook with spaces.pdf')

    @dec.onlyif_cmds_exist('pdflatex')
    @dec.onlyif_cmds_exist('pandoc')
    def test_post_processor(self):
        """
        Do post processors work?
        """
        with self.create_temp_cwd(['notebook1.ipynb']):
            self.call('nbconvert --log-level 0 --to latex notebook1 '
                      '--post PDF --PDFPostProcessor.verbose=True')
            assert os.path.isfile('notebook1.tex')
            assert os.path.isfile('notebook1.pdf')

    @dec.onlyif_cmds_exist('pandoc')
    def test_spurious_cr(self):
        """Check for extra CR characters"""
        with self.create_temp_cwd(['notebook2.ipynb']):
            self.call('nbconvert --log-level 0 --to latex notebook2')
            assert os.path.isfile('notebook2.tex')
            with open('notebook2.tex') as f:
                tex = f.read()
            self.call('nbconvert --log-level 0 --to html notebook2')
            assert os.path.isfile('notebook2.html')
            with open('notebook2.html') as f:
                html = f.read()
        self.assertEqual(tex.count('\r'), tex.count('\r\n'))
        self.assertEqual(html.count('\r'), html.count('\r\n'))

    @dec.onlyif_cmds_exist('pandoc')
    def test_png_base64_html_ok(self):
        """Is embedded png data well formed in HTML?"""
        with self.create_temp_cwd(['notebook2.ipynb']):
            self.call('nbconvert --log-level 0 --to HTML '
                      'notebook2.ipynb --template full')
            assert os.path.isfile('notebook2.html')
            with open('notebook2.html') as f:
                assert "data:image/png;base64,b'" not in f.read()

    @dec.onlyif_cmds_exist('pandoc')
    def test_template(self):
        """
        Do export templates work?
        """
        with self.create_temp_cwd(['notebook2.ipynb']):
            self.call('nbconvert --log-level 0 --to slides '  
                      'notebook2.ipynb')
            assert os.path.isfile('notebook2.slides.html')
            with open('notebook2.slides.html') as f:
                assert '/reveal.css' in f.read()


    def test_glob_explicit(self):
        """
        Can a search pattern be used along with matching explicit notebook names?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            self.call('nbconvert --log-level 0 --to python '
                      '*.ipynb notebook1.ipynb notebook2.ipynb')
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_explicit_glob(self):
        """
        Can explicit notebook names be used and then a matching search pattern?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            self.call('nbconvert --log-level 0 --to=python '
                      'notebook1.ipynb notebook2.ipynb *.ipynb')
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_default_config(self):
        """
        Does the default config work?
        """
        with self.create_temp_cwd(['notebook*.ipynb', 'ipython_nbconvert_config.py']):
            self.call('nbconvert --log-level 0')
            assert os.path.isfile('notebook1.py')
            assert not os.path.isfile('notebook2.py')


    def test_override_config(self):
        """
        Can the default config be overriden?
        """
        with self.create_temp_cwd(['notebook*.ipynb',
                                   'ipython_nbconvert_config.py',
                                   'override.py']):
            self.call('nbconvert --log-level 0 --config="override.py"')
            assert not os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')

    def test_accents_in_filename(self):
        """
        Can notebook names include accents?
        """
        with self.create_temp_cwd():
            self.create_empty_notebook(u'nb1_análisis.ipynb')
            self.call('nbconvert --log-level 0 --to python nb1_*')
            assert os.path.isfile(u'nb1_análisis.py')
    
    @dec.onlyif_cmds_exist('pdflatex', 'pandoc')
    def test_filename_accent_pdf(self):
        """
        Generate PDFs if notebooks have an accent in their name?
        """
        with self.create_temp_cwd():
            self.create_empty_notebook(u'nb1_análisis.ipynb')
            self.call('nbconvert --log-level 0 --to latex '
                            '"nb1_*" --post PDF '
                            '--PDFPostProcessor.verbose=True')
            assert os.path.isfile(u'nb1_análisis.tex')
            assert os.path.isfile(u'nb1_análisis.pdf')

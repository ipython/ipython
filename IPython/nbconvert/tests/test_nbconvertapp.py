"""
Contains tests for the nbconvertapp
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
from .base import TestsBase

from IPython.utils import py3compat
from IPython.testing import decorators as dec

    
#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Define ipython commandline name
if py3compat.PY3:
    IPYTHON = 'ipython3'
else:
    IPYTHON = 'ipython'


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestNbConvertApp(TestsBase):
    """Collection of NbConvertApp tests"""


    def test_notebook_help(self):
        """
        Will help show if no notebooks are specified?
        """
        with self.create_temp_cwd():
            assert "see '--help-all'" in self.call([IPYTHON, 'nbconvert'])


    def test_glob(self):
        """
        Do search patterns work for notebook names?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', 
                '--to="python"', '--notebooks=["*.ipynb"]']).lower()
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_glob_subdir(self):
        """
        Do search patterns work for subdirectory notebook names?
        """
        with self.create_temp_cwd() as cwd:
            self.copy_files_to(['notebook*.ipynb'], 'subdir/')
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="python"', 
                '--notebooks=["%s"]' % os.path.join('subdir', '*.ipynb')]).lower()
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_explicit(self):
        """
        Do explicit notebook names work?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="python"', 
                '--notebooks=["notebook2.ipynb"]']).lower()
            assert not os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    #@dec.skip_known_failure
    def test_post_processor(self):
        """
        Do post processors work?
        """
        with self.create_temp_cwd(['notebook1.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="latex"', 
                'notebook1', '--post="PDF"', 'PDFPostProcessor.verbose=True']).lower()
            assert os.path.isfile('notebook1.tex')
            print("\n\n\t" + "\n\t".join([f for f in os.listdir('.') if os.path.isfile(f)]) + "\n\n")
            assert os.path.isfile('notebook1.pdf')


    def test_template(self):
        """
        Do export templates work?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="slides"', 
                '--notebooks=["notebook2.ipynb"]', '--template="reveal"']).lower()
            assert os.path.isfile('notebook2.html')
            with open('notebook2.html') as f:
                assert '/reveal.css' in f.read()


    def test_glob_explicit(self):
        """
        Can a search pattern be used along with matching explicit notebook names?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="python"', 
                '--notebooks=["*.ipynb", "notebook1.ipynb", "notebook2.ipynb"]']).lower()
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_explicit_glob(self):
        """
        Can explicit notebook names be used and then a matching search pattern?
        """
        with self.create_temp_cwd(['notebook*.ipynb']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--to="python"', 
                '--notebooks=["notebook1.ipynb", "notebook2.ipynb", "*.ipynb"]']).lower()
            assert os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')


    def test_default_config(self):
        """
        Does the default config work?
        """
        with self.create_temp_cwd(['notebook*.ipynb', 'ipython_nbconvert_config.py']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert']).lower()
            assert os.path.isfile('notebook1.py')
            assert not os.path.isfile('notebook2.py')


    def test_override_config(self):
        """
        Can the default config be overriden?
        """
        with self.create_temp_cwd(['notebook*.ipynb', 'ipython_nbconvert_config.py', 
                                   'override.py']):
            assert not 'error' in self.call([IPYTHON, 'nbconvert', '--config="override.py"']).lower()
            assert not os.path.isfile('notebook1.py')
            assert os.path.isfile('notebook2.py')

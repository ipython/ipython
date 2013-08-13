"""Tests for the notebook manager."""

import os
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError

from ..filenbmanager import FileNotebookManager
from ..nbmanager import NotebookManager

class TestFileNotebookManager(TestCase):

    def test_nb_dir(self):
        with TemporaryDirectory() as td:
            km = FileNotebookManager(notebook_dir=td)
            self.assertEqual(km.notebook_dir, td)

    def test_create_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebooks')
            km = FileNotebookManager(notebook_dir=nbdir)
            self.assertEqual(km.notebook_dir, nbdir)

    def test_missing_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebook', 'dir', 'is', 'missing')
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=nbdir)

    def test_invalid_nb_dir(self):
        with NamedTemporaryFile() as tf:
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=tf.name)

class TestNotebookManager(TestCase):
    def test_named_notebook_path(self):
        nm = NotebookManager()
        
        # doesn't end with ipynb, should just be path
        name, path = nm.named_notebook_path('hello')
        self.assertEqual(name, None)
        self.assertEqual(path, 'hello/')

        name, path = nm.named_notebook_path('hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, None)
        
        name, path = nm.named_notebook_path('/this/is/a/path/hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, '/this/is/a/path/')



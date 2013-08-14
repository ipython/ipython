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
            fm = FileNotebookManager(notebook_dir=td)
            self.assertEqual(fm.notebook_dir, td)

    def test_create_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebooks')
            fm = FileNotebookManager(notebook_dir=nbdir)
            self.assertEqual(fm.notebook_dir, nbdir)

    def test_missing_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebook', 'dir', 'is', 'missing')
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=nbdir)

    def test_invalid_nb_dir(self):
        with NamedTemporaryFile() as tf:
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=tf.name)

    def test_get_os_path(self):
        # full filesystem path should be returned with correct operating system
        # separators.
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebooks')
            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm.get_os_path('test.ipynb', '/path/to/notebook/')
            rel_path_list =  '/path/to/notebook/test.ipynb'.split('/')
            fs_path = os.path.join(fm.notebook_dir, *rel_path_list)
            self.assertEqual(path, fs_path)

            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm.get_os_path('test.ipynb')
            fs_path = os.path.join(fm.notebook_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm.get_os_path('test.ipynb', '////')
            fs_path = os.path.join(fm.notebook_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

class TestNotebookManager(TestCase):
    def test_named_notebook_path(self):
        nm = NotebookManager()

        # doesn't end with ipynb, should just be path
        name, path = nm.named_notebook_path('hello')
        self.assertEqual(name, None)
        self.assertEqual(path, '/hello/')

        name, path = nm.named_notebook_path('/')
        self.assertEqual(name, None)
        self.assertEqual(path, '/')

        name, path = nm.named_notebook_path('hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, '/')

        name, path = nm.named_notebook_path('/hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, '/')

        name, path = nm.named_notebook_path('/this/is/a/path/hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, '/this/is/a/path/')

        name, path = nm.named_notebook_path('path/without/leading/slash/hello.ipynb')
        self.assertEqual(name, 'hello.ipynb')
        self.assertEqual(path, '/path/without/leading/slash/')

    def test_url_encode(self):
        nm = NotebookManager()

        # changes path or notebook name with special characters to url encoding
        # these tests specifically encode paths with spaces
        path = nm.url_encode('/this is a test/for spaces/')
        self.assertEqual(path, '/this%20is%20a%20test/for%20spaces/')

        path = nm.url_encode('notebook with space.ipynb')
        self.assertEqual(path, 'notebook%20with%20space.ipynb')

        path = nm.url_encode('/path with a/notebook and space.ipynb')
        self.assertEqual(path, '/path%20with%20a/notebook%20and%20space.ipynb')

    def test_url_decode(self):
        nm = NotebookManager()
        
        # decodes a url string to a plain string
        # these tests decode paths with spaces
        path = nm.url_decode('/this%20is%20a%20test/for%20spaces/')
        self.assertEqual(path, '/this is a test/for spaces/')
        
        path = nm.url_decode('notebook%20with%20space.ipynb')
        self.assertEqual(path, 'notebook with space.ipynb')
        
        path = nm.url_decode('/path%20with%20a/notebook%20and%20space.ipynb')
        self.assertEqual(path, '/path with a/notebook and space.ipynb')

"""Tests for the notebook manager."""

import os

from tornado.web import HTTPError
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError
from IPython.html.utils import url_path_join

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
    
    def make_dir(self, abs_path, rel_path):
        """make subdirectory, rel_path is the relative path
        to that directory from the location where the server started"""
        os_path = os.path.join(abs_path, rel_path)
        try:
            os.makedirs(os_path)
        except OSError:
            print "Directory already exists."

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
        
        path = nm.url_encode('/ !@$#%^&* / test %^ notebook @#$ name.ipynb')
        self.assertEqual(path,
            '/%20%21%40%24%23%25%5E%26%2A%20/%20test%20%25%5E%20notebook%20%40%23%24%20name.ipynb')

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

        path = nm.url_decode(
            '/%20%21%40%24%23%25%5E%26%2A%20/%20test%20%25%5E%20notebook%20%40%23%24%20name.ipynb')
        self.assertEqual(path, '/ !@$#%^&* / test %^ notebook @#$ name.ipynb')

    def test_create_notebook_model(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook_model()
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], '/')

            # Test in sub-directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook_model(None, sub_dir)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], sub_dir)

    def test_get_notebook_model(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook_model()
            name = model['name']
            path = model['path']

            # Check that we 'get' on the notebook we just created
            model2 = nm.get_notebook_model(name, path)
            assert isinstance(model2, dict)
            self.assertIn('name', model2)
            self.assertIn('path', model2)
            self.assertEqual(model['name'], name)
            self.assertEqual(model['path'], path)

            # Test in sub-directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook_model(None, sub_dir)
            model2 = nm.get_notebook_model(name, sub_dir)
            assert isinstance(model2, dict)
            self.assertIn('name', model2)
            self.assertIn('path', model2)
            self.assertIn('content', model2)
            self.assertEqual(model2['name'], 'Untitled0.ipynb')
            self.assertEqual(model2['path'], sub_dir)
            
    def test_update_notebook_model(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook_model()
            name = model['name']
            path = model['path']

            # Change the name in the model for rename
            model['name'] = 'test.ipynb'
            model = nm.update_notebook_model(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'test.ipynb')

            # Make sure the old name is gone
            self.assertRaises(HTTPError, nm.get_notebook_model, name, path)

            # Test in sub-directory
            # Create a directory and notebook in that directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook_model(None, sub_dir)
            name = model['name']
            path = model['path']
            
            # Change the name in the model for rename
            model['name'] = 'test_in_sub.ipynb'
            model = nm.update_notebook_model(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'test_in_sub.ipynb')
            self.assertEqual(model['path'], sub_dir)
            
            # Make sure the old name is gone
            self.assertRaises(HTTPError, nm.get_notebook_model, name, path)

    def test_save_notebook_model(self):
        with TemporaryDirectory() as td:
            # Test in the root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook_model()
            name = model['name']
            path = model['path']

            # Get the model with 'content'
            full_model = nm.get_notebook_model(name, path)

            # Save the notebook
            model = nm.save_notebook_model(full_model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], name)
            self.assertEqual(model['path'], path)

            # Test in sub-directory
            # Create a directory and notebook in that directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook_model(None, sub_dir)
            name = model['name']
            path = model['path']
            model = nm.get_notebook_model(name, path)

            # Change the name in the model for rename
            model = nm.save_notebook_model(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], sub_dir)          

    def test_delete_notebook_model(self):
        with TemporaryDirectory() as td:
            # Test in the root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook_model()
            name = model['name']
            path = model['path']
            
            # Delete the notebook
            nm.delete_notebook_model(name, path)
            
            # Check that a 'get' on the deleted notebook raises and error
            self.assertRaises(HTTPError, nm.get_notebook_model, name, path)

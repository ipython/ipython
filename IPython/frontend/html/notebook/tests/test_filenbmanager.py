"""Tests for the notebook manager."""

import os
import shutil
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError

from tornado import web
from IPython.frontend.html.notebook.filenbmanager import FileNotebookManager

def touch(*parts):
    with open(os.path.join(*parts), 'w+'):
        pass

def fixture_path(name):
    return os.path.join(os.path.dirname(__file__), 'fixtures', name)

def copy_fixture(name, dir):
    shutil.copy(fixture_path('fixture1.ipynb'), os.path.join(dir, 'fixture1.ipynb'))

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

    def test_only_get_nb_files(self):
        with TemporaryDirectory() as td:
            touch(td, 'non-notebook')
            touch(td, 'notebook.ipynb')

            km = FileNotebookManager(notebook_dir=td)

            self.assertEqual(km.get_notebook_names(), ['notebook'])

    def test_get_nb_files_recursively(self):
        with TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "subdir", "sub"))
            os.makedirs(os.path.join(td, "dirsub"))
            touch(td, 'dirsub', 'notebook3.ipynb')
            touch(td, 'notebook1.ipynb')
            touch(td, 'subdir', 'notebook2.ipynb')
            touch(td, 'subdir', 'sub', 'notebook4.ipynb')
            
            km = FileNotebookManager(notebook_dir=td)

            expected = [os.path.join(*parts) for parts in [
                ('dirsub', 'notebook3',),
                ('notebook1',), 
                ('subdir', 'notebook2',),
                ('subdir', 'sub', 'notebook4',)
            ]]
            self.assertEqual(km.get_notebook_names(), expected)

    def test_list_notebooks(self):
        with TemporaryDirectory() as td:
            copy_fixture('fixture1.ipynb', td)

            km = FileNotebookManager(notebook_dir=td)
            nbs = km.list_notebooks()

            self.assertEquals(len(nbs), 1)
            self.assertEquals(nbs[0]['name'], 'fixture1')

    def test_read_notebook_object(self):
        with TemporaryDirectory() as td:
            shutil.copy(fixture_path('fixture1.ipynb'), os.path.join(td, 'fixture1.ipynb'))
            
            km = FileNotebookManager(notebook_dir=td)
            nb_id = km.new_notebook_id('fixture1')

            _, nb = km.read_notebook_object(nb_id)
    
            self.assertEquals(nb['nbformat'], 3)
            self.assertEquals(nb.metadata.name, 'fixture1')

    def test_read_subdir_notebook_object(self):
        with TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, 'subdir'))
            shutil.copy(fixture_path('fixture1.ipynb'), os.path.join(td, 'subdir', 'fixture1.ipynb'))

            km = FileNotebookManager(notebook_dir=td)
            nb_id = km.new_notebook_id('subdir/fixture1')

            _, nb = km.read_notebook_object(nb_id)

            self.assertEquals(nb['nbformat'], 3)
            self.assertEquals(nb.metadata.name, 'subdir/fixture1')

    def test_write_notebook_object(self):
        with TemporaryDirectory() as td:
            km1 = FileNotebookManager(notebook_dir=fixture_path(''))
            _, nb = km1.read_notebook_object(km1.new_notebook_id('fixture1'))

            km = FileNotebookManager(notebook_dir=td)
            nb_id = km.write_notebook_object(nb)
            
            self.assertTrue(os.path.exists(os.path.join(td, 'fixture1.ipynb')))

            nb.metadata.name = 'fixture2'
            km.write_notebook_object(nb, nb_id)

            self.assertTrue(os.path.exists(os.path.join(td, 'fixture2.ipynb')))
            self.assertFalse(os.path.exists(os.path.join(td, 'fixture1.ipynb')))

    def test_write_notebook_object_fails_with_dotdot(self):
        with TemporaryDirectory() as td:
            km1 = FileNotebookManager(notebook_dir=fixture_path(''))
            _, nb = km1.read_notebook_object(km1.new_notebook_id('fixture1'))
            nb.metadata.name = '../fixture1'

            km = FileNotebookManager(notebook_dir=td)
            self.assertRaises(web.HTTPError, km.write_notebook_object, nb)

    def test_write_subdir_notebook_object(self):
        with TemporaryDirectory() as td:
            km1 = FileNotebookManager(notebook_dir=fixture_path(''))
            _, nb = km1.read_notebook_object(km1.new_notebook_id('fixture1'))
            nb.metadata.name = 'subdir/fixture1'

            km = FileNotebookManager(notebook_dir=td)
            nb_id = km.write_notebook_object(nb)

            self.assertTrue(os.path.exists(os.path.join(td, 'subdir', 'fixture1.ipynb')))

            nb.metadata.name = 'fixture2'
            km.write_notebook_object(nb, nb_id)

            self.assertTrue(os.path.exists(os.path.join(td, 'fixture2.ipynb')))
            self.assertFalse(os.path.exists(os.path.join(td, 'subdir', 'fixture1.ipynb')))
            self.assertFalse(os.path.exists(os.path.join(td, 'subdir')))

    def test_delete_notebook(self):
        with TemporaryDirectory() as td:
            shutil.copy(fixture_path('fixture1.ipynb'), os.path.join(td, 'fixture1.ipynb'))
            
            km = FileNotebookManager(notebook_dir=td)
            nb_id = km.new_notebook_id('fixture1')

            km.delete_notebook(nb_id)
            
            self.assertFalse(os.path.exists(os.path.join(td, 'fixture1.ipynb')))
            self.assertTrue(os.path.exists(td))

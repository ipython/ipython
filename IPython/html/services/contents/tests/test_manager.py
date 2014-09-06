# coding: utf-8
"""Tests for the notebook manager."""
from __future__ import print_function

import logging
import os

from tornado.web import HTTPError
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.nbformat import current

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError
from IPython.html.utils import url_path_join
from IPython.testing import decorators as dec

from ..filemanager import FileContentsManager
from ..manager import ContentsManager


class TestFileContentsManager(TestCase):

    def test_root_dir(self):
        with TemporaryDirectory() as td:
            fm = FileContentsManager(root_dir=td)
            self.assertEqual(fm.root_dir, td)

    def test_missing_root_dir(self):
        with TemporaryDirectory() as td:
            root = os.path.join(td, 'notebook', 'dir', 'is', 'missing')
            self.assertRaises(TraitError, FileContentsManager, root_dir=root)

    def test_invalid_root_dir(self):
        with NamedTemporaryFile() as tf:
            self.assertRaises(TraitError, FileContentsManager, root_dir=tf.name)

    def test_get_os_path(self):
        # full filesystem path should be returned with correct operating system
        # separators.
        with TemporaryDirectory() as td:
            root = td
            fm = FileContentsManager(root_dir=root)
            path = fm._get_os_path('test.ipynb', '/path/to/notebook/')
            rel_path_list =  '/path/to/notebook/test.ipynb'.split('/')
            fs_path = os.path.join(fm.root_dir, *rel_path_list)
            self.assertEqual(path, fs_path)

            fm = FileContentsManager(root_dir=root)
            path = fm._get_os_path('test.ipynb')
            fs_path = os.path.join(fm.root_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

            fm = FileContentsManager(root_dir=root)
            path = fm._get_os_path('test.ipynb', '////')
            fs_path = os.path.join(fm.root_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

    def test_checkpoint_subdir(self):
        subd = u'sub ∂ir'
        cp_name = 'test-cp.ipynb'
        with TemporaryDirectory() as td:
            root = td
            os.mkdir(os.path.join(td, subd))
            fm = FileContentsManager(root_dir=root)
            cp_dir = fm.get_checkpoint_path('cp', 'test.ipynb', '/')
            cp_subdir = fm.get_checkpoint_path('cp', 'test.ipynb', '/%s/' % subd)
        self.assertNotEqual(cp_dir, cp_subdir)
        self.assertEqual(cp_dir, os.path.join(root, fm.checkpoint_dir, cp_name))
        self.assertEqual(cp_subdir, os.path.join(root, subd, fm.checkpoint_dir, cp_name))


class TestContentsManager(TestCase):

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.td = self._temp_dir.name
        self.contents_manager = FileContentsManager(
            root_dir=self.td,
            log=logging.getLogger()
        )

    def tearDown(self):
        self._temp_dir.cleanup()

    def make_dir(self, abs_path, rel_path):
        """make subdirectory, rel_path is the relative path
        to that directory from the location where the server started"""
        os_path = os.path.join(abs_path, rel_path)
        try:
            os.makedirs(os_path)
        except OSError:
            print("Directory already exists: %r" % os_path)
        return os_path

    def add_code_cell(self, nb):
        output = current.new_output("display_data", output_javascript="alert('hi');")
        cell = current.new_code_cell("print('hi')", outputs=[output])
        if not nb.worksheets:
            nb.worksheets.append(current.new_worksheet())
        nb.worksheets[0].cells.append(cell)

    def new_notebook(self):
        cm = self.contents_manager
        model = cm.create_file()
        name = model['name']
        path = model['path']

        full_model = cm.get_model(name, path)
        nb = full_model['content']
        self.add_code_cell(nb)

        cm.save(full_model, name, path)
        return nb, name, path

    def test_create_file(self):
        cm = self.contents_manager
        # Test in root directory
        model = cm.create_file()
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'Untitled0.ipynb')
        self.assertEqual(model['path'], '')

        # Test in sub-directory
        sub_dir = '/foo/'
        self.make_dir(cm.root_dir, 'foo')
        model = cm.create_file(None, sub_dir)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'Untitled0.ipynb')
        self.assertEqual(model['path'], sub_dir.strip('/'))

    def test_get(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.create_file()
        name = model['name']
        path = model['path']

        # Check that we 'get' on the notebook we just created
        model2 = cm.get_model(name, path)
        assert isinstance(model2, dict)
        self.assertIn('name', model2)
        self.assertIn('path', model2)
        self.assertEqual(model['name'], name)
        self.assertEqual(model['path'], path)

        # Test in sub-directory
        sub_dir = '/foo/'
        self.make_dir(cm.root_dir, 'foo')
        model = cm.create_file(None, sub_dir)
        model2 = cm.get_model(name, sub_dir)
        assert isinstance(model2, dict)
        self.assertIn('name', model2)
        self.assertIn('path', model2)
        self.assertIn('content', model2)
        self.assertEqual(model2['name'], 'Untitled0.ipynb')
        self.assertEqual(model2['path'], sub_dir.strip('/'))
    
    @dec.skip_win32
    def test_bad_symlink(self):
        cm = self.contents_manager
        path = 'test bad symlink'
        os_path = self.make_dir(cm.root_dir, path)
        
        file_model = cm.create_file(path=path, ext='.txt')
        
        # create a broken symlink
        os.symlink("target", os.path.join(os_path, "bad symlink"))
        model = cm.get_model(path)
        self.assertEqual(model['content'], [file_model])
    
    @dec.skip_win32
    def test_good_symlink(self):
        cm = self.contents_manager
        path = 'test good symlink'
        os_path = self.make_dir(cm.root_dir, path)
        
        file_model = cm.create_file(path=path, ext='.txt')
        
        # create a good symlink
        os.symlink(file_model['name'], os.path.join(os_path, "good symlink"))
        symlink_model = cm.get_model(name="good symlink", path=path, content=False)
        
        dir_model = cm.get_model(path)
        self.assertEqual(
            sorted(dir_model['content'], key=lambda x: x['name']),
            [symlink_model, file_model],
        )
    
    def test_update(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.create_file()
        name = model['name']
        path = model['path']

        # Change the name in the model for rename
        model['name'] = 'test.ipynb'
        model = cm.update(model, name, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test.ipynb')

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get_model, name, path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir(cm.root_dir, 'foo')
        model = cm.create_file(None, sub_dir)
        name = model['name']
        path = model['path']

        # Change the name in the model for rename
        model['name'] = 'test_in_sub.ipynb'
        model = cm.update(model, name, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test_in_sub.ipynb')
        self.assertEqual(model['path'], sub_dir.strip('/'))

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get_model, name, path)

    def test_save(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.create_file()
        name = model['name']
        path = model['path']

        # Get the model with 'content'
        full_model = cm.get_model(name, path)

        # Save the notebook
        model = cm.save(full_model, name, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], name)
        self.assertEqual(model['path'], path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir(cm.root_dir, 'foo')
        model = cm.create_file(None, sub_dir)
        name = model['name']
        path = model['path']
        model = cm.get_model(name, path)

        # Change the name in the model for rename
        model = cm.save(model, name, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'Untitled0.ipynb')
        self.assertEqual(model['path'], sub_dir.strip('/'))

    def test_delete(self):
        cm = self.contents_manager
        # Create a notebook
        nb, name, path = self.new_notebook()

        # Delete the notebook
        cm.delete(name, path)

        # Check that a 'get' on the deleted notebook raises and error
        self.assertRaises(HTTPError, cm.get_model, name, path)

    def test_copy(self):
        cm = self.contents_manager
        path = u'å b'
        name = u'nb √.ipynb'
        os.mkdir(os.path.join(cm.root_dir, path))
        orig = cm.create_file({'name' : name}, path=path)

        # copy with unspecified name
        copy = cm.copy(name, path=path)
        self.assertEqual(copy['name'], orig['name'].replace('.ipynb', '-Copy0.ipynb'))

        # copy with specified name
        copy2 = cm.copy(name, u'copy 2.ipynb', path=path)
        self.assertEqual(copy2['name'], u'copy 2.ipynb')

    def test_trust_notebook(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        untrusted = cm.get_model(name, path)['content']
        assert not cm.notary.check_cells(untrusted)

        # print(untrusted)
        cm.trust_notebook(name, path)
        trusted = cm.get_model(name, path)['content']
        # print(trusted)
        assert cm.notary.check_cells(trusted)

    def test_mark_trusted_cells(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        cm.mark_trusted_cells(nb, name, path)
        for cell in nb.worksheets[0].cells:
            if cell.cell_type == 'code':
                assert not cell.trusted

        cm.trust_notebook(name, path)
        nb = cm.get_model(name, path)['content']
        for cell in nb.worksheets[0].cells:
            if cell.cell_type == 'code':
                assert cell.trusted

    def test_check_and_sign(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        cm.mark_trusted_cells(nb, name, path)
        cm.check_and_sign(nb, name, path)
        assert not cm.notary.check_signature(nb)

        cm.trust_notebook(name, path)
        nb = cm.get_model(name, path)['content']
        cm.mark_trusted_cells(nb, name, path)
        cm.check_and_sign(nb, name, path)
        assert cm.notary.check_signature(nb)

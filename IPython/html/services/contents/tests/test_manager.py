# coding: utf-8
"""Tests for the notebook manager."""
from __future__ import print_function

import os
import sys
import time
from contextlib import contextmanager

from nose import SkipTest
from tornado.web import HTTPError
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.nbformat import v4 as nbformat

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError
from IPython.testing import decorators as dec

from ..filemanager import FileContentsManager


def _make_dir(contents_manager, api_path):
    """
    Make a directory.
    """
    os_path = contents_manager._get_os_path(api_path)
    try:
        os.makedirs(os_path)
    except OSError:
        print("Directory already exists: %r" % os_path)


class TestFileContentsManager(TestCase):

    @contextmanager
    def assertRaisesHTTPError(self, status, msg=None):
        msg = msg or "Should have raised HTTPError(%i)" % status
        try:
            yield
        except HTTPError as e:
            self.assertEqual(e.status_code, status)
        else:
            self.fail(msg)

    def symlink(self, contents_manager, src, dst):
        """Make a symlink to src from dst
        
        src and dst are api_paths
        """
        src_os_path = contents_manager._get_os_path(src)
        dst_os_path = contents_manager._get_os_path(dst)
        print(src_os_path, dst_os_path, os.path.isfile(src_os_path))
        os.symlink(src_os_path, dst_os_path)

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
            path = fm._get_os_path('/path/to/notebook/test.ipynb')
            rel_path_list =  '/path/to/notebook/test.ipynb'.split('/')
            fs_path = os.path.join(fm.root_dir, *rel_path_list)
            self.assertEqual(path, fs_path)

            fm = FileContentsManager(root_dir=root)
            path = fm._get_os_path('test.ipynb')
            fs_path = os.path.join(fm.root_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

            fm = FileContentsManager(root_dir=root)
            path = fm._get_os_path('////test.ipynb')
            fs_path = os.path.join(fm.root_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

    def test_checkpoint_subdir(self):
        subd = u'sub ∂ir'
        cp_name = 'test-cp.ipynb'
        with TemporaryDirectory() as td:
            root = td
            os.mkdir(os.path.join(td, subd))
            fm = FileContentsManager(root_dir=root)
            cpm = fm.checkpoints
            cp_dir = cpm.checkpoint_path(
                'cp', 'test.ipynb'
            )
            cp_subdir = cpm.checkpoint_path(
                'cp', '/%s/test.ipynb' % subd
            )
        self.assertNotEqual(cp_dir, cp_subdir)
        self.assertEqual(cp_dir, os.path.join(root, cpm.checkpoint_dir, cp_name))
        self.assertEqual(cp_subdir, os.path.join(root, subd, cpm.checkpoint_dir, cp_name))
    
    @dec.skip_win32
    def test_bad_symlink(self):
        with TemporaryDirectory() as td:
            cm = FileContentsManager(root_dir=td)
            path = 'test bad symlink'
            _make_dir(cm, path)

            file_model = cm.new_untitled(path=path, ext='.txt')

            # create a broken symlink
            self.symlink(cm, "target", '%s/%s' % (path, 'bad symlink'))
            model = cm.get(path)
            self.assertEqual(model['content'], [file_model])
    
    @dec.skip_win32
    def test_good_symlink(self):
        with TemporaryDirectory() as td:
            cm = FileContentsManager(root_dir=td)
            parent = 'test good symlink'
            name = 'good symlink'
            path = '{0}/{1}'.format(parent, name)
            _make_dir(cm, parent)

            file_model = cm.new(path=parent + '/zfoo.txt')

            # create a good symlink
            self.symlink(cm, file_model['path'], path)
            symlink_model = cm.get(path, content=False)
            dir_model = cm.get(parent)
            self.assertEqual(
                sorted(dir_model['content'], key=lambda x: x['name']),
                [symlink_model, file_model],
            )
    
    def test_403(self):
        if hasattr(os, 'getuid'):
            if os.getuid() == 0:
                raise SkipTest("Can't test permissions as root")
        if sys.platform.startswith('win'):
            raise SkipTest("Can't test permissions on Windows")
        
        with TemporaryDirectory() as td:
            cm = FileContentsManager(root_dir=td)
            model = cm.new_untitled(type='file')
            os_path = cm._get_os_path(model['path'])
        
            os.chmod(os_path, 0o400)
            try:
                with cm.open(os_path, 'w') as f:
                    f.write(u"don't care")
            except HTTPError as e:
                self.assertEqual(e.status_code, 403)
            else:
                self.fail("Should have raised HTTPError(403)")

    def test_escape_root(self):
        with TemporaryDirectory() as td:
            cm = FileContentsManager(root_dir=td)
            # make foo, bar next to root
            with open(os.path.join(cm.root_dir, '..', 'foo'), 'w') as f:
                f.write('foo')
            with open(os.path.join(cm.root_dir, '..', 'bar'), 'w') as f:
                f.write('bar')

            with self.assertRaisesHTTPError(404):
                cm.get('..')
            with self.assertRaisesHTTPError(404):
                cm.get('foo/../../../bar')
            with self.assertRaisesHTTPError(404):
                cm.delete('../foo')
            with self.assertRaisesHTTPError(404):
                cm.rename('../foo', '../bar')
            with self.assertRaisesHTTPError(404):
                cm.save(model={
                    'type': 'file',
                    'content': u'',
                    'format': 'text',
                }, path='../foo')


class TestContentsManager(TestCase):
    
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.td = self._temp_dir.name
        self.contents_manager = FileContentsManager(
            root_dir=self.td,
        )

    def tearDown(self):
        self._temp_dir.cleanup()
    
    def make_dir(self, api_path):
        """make a subdirectory at api_path
        
        override in subclasses if contents are not on the filesystem.
        """
        _make_dir(self.contents_manager, api_path)

    def add_code_cell(self, nb):
        output = nbformat.new_output("display_data", {'application/javascript': "alert('hi');"})
        cell = nbformat.new_code_cell("print('hi')", outputs=[output])
        nb.cells.append(cell)

    def new_notebook(self):
        cm = self.contents_manager
        model = cm.new_untitled(type='notebook')
        name = model['name']
        path = model['path']

        full_model = cm.get(path)
        nb = full_model['content']
        nb['metadata']['counter'] = int(1e6 * time.time())
        self.add_code_cell(nb)

        cm.save(full_model, path)
        return nb, name, path

    def test_new_untitled(self):
        cm = self.contents_manager
        # Test in root directory
        model = cm.new_untitled(type='notebook')
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertIn('type', model)
        self.assertEqual(model['type'], 'notebook')
        self.assertEqual(model['name'], 'Untitled.ipynb')
        self.assertEqual(model['path'], 'Untitled.ipynb')

        # Test in sub-directory
        model = cm.new_untitled(type='directory')
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertIn('type', model)
        self.assertEqual(model['type'], 'directory')
        self.assertEqual(model['name'], 'Untitled Folder')
        self.assertEqual(model['path'], 'Untitled Folder')
        sub_dir = model['path']
        
        model = cm.new_untitled(path=sub_dir)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertIn('type', model)
        self.assertEqual(model['type'], 'file')
        self.assertEqual(model['name'], 'untitled')
        self.assertEqual(model['path'], '%s/untitled' % sub_dir)

    def test_modified_date(self):

        cm = self.contents_manager

        # Create a new notebook.
        nb, name, path = self.new_notebook()
        model = cm.get(path)

        # Add a cell and save.
        self.add_code_cell(model['content'])
        cm.save(model, path)

        # Reload notebook and verify that last_modified incremented.
        saved = cm.get(path)
        self.assertGreaterEqual(saved['last_modified'], model['last_modified'])

        # Move the notebook and verify that last_modified stayed the same.
        # (The frontend fires a warning if last_modified increases on the
        # renamed file.)
        new_path = 'renamed.ipynb'
        cm.rename(path, new_path)
        renamed = cm.get(new_path)
        self.assertGreaterEqual(
            renamed['last_modified'],
            saved['last_modified'],
        )

    def test_get(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.new_untitled(type='notebook')
        name = model['name']
        path = model['path']

        # Check that we 'get' on the notebook we just created
        model2 = cm.get(path)
        assert isinstance(model2, dict)
        self.assertIn('name', model2)
        self.assertIn('path', model2)
        self.assertEqual(model['name'], name)
        self.assertEqual(model['path'], path)

        nb_as_file = cm.get(path, content=True, type='file')
        self.assertEqual(nb_as_file['path'], path)
        self.assertEqual(nb_as_file['type'], 'file')
        self.assertEqual(nb_as_file['format'], 'text')
        self.assertNotIsInstance(nb_as_file['content'], dict)

        nb_as_bin_file = cm.get(path, content=True, type='file', format='base64')
        self.assertEqual(nb_as_bin_file['format'], 'base64')

        # Test in sub-directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        model = cm.new_untitled(path=sub_dir, ext='.ipynb')
        model2 = cm.get(sub_dir + name)
        assert isinstance(model2, dict)
        self.assertIn('name', model2)
        self.assertIn('path', model2)
        self.assertIn('content', model2)
        self.assertEqual(model2['name'], 'Untitled.ipynb')
        self.assertEqual(model2['path'], '{0}/{1}'.format(sub_dir.strip('/'), name))

        # Test with a regular file.
        file_model_path = cm.new_untitled(path=sub_dir, ext='.txt')['path']
        file_model = cm.get(file_model_path)
        self.assertDictContainsSubset(
            {
                'content': u'',
                'format': u'text',
                'mimetype': u'text/plain',
                'name': u'untitled.txt',
                'path': u'foo/untitled.txt',
                'type': u'file',
                'writable': True,
            },
            file_model,
        )
        self.assertIn('created', file_model)
        self.assertIn('last_modified', file_model)

        # Test getting directory model

        # Create a sub-sub directory to test getting directory contents with a
        # subdir.
        self.make_dir('foo/bar')
        dirmodel = cm.get('foo')
        self.assertEqual(dirmodel['type'], 'directory')
        self.assertIsInstance(dirmodel['content'], list)
        self.assertEqual(len(dirmodel['content']), 3)
        self.assertEqual(dirmodel['path'], 'foo')
        self.assertEqual(dirmodel['name'], 'foo')

        # Directory contents should match the contents of each individual entry
        # when requested with content=False.
        model2_no_content = cm.get(sub_dir + name, content=False)
        file_model_no_content = cm.get(u'foo/untitled.txt', content=False)
        sub_sub_dir_no_content = cm.get('foo/bar', content=False)
        self.assertEqual(sub_sub_dir_no_content['path'], 'foo/bar')
        self.assertEqual(sub_sub_dir_no_content['name'], 'bar')

        for entry in dirmodel['content']:
            # Order isn't guaranteed by the spec, so this is a hacky way of
            # verifying that all entries are matched.
            if entry['path'] == sub_sub_dir_no_content['path']:
                self.assertEqual(entry, sub_sub_dir_no_content)
            elif entry['path'] == model2_no_content['path']:
                self.assertEqual(entry, model2_no_content)
            elif entry['path'] == file_model_no_content['path']:
                self.assertEqual(entry, file_model_no_content)
            else:
                self.fail("Unexpected directory entry: %s" % entry())

        with self.assertRaises(HTTPError):
            cm.get('foo', type='file')

    def test_update(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.new_untitled(type='notebook')
        name = model['name']
        path = model['path']

        # Change the name in the model for rename
        model['path'] = 'test.ipynb'
        model = cm.update(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test.ipynb')

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get, path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        model = cm.new_untitled(path=sub_dir, type='notebook')
        path = model['path']

        # Change the name in the model for rename
        d = path.rsplit('/', 1)[0]
        new_path = model['path'] = d + '/test_in_sub.ipynb'
        model = cm.update(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'test_in_sub.ipynb')
        self.assertEqual(model['path'], new_path)

        # Make sure the old name is gone
        self.assertRaises(HTTPError, cm.get, path)

    def test_save(self):
        cm = self.contents_manager
        # Create a notebook
        model = cm.new_untitled(type='notebook')
        name = model['name']
        path = model['path']

        # Get the model with 'content'
        full_model = cm.get(path)

        # Save the notebook
        model = cm.save(full_model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], name)
        self.assertEqual(model['path'], path)

        # Test in sub-directory
        # Create a directory and notebook in that directory
        sub_dir = '/foo/'
        self.make_dir('foo')
        model = cm.new_untitled(path=sub_dir, type='notebook')
        name = model['name']
        path = model['path']
        model = cm.get(path)

        # Change the name in the model for rename
        model = cm.save(model, path)
        assert isinstance(model, dict)
        self.assertIn('name', model)
        self.assertIn('path', model)
        self.assertEqual(model['name'], 'Untitled.ipynb')
        self.assertEqual(model['path'], 'foo/Untitled.ipynb')

    def test_delete(self):
        cm = self.contents_manager
        # Create a notebook
        nb, name, path = self.new_notebook()

        # Delete the notebook
        cm.delete(path)

        # Check that deleting a non-existent path raises an error.
        self.assertRaises(HTTPError, cm.delete, path)

        # Check that a 'get' on the deleted notebook raises and error
        self.assertRaises(HTTPError, cm.get, path)

    def test_delete_root(self):
        cm = self.contents_manager
        with self.assertRaises(HTTPError) as err:
            cm.delete('')
        self.assertEqual(err.exception.status_code, 400)

    def test_copy(self):
        cm = self.contents_manager
        parent = u'å b'
        name = u'nb √.ipynb'
        path = u'{0}/{1}'.format(parent, name)
        self.make_dir(parent)

        orig = cm.new(path=path)
        # copy with unspecified name
        copy = cm.copy(path)
        self.assertEqual(copy['name'], orig['name'].replace('.ipynb', '-Copy1.ipynb'))

        # copy with specified name
        copy2 = cm.copy(path, u'å b/copy 2.ipynb')
        self.assertEqual(copy2['name'], u'copy 2.ipynb')
        self.assertEqual(copy2['path'], u'å b/copy 2.ipynb')
        # copy with specified path
        copy2 = cm.copy(path, u'/')
        self.assertEqual(copy2['name'], name)
        self.assertEqual(copy2['path'], name)

    def test_trust_notebook(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        untrusted = cm.get(path)['content']
        assert not cm.notary.check_cells(untrusted)

        # print(untrusted)
        cm.trust_notebook(path)
        trusted = cm.get(path)['content']
        # print(trusted)
        assert cm.notary.check_cells(trusted)

    def test_mark_trusted_cells(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        cm.mark_trusted_cells(nb, path)
        for cell in nb.cells:
            if cell.cell_type == 'code':
                assert not cell.metadata.trusted

        cm.trust_notebook(path)
        nb = cm.get(path)['content']
        for cell in nb.cells:
            if cell.cell_type == 'code':
                assert cell.metadata.trusted

    def test_check_and_sign(self):
        cm = self.contents_manager
        nb, name, path = self.new_notebook()

        cm.mark_trusted_cells(nb, path)
        cm.check_and_sign(nb, path)
        assert not cm.notary.check_signature(nb)

        cm.trust_notebook(path)
        nb = cm.get(path)['content']
        cm.mark_trusted_cells(nb, path)
        cm.check_and_sign(nb, path)
        assert cm.notary.check_signature(nb)

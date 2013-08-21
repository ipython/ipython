"""Tests for the content manager."""

import os
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError

from ..contentmanager import ContentManager


class TestContentManager(TestCase):

    def test_new_folder(self):
        with TemporaryDirectory() as td:
            # Test that a new directory/folder is created
            cm = ContentManager(content_dir=td)
            name = cm.new_folder(None, '/')
            path = cm.get_os_path(name, '/')
            self.assertTrue(os.path.isdir(path))
            
            # Test that a new directory is created with
            # the name given.
            name = cm.new_folder('foo')
            path = cm.get_os_path(name)
            self.assertTrue(os.path.isdir(path))
            
            # Test that a new directory/folder is created
            # in the '/foo' subdirectory
            name1 = cm.new_folder(None, '/foo/')
            path1 = cm.get_os_path(name1, '/foo/')
            self.assertTrue(os.path.isdir(path1))

            # make another file and make sure it incremented
            # the name and does not write over another file.
            name2 = cm.new_folder(None, '/foo/')
            path2 = cm.get_os_path(name, '/foo/')
            self.assertEqual(name2, 'new_folder1')
            
            # Test that an HTTP Error is raised when the user
            # tries to create a new folder with a name that 
            # already exists
            bad_name = 'new_folder1'
            self.assertRaises(HTTPError, cm.new_folder, name=bad_name, path='/foo/')

    def test_delete_folder(self):
        with TemporaryDirectory() as td:
            # Create a folder
            cm = ContentManager(content_dir=td)
            name = cm.new_folder('test_folder', '/')
            path = cm.get_os_path(name, '/')
            
            # Raise an exception when trying to delete a 
            # folder that does not exist.
            self.assertRaises(HTTPError, cm.delete_content, name='non_existing_folder', content_path='/')
            
            # Create a subfolder in the folder created above. 
            # *Recall 'name' = 'test_folder' (the new path for
            # subfolder)
            name01 = cm.new_folder(None, name)
            path01 = cm.get_os_path(name01, name)
            # Try to delete a subfolder that does not exist.
            self.assertRaises(HTTPError, cm.delete_content, name='non_existing_folder', content_path='/')
            # Delete the created subfolder
            cm.delete_content(name01, name)
            self.assertFalse(os.path.isdir(path01))
            
            # Delete the created folder
            cm.delete_content(name, '/')
            self.assertFalse(os.path.isdir(path))
            
            self.assertRaises(HTTPError, cm.delete_content, name=None, content_path='/')
            self.assertRaises(HTTPError, cm.delete_content, name='/', content_path='/')
            
            
    def test_get_content_names(self):
        with TemporaryDirectory() as td:
            # Create a few folders and subfolders
            cm = ContentManager(content_dir=td)
            name1 = cm.new_folder('fold1', '/')
            name2 = cm.new_folder('fold2', '/')
            name3 = cm.new_folder('fold3', '/')
            name01 = cm.new_folder('fold01', 'fold1')
            name02 = cm.new_folder('fold02', 'fold1')
            name03 = cm.new_folder('fold03', 'fold1')
            
            # List the names in the root folder
            names = cm.get_content_names('/')
            expected = ['fold1', 'fold2', 'fold3']
            self.assertEqual(set(names), set(expected))
            
            # List the names in the subfolder 'fold1'.
            names = cm.get_content_names('fold1')
            expected = ['fold01', 'fold02', 'fold03']
            self.assertEqual(set(names), set(expected))

    def test_content_model(self):
        with TemporaryDirectory() as td:
            # Create a few folders and subfolders
            cm = ContentManager(content_dir=td)
            name1 = cm.new_folder('fold1', '/')
            name2 = cm.new_folder('fold2', '/')
            name01 = cm.new_folder('fold01', 'fold1')
            name02 = cm.new_folder('fold02', 'fold1')
            
            # Check to see if the correct model and list of 
            # model dicts are returned for root directory
            # and subdirectory.
            contents = cm.list_contents('/')
            contents1 = cm.list_contents('fold1')
            self.assertEqual(type(contents), type(list()))
            self.assertEqual(type(contents[0]), type(dict()))
            self.assertEqual(contents[0]['path'], '/')
            self.assertEqual(contents1[0]['path'], 'fold1')

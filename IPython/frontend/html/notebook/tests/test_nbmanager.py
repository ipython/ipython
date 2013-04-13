"""Tests for the notebook manager."""

import os
from unittest import TestCase
from tempfile import NamedTemporaryFile
import glob
import pdb

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError

from IPython.frontend.html.notebook.filenbmanager import FileNotebookManager

class TestNotebookManager(TestCase):

    def test_nb_dir(self):
        with TemporaryDirectory() as td:
            km = FileNotebookManager(notebook_dir=td)
            self.assertEqual(km.notebook_dir, td)

    def test_create_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebooks')
            km = FileNotebookManager(notebook_dir=nbdir)
            self.assertEqual(km.notebook_dir, nbdir)

    def _test_missing_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebook', 'dir', 'is', 'missing')
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=nbdir)

    def _test_invalid_nb_dir(self):
        with NamedTemporaryFile() as tf:
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=tf.name)

SIMPLE_NB = """
{"metadata": {"name": "simple"},"nbformat": 3,"nbformat_minor": 0,"worksheets": [{"cells": [ { "cell_type": "code",     "collapsed": false,     "input": [      "asdf"     ],     "language": "python",     "metadata": {},     "outputs": [      {       "output_type": "pyout",       "prompt_number": 1,       "text": [        "''"       ]      }     ],     "prompt_number": 1    },    {     "cell_type": "code",     "collapsed": false,     "input": [],     "language": "python",     "metadata": {},     "outputs": []    }   ],   "metadata": {}  } ]}"""
class TestDirHandling(TestCase):

    def test_nb_dir(self):
        with TemporaryDirectory() as td1:
            with TemporaryDirectory() as td2:
                km = FileNotebookManager(notebook_dir=td1)
                NAME1 = "first_notebook"
                NAME2 = "td2_nb"
                #there shouldn't be any notebooks to start with in td1
                self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 0)
                self.assertEquals(len(glob.glob(td2 + "/*ipynb")), 0)
                new_id = km.new_notebook()
                #the first notebook is created
                self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 1)
                self.assertEquals(len(glob.glob(td2 + "/*ipynb")), 0)
                #the first notebook shouldn't be named first notebook
                self.assertEquals(len(glob.glob(td1 + "/first_notebook*ipynb")), 0)
                # it should have untitled in it's name
                print glob.glob(td1 + "/*ipynb")
                self.assertEquals(len(glob.glob(td1 + "/Untit*ipynb")), 1)
                self.assertTrue(km.notebook_exists(new_id))
                km.save_notebook(new_id, SIMPLE_NB, name=NAME1, format="json")
                #there should still be only one notebook in td1
                self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 1)
                self.assertEquals(len(glob.glob(td2 + "/*ipynb")), 0)
                # the notebook should now be named first_notebook
                #pdb.set_trace()
                self.assertEquals(len(glob.glob(td1 + "/first_notebook.ipynb")), 1)
                # the Untitled notebook should have been removed
                self.assertEquals(len(glob.glob(td1 + "/Untit*ipynb")), 0)
                # if this file wasn't written properly it will raise
                # an exception'
                self.assertEquals(len(km.read_notebook_object(new_id)), 2)
                km.notebook_dir = td2
                self.assertEquals(km.notebook_dir, td2)
                # we should still read from original notebook_dir, not the new one
                self.assertEquals(len(km.read_notebook_object(new_id)), 2)

                
                km.save_notebook(new_id, SIMPLE_NB, name=NAME1, format="json")
                # after saving the first notebook, it should still save to td1, not td2
                self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 1)
                self.assertEquals(len(glob.glob(td2 + "/*ipynb")), 0)
                # the notebook should now be named first_notebook
                self.assertEquals(len(glob.glob(td1 + "/first_notebook*ipynb")), 1)
                #pdb.set_trace()
                td2_nb_id = km.new_notebook()
                km.save_notebook(td2_nb_id, SIMPLE_NB, name=NAME2, format="json")
                #there should now be a notebook in both directories
                self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 1)
                self.assertEquals(len(glob.glob(td2 + "/*ipynb")), 1)


                #km.save_notebook(new_id, SIMPLE_NB, name=NAME1, format="json")
                #self.assertTrue(km.notebook_exists(NAME1))
                print NAME1

    def test_nb_dir2(self):
        with TemporaryDirectory() as td1:
            km = FileNotebookManager(notebook_dir=td1)
            NAME1 = "first_notebook"
            NAME2 = "td2_nb"


            #there shouldn't be any notebooks to start with in td1
            self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 0)
            new_id = km.new_notebook()
            #the first notebook is created
            self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 1)
            km.save_notebook(new_id, SIMPLE_NB, name=NAME1, format="json")
            #there should still be only one notebook in td1
            self.assertEquals(len(glob.glob(td1 + "/first_notebook*ipynb")), 1)
            km.delete_notebook_id(new_id)
            #after deleting the notebook, the directory should be empty
            self.assertEquals(len(glob.glob(td1 + "/*ipynb")), 0)

    def test_new_notebook(self):
        with TemporaryDirectory() as td1:
            with TemporaryDirectory() as td2:
                km = FileNotebookManager(notebook_dir=td1)
                nb1_id = km.new_notebook()
                # I don't  know how else to assert that the notebook is named Untitled0
                self.assertEquals(len(glob.glob(td1 + "/Untitled0.ipynb")), 1)
                km.notebook_dir = td2
                nb2_id = km.new_notebook()
                self.assertEquals(len(glob.glob(td2 + "/Untitled1.ipynb")), 1)
                km.save_notebook(nb1_id, SIMPLE_NB, name="not_untitled", format="json")
                km.save_notebook(nb2_id, SIMPLE_NB, name="not_untitled2", format="json")
if __name__ == "__main__":
    import unittest
    unittest.main()

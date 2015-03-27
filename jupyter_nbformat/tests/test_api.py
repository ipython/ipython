"""Test the APIs at the top-level of nbformat"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os

from .base import TestsBase

from IPython.utils.tempdir import TemporaryDirectory
from ..reader import get_version
from IPython.nbformat import read, current_nbformat, writes, write


class TestAPI(TestsBase):

    def test_read(self):
        """Can older notebooks be opened and automatically converted to the current 
        nbformat?"""

        # Open a version 2 notebook.
        with self.fopen(u'test2.ipynb', 'r') as f:
            nb = read(f, as_version=current_nbformat)

        # Check that the notebook was upgraded to the latest version automatically.
        (major, minor) = get_version(nb)
        self.assertEqual(major, current_nbformat)

    def test_write_downgrade_2(self):
        """dowgrade a v3 notebook to v2"""
        # Open a version 3 notebook.
        with self.fopen(u'test3.ipynb', 'r') as f:
            nb = read(f, as_version=3)

        jsons = writes(nb, version=2)
        nb2 = json.loads(jsons)
        (major, minor) = get_version(nb2)
        self.assertEqual(major, 2)

    def test_read_write_path(self):
        """read() and write() take filesystem paths"""
        path = os.path.join(self._get_files_path(), u'test4.ipynb')
        nb = read(path, as_version=4)

        with TemporaryDirectory() as td:
            dest = os.path.join(td, 'echidna.ipynb')
            write(nb, dest)
            assert os.path.isfile(dest)

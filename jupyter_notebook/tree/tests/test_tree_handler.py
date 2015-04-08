"""Test the /tree handlers"""
import os
import io
from IPython.html.utils import url_path_join
from IPython.nbformat import write
from IPython.nbformat.v4 import new_notebook

import requests

from IPython.html.tests.launchnotebook import NotebookTestBase

class TreeTest(NotebookTestBase):
    def setUp(self):
        nbdir = self.notebook_dir.name
        d = os.path.join(nbdir, 'foo')
        os.mkdir(d)

        with io.open(os.path.join(d, 'bar.ipynb'), 'w', encoding='utf-8') as f:
            nb = new_notebook()
            write(nb, f, version=4)

        with io.open(os.path.join(d, 'baz.txt'), 'w', encoding='utf-8') as f:
            f.write(u'flamingo')

        self.base_url()

    def test_redirect(self):
        r = requests.get(url_path_join(self.base_url(), 'tree/foo/bar.ipynb'))
        self.assertEqual(r.url, self.base_url() + 'notebooks/foo/bar.ipynb')

        r = requests.get(url_path_join(self.base_url(), 'tree/foo/baz.txt'))
        self.assertEqual(r.url, url_path_join(self.base_url(), 'files/foo/baz.txt'))

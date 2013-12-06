import io
import json
import os
from os.path import join as pjoin
import shutil

import requests

from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase, assert_http_error
from IPython.nbformat.current import (new_notebook, write, new_worksheet,
                                      new_heading_cell, new_code_cell)

class NbconvertAPI(object):
    """Wrapper for nbconvert API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    def _req(self, verb, path, body=None):
        response = requests.request(verb,
                url_path_join(self.base_url, 'nbconvert', path),
                data=body,
        )
        response.raise_for_status()
        return response

    def from_file(self, format, path, name):
        return self._req('GET', url_path_join(format, path, name))

    def from_post(self, format, nbmodel):
        body = json.dumps(nbmodel)
        return self._req('POST', format, body)

class APITest(NotebookTestBase):
    def setUp(self):
        nbdir = self.notebook_dir.name
        
        if not os.path.isdir(pjoin(nbdir, 'foo')):
            os.mkdir(pjoin(nbdir, 'foo'))
        
        nb = new_notebook(name='testnb')
        
        ws = new_worksheet()
        nb.worksheets = [ws]
        ws.cells.append(new_heading_cell(u'Created by test ³'))
        ws.cells.append(new_code_cell(input=u'print(2*6)'))
        
        with io.open(pjoin(nbdir, 'foo', 'testnb.ipynb'), 'w',
                     encoding='utf-8') as f:
            write(nb, f, format='ipynb')

        self.nbconvert_api = NbconvertAPI(self.base_url())

    def tearDown(self):
        nbdir = self.notebook_dir.name

        for dname in ['foo']:
            shutil.rmtree(pjoin(nbdir, dname), ignore_errors=True)
    
    def test_from_file(self):
        r = self.nbconvert_api.from_file('html', 'foo', 'testnb.ipynb')
        self.assertEqual(r.status_code, 200)
        self.assertIn(u'Created by test', r.text)
        self.assertIn(u'print', r.text)
        
        r = self.nbconvert_api.from_file('python', 'foo', 'testnb.ipynb')
        self.assertIn(u'print(2*6)', r.text)

    def test_from_file_404(self):
        with assert_http_error(404):
            self.nbconvert_api.from_file('html', 'foo', 'thisdoesntexist.ipynb')

    def test_from_post(self):
        nbmodel_url = url_path_join(self.base_url(), 'api/notebooks/foo/testnb.ipynb')
        nbmodel = requests.get(nbmodel_url).json()
        
        r = self.nbconvert_api.from_post(format='html', nbmodel=nbmodel)
        self.assertEqual(r.status_code, 200)
        self.assertIn(u'Created by test', r.text)
        self.assertIn(u'print', r.text)
        
        r = self.nbconvert_api.from_post(format='python', nbmodel=nbmodel)
        self.assertIn(u'print(2*6)', r.text)
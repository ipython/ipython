# coding: utf-8
"""Test the /files/ handler."""

import io
import os
from unicodedata import normalize

pjoin = os.path.join

import requests

from IPython.html.utils import url_path_join
from .launchnotebook import NotebookTestBase
from IPython.utils import py3compat

class FilesTest(NotebookTestBase):
    def test_hidden_files(self):
        not_hidden = [
            u'å b',
            pjoin(u'å b/ç. d')
        ]
        hidden = [
            u'.å b',
            pjoin(u'å b/.ç d')
        ]
        dirs = not_hidden + hidden
        
        nbdir = self.notebook_dir.name
        for d in dirs:
            path = pjoin(nbdir, d.replace('/', os.path.sep))
            if not os.path.exists(path):
                os.mkdir(path)
            with open(pjoin(path, 'foo'), 'w') as f:
                f.write('foo')
            with open(pjoin(path, '.foo'), 'w') as f:
                f.write('.foo')
        url = self.base_url()
        
        for d in not_hidden:
            path = pjoin(nbdir, d.replace('/', os.path.sep))
            r = requests.get(url_path_join(url, 'files', d, 'foo'))
            r.raise_for_status()
            self.assertEqual(r.content, b'foo')
            r = requests.get(url_path_join(url, 'files', d, '.foo'))
            self.assertEqual(r.status_code, 403)
            
        for d in hidden:
            path = pjoin(nbdir, d.replace('/', os.path.sep))
            for foo in ('foo', '.foo'):
                r = requests.get(url_path_join(url, 'files', d, foo))
                self.assertEqual(r.status_code, 403)

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
            u'å b/ç. d',
        ]
        hidden = [
            u'.å b',
            u'å b/.ç d',
        ]
        dirs = not_hidden + hidden
        
        nbdir = self.notebook_dir.name
        for d in dirs:
            path = pjoin(nbdir, d.replace('/', os.sep))
            if not os.path.exists(path):
                os.mkdir(path)
            with open(pjoin(path, 'foo'), 'w') as f:
                f.write('foo')
            with open(pjoin(path, '.foo'), 'w') as f:
                f.write('.foo')
        url = self.base_url()
        
        for d in not_hidden:
            path = pjoin(nbdir, d.replace('/', os.sep))
            r = requests.get(url_path_join(url, 'files', d, 'foo'))
            r.raise_for_status()
            self.assertEqual(r.text, 'foo')
            r = requests.get(url_path_join(url, 'files', d, '.foo'))
            self.assertEqual(r.status_code, 404)
            
        for d in hidden:
            path = pjoin(nbdir, d.replace('/', os.sep))
            for foo in ('foo', '.foo'):
                r = requests.get(url_path_join(url, 'files', d, foo))
                self.assertEqual(r.status_code, 404)
    
    def test_old_files_redirect(self):
        """pre-2.0 'files/' prefixed links are properly redirected"""
        nbdir = self.notebook_dir.name
        base = self.base_url()
        
        os.mkdir(pjoin(nbdir, 'files'))
        os.makedirs(pjoin(nbdir, 'sub', 'files'))
        
        for prefix in ('', 'sub'):
            with open(pjoin(nbdir, prefix, 'files', 'f1.txt'), 'w') as f:
                f.write(prefix + '/files/f1')
            with open(pjoin(nbdir, prefix, 'files', 'f2.txt'), 'w') as f:
                f.write(prefix + '/files/f2')
            with open(pjoin(nbdir, prefix, 'f2.txt'), 'w') as f:
                f.write(prefix + '/f2')
            with open(pjoin(nbdir, prefix, 'f3.txt'), 'w') as f:
                f.write(prefix + '/f3')
            
            url = url_path_join(base, 'notebooks', prefix, 'files', 'f1.txt')
            r = requests.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.text, prefix + '/files/f1')

            url = url_path_join(base, 'notebooks', prefix, 'files', 'f2.txt')
            r = requests.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.text, prefix + '/files/f2')

            url = url_path_join(base, 'notebooks', prefix, 'files', 'f3.txt')
            r = requests.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.text, prefix + '/f3')


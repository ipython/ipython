# coding: utf-8
"""Test the /files/ handler."""

import io
import os
from unicodedata import normalize

pjoin = os.path.join

import requests
import json

from IPython.nbformat import write
from IPython.nbformat.v4 import (new_notebook,
                              new_markdown_cell, new_code_cell,
                              new_output)

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
    
    def test_contents_manager(self):
        "make sure ContentsManager returns right files (ipynb, bin, txt)."

        nbdir = self.notebook_dir.name
        base = self.base_url()

        nb = new_notebook(
            cells=[
                new_markdown_cell(u'Created by test ³'),
                new_code_cell("print(2*6)", outputs=[
                    new_output("stream", text="12"),
                ])
            ]
        )

        with io.open(pjoin(nbdir, 'testnb.ipynb'), 'w', 
            encoding='utf-8') as f:
            write(nb, f, version=4)

        with io.open(pjoin(nbdir, 'test.bin'), 'wb') as f:
            f.write(b'\xff' + os.urandom(5))
            f.close()

        with io.open(pjoin(nbdir, 'test.txt'), 'w') as f:
            f.write(u'foobar')
            f.close()

        r = requests.get(url_path_join(base, 'files', 'testnb.ipynb'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('print(2*6)', r.text)
        json.loads(r.text)

        r = requests.get(url_path_join(base, 'files', 'test.bin'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['content-type'], 'application/octet-stream')
        self.assertEqual(r.content[:1], b'\xff')
        self.assertEqual(len(r.content), 6)

        r = requests.get(url_path_join(base, 'files', 'test.txt'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers['content-type'], 'text/plain')
        self.assertEqual(r.text, 'foobar')
    
    def test_download(self):
        nbdir = self.notebook_dir.name
        base = self.base_url()
        
        text = 'hello'
        with open(pjoin(nbdir, 'test.txt'), 'w') as f:
            f.write(text)
        
        r = requests.get(url_path_join(base, 'files', 'test.txt'))
        disposition = r.headers.get('Content-Disposition', '')
        self.assertNotIn('attachment', disposition)

        r = requests.get(url_path_join(base, 'files', 'test.txt') + '?download=1')
        disposition = r.headers.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('filename="test.txt"', disposition)

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


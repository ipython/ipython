# coding: utf-8
"""Test the contents webservice API."""

import base64
import io
import json
import os
import shutil
from unicodedata import normalize

pjoin = os.path.join

import requests

from IPython.html.utils import url_path_join, url_escape
from IPython.html.tests.launchnotebook import NotebookTestBase, assert_http_error
from IPython.nbformat import current
from IPython.nbformat.current import (new_notebook, write, read, new_worksheet,
                                      new_heading_cell, to_notebook_json)
from IPython.nbformat import v2
from IPython.utils import py3compat
from IPython.utils.data import uniq_stable


def notebooks_only(dir_model):
    return [nb for nb in dir_model['content'] if nb['type']=='notebook']

def dirs_only(dir_model):
    return [x for x in dir_model['content'] if x['type']=='directory']


class API(object):
    """Wrapper for contents API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    def _req(self, verb, path, body=None):
        response = requests.request(verb,
                url_path_join(self.base_url, 'api/contents', path),
                data=body,
        )
        response.raise_for_status()
        return response

    def list(self, path='/'):
        return self._req('GET', path)

    def read(self, name, path='/'):
        return self._req('GET', url_path_join(path, name))

    def create_untitled(self, path='/', ext=None):
        body = None
        if ext:
            body = json.dumps({'ext': ext})
        return self._req('POST', path, body)

    def upload_untitled(self, body, path='/'):
        return self._req('POST', path, body)

    def copy_untitled(self, copy_from, path='/'):
        body = json.dumps({'copy_from':copy_from})
        return self._req('POST', path, body)

    def create(self, name, path='/'):
        return self._req('PUT', url_path_join(path, name))

    def upload(self, name, body, path='/'):
        return self._req('PUT', url_path_join(path, name), body)

    def mkdir(self, name, path='/'):
        return self._req('PUT', url_path_join(path, name), json.dumps({'type': 'directory'}))

    def copy(self, copy_from, copy_to, path='/'):
        body = json.dumps({'copy_from':copy_from})
        return self._req('PUT', url_path_join(path, copy_to), body)

    def save(self, name, body, path='/'):
        return self._req('PUT', url_path_join(path, name), body)

    def delete(self, name, path='/'):
        return self._req('DELETE', url_path_join(path, name))

    def rename(self, name, path, new_name):
        body = json.dumps({'name': new_name})
        return self._req('PATCH', url_path_join(path, name), body)

    def get_checkpoints(self, name, path):
        return self._req('GET', url_path_join(path, name, 'checkpoints'))

    def new_checkpoint(self, name, path):
        return self._req('POST', url_path_join(path, name, 'checkpoints'))

    def restore_checkpoint(self, name, path, checkpoint_id):
        return self._req('POST', url_path_join(path, name, 'checkpoints', checkpoint_id))

    def delete_checkpoint(self, name, path, checkpoint_id):
        return self._req('DELETE', url_path_join(path, name, 'checkpoints', checkpoint_id))

class APITest(NotebookTestBase):
    """Test the kernels web service API"""
    dirs_nbs = [('', 'inroot'),
                ('Directory with spaces in', 'inspace'),
                (u'unicodé', 'innonascii'),
                ('foo', 'a'),
                ('foo', 'b'),
                ('foo', 'name with spaces'),
                ('foo', u'unicodé'),
                ('foo/bar', 'baz'),
                ('ordering', 'A'),
                ('ordering', 'b'),
                ('ordering', 'C'),
                (u'å b', u'ç d'),
               ]
    hidden_dirs = ['.hidden', '__pycache__']

    dirs = uniq_stable([py3compat.cast_unicode(d) for (d,n) in dirs_nbs])
    del dirs[0]  # remove ''
    top_level_dirs = {normalize('NFC', d.split('/')[0]) for d in dirs}

    @staticmethod
    def _blob_for_name(name):
        return name.encode('utf-8') + b'\xFF'

    @staticmethod
    def _txt_for_name(name):
        return u'%s text file' % name

    def setUp(self):
        nbdir = self.notebook_dir.name
        self.blob = os.urandom(100)
        self.b64_blob = base64.encodestring(self.blob).decode('ascii')



        for d in (self.dirs + self.hidden_dirs):
            d.replace('/', os.sep)
            if not os.path.isdir(pjoin(nbdir, d)):
                os.mkdir(pjoin(nbdir, d))

        for d, name in self.dirs_nbs:
            d = d.replace('/', os.sep)
            # create a notebook
            with io.open(pjoin(nbdir, d, '%s.ipynb' % name), 'w',
                         encoding='utf-8') as f:
                nb = new_notebook(name=name)
                write(nb, f, format='ipynb')

            # create a text file
            with io.open(pjoin(nbdir, d, '%s.txt' % name), 'w',
                         encoding='utf-8') as f:
                f.write(self._txt_for_name(name))

            # create a binary file
            with io.open(pjoin(nbdir, d, '%s.blob' % name), 'wb') as f:
                f.write(self._blob_for_name(name))

        self.api = API(self.base_url())

    def tearDown(self):
        nbdir = self.notebook_dir.name

        for dname in (list(self.top_level_dirs) + self.hidden_dirs):
            shutil.rmtree(pjoin(nbdir, dname), ignore_errors=True)

        if os.path.isfile(pjoin(nbdir, 'inroot.ipynb')):
            os.unlink(pjoin(nbdir, 'inroot.ipynb'))

    def test_list_notebooks(self):
        nbs = notebooks_only(self.api.list().json())
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'inroot.ipynb')

        nbs = notebooks_only(self.api.list('/Directory with spaces in/').json())
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'inspace.ipynb')

        nbs = notebooks_only(self.api.list(u'/unicodé/').json())
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'innonascii.ipynb')
        self.assertEqual(nbs[0]['path'], u'unicodé')

        nbs = notebooks_only(self.api.list('/foo/bar/').json())
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'baz.ipynb')
        self.assertEqual(nbs[0]['path'], 'foo/bar')

        nbs = notebooks_only(self.api.list('foo').json())
        self.assertEqual(len(nbs), 4)
        nbnames = { normalize('NFC', n['name']) for n in nbs }
        expected = [ u'a.ipynb', u'b.ipynb', u'name with spaces.ipynb', u'unicodé.ipynb']
        expected = { normalize('NFC', name) for name in expected }
        self.assertEqual(nbnames, expected)

        nbs = notebooks_only(self.api.list('ordering').json())
        nbnames = [n['name'] for n in nbs]
        expected = ['A.ipynb', 'b.ipynb', 'C.ipynb']
        self.assertEqual(nbnames, expected)

    def test_list_dirs(self):
        dirs = dirs_only(self.api.list().json())
        dir_names = {normalize('NFC', d['name']) for d in dirs}
        self.assertEqual(dir_names, self.top_level_dirs)  # Excluding hidden dirs

    def test_list_nonexistant_dir(self):
        with assert_http_error(404):
            self.api.list('nonexistant')

    def test_get_nb_contents(self):
        for d, name in self.dirs_nbs:
            nb = self.api.read('%s.ipynb' % name, d+'/').json()
            self.assertEqual(nb['name'], u'%s.ipynb' % name)
            self.assertEqual(nb['type'], 'notebook')
            self.assertIn('content', nb)
            self.assertEqual(nb['format'], 'json')
            self.assertIn('content', nb)
            self.assertIn('metadata', nb['content'])
            self.assertIsInstance(nb['content']['metadata'], dict)

    def test_get_contents_no_such_file(self):
        # Name that doesn't exist - should be a 404
        with assert_http_error(404):
            self.api.read('q.ipynb', 'foo')

    def test_get_text_file_contents(self):
        for d, name in self.dirs_nbs:
            model = self.api.read(u'%s.txt' % name, d+'/').json()
            self.assertEqual(model['name'], u'%s.txt' % name)
            self.assertIn('content', model)
            self.assertEqual(model['format'], 'text')
            self.assertEqual(model['type'], 'file')
            self.assertEqual(model['content'], self._txt_for_name(name))

        # Name that doesn't exist - should be a 404
        with assert_http_error(404):
            self.api.read('q.txt', 'foo')

    def test_get_binary_file_contents(self):
        for d, name in self.dirs_nbs:
            model = self.api.read(u'%s.blob' % name, d+'/').json()
            self.assertEqual(model['name'], u'%s.blob' % name)
            self.assertIn('content', model)
            self.assertEqual(model['format'], 'base64')
            self.assertEqual(model['type'], 'file')
            b64_data = base64.encodestring(self._blob_for_name(name)).decode('ascii')
            self.assertEqual(model['content'], b64_data)

        # Name that doesn't exist - should be a 404
        with assert_http_error(404):
            self.api.read('q.txt', 'foo')

    def _check_created(self, resp, name, path, type='notebook'):
        self.assertEqual(resp.status_code, 201)
        location_header = py3compat.str_to_unicode(resp.headers['Location'])
        self.assertEqual(location_header, url_escape(url_path_join(u'/api/contents', path, name)))
        rjson = resp.json()
        self.assertEqual(rjson['name'], name)
        self.assertEqual(rjson['path'], path)
        self.assertEqual(rjson['type'], type)
        isright = os.path.isdir if type == 'directory' else os.path.isfile
        assert isright(pjoin(
            self.notebook_dir.name,
            path.replace('/', os.sep),
            name,
        ))

    def test_create_untitled(self):
        resp = self.api.create_untitled(path=u'å b')
        self._check_created(resp, 'Untitled0.ipynb', u'å b')

        # Second time
        resp = self.api.create_untitled(path=u'å b')
        self._check_created(resp, 'Untitled1.ipynb', u'å b')

        # And two directories down
        resp = self.api.create_untitled(path='foo/bar')
        self._check_created(resp, 'Untitled0.ipynb', 'foo/bar')

    def test_create_untitled_txt(self):
        resp = self.api.create_untitled(path='foo/bar', ext='.txt')
        self._check_created(resp, 'untitled0.txt', 'foo/bar', type='file')

        resp = self.api.read(path='foo/bar', name='untitled0.txt')
        model = resp.json()
        self.assertEqual(model['type'], 'file')
        self.assertEqual(model['format'], 'text')
        self.assertEqual(model['content'], '')

    def test_upload_untitled(self):
        nb = new_notebook(name='Upload test')
        nbmodel = {'content': nb, 'type': 'notebook'}
        resp = self.api.upload_untitled(path=u'å b',
                                              body=json.dumps(nbmodel))
        self._check_created(resp, 'Untitled0.ipynb', u'å b')

    def test_upload(self):
        nb = new_notebook(name=u'ignored')
        nbmodel = {'content': nb, 'type': 'notebook'}
        resp = self.api.upload(u'Upload tést.ipynb', path=u'å b',
                                              body=json.dumps(nbmodel))
        self._check_created(resp, u'Upload tést.ipynb', u'å b')

    def test_mkdir(self):
        resp = self.api.mkdir(u'New ∂ir', path=u'å b')
        self._check_created(resp, u'New ∂ir', u'å b', type='directory')

    def test_mkdir_hidden_400(self):
        with assert_http_error(400):
            resp = self.api.mkdir(u'.hidden', path=u'å b')

    def test_upload_txt(self):
        body = u'ünicode téxt'
        model = {
            'content' : body,
            'format'  : 'text',
            'type'    : 'file',
        }
        resp = self.api.upload(u'Upload tést.txt', path=u'å b',
                                              body=json.dumps(model))

        # check roundtrip
        resp = self.api.read(path=u'å b', name=u'Upload tést.txt')
        model = resp.json()
        self.assertEqual(model['type'], 'file')
        self.assertEqual(model['format'], 'text')
        self.assertEqual(model['content'], body)

    def test_upload_b64(self):
        body = b'\xFFblob'
        b64body = base64.encodestring(body).decode('ascii')
        model = {
            'content' : b64body,
            'format'  : 'base64',
            'type'    : 'file',
        }
        resp = self.api.upload(u'Upload tést.blob', path=u'å b',
                                              body=json.dumps(model))

        # check roundtrip
        resp = self.api.read(path=u'å b', name=u'Upload tést.blob')
        model = resp.json()
        self.assertEqual(model['type'], 'file')
        self.assertEqual(model['format'], 'base64')
        decoded = base64.decodestring(model['content'].encode('ascii'))
        self.assertEqual(decoded, body)

    def test_upload_v2(self):
        nb = v2.new_notebook()
        ws = v2.new_worksheet()
        nb.worksheets.append(ws)
        ws.cells.append(v2.new_code_cell(input='print("hi")'))
        nbmodel = {'content': nb, 'type': 'notebook'}
        resp = self.api.upload(u'Upload tést.ipynb', path=u'å b',
                                              body=json.dumps(nbmodel))
        self._check_created(resp, u'Upload tést.ipynb', u'å b')
        resp = self.api.read(u'Upload tést.ipynb', u'å b')
        data = resp.json()
        self.assertEqual(data['content']['nbformat'], current.nbformat)
        self.assertEqual(data['content']['orig_nbformat'], 2)

    def test_copy_untitled(self):
        resp = self.api.copy_untitled(u'ç d.ipynb', path=u'å b')
        self._check_created(resp, u'ç d-Copy0.ipynb', u'å b')

    def test_copy(self):
        resp = self.api.copy(u'ç d.ipynb', u'cøpy.ipynb', path=u'å b')
        self._check_created(resp, u'cøpy.ipynb', u'å b')

    def test_copy_path(self):
        resp = self.api.copy(u'foo/a.ipynb', u'cøpyfoo.ipynb', path=u'å b')
        self._check_created(resp, u'cøpyfoo.ipynb', u'å b')

    def test_copy_dir_400(self):
        # can't copy directories
        with assert_http_error(400):
            resp = self.api.copy(u'å b', u'å c')

    def test_delete(self):
        for d, name in self.dirs_nbs:
            resp = self.api.delete('%s.ipynb' % name, d)
            self.assertEqual(resp.status_code, 204)

        for d in self.dirs + ['/']:
            nbs = notebooks_only(self.api.list(d).json())
            self.assertEqual(len(nbs), 0)

    def test_delete_dirs(self):
        # depth-first delete everything, so we don't try to delete empty directories
        for name in sorted(self.dirs + ['/'], key=len, reverse=True):
            listing = self.api.list(name).json()['content']
            for model in listing:
                self.api.delete(model['name'], model['path'])
        listing = self.api.list('/').json()['content']
        self.assertEqual(listing, [])

    def test_delete_non_empty_dir(self):
        """delete non-empty dir raises 400"""
        with assert_http_error(400):
            self.api.delete(u'å b')

    def test_rename(self):
        resp = self.api.rename('a.ipynb', 'foo', 'z.ipynb')
        self.assertEqual(resp.headers['Location'].split('/')[-1], 'z.ipynb')
        self.assertEqual(resp.json()['name'], 'z.ipynb')
        assert os.path.isfile(pjoin(self.notebook_dir.name, 'foo', 'z.ipynb'))

        nbs = notebooks_only(self.api.list('foo').json())
        nbnames = set(n['name'] for n in nbs)
        self.assertIn('z.ipynb', nbnames)
        self.assertNotIn('a.ipynb', nbnames)

    def test_rename_existing(self):
        with assert_http_error(409):
            self.api.rename('a.ipynb', 'foo', 'b.ipynb')

    def test_save(self):
        resp = self.api.read('a.ipynb', 'foo')
        nbcontent = json.loads(resp.text)['content']
        nb = to_notebook_json(nbcontent)
        ws = new_worksheet()
        nb.worksheets = [ws]
        ws.cells.append(new_heading_cell(u'Created by test ³'))

        nbmodel= {'name': 'a.ipynb', 'path':'foo', 'content': nb, 'type': 'notebook'}
        resp = self.api.save('a.ipynb', path='foo', body=json.dumps(nbmodel))

        nbfile = pjoin(self.notebook_dir.name, 'foo', 'a.ipynb')
        with io.open(nbfile, 'r', encoding='utf-8') as f:
            newnb = read(f, format='ipynb')
        self.assertEqual(newnb.worksheets[0].cells[0].source,
                         u'Created by test ³')
        nbcontent = self.api.read('a.ipynb', 'foo').json()['content']
        newnb = to_notebook_json(nbcontent)
        self.assertEqual(newnb.worksheets[0].cells[0].source,
                         u'Created by test ³')

        # Save and rename
        nbmodel= {'name': 'a2.ipynb', 'path':'foo/bar', 'content': nb, 'type': 'notebook'}
        resp = self.api.save('a.ipynb', path='foo', body=json.dumps(nbmodel))
        saved = resp.json()
        self.assertEqual(saved['name'], 'a2.ipynb')
        self.assertEqual(saved['path'], 'foo/bar')
        assert os.path.isfile(pjoin(self.notebook_dir.name,'foo','bar','a2.ipynb'))
        assert not os.path.isfile(pjoin(self.notebook_dir.name, 'foo', 'a.ipynb'))
        with assert_http_error(404):
            self.api.read('a.ipynb', 'foo')

    def test_checkpoints(self):
        resp = self.api.read('a.ipynb', 'foo')
        r = self.api.new_checkpoint('a.ipynb', 'foo')
        self.assertEqual(r.status_code, 201)
        cp1 = r.json()
        self.assertEqual(set(cp1), {'id', 'last_modified'})
        self.assertEqual(r.headers['Location'].split('/')[-1], cp1['id'])

        # Modify it
        nbcontent = json.loads(resp.text)['content']
        nb = to_notebook_json(nbcontent)
        ws = new_worksheet()
        nb.worksheets = [ws]
        hcell = new_heading_cell('Created by test')
        ws.cells.append(hcell)
        # Save
        nbmodel= {'name': 'a.ipynb', 'path':'foo', 'content': nb, 'type': 'notebook'}
        resp = self.api.save('a.ipynb', path='foo', body=json.dumps(nbmodel))

        # List checkpoints
        cps = self.api.get_checkpoints('a.ipynb', 'foo').json()
        self.assertEqual(cps, [cp1])

        nbcontent = self.api.read('a.ipynb', 'foo').json()['content']
        nb = to_notebook_json(nbcontent)
        self.assertEqual(nb.worksheets[0].cells[0].source, 'Created by test')

        # Restore cp1
        r = self.api.restore_checkpoint('a.ipynb', 'foo', cp1['id'])
        self.assertEqual(r.status_code, 204)
        nbcontent = self.api.read('a.ipynb', 'foo').json()['content']
        nb = to_notebook_json(nbcontent)
        self.assertEqual(nb.worksheets, [])

        # Delete cp1
        r = self.api.delete_checkpoint('a.ipynb', 'foo', cp1['id'])
        self.assertEqual(r.status_code, 204)
        cps = self.api.get_checkpoints('a.ipynb', 'foo').json()
        self.assertEqual(cps, [])

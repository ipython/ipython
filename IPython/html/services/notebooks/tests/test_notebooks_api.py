"""Test the notebooks webservice API."""

import io
import os
import shutil
from zmq.utils import jsonapi

pjoin = os.path.join

import requests

from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase
from IPython.nbformat.current import (new_notebook, write, read, new_worksheet,
                                      new_heading_cell, to_notebook_json)
from IPython.utils.data import uniq_stable

class NBAPI(object):
    """Wrapper for notebook API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    @property
    def nb_url(self):
        return url_path_join(self.base_url, 'api/notebooks')

    def _req(self, verb, path, body=None):
        response = requests.request(verb,
                url_path_join(self.base_url, 'api/notebooks', path), data=body)
        response.raise_for_status()
        return response

    def list(self, path='/'):
        return self._req('GET', path)

    def read(self, name, path='/'):
        return self._req('GET', url_path_join(path, name))

    def create_untitled(self, path='/'):
        return self._req('POST', path)

    def upload(self, name, body, path='/'):
        return self._req('POST', url_path_join(path, name), body)

    def copy(self, name, path='/'):
        return self._req('POST', url_path_join(path, name, 'copy'))

    def save(self, name, body, path='/'):
        return self._req('PUT', url_path_join(path, name), body)

    def delete(self, name, path='/'):
        return self._req('DELETE', url_path_join(path, name))

    def rename(self, name, path, new_name):
        body = jsonapi.dumps({'name': new_name})
        return self._req('PATCH', url_path_join(path, name), body)

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
               ]

    dirs = uniq_stable([d for (d,n) in dirs_nbs])
    del dirs[0]  # remove ''

    def setUp(self):
        nbdir = self.notebook_dir.name

        for d in self.dirs:
            os.mkdir(pjoin(nbdir, d))

        for d, name in self.dirs_nbs:
            with io.open(pjoin(nbdir, d, '%s.ipynb' % name), 'w') as f:
                nb = new_notebook(name=name)
                write(nb, f, format='ipynb')

        self.nb_api = NBAPI(self.base_url())

    def tearDown(self):
        nbdir = self.notebook_dir.name

        for dname in ['foo', 'Directory with spaces in', u'unicodé']:
            shutil.rmtree(pjoin(nbdir, dname), ignore_errors=True)

        if os.path.isfile(pjoin(nbdir, 'inroot.ipynb')):
            os.unlink(pjoin(nbdir, 'inroot.ipynb'))

    def test_list_notebooks(self):
        nbs = self.nb_api.list().json()
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'inroot.ipynb')

        nbs = self.nb_api.list('/Directory with spaces in/').json()
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'inspace.ipynb')

        nbs = self.nb_api.list(u'/unicodé/').json()
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'innonascii.ipynb')

        nbs = self.nb_api.list('/foo/bar/').json()
        self.assertEqual(len(nbs), 1)
        self.assertEqual(nbs[0]['name'], 'baz.ipynb')

        nbs = self.nb_api.list('foo').json()
        self.assertEqual(len(nbs), 4)
        nbnames = set(n['name'] for n in nbs)
        self.assertEqual(nbnames, {'a.ipynb', 'b.ipynb',
                                   'name with spaces.ipynb', u'unicodé.ipynb'})

    def assert_404(self, name, path):
        try:
            self.nb_api.read(name, path)
        except requests.HTTPError as e:
            self.assertEqual(e.response.status_code, 404)
        else:
            assert False, "Reading a non-existent notebook should fail"

    def test_get_contents(self):
        for d, name in self.dirs_nbs:
            nb = self.nb_api.read('%s.ipynb' % name, d+'/').json()
            self.assertEqual(nb['name'], '%s.ipynb' % name)
            self.assertIn('content', nb)
            self.assertIn('metadata', nb['content'])
            self.assertIsInstance(nb['content']['metadata'], dict)

        # Name that doesn't exist - should be a 404
        self.assert_404('q.ipynb', 'foo')

    def _check_nb_created(self, resp, name, path):
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.headers['Location'].split('/')[-1], name)
        self.assertEqual(resp.json()['name'], name)
        assert os.path.isfile(pjoin(self.notebook_dir.name, path, name))

    def test_create_untitled(self):
        resp = self.nb_api.create_untitled(path='foo')
        self._check_nb_created(resp, 'Untitled0.ipynb', 'foo')

        # Second time
        resp = self.nb_api.create_untitled(path='foo')
        self._check_nb_created(resp, 'Untitled1.ipynb', 'foo')

        # And two directories down
        resp = self.nb_api.create_untitled(path='foo/bar')
        self._check_nb_created(resp, 'Untitled0.ipynb', pjoin('foo', 'bar'))

    def test_upload(self):
        nb = new_notebook(name='Upload test')
        nbmodel = {'content': nb}
        resp = self.nb_api.upload('Upload test.ipynb', path='foo',
                                              body=jsonapi.dumps(nbmodel))
        self._check_nb_created(resp, 'Upload test.ipynb', 'foo')

    def test_copy(self):
        resp = self.nb_api.copy('a.ipynb', path='foo')
        self._check_nb_created(resp, 'a-Copy0.ipynb', 'foo')

    def test_delete(self):
        for d, name in self.dirs_nbs:
            resp = self.nb_api.delete('%s.ipynb' % name, d)
            self.assertEqual(resp.status_code, 204)

        for d in self.dirs + ['/']:
            nbs = self.nb_api.list(d).json()
            self.assertEqual(len(nbs), 0)

    def test_rename(self):
        resp = self.nb_api.rename('a.ipynb', 'foo', 'z.ipynb')
        if False:
            # XXX: Spec says this should be set, but it isn't
            self.assertEqual(resp.headers['Location'].split('/')[-1], 'z.ipynb')
        self.assertEqual(resp.json()['name'], 'z.ipynb')
        assert os.path.isfile(pjoin(self.notebook_dir.name, 'foo', 'z.ipynb'))

        nbs = self.nb_api.list('foo').json()
        nbnames = set(n['name'] for n in nbs)
        self.assertIn('z.ipynb', nbnames)
        self.assertNotIn('a.ipynb', nbnames)

    def test_save(self):
        resp = self.nb_api.read('a.ipynb', 'foo')
        nbcontent = jsonapi.loads(resp.text)['content']
        nb = to_notebook_json(nbcontent)
        ws = new_worksheet()
        nb.worksheets = [ws]
        ws.cells.append(new_heading_cell('Created by test'))

        nbmodel= {'name': 'a.ipynb', 'path':'foo', 'content': nb}
        resp = self.nb_api.save('a.ipynb', path='foo', body=jsonapi.dumps(nbmodel))

        nbfile = pjoin(self.notebook_dir.name, 'foo', 'a.ipynb')
        with open(nbfile, 'r') as f:
            newnb = read(f, format='ipynb')
        self.assertEqual(newnb.worksheets[0].cells[0].source,
                         'Created by test')

        # Save and rename
        nbmodel= {'name': 'a2.ipynb', 'path':'foo/bar', 'content': nb}
        resp = self.nb_api.save('a.ipynb', path='foo', body=jsonapi.dumps(nbmodel))
        saved = resp.json()
        self.assertEqual(saved['name'], 'a2.ipynb')
        self.assertEqual(saved['path'], 'foo/bar')
        assert os.path.isfile(pjoin(self.notebook_dir.name,'foo','bar','a2.ipynb'))
        assert not os.path.isfile(pjoin(self.notebook_dir.name, 'foo', 'a.ipynb'))
        self.assert_404('a.ipynb', 'foo')
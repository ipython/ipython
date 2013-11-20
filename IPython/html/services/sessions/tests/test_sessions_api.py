"""Test the sessions web service API."""

import errno
import io
import os
import json
import requests
import shutil

pjoin = os.path.join

from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase, assert_http_error
from IPython.nbformat.current import new_notebook, write

class SessionAPI(object):
    """Wrapper for notebook API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    def _req(self, verb, path, body=None):
        response = requests.request(verb,
                url_path_join(self.base_url, 'api/sessions', path), data=body)

        if 400 <= response.status_code < 600:
            try:
                response.reason = response.json()['message']
            except:
                pass
        response.raise_for_status()

        return response

    def list(self):
        return self._req('GET', '')

    def get(self, id):
        return self._req('GET', id)

    def create(self, name, path):
        body = json.dumps({'notebook': {'name':name, 'path':path}})
        return self._req('POST', '', body)

    def modify(self, id, name, path):
        body = json.dumps({'notebook': {'name':name, 'path':path}})
        return self._req('PATCH', id, body)

    def delete(self, id):
        return self._req('DELETE', id)

class SessionAPITest(NotebookTestBase):
    """Test the sessions web service API"""
    def setUp(self):
        nbdir = self.notebook_dir.name
        try:
            os.mkdir(pjoin(nbdir, 'foo'))
        except OSError as e:
            # Deleting the folder in an earlier test may have failed
            if e.errno != errno.EEXIST:
                raise

        with io.open(pjoin(nbdir, 'foo', 'nb1.ipynb'), 'w',
                     encoding='utf-8') as f:
            nb = new_notebook(name='nb1')
            write(nb, f, format='ipynb')

        self.sess_api = SessionAPI(self.base_url())

    def tearDown(self):
        for session in self.sess_api.list().json():
            self.sess_api.delete(session['id'])
        shutil.rmtree(pjoin(self.notebook_dir.name, 'foo'),
                      ignore_errors=True)

    def test_create(self):
        sessions = self.sess_api.list().json()
        self.assertEqual(len(sessions), 0)

        resp = self.sess_api.create('nb1.ipynb', 'foo')
        self.assertEqual(resp.status_code, 201)
        newsession = resp.json()
        self.assertIn('id', newsession)
        self.assertEqual(newsession['notebook']['name'], 'nb1.ipynb')
        self.assertEqual(newsession['notebook']['path'], 'foo')
        self.assertEqual(resp.headers['Location'], '/api/sessions/{0}'.format(newsession['id']))

        sessions = self.sess_api.list().json()
        self.assertEqual(sessions, [newsession])

        # Retrieve it
        sid = newsession['id']
        got = self.sess_api.get(sid).json()
        self.assertEqual(got, newsession)

    def test_delete(self):
        newsession = self.sess_api.create('nb1.ipynb', 'foo').json()
        sid = newsession['id']

        resp = self.sess_api.delete(sid)
        self.assertEqual(resp.status_code, 204)

        sessions = self.sess_api.list().json()
        self.assertEqual(sessions, [])

        with assert_http_error(404):
            self.sess_api.get(sid)

    def test_modify(self):
        newsession = self.sess_api.create('nb1.ipynb', 'foo').json()
        sid = newsession['id']

        changed = self.sess_api.modify(sid, 'nb2.ipynb', '').json()
        self.assertEqual(changed['id'], sid)
        self.assertEqual(changed['notebook']['name'], 'nb2.ipynb')
        self.assertEqual(changed['notebook']['path'], '')

"""Test the sessions web service API."""

import io
import os
import json
import requests
import shutil

pjoin = os.path.join

from IPython.utils.jsonutil import date_default
from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase
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
        os.mkdir(pjoin(nbdir, 'foo'))

        with io.open(pjoin(nbdir, 'foo', 'nb1.ipynb'), 'w') as f:
            nb = new_notebook(name='nb1')
            write(nb, f, format='ipynb')

        self.sess_api = SessionAPI(self.base_url())

    def tearDown(self):
        for session in self.sess_api.list().json():
            self.sess_api.delete(session['id'])
        shutil.rmtree(pjoin(self.notebook_dir.name, 'foo'))

    def assert_404(self, id):
        try:
            self.sess_api.get(id)
        except requests.HTTPError as e:
            self.assertEqual(e.response.status_code, 404)
        else:
            assert False, "Getting nonexistent session didn't give HTTP error"

    def test_create(self):
        sessions = self.sess_api.list().json()
        self.assertEqual(len(sessions), 0)

        resp = self.sess_api.create('nb1.ipynb', 'foo')
        self.assertEqual(resp.status_code, 201)
        newsession = resp.json()
        self.assertIn('id', newsession)
        self.assertEqual(newsession['notebook']['name'], 'nb1.ipynb')
        self.assertEqual(newsession['notebook']['path'], 'foo')

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

        self.assert_404(sid)

    def test_modify(self):
        newsession = self.sess_api.create('nb1.ipynb', 'foo').json()
        sid = newsession['id']

        changed = self.sess_api.modify(sid, 'nb2.ipynb', '').json()
        self.assertEqual(changed['id'], sid)
        self.assertEqual(changed['notebook']['name'], 'nb2.ipynb')
        self.assertEqual(changed['notebook']['path'], '')

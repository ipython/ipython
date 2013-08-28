"""Test the sessions web service API."""


import os
import sys
import json
import requests

from IPython.utils.jsonutil import date_default
from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase

class SessionAPITest(NotebookTestBase):
    """Test the sessions web service API"""
    
    def notebook_url(self):
        return url_path_join(super(SessionAPITest,self).base_url(), 'api/notebooks')

    def session_url(self):
        return super(SessionAPITest,self).base_url() + 'api/sessions'

    def mknb(self, name='', path='/'):
        url = self.notebook_url() + path
        return url, requests.post(url)

    def delnb(self, name, path='/'):
        url = self.notebook_url() + path + name
        r = requests.delete(url)
        return r.status_code

    def test_no_sessions(self):
        """Make sure there are no sessions running at the start"""
        url = self.session_url()
        r = requests.get(url)
        self.assertEqual(r.json(), [])

    def test_session_root_handler(self):
        # POST a session
        url, nb = self.mknb()
        notebook = nb.json()
        model = {'notebook': {'name':notebook['name'], 'path': notebook['path']}}
        r = requests.post(self.session_url(), data=json.dumps(model, default=date_default))
        data = r.json()
        assert isinstance(data, dict)
        self.assertIn('name', data['notebook'])
        self.assertEqual(data['notebook']['name'], notebook['name'])

        # GET sessions
        r = requests.get(self.session_url())
        assert isinstance(r.json(), list)
        assert isinstance(r.json()[0], dict)
        self.assertEqual(r.json()[0]['id'], data['id'])

        # Clean up
        self.delnb('Untitled0.ipynb')
        sess_url = self.session_url() +'/'+data['id']
        r = requests.delete(sess_url)
        self.assertEqual(r.status_code, 204)

    def test_session_handler(self):
        # Create a session
        url, nb = self.mknb()
        notebook = nb.json()
        model = {'notebook': {'name':notebook['name'], 'path': notebook['path']}}
        r = requests.post(self.session_url(), data=json.dumps(model, default=date_default))
        session = r.json()

        # GET a session
        sess_url = self.session_url() + '/' + session['id']
        r = requests.get(sess_url)
        assert isinstance(r.json(), dict)
        self.assertEqual(r.json(), session)

        # PATCH a session
        model = {'notebook': {'name':'test.ipynb', 'path': '/'}}
        r = requests.patch(sess_url, data=json.dumps(model, default=date_default))
        
        # Patching the notebook webservice too (just for consistency)
        requests.patch(self.notebook_url() + '/Untitled0.ipynb', 
            data=json.dumps({'name':'test.ipynb'}))
        print r.json()
        assert isinstance(r.json(), dict)
        self.assertIn('name', r.json()['notebook'])
        self.assertIn('id', r.json())
        self.assertEqual(r.json()['notebook']['name'], 'test.ipynb')
        self.assertEqual(r.json()['id'], session['id'])

        # DELETE a session
        r = requests.delete(sess_url)
        self.assertEqual(r.status_code, 204)
        r = requests.get(self.session_url())
        self.assertEqual(r.json(), [])
        
        # Clean up
        r = self.delnb('test.ipynb')
        self.assertEqual(r, 204)
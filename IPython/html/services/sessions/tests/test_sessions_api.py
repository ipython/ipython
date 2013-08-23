"""Test the sessions web service API."""


import os
import sys
import json
from zmq.utils import jsonapi

import requests

from IPython.html.tests.launchnotebook import NotebookTestBase


class SessionAPITest(NotebookTestBase):
    """Test the sessions web service API"""
    
    def notebook_url(self):
        return super(SessionAPITest,self).base_url() + 'api/notebooks'

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
        param = {'notebook_path': notebook['path'] + notebook['name']}
        r = requests.post(self.session_url(), params=param)
        data = r.json()
        assert isinstance(data, dict)
        assert data.has_key('name')
        self.assertEqual(data['name'], notebook['name'])

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
        param = {'notebook_path': notebook['path'] + notebook['name']}
        r = requests.post(self.session_url(), params=param)
        session = r.json()

        # GET a session
        sess_url = self.session_url() + '/' + session['id']
        r = requests.get(sess_url)
        assert isinstance(r.json(), dict)
        self.assertEqual(r.json(), session)

        # PATCH a session
        data = {'notebook_path': 'test.ipynb'}
        r = requests.patch(sess_url, data=jsonapi.dumps(data))
        # Patching the notebook webservice too (just for consistency)
        requests.patch(self.notebook_url() + '/Untitled0.ipynb', 
            data=jsonapi.dumps({'name':'test.ipynb'}))
        assert isinstance(r.json(), dict)
        assert r.json().has_key('name')
        assert r.json().has_key('id')
        self.assertEqual(r.json()['name'], 'test.ipynb')
        self.assertEqual(r.json()['id'], session['id'])

        # DELETE a session
        r = requests.delete(sess_url)
        self.assertEqual(r.status_code, 204)
        r = requests.get(self.session_url())
        assert r.json() == []
        
        # Clean up
        r = self.delnb('test.ipynb')
        assert r == 204
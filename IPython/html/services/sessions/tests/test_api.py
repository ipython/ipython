"""Test the sessions service API."""


import os
import sys
import json
import urllib

import requests

from IPython.html.tests.launchnotebook import NotebookTestBase

'''
class SessionAPITest(NotebookTestBase):
    """Test the sessions web service API"""

    def base_url(self):
        return super(SessionAPITest,self).base_url() + 'api/sessions'

    def test_no_sessions(self):
        """Make sure there are no sessions running at the start"""
        url = self.base_url()
        r = requests.get(url)
        self.assertEqual(r.json(), [])

    def test_start_session(self):
        url = self.base_url()
        param = urllib.urlencode({'notebook_path': 'test.ipynb'})
        r = requests.post(url, params=param)
        print r
        #self.assertNotEqual(r.json(), [])
'''
"""Test the kernels service API."""


import os
import sys
import json

import requests

from IPython.html.tests.launchnotebook import NotebookTestBase


class KernelAPITest(NotebookTestBase):
    """Test the kernels web service API"""

    def base_url(self):
        return super(KernelAPITest,self).base_url() + 'api/kernels'

    def mkkernel(self):
        r = requests.post(self.base_url())
        return r.json()

    def test_no_kernels(self):
        """Make sure there are no kernels running at the start"""
        url = self.base_url()
        r = requests.get(url)
        self.assertEqual(r.json(), [])

    def test_main_kernel_handler(self):
        # POST request
        r = requests.post(self.base_url())
        data = r.json()
        assert isinstance(data, dict)

        # GET request
        r = requests.get(self.base_url())
        assert isinstance(r.json(), list)
        self.assertEqual(r.json()[0], data['id'])

    def test_kernel_handler(self):
        # GET kernel with id
        data = self.mkkernel()
        url = self.base_url() +'/' + data['id']
        r = requests.get(url)
        assert isinstance(r.json(), dict)
        self.assertIn('id', r.json())
        self.assertEqual(r.json()['id'], data['id'])
        
        # DELETE kernel with id
        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)
        r = requests.get(self.base_url())
        self.assertEqual(r.json(), [])
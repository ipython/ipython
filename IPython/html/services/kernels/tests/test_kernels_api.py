"""Test the kernels service API."""


import os
import sys
import json

import requests

from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase


class KernelAPITest(NotebookTestBase):
    """Test the kernels web service API"""

    def base_url(self):
        return url_path_join(super(KernelAPITest,self).base_url(), 'api/kernels')

    def mkkernel(self):
        r = requests.post(self.base_url())
        return r.json()

    def test__no_kernels(self):
        """Make sure there are no kernels running at the start"""
        url = self.base_url()
        r = requests.get(url)
        self.assertEqual(r.json(), [])

    def test_main_kernel_handler(self):
        # POST request
        r = requests.post(self.base_url())
        data = r.json()
        status = r.status_code
        header = r.headers
        self.assertIn('location', header)
        self.assertEquals(header['location'], '/api/kernels/' + data['id'])
        self.assertEquals(status, 201)
        assert isinstance(data, dict)

        # GET request
        r = requests.get(self.base_url())
        status = r.status_code
        self.assertEquals(status, 200)
        assert isinstance(r.json(), list)
        self.assertEqual(r.json()[0]['id'], data['id'])
        
        # create another kernel and check that they both are added to the 
        # list of kernels from a GET request
        data2 = self.mkkernel()
        assert isinstance(data2, dict)
        r = requests.get(self.base_url())
        kernels = r.json()
        status = r.status_code
        self.assertEquals(status, 200)
        assert isinstance(kernels, list)
        self.assertEquals(len(kernels), 2)

    def test_kernel_handler(self):
        # GET kernel with given id
        data = self.mkkernel()
        url = self.base_url() +'/' + data['id']
        r = requests.get(url)
        data1 = r.json()
        status = r.status_code
        self.assertEquals(status, 200)
        assert isinstance(data1, dict)
        self.assertIn('id', data1)
        self.assertIn('ws_url', data1)
        self.assertEqual(data1['id'], data['id'])
        
        # Request a bad kernel id and check that a JSON
        # message is returned!
        bad_id = '111-111-111-111-111'
        bad_url = self.base_url() + '/' + bad_id
        r = requests.get(bad_url)
        status = r.status_code
        message = r.json()
        self.assertEquals(status, 404)
        assert isinstance(message, dict)
        self.assertIn('message', message)
        self.assertEquals(message['message'], 'Kernel does not exist: ' + bad_id)
        
        # DELETE kernel with id
        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)
        r = requests.get(self.base_url())
        self.assertEqual(r.json(), [])
        
        # Request to delete a non-existent kernel id
        bad_id = '111-111-111-111-111'
        bad_url = self.base_url() + '/' + bad_id
        r = requests.delete(bad_url)
        status = r.status_code
        message = r.json()
        self.assertEquals(status, 404)
        assert isinstance(message, dict)
        self.assertIn('message', message)
        self.assertEquals(message['message'], 'Kernel does not exist: ' + bad_id)
        
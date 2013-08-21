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

    def test_no_kernels(self):
        """Make sure there are no kernels running at the start"""
        url = self.base_url()
        r = requests.get(url)
        assert r.json() == []

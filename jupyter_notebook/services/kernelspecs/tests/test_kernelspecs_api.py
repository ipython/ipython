# coding: utf-8
"""Test the kernel specs webservice API."""

import errno
import io
import json
import os
import shutil

pjoin = os.path.join

import requests

from IPython.kernel.kernelspec import NATIVE_KERNEL_NAME
from IPython.html.utils import url_path_join
from IPython.html.tests.launchnotebook import NotebookTestBase, assert_http_error

# Copied from IPython.kernel.tests.test_kernelspec so updating that doesn't
# break these tests
sample_kernel_json = {'argv':['cat', '{connection_file}'],
                      'display_name':'Test kernel',
                     }

some_resource = u"The very model of a modern major general"


class KernelSpecAPI(object):
    """Wrapper for notebook API calls."""
    def __init__(self, base_url):
        self.base_url = base_url

    def _req(self, verb, path, body=None):
        response = requests.request(verb,
                url_path_join(self.base_url, path),
                data=body,
        )
        response.raise_for_status()
        return response

    def list(self):
        return self._req('GET', 'api/kernelspecs')

    def kernel_spec_info(self, name):
        return self._req('GET', url_path_join('api/kernelspecs', name))
    
    def kernel_resource(self, name, path):
        return self._req('GET', url_path_join('kernelspecs', name, path))

class APITest(NotebookTestBase):
    """Test the kernelspec web service API"""
    def setUp(self):
        ipydir = self.ipython_dir.name
        sample_kernel_dir = pjoin(ipydir, 'kernels', 'sample')
        try:
            os.makedirs(sample_kernel_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        
        with open(pjoin(sample_kernel_dir, 'kernel.json'), 'w') as f:
            json.dump(sample_kernel_json, f)
        
        with io.open(pjoin(sample_kernel_dir, 'resource.txt'), 'w',
                     encoding='utf-8') as f:
            f.write(some_resource)

        self.ks_api = KernelSpecAPI(self.base_url())

    def test_list_kernelspecs_bad(self):
        """Can list kernelspecs when one is invalid"""
        bad_kernel_dir = pjoin(self.ipython_dir.name, 'kernels', 'bad')
        try:
            os.makedirs(bad_kernel_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        
        with open(pjoin(bad_kernel_dir, 'kernel.json'), 'w') as f:
            f.write("garbage")
        
        model = self.ks_api.list().json()
        assert isinstance(model, dict)
        self.assertEqual(model['default'], NATIVE_KERNEL_NAME)
        specs = model['kernelspecs']
        assert isinstance(specs, dict)
        # 2: the sample kernelspec created in setUp, and the native Python kernel
        self.assertGreaterEqual(len(specs), 2)
        
        shutil.rmtree(bad_kernel_dir)
    
    def test_list_kernelspecs(self):
        model = self.ks_api.list().json()
        assert isinstance(model, dict)
        self.assertEqual(model['default'], NATIVE_KERNEL_NAME)
        specs = model['kernelspecs']
        assert isinstance(specs, dict)

        # 2: the sample kernelspec created in setUp, and the native Python kernel
        self.assertGreaterEqual(len(specs), 2)

        def is_sample_kernelspec(s):
            return s['name'] == 'sample' and s['spec']['display_name'] == 'Test kernel'

        def is_default_kernelspec(s):
            return s['name'] == NATIVE_KERNEL_NAME and s['spec']['display_name'].startswith("Python")

        assert any(is_sample_kernelspec(s) for s in specs.values()), specs
        assert any(is_default_kernelspec(s) for s in specs.values()), specs

    def test_get_kernelspec(self):
        model = self.ks_api.kernel_spec_info('Sample').json()  # Case insensitive
        self.assertEqual(model['name'].lower(), 'sample')
        self.assertIsInstance(model['spec'], dict)
        self.assertEqual(model['spec']['display_name'], 'Test kernel')
        self.assertIsInstance(model['resources'], dict)

    def test_get_nonexistant_kernelspec(self):
        with assert_http_error(404):
            self.ks_api.kernel_spec_info('nonexistant')
    
    def test_get_kernel_resource_file(self):
        res = self.ks_api.kernel_resource('sAmple', 'resource.txt')
        self.assertEqual(res.text, some_resource)
    
    def test_get_nonexistant_resource(self):
        with assert_http_error(404):
            self.ks_api.kernel_resource('nonexistant', 'resource.txt')
        
        with assert_http_error(404):
            self.ks_api.kernel_resource('sample', 'nonexistant.txt')

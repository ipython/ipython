import json
import os
from os.path import join as pjoin
import unittest

from IPython.utils.tempdir import TemporaryDirectory
from IPython.kernel import kernelspec

sample_kernel_json = {'argv':['cat', '{connection_file}'],
                      'display_name':'Test kernel',
                      'language':'bash',
                     }

class KernelSpecTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = td = TemporaryDirectory()
        self.sample_kernel_dir = pjoin(td.name, 'kernels', 'Sample')
        os.makedirs(self.sample_kernel_dir)
        json_file = pjoin(self.sample_kernel_dir, 'kernel.json')
        with open(json_file, 'w') as f:
            json.dump(sample_kernel_json, f)

        self.ksm = kernelspec.KernelSpecManager(ipython_dir=td.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_find_kernel_specs(self):
        kernels = self.ksm.find_kernel_specs()
        self.assertEqual(kernels['sample'], self.sample_kernel_dir)

    def test_get_kernel_spec(self):
        ks = self.ksm.get_kernel_spec('SAMPLE')  # Case insensitive
        self.assertEqual(ks.resource_dir, self.sample_kernel_dir)
        self.assertEqual(ks.argv, sample_kernel_json['argv'])
        self.assertEqual(ks.display_name, sample_kernel_json['display_name'])
        self.assertEqual(ks.language, sample_kernel_json['language'])
        self.assertEqual(ks.codemirror_mode, sample_kernel_json['language'])
        self.assertEqual(ks.env, {})
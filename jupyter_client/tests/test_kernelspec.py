import json
import os
from os.path import join as pjoin
import unittest

from IPython.testing.decorators import onlyif
from IPython.utils.tempdir import TemporaryDirectory
from IPython.kernel import kernelspec

sample_kernel_json = {'argv':['cat', '{connection_file}'],
                      'display_name':'Test kernel',
                     }

class KernelSpecTests(unittest.TestCase):
    def setUp(self):
        td = TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.sample_kernel_dir = pjoin(td.name, 'kernels', 'Sample')
        os.makedirs(self.sample_kernel_dir)
        json_file = pjoin(self.sample_kernel_dir, 'kernel.json')
        with open(json_file, 'w') as f:
            json.dump(sample_kernel_json, f)

        self.ksm = kernelspec.KernelSpecManager(ipython_dir=td.name)
        
        td2 = TemporaryDirectory()
        self.addCleanup(td2.cleanup)
        self.installable_kernel = td2.name
        with open(pjoin(self.installable_kernel, 'kernel.json'), 'w') as f:
            json.dump(sample_kernel_json, f)

    def test_find_kernel_specs(self):
        kernels = self.ksm.find_kernel_specs()
        self.assertEqual(kernels['sample'], self.sample_kernel_dir)

    def test_get_kernel_spec(self):
        ks = self.ksm.get_kernel_spec('SAMPLE')  # Case insensitive
        self.assertEqual(ks.resource_dir, self.sample_kernel_dir)
        self.assertEqual(ks.argv, sample_kernel_json['argv'])
        self.assertEqual(ks.display_name, sample_kernel_json['display_name'])
        self.assertEqual(ks.env, {})
    
    def test_install_kernel_spec(self):
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     user=True)
        self.assertIn('tstinstalled', self.ksm.find_kernel_specs())
        
        with self.assertRaises(OSError):
            self.ksm.install_kernel_spec(self.installable_kernel,
                                         kernel_name='tstinstalled',
                                         user=True)
        
        # Smoketest that this succeeds
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     replace=True, user=True)

    @onlyif(os.name != 'nt' and not os.access('/usr/local/share', os.W_OK), "needs Unix system without root privileges")
    def test_cant_install_kernel_spec(self):
        with self.assertRaises(OSError):
            self.ksm.install_kernel_spec(self.installable_kernel,
                                         kernel_name='tstinstalled',
                                         user=False)

"""Tests for the notebook kernel and session manager."""

from unittest import TestCase

from IPython.frontend.html.notebook.kernelmanager import MultiKernelManager

class TestKernelManager(TestCase):

    def test_km_lifecycle(self):
        km = MultiKernelManager()
        kid = km.start_kernel()
        self.assertTrue(kid in km)
        self.assertEqual(len(km),1)
        km.kill_kernel(kid)
        self.assertTrue(not kid in km)

        kid = km.start_kernel()
        self.assertEqual('127.0.0.1',km.get_kernel_ip(kid))
        port_dict = km.get_kernel_ports(kid)
        self.assertTrue('stdin_port' in port_dict)
        self.assertTrue('iopub_port' in port_dict)
        self.assertTrue('shell_port' in port_dict)
        self.assertTrue('hb_port' in port_dict)
        km.get_kernel(kid)
        km.kill_kernel(kid)



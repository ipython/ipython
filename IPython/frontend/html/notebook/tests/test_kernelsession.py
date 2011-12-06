"""Tests for the notebook kernel and session manager."""

from unittest import TestCase

from IPython.frontend.html.notebook.kernelmanager import MultiKernelManager

class TestKernelManager(TestCase):

    def test_km_lifecycle(self):
        km = MultiKernelManager()
        kid = km.start_kernel()
        self.assert_(kid in km)
        self.assertEquals(len(km),1)
        km.kill_kernel(kid)
        self.assert_(not kid in km)

        kid = km.start_kernel()
        self.assertEquals('127.0.0.1',km.get_kernel_ip(kid))
        port_dict = km.get_kernel_ports(kid)
        self.assert_('stdin_port' in port_dict)
        self.assert_('iopub_port' in port_dict)
        self.assert_('shell_port' in port_dict)
        self.assert_('hb_port' in port_dict)
        km.get_kernel(kid)
        km.kill_kernel(kid)



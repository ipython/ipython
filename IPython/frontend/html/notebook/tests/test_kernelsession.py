"""Tests for the notebook kernel and session manager."""

from unittest import TestCase

from IPython.frontend.html.notebook.kernelmanager import MultiKernelManager

class TestKernelManager(TestCase):

    def test_km_lifecycle(self):
        km = MultiKernelManager()
        kid = km.start_kernel()
        self.assertTrue(kid in km)
        self.assertTrue(kid in km.list_kernel_ids())
        self.assertEqual(len(km),1)
        new_kid = km.restart_kernel(kid)
        self.assertTrue(kid, new_kid)
        km.interrupt_kernel(kid)
        km.kill_kernel(kid)
        self.assertTrue(not kid in km)

        kid = km.start_kernel()
        cdata = km.get_connection_data(kid)
        self.assertEqual('127.0.0.1', cdata['ip'])
        self.assertTrue('stdin_port' in cdata)
        self.assertTrue('iopub_port' in cdata)
        self.assertTrue('shell_port' in cdata)
        self.assertTrue('hb_port' in cdata)
        km.get_kernel(kid)
        km.kill_kernel(kid)



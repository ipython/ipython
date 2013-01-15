"""Tests for the notebook kernel and session manager."""

from unittest import TestCase

from IPython.config.loader import Config
from IPython.frontend.html.notebook.kernelmanager import MultiKernelManager
from IPython.zmq.kernelmanager import KernelManager

class TestKernelManager(TestCase):

    def _get_tcp_km(self):
        return MultiKernelManager()

    def _get_ipc_km(self):
        c = Config()
        c.KernelManager.transport = 'ipc'
        c.KernelManager.ip = 'test'
        km = MultiKernelManager(config=c)
        return km

    def _run_lifecycle(self, km):
        kid = km.start_kernel()
        self.assertTrue(kid in km)
        self.assertTrue(kid in km.list_kernel_ids())
        self.assertEqual(len(km),1)
        km.restart_kernel(kid)
        self.assertTrue(kid in km.list_kernel_ids())
        km.interrupt_kernel(kid)
        k = km.get_kernel(kid)
        self.assertTrue(isinstance(k, KernelManager))
        km.shutdown_kernel(kid)
        self.assertTrue(not kid in km)

    def test_km_tcp(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)

    def test_km_ipc(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)

    def test_tcp_cinfo(self):
        km = self._get_tcp_km()
        kid = km.start_kernel()
        k = km.get_kernel(kid)
        cinfo = km.get_connection_info(kid)
        self.assertEqual('tcp', cinfo['transport'])
        self.assertEqual('127.0.0.1', cinfo['ip'])
        self.assertTrue('stdin_port' in cinfo)
        self.assertTrue('iopub_port' in cinfo)
        self.assertTrue('shell_port' in cinfo)
        self.assertTrue('hb_port' in cinfo)
        km.shutdown_kernel(kid)

    def test_ipc_cinfo(self):
        km = self._get_ipc_km()
        kid = km.start_kernel()
        k = km.get_kernel(kid)
        cinfo = km.get_connection_info(kid)
        self.assertEqual('ipc', cinfo['transport'])
        self.assertEqual('test', cinfo['ip'])
        self.assertTrue('stdin_port' in cinfo)
        self.assertTrue('iopub_port' in cinfo)
        self.assertTrue('shell_port' in cinfo)
        self.assertTrue('hb_port' in cinfo)
        km.shutdown_kernel(kid)


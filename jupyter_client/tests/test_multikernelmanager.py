"""Tests for the notebook kernel and session manager."""

from subprocess import PIPE
import time
from unittest import TestCase

from IPython.testing import decorators as dec

from IPython.config.loader import Config
from IPython.utils.localinterfaces import localhost
from IPython.kernel import KernelManager
from IPython.kernel.multikernelmanager import MultiKernelManager

class TestKernelManager(TestCase):

    def _get_tcp_km(self):
        c = Config()
        km = MultiKernelManager(config=c)
        return km

    def _get_ipc_km(self):
        c = Config()
        c.KernelManager.transport = 'ipc'
        c.KernelManager.ip = 'test'
        km = MultiKernelManager(config=c)
        return km

    def _run_lifecycle(self, km):
        kid = km.start_kernel(stdout=PIPE, stderr=PIPE)
        self.assertTrue(km.is_alive(kid))
        self.assertTrue(kid in km)
        self.assertTrue(kid in km.list_kernel_ids())
        self.assertEqual(len(km),1)
        km.restart_kernel(kid, now=True)
        self.assertTrue(km.is_alive(kid))
        self.assertTrue(kid in km.list_kernel_ids())
        km.interrupt_kernel(kid)
        k = km.get_kernel(kid)
        self.assertTrue(isinstance(k, KernelManager))
        km.shutdown_kernel(kid, now=True)
        self.assertTrue(not kid in km)

    def _run_cinfo(self, km, transport, ip):
        kid = km.start_kernel(stdout=PIPE, stderr=PIPE)
        k = km.get_kernel(kid)
        cinfo = km.get_connection_info(kid)
        self.assertEqual(transport, cinfo['transport'])
        self.assertEqual(ip, cinfo['ip'])
        self.assertTrue('stdin_port' in cinfo)
        self.assertTrue('iopub_port' in cinfo)
        stream = km.connect_iopub(kid)
        stream.close()
        self.assertTrue('shell_port' in cinfo)
        stream = km.connect_shell(kid)
        stream.close()
        self.assertTrue('hb_port' in cinfo)
        stream = km.connect_hb(kid)
        stream.close()
        km.shutdown_kernel(kid, now=True)

    def test_tcp_lifecycle(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)
    
    def test_shutdown_all(self):
        km = self._get_tcp_km()
        kid = km.start_kernel(stdout=PIPE, stderr=PIPE)
        self.assertIn(kid, km)
        km.shutdown_all()
        self.assertNotIn(kid, km)
        # shutdown again is okay, because we have no kernels
        km.shutdown_all()
    
    def test_tcp_cinfo(self):
        km = self._get_tcp_km()
        self._run_cinfo(km, 'tcp', localhost())

    @dec.skip_win32
    def test_ipc_lifecycle(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)
    
    @dec.skip_win32
    def test_ipc_cinfo(self):
        km = self._get_ipc_km()
        self._run_cinfo(km, 'ipc', 'test')


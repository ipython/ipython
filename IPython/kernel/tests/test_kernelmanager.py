"""Tests for the notebook kernel and session manager"""

from subprocess import PIPE
import time
from unittest import TestCase

from IPython.testing import decorators as dec

from IPython.config.loader import Config
from IPython.kernel import KernelManager

class TestKernelManager(TestCase):

    def _get_tcp_km(self):
        c = Config()
        km = KernelManager(config=c)
        return km

    def _get_ipc_km(self):
        c = Config()
        c.KernelManager.transport = 'ipc'
        c.KernelManager.ip = 'test'
        km = KernelManager(config=c)
        return km

    def _run_lifecycle(self, km):
        km.start_kernel(stdout=PIPE, stderr=PIPE)
        self.assertTrue(km.is_alive())
        km.restart_kernel(now=True)
        self.assertTrue(km.is_alive())
        km.interrupt_kernel()
        self.assertTrue(isinstance(km, KernelManager))
        km.shutdown_kernel(now=True)

    def test_tcp_lifecycle(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)

    @dec.skip_win32
    def test_ipc_lifecycle(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)
    
    def test_get_connect_info(self):
        km = self._get_tcp_km()
        cinfo = km.get_connection_info()
        keys = sorted(cinfo.keys())
        expected = sorted([
            'ip', 'transport',
            'hb_port', 'shell_port', 'stdin_port', 'iopub_port', 'control_port',
            'key', 'signature_scheme',
        ])
        self.assertEqual(keys, expected)


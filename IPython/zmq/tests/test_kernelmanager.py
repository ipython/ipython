"""Tests for the notebook kernel and session manager."""

from unittest import TestCase

from IPython.config.loader import Config
from IPython.zmq.kernelmanager import KernelManager

class TestKernelManager(TestCase):

    def _get_tcp_km(self):
        return KernelManager()

    def _get_ipc_km(self):
        c = Config()
        c.KernelManager.transport = 'ipc'
        c.KernelManager.ip = 'test'
        km = KernelManager(config=c)
        return km

    def _run_lifecycle(self, km):
        km.start_kernel()
        km.start_channels(shell=True, iopub=False, stdin=False, hb=False)
        # km.shell_channel.start()
        km.restart_kernel()
        km.interrupt_kernel()
        self.assertTrue(isinstance(km, KernelManager))
        km.shutdown_kernel()
        km.shell_channel.stop()

    def test_km_tcp(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)

    def test_km_ipc(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)

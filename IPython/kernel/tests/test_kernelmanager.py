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
        # c.KernelManager.autorestart=False
        km = KernelManager(config=c)
        return km

    def _get_ipc_km(self):
        c = Config()
        c.KernelManager.transport = 'ipc'
        c.KernelManager.ip = 'test'
        # c.KernelManager.autorestart=False
        km = KernelManager(config=c)
        return km

    def _run_lifecycle(self, km):
        km.start_kernel(stdout=PIPE, stderr=PIPE)
        self.assertTrue(km.is_alive())
        km.restart_kernel()
        self.assertTrue(km.is_alive())
        # We need a delay here to give the restarting kernel a chance to
        # restart. Otherwise, the interrupt will kill it, causing the test
        # suite to hang. The reason it *hangs* is that the shutdown
        # message for the restart sometimes hasn't been sent to the kernel.
        # Because linger is oo on the shell channel, the context can't
        # close until the message is sent to the kernel, which is not dead.
        time.sleep(1.0)
        km.interrupt_kernel()
        self.assertTrue(isinstance(km, KernelManager))
        km.shutdown_kernel()

    def test_tcp_lifecycle(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)

    @dec.skip_win32
    def test_ipc_lifecycle(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)


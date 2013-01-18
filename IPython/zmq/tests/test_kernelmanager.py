"""Tests for the notebook kernel and session manager"""

from subprocess import PIPE
import time
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
        km.start_kernel(stdout=PIPE, stderr=PIPE)
        km.start_channels(shell=True, iopub=False, stdin=False, hb=False)
        km.restart_kernel()
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
        km.shell_channel.stop()

    def test_tcp_lifecycle(self):
        km = self._get_tcp_km()
        self._run_lifecycle(km)

    def testipc_lifecycle(self):
        km = self._get_ipc_km()
        self._run_lifecycle(km)


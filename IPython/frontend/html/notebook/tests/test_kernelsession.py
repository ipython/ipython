
from unittest import TestCase

from IPython.frontend.html.notebook.kernelmanager import KernelManager
from IPython.frontend.html.notebook.sessionmanager import SessionManagerRunningError

class TestKernelManager(TestCase):

    def test_km_lifecycle(self):
        km = KernelManager()
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
        km.get_kernel_process(kid)

    def test_session_manager(self):
        km = KernelManager()
        kid = km.start_kernel()
        sm = km.create_session_manager(kid)
        self.assert_(sm._running)
        sm.stop()
        self.assert_(not sm._running)
        sm.start()
        self.assertRaises(SessionManagerRunningError, sm.start)
        sm.get_iopub_stream()
        sm.get_shell_stream()
        sm.session


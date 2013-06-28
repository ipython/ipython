""" Defines a KernelClient that provides signals and slots.
"""

from IPython.external.qt import QtCore

# Local imports
from IPython.utils.traitlets import Bool, Instance

from IPython.kernel import KernelManager
from IPython.kernel.restarter import KernelRestarter

from .kernel_mixins import QtKernelManagerMixin, QtKernelRestarterMixin


class QtKernelRestarter(KernelRestarter, QtKernelRestarterMixin):

    def start(self):
        if self._timer is None:
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self.poll)
        self._timer.start(self.time_to_dead * 1000)

    def stop(self):
        self._timer.stop()

    def poll(self):
        super(QtKernelRestarter, self).poll()


class QtKernelManager(KernelManager, QtKernelManagerMixin):
    """A KernelManager with Qt signals for restart"""

    autorestart = Bool(True, config=True)

    def start_restarter(self):
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = QtKernelRestarter(
                    kernel_manager=self,
                    config=self.config,
                    log=self.log,
                )
                self._restarter.add_callback(self._handle_kernel_restarted)
            self._restarter.start()

    def stop_restarter(self):
        if self.autorestart:
            if self._restarter is not None:
                self._restarter.stop()

    def _handle_kernel_restarted(self):
        self.kernel_restarted.emit()

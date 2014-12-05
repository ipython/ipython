""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.external.qt import QtCore
from IPython.kernel.inprocess import (
    InProcessHBChannel, InProcessKernelClient, InProcessKernelManager,
)
from IPython.kernel.inprocess.channels import InProcessChannel

from IPython.utils.traitlets import Type
from .util import SuperQObject
from .kernel_mixins import (
    QtKernelClientMixin, QtKernelManagerMixin,
)

class QtInProcessChannel(SuperQObject, InProcessChannel):
    # Emitted when the channel is started.
    started = QtCore.Signal()

    # Emitted when the channel is stopped.
    stopped = QtCore.Signal()

    # Emitted when any message is received.
    message_received = QtCore.Signal(object)

    def start(self):
        """ Reimplemented to emit signal.
        """
        super(QtInProcessChannel, self).start()
        self.started.emit()

    def stop(self):
        """ Reimplemented to emit signal.
        """
        super(QtInProcessChannel, self).stop()
        self.stopped.emit()

    def call_handlers_later(self, *args, **kwds):
        """ Call the message handlers later.
        """
        do_later = lambda: self.call_handlers(*args, **kwds)
        QtCore.QTimer.singleShot(0, do_later)

    def call_handlers(self, msg):
        self.message_received.emit(msg)

    def process_events(self):
        """ Process any pending GUI events.
        """
        QtCore.QCoreApplication.instance().processEvents()

    def flush(self, timeout=1.0):
        """ Reimplemented to ensure that signals are dispatched immediately.
        """
        super(QtInProcessChannel, self).flush()
        self.process_events()


class QtInProcessHBChannel(SuperQObject, InProcessHBChannel):
    # This signal will never be fired, but it needs to exist
    kernel_died = QtCore.Signal()


class QtInProcessKernelClient(QtKernelClientMixin, InProcessKernelClient):
    """ An in-process KernelManager with signals and slots.
    """

    iopub_channel_class = Type(QtInProcessChannel)
    shell_channel_class = Type(QtInProcessChannel)
    stdin_channel_class = Type(QtInProcessChannel)
    hb_channel_class = Type(QtInProcessHBChannel)

class QtInProcessKernelManager(QtKernelManagerMixin, InProcessKernelManager):
    client_class = __module__ + '.QtInProcessKernelClient'

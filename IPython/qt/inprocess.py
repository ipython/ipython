""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.external.qt import QtCore
from IPython.kernel.inprocess import (
    InProcessShellChannel, InProcessIOPubChannel, InProcessStdInChannel,
    InProcessHBChannel, InProcessKernelClient, InProcessKernelManager,
)

from IPython.utils.traitlets import Type
from .kernel_mixins import ( ChannelQObject,
    QtHBChannelMixin, QtKernelClientMixin,
    QtKernelManagerMixin,
)


class QtInProcessShellChannel(ChannelQObject, InProcessShellChannel):
    # Emitted when a reply has been received for the corresponding request type.
    execute_reply = QtCore.Signal(object)
    complete_reply = QtCore.Signal(object)
    inspect_reply = QtCore.Signal(object)
    history_reply = QtCore.Signal(object)
    kernel_info_reply = QtCore.Signal(object)

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        if msg_type == 'kernel_info_reply':
            self._handle_kernel_info_reply(msg)

        signal = getattr(self, msg_type, None)
        if signal:
            signal.emit(msg)

class QtInProcessIOPubChannel(ChannelQObject, InProcessIOPubChannel):
    # Emitted when a message of type 'stream' is received.
    stream_received = QtCore.Signal(object)

    # Emitted when a message of type 'execute_input' is received.
    execute_input_received = QtCore.Signal(object)

    # Emitted when a message of type 'execute_result' is received.
    execute_result_received = QtCore.Signal(object)

    # Emitted when a message of type 'error' is received.
    error_received = QtCore.Signal(object)

    # Emitted when a message of type 'display_data' is received
    display_data_received = QtCore.Signal(object)

    # Emitted when a crash report message is received from the kernel's
    # last-resort sys.excepthook.
    crash_received = QtCore.Signal(object)

    # Emitted when a shutdown is noticed.
    shutdown_reply_received = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # 'IOPubChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)
        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        signal = getattr(self, msg_type + '_received', None)
        if signal:
            signal.emit(msg)
        elif msg_type in ('stdout', 'stderr'):
            self.stream_received.emit(msg)

    def flush(self):
        """ Reimplemented to ensure that signals are dispatched immediately.
        """
        super(QtInProcessIOPubChannel, self).flush()
        QtCore.QCoreApplication.instance().processEvents()

class QtInProcessStdInChannel(ChannelQObject, InProcessStdInChannel):
    # Emitted when an input request is received.
    input_requested = QtCore.Signal(object)

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        if msg_type == 'input_request':
            self.input_requested.emit(msg)

class QtInProcessHBChannel(QtHBChannelMixin, InProcessHBChannel):
    pass

class QtInProcessKernelClient(QtKernelClientMixin, InProcessKernelClient):
    """ An in-process KernelManager with signals and slots.
    """

    iopub_channel_class = Type(QtInProcessIOPubChannel)
    shell_channel_class = Type(QtInProcessShellChannel)
    stdin_channel_class = Type(QtInProcessStdInChannel)
    hb_channel_class = Type(QtInProcessHBChannel)

class QtInProcessKernelManager(QtKernelManagerMixin, InProcessKernelManager):
    client_class = __module__ + '.QtInProcessKernelClient'

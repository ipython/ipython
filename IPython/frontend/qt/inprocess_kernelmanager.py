""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.inprocess.kernelmanager import \
    InProcessShellChannel, InProcessIOPubChannel, InProcessStdInChannel, \
    InProcessHBChannel, InProcessKernelManager
from IPython.utils.traitlets import Type
from base_kernelmanager import QtShellChannelMixin, QtIOPubChannelMixin, \
    QtStdInChannelMixin, QtHBChannelMixin, QtKernelManagerMixin


class QtInProcessShellChannel(QtShellChannelMixin, InProcessShellChannel):
    pass

class QtInProcessIOPubChannel(QtIOPubChannelMixin, InProcessIOPubChannel):
    pass

class QtInProcessStdInChannel(QtStdInChannelMixin, InProcessStdInChannel):
    pass

class QtInProcessHBChannel(QtHBChannelMixin, InProcessHBChannel):
    pass


class QtInProcessKernelManager(QtKernelManagerMixin, InProcessKernelManager):
    """ An in-process KernelManager with signals and slots.
    """

    iopub_channel_class = Type(QtInProcessIOPubChannel)
    shell_channel_class = Type(QtInProcessShellChannel)
    stdin_channel_class = Type(QtInProcessStdInChannel)
    hb_channel_class = Type(QtInProcessHBChannel)

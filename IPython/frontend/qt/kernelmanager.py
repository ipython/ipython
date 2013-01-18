""" Defines a KernelManager that provides signals and slots.
"""

# Local imports.
from IPython.utils.traitlets import Type
from IPython.zmq.kernelmanager import ShellChannel, IOPubChannel, \
    StdInChannel, HBChannel, KernelManager
from base_kernelmanager import QtShellChannelMixin, QtIOPubChannelMixin, \
    QtStdInChannelMixin, QtHBChannelMixin, QtKernelManagerMixin


class QtShellChannel(QtShellChannelMixin, ShellChannel):
    pass

class QtIOPubChannel(QtIOPubChannelMixin, IOPubChannel):
    pass

class QtStdInChannel(QtStdInChannelMixin, StdInChannel):
    pass

class QtHBChannel(QtHBChannelMixin, HBChannel):
    pass


class QtKernelManager(QtKernelManagerMixin, KernelManager):
    """ A KernelManager that provides signals and slots.
    """

    iopub_channel_class = Type(QtIOPubChannel)
    shell_channel_class = Type(QtShellChannel)
    stdin_channel_class = Type(QtStdInChannel)
    hb_channel_class = Type(QtHBChannel)

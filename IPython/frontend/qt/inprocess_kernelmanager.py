""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.inprocess.kernelmanager import \
    ShellInProcessChannel, SubInProcessChannel, StdInInProcessChannel, \
    HBInProcessChannel, InProcessKernelManager
from IPython.utils.traitlets import Type
from base_kernelmanager import QtShellChannelMixin, QtSubChannelMixin, \
    QtStdInChannelMixin, QtHBChannelMixin, QtKernelManagerMixin


class QtShellInProcessChannel(QtShellChannelMixin, ShellInProcessChannel):
    pass

class QtSubInProcessChannel(QtSubChannelMixin, SubInProcessChannel):
    pass

class QtStdInInProcessChannel(QtStdInChannelMixin, StdInInProcessChannel):
    pass

class QtHBInProcessChannel(QtHBChannelMixin, HBInProcessChannel):
    pass


class QtInProcessKernelManager(QtKernelManagerMixin, InProcessKernelManager):
    """ An in-process KernelManager with signals and slots.
    """

    sub_channel_class = Type(QtSubInProcessChannel)
    shell_channel_class = Type(QtShellInProcessChannel)
    stdin_channel_class = Type(QtStdInInProcessChannel)
    hb_channel_class = Type(QtHBInProcessChannel)

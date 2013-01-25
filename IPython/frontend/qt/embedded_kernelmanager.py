""" Defines an embedded KernelManager that provides signals and slots.
"""

# Local imports.
from IPython.embedded.kernelmanager import \
    ShellEmbeddedChannel, SubEmbeddedChannel, StdInEmbeddedChannel, \
    HBEmbeddedChannel, EmbeddedKernelManager
from IPython.utils.traitlets import Type
from base_kernelmanager import QtShellChannelMixin, QtSubChannelMixin, \
    QtStdInChannelMixin, QtHBChannelMixin, QtKernelManagerMixin


class QtShellEmbeddedChannel(QtShellChannelMixin, ShellEmbeddedChannel):
    pass

class QtSubEmbeddedChannel(QtSubChannelMixin, SubEmbeddedChannel):
    pass

class QtStdInEmbeddedChannel(QtStdInChannelMixin, StdInEmbeddedChannel):
    pass

class QtHBEmbeddedChannel(QtHBChannelMixin, HBEmbeddedChannel):
    pass


class QtEmbeddedKernelManager(QtKernelManagerMixin, EmbeddedKernelManager):
    """ An embedded KernelManager that provides signals and slots.
    """

    sub_channel_class = Type(QtSubEmbeddedChannel)
    shell_channel_class = Type(QtShellEmbeddedChannel)
    stdin_channel_class = Type(QtStdInEmbeddedChannel)
    hb_channel_class = Type(QtHBEmbeddedChannel)

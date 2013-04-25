""" Defines a KernelClient that provides signals and slots.
"""

# Local imports
from IPython.utils.traitlets import Type
from IPython.kernel.channels import (
    ShellChannel, IOPubChannel, StdInChannel, HBChannel
)
from IPython.kernel import KernelClient

from .kernel_mixins import (
    QtShellChannelMixin, QtIOPubChannelMixin,
    QtStdInChannelMixin, QtHBChannelMixin,
    QtKernelClientMixin
)

class QtShellChannel(QtShellChannelMixin, ShellChannel):
    pass

class QtIOPubChannel(QtIOPubChannelMixin, IOPubChannel):
    pass

class QtStdInChannel(QtStdInChannelMixin, StdInChannel):
    pass

class QtHBChannel(QtHBChannelMixin, HBChannel):
    pass


class QtKernelClient(QtKernelClientMixin, KernelClient):
    """ A KernelClient that provides signals and slots.
    """

    iopub_channel_class = Type(QtIOPubChannel)
    shell_channel_class = Type(QtShellChannel)
    stdin_channel_class = Type(QtStdInChannel)
    hb_channel_class = Type(QtHBChannel)

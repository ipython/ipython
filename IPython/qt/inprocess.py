""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.kernel.inprocess import (
    InProcessShellChannel, InProcessIOPubChannel, InProcessStdInChannel,
    InProcessHBChannel, InProcessKernelClient, InProcessKernelManager,
)

from IPython.utils.traitlets import Type
from .kernel_mixins import (
    QtShellChannelMixin, QtIOPubChannelMixin,
    QtStdInChannelMixin, QtHBChannelMixin, QtKernelClientMixin,
    QtKernelManagerMixin,
)


class QtInProcessShellChannel(QtShellChannelMixin, InProcessShellChannel):
    pass

class QtInProcessIOPubChannel(QtIOPubChannelMixin, InProcessIOPubChannel):
    pass

class QtInProcessStdInChannel(QtStdInChannelMixin, InProcessStdInChannel):
    pass

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

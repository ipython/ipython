""" Defines an in-process KernelManager with signals and slots.
"""

# Local imports.
from IPython.external.qt import QtCore
from IPython.kernel.inprocess import (
    InProcessHBChannel, InProcessKernelClient, InProcessKernelManager,
)
from IPython.kernel.inprocess.channels import InProcessChannel

from IPython.utils.traitlets import Type
from .kernel_mixins import ( ChannelQObject,
    QtHBChannelMixin, QtKernelClientMixin,
    QtKernelManagerMixin,
)

class QtInProcessChannel(ChannelQObject, InProcessChannel):
    pass

class QtInProcessHBChannel(QtHBChannelMixin, InProcessHBChannel):
    pass

class QtInProcessKernelClient(QtKernelClientMixin, InProcessKernelClient):
    """ An in-process KernelManager with signals and slots.
    """

    iopub_channel_class = Type(QtInProcessChannel)
    shell_channel_class = Type(QtInProcessChannel)
    stdin_channel_class = Type(QtInProcessChannel)
    hb_channel_class = Type(QtInProcessHBChannel)

class QtInProcessKernelManager(QtKernelManagerMixin, InProcessKernelManager):
    client_class = __module__ + '.QtInProcessKernelClient'

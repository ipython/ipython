"""Defines a KernelManager that provides signals and slots."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.external.qt import QtCore

from IPython.utils.traitlets import HasTraits, Type
from .util import MetaQObjectHasTraits, SuperQObject


class QtKernelRestarterMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):

    _timer = None


class QtKernelManagerMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):
    """ A KernelClient that provides signals and slots.
    """

    kernel_restarted = QtCore.Signal()


class QtKernelClientMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):
    """ A KernelClient that provides signals and slots.
    """

    # Emitted when the kernel client has started listening.
    started_channels = QtCore.Signal()

    # Emitted when the kernel client has stopped listening.
    stopped_channels = QtCore.Signal()

    #---------------------------------------------------------------------------
    # 'KernelClient' interface
    #---------------------------------------------------------------------------

    #------ Channel management -------------------------------------------------

    def start_channels(self, *args, **kw):
        """ Reimplemented to emit signal.
        """
        super(QtKernelClientMixin, self).start_channels(*args, **kw)
        self.started_channels.emit()

    def stop_channels(self):
        """ Reimplemented to emit signal.
        """
        super(QtKernelClientMixin, self).stop_channels()
        self.stopped_channels.emit()

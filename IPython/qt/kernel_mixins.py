"""Defines a KernelManager that provides signals and slots."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.external.qt import QtCore

from IPython.utils.traitlets import HasTraits, Type
from .util import MetaQObjectHasTraits, SuperQObject


class ChannelQObject(SuperQObject):

    # Emitted when the channel is started.
    started = QtCore.Signal()

    # Emitted when the channel is stopped.
    stopped = QtCore.Signal()

    # Emitted when any message is received.
    message_received = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # Channel interface
    #---------------------------------------------------------------------------

    def start(self):
        """ Reimplemented to emit signal.
        """
        super(ChannelQObject, self).start()
        self.started.emit()

    def stop(self):
        """ Reimplemented to emit signal.
        """
        super(ChannelQObject, self).stop()
        self.stopped.emit()

    #---------------------------------------------------------------------------
    # InProcessChannel interface
    #---------------------------------------------------------------------------

    def call_handlers_later(self, *args, **kwds):
        """ Call the message handlers later.
        """
        do_later = lambda: self.call_handlers(*args, **kwds)
        QtCore.QTimer.singleShot(0, do_later)

    def process_events(self):
        """ Process any pending GUI events.
        """
        QtCore.QCoreApplication.instance().processEvents()


class QtHBChannelMixin(ChannelQObject):

    # Emitted when the kernel has died.
    kernel_died = QtCore.Signal(object)

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        self.kernel_died.emit(since_last_heartbeat)


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

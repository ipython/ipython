""" Defines a KernelManager that provides signals and slots.
"""

# System library imports.
from IPython.external.qt import QtCore

# IPython imports.
from IPython.utils.traitlets import HasTraits, Type
from util import MetaQObjectHasTraits, SuperQObject


class ChannelQObject(SuperQObject):

    # Emitted when the channel is started.
    started = QtCore.Signal()

    # Emitted when the channel is stopped.
    stopped = QtCore.Signal()

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


class QtShellChannelMixin(ChannelQObject):

    # Emitted when any message is received.
    message_received = QtCore.Signal(object)

    # Emitted when a reply has been received for the corresponding request type.
    execute_reply = QtCore.Signal(object)
    complete_reply = QtCore.Signal(object)
    object_info_reply = QtCore.Signal(object)
    history_reply = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # 'ShellChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        signal = getattr(self, msg_type, None)
        if signal:
            signal.emit(msg)


class QtIOPubChannelMixin(ChannelQObject):

    # Emitted when any message is received.
    message_received = QtCore.Signal(object)

    # Emitted when a message of type 'stream' is received.
    stream_received = QtCore.Signal(object)

    # Emitted when a message of type 'pyin' is received.
    pyin_received = QtCore.Signal(object)

    # Emitted when a message of type 'pyout' is received.
    pyout_received = QtCore.Signal(object)

    # Emitted when a message of type 'pyerr' is received.
    pyerr_received = QtCore.Signal(object)

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
        super(QtIOPubChannelMixin, self).flush()
        QtCore.QCoreApplication.instance().processEvents()


class QtStdInChannelMixin(ChannelQObject):

    # Emitted when any message is received.
    message_received = QtCore.Signal(object)

    # Emitted when an input request is received.
    input_requested = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # 'StdInChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)

        # Emit signals for specialized message types.
        msg_type = msg['header']['msg_type']
        if msg_type == 'input_request':
            self.input_requested.emit(msg)


class QtHBChannelMixin(ChannelQObject):

    # Emitted when the kernel has died.
    kernel_died = QtCore.Signal(object)

    #---------------------------------------------------------------------------
    # 'HBChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.kernel_died.emit(since_last_heartbeat)


class QtKernelRestarterMixin(HasTraits, SuperQObject):

    __metaclass__ = MetaQObjectHasTraits
    _timer = None


class QtKernelManagerMixin(HasTraits, SuperQObject):
    """ A KernelClient that provides signals and slots.
    """

    __metaclass__ = MetaQObjectHasTraits

    kernel_restarted = QtCore.Signal()


class QtKernelClientMixin(HasTraits, SuperQObject):
    """ A KernelClient that provides signals and slots.
    """

    __metaclass__ = MetaQObjectHasTraits

    # Emitted when the kernel client has started listening.
    started_channels = QtCore.Signal()

    # Emitted when the kernel client has stopped listening.
    stopped_channels = QtCore.Signal()

    # Use Qt-specific channel classes that emit signals.
    iopub_channel_class = Type(QtIOPubChannelMixin)
    shell_channel_class = Type(QtShellChannelMixin)
    stdin_channel_class = Type(QtStdInChannelMixin)
    hb_channel_class = Type(QtHBChannelMixin)

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

""" Defines a KernelManager that provides signals and slots.
"""

# System library imports.
from PyQt4 import QtCore

# IPython imports.
from IPython.utils.traitlets import Type
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel, HBSocketChannel
from util import MetaQObjectHasTraits, SuperQObject


class SocketChannelQObject(SuperQObject):

    # Emitted when the channel is started.
    started = QtCore.pyqtSignal()

    # Emitted when the channel is stopped.
    stopped = QtCore.pyqtSignal()

    #---------------------------------------------------------------------------
    # 'ZmqSocketChannel' interface
    #---------------------------------------------------------------------------

    def start(self):
        """ Reimplemented to emit signal.
        """
        super(SocketChannelQObject, self).start()
        self.started.emit()

    def stop(self):
        """ Reimplemented to emit signal.
        """
        super(SocketChannelQObject, self).stop()
        self.stopped.emit()


class QtXReqSocketChannel(SocketChannelQObject, XReqSocketChannel):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(object)

    # Emitted when a reply has been received for the corresponding request
    # type.
    execute_reply = QtCore.pyqtSignal(object)
    complete_reply = QtCore.pyqtSignal(object)
    object_info_reply = QtCore.pyqtSignal(object)

    # Emitted when the first reply comes back.
    first_reply = QtCore.pyqtSignal()

    # Used by the first_reply signal logic to determine if a reply is the 
    # first.
    _handlers_called = False

    #---------------------------------------------------------------------------
    # 'XReqSocketChannel' interface
    #---------------------------------------------------------------------------
    
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)
        
        # Emit signals for specialized message types.
        msg_type = msg['msg_type']
        signal = getattr(self, msg_type, None)
        if signal:
            signal.emit(msg)

        if not self._handlers_called:
            self.first_reply.emit()
            self._handlers_called = True

    #---------------------------------------------------------------------------
    # 'QtXReqSocketChannel' interface
    #---------------------------------------------------------------------------

    def reset_first_reply(self):
        """ Reset the first_reply signal to fire again on the next reply.
        """
        self._handlers_called = False


class QtSubSocketChannel(SocketChannelQObject, SubSocketChannel):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'stream' is received.
    stream_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'pyin' is received.
    pyin_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'pyout' is received.
    pyout_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'pyerr' is received.
    pyerr_received = QtCore.pyqtSignal(object)

    # Emitted when a crash report message is received from the kernel's
    # last-resort sys.excepthook.
    crash_received = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'SubSocketChannel' interface
    #---------------------------------------------------------------------------
    
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)
        
        # Emit signals for specialized message types.
        msg_type = msg['msg_type']
        signal = getattr(self, msg_type + '_received', None)
        if signal:
            signal.emit(msg)
        elif msg_type in ('stdout', 'stderr'):
            self.stream_received.emit(msg)

    def flush(self):
        """ Reimplemented to ensure that signals are dispatched immediately.
        """
        super(QtSubSocketChannel, self).flush()
        QtCore.QCoreApplication.instance().processEvents()


class QtRepSocketChannel(SocketChannelQObject, RepSocketChannel):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(object)

    # Emitted when an input request is received.
    input_requested = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'RepSocketChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)
        
        # Emit signals for specialized message types.
        msg_type = msg['msg_type']
        if msg_type == 'input_request':
            self.input_requested.emit(msg)


class QtHBSocketChannel(SocketChannelQObject, HBSocketChannel):

    # Emitted when the kernel has died.
    kernel_died = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'HBSocketChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.kernel_died.emit(since_last_heartbeat)


class QtKernelManager(KernelManager, SuperQObject):
    """ A KernelManager that provides signals and slots.
    """

    __metaclass__ = MetaQObjectHasTraits

    # Emitted when the kernel manager has started listening.
    started_channels = QtCore.pyqtSignal()

    # Emitted when the kernel manager has stopped listening.
    stopped_channels = QtCore.pyqtSignal()

    # Use Qt-specific channel classes that emit signals.
    sub_channel_class = Type(QtSubSocketChannel)
    xreq_channel_class = Type(QtXReqSocketChannel)
    rep_channel_class = Type(QtRepSocketChannel)
    hb_channel_class = Type(QtHBSocketChannel)

    #---------------------------------------------------------------------------
    # 'KernelManager' interface
    #---------------------------------------------------------------------------

    #------ Kernel process management ------------------------------------------

    def start_kernel(self, *args, **kw):
        """ Reimplemented for proper heartbeat management.
        """
        if self._xreq_channel is not None:
            self._xreq_channel.reset_first_reply()
        super(QtKernelManager, self).start_kernel(*args, **kw)

    #------ Channel management -------------------------------------------------
    
    def start_channels(self, *args, **kw):
        """ Reimplemented to emit signal.
        """
        super(QtKernelManager, self).start_channels(*args, **kw)
        self.started_channels.emit()

    def stop_channels(self):
        """ Reimplemented to emit signal.
        """ 
        super(QtKernelManager, self).stop_channels()
        self.stopped_channels.emit()

    @property
    def xreq_channel(self):
        """ Reimplemented for proper heartbeat management.
        """
        if self._xreq_channel is None:
            self._xreq_channel = super(QtKernelManager, self).xreq_channel
            self._xreq_channel.first_reply.connect(self._first_reply)
        return self._xreq_channel

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------
    
    def _first_reply(self):
        """ Unpauses the heartbeat channel when the first reply is received on
            the execute channel. Note that this will *not* start the heartbeat
            channel if it is not already running!
        """
        if self._hb_channel is not None:
            self._hb_channel.unpause()

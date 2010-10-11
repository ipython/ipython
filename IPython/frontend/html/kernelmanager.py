""" Defines a KernelManager that provides signals and slots.
"""
# IPython imports.
from IPython.utils.traitlets import Type
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel, HBSocketChannel
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class HttpXReqSocketChannel(XReqSocketChannel):
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
    # 'HttpXReqSocketChannel' interface
    #---------------------------------------------------------------------------

    def reset_first_reply(self):
        """ Reset the first_reply signal to fire again on the next reply.
        """
        self._handlers_called = False


class HttpSubSocketChannel(SocketChannelQObject, SubSocketChannel):

    #---------------------------------------------------------------------------
    # 'SubSocketChannel' interface
    #---------------------------------------------------------------------------
    
    def call_handlers(self, msg):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        
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
        super(HttpSubSocketChannel, self).flush()


class HttpRepSocketChannel(SocketChannelQObject, RepSocketChannel):

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


class HttpHBSocketChannel(SocketChannelQObject, HBSocketChannel):
    #---------------------------------------------------------------------------
    # 'HBSocketChannel' interface
    #---------------------------------------------------------------------------

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.kernel_died.emit(since_last_heartbeat)


class HttpKernelManager(KernelManager, SuperQObject):
    """ A KernelManager that provides signals and slots.
    """

    # Use Http-specific channel classes that emit signals.
    sub_channel_class = Type(HttpSubSocketChannel)
    xreq_channel_class = Type(HttpXReqSocketChannel)
    rep_channel_class = Type(HttpRepSocketChannel)
    hb_channel_class = Type(HttpHBSocketChannel)

    #---------------------------------------------------------------------------
    # 'KernelManager' interface
    #---------------------------------------------------------------------------

    #------ Kernel process management ------------------------------------------

    def start_kernel(self, *args, **kw):
        """ Reimplemented for proper heartbeat management.
        """
        if self._xreq_channel is not None:
            self._xreq_channel.reset_first_reply()
        super(HttpKernelManager, self).start_kernel(*args, **kw)

    @property
    def xreq_channel(self):
        """ Reimplemented for proper heartbeat management.
        """
        if self._xreq_channel is None:
            self._xreq_channel = super(HttpKernelManager, self).xreq_channel
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

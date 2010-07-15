""" A KernelManager that provides channels that use signals and slots.
"""

# System library imports.
from PyQt4 import QtCore

# IPython imports.
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel


class QtSubSocketChannel(SubSocketChannel, QtCore.QObject):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'pyout' or 'stdout' is received.
    output_received = QtCore.pyqtSignal(object)

    # Emitted when a message of type 'pyerr' or 'stderr' is received.
    error_received = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        """ Reimplemented to ensure that QtCore.QObject is initialized first.
        """
        QtCore.QObject.__init__(self)
        SubSocketChannel.__init__(self, *args, **kw)

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
        if msg_type in ('pyout', 'stdout'):
            self.output_received.emit(msg)
        elif msg_type in ('pyerr', 'stderr'):
            self.error_received.emit(msg)

    def flush(self):
        """ Reimplemented to ensure that signals are dispatched immediately.
        """
        super(QtSubSocketChannel, self).flush()
        QtCore.QCoreApplication.instance().processEvents()


class QtXReqSocketChannel(XReqSocketChannel, QtCore.QObject):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(object)

    # Emitted when a reply has been received for the corresponding request type.
    execute_reply = QtCore.pyqtSignal(object)
    complete_reply = QtCore.pyqtSignal(object)
    object_info_reply = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        """ Reimplemented to ensure that QtCore.QObject is initialized first.
        """
        QtCore.QObject.__init__(self)
        XReqSocketChannel.__init__(self, *args, **kw)
    
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

    def _queue_request(self, msg, callback):
        """ Reimplemented to skip callback handling.
        """
        self.command_queue.put(msg)


class QtRepSocketChannel(RepSocketChannel, QtCore.QObject):

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        """ Reimplemented to ensure that QtCore.QObject is initialized first.
        """
        QtCore.QObject.__init__(self)
        RepSocketChannel.__init__(self, *args, **kw)


class QtKernelManager(KernelManager):
    """ A KernelManager that provides channels that use signals and slots.
    """

    sub_channel_class = QtSubSocketChannel
    xreq_channel_class = QtXReqSocketChannel
    rep_channel_class = QtRepSocketChannel

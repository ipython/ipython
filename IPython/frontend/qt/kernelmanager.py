""" A KernelManager that provides channels that use signals and slots.
"""

# System library imports.
from PyQt4 import QtCore

# IPython imports.
from IPython.zmq.kernel_manager import KernelManager, SubSocketChannel, \
    XReqSocketChannel, RepSocketChannel


class QtKernelManager(KernelManager):
    """ A KernelManager that provides channels that use signals and slots.
    """

    sub_channel_class = QtSubSocketChannel
    xreq_channel_class = QtXReqSocketChannel
    rep_channel_class = QtRepSocketChannel


class QtSubSocketChannel(SubSocketChannel, QtCore.QObject):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(dict)

    # Emitted when a message of type 'pyout' or 'stdout' is received.
    output_received = QtCore.pyqtSignal(dict)

    # Emitted when a message of type 'pyerr' or 'stderr' is received.
    error_received = QtCore.pyqtSignal(dict)

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


class QtXReqSocketChannel(XReqSocketChannel, QtCore.QObject):

    # Emitted when any message is received.
    message_received = QtCore.pyqtSignal(dict)

    # Emitted when a reply has been received for the corresponding request type.
    execute_reply = QtCore.pyqtSignal(dict)
    complete_reply = QtCore.pyqtSignal(dict)
    object_info_reply = QtCore.pyqtSignal(dict)
    
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


class QtRepSocketChannel(RepSocketChannel, QtCore.QObject):

    pass

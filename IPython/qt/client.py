""" Defines a KernelClient that provides signals and slots.
"""
import atexit
import errno
from threading import Thread
import time

import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

from IPython.external.qt import QtCore

# Local imports
from IPython.utils.traitlets import Type, Instance
from IPython.kernel.channels import HBChannel
from IPython.kernel import KernelClient
from IPython.kernel.channels import InvalidPortNumber
from IPython.kernel.threaded import ThreadedKernelClient, ThreadedZMQSocketChannel

from .kernel_mixins import QtKernelClientMixin
from .util import SuperQObject

class QtHBChannel(SuperQObject, HBChannel):
    # A longer timeout than the base class
    time_to_dead = 3.0

    # Emitted when the kernel has died.
    kernel_died = QtCore.Signal(object)

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.kernel_died.emit(since_last_heartbeat)

from IPython.core.release import kernel_protocol_version_info

major_protocol_version = kernel_protocol_version_info[0]

class QtZMQSocketChannel(ThreadedZMQSocketChannel,SuperQObject):
    """A ZMQ socket emitting a Qt signal when a message is received."""
    message_received = QtCore.Signal(object)

    def process_events(self):
        """ Process any pending GUI events.
        """
        QtCore.QCoreApplication.instance().processEvents()


    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)


class QtKernelClient(QtKernelClientMixin, ThreadedKernelClient):
    """ A KernelClient that provides signals and slots.
    """

    iopub_channel_class = Type(QtZMQSocketChannel)
    shell_channel_class = Type(QtZMQSocketChannel)
    stdin_channel_class = Type(QtZMQSocketChannel)
    hb_channel_class = Type(QtHBChannel)

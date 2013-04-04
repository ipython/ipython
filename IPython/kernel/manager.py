"""Base class to manage a running kernel
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import

# Standard library imports
import signal
import sys
import time

import zmq

# Local imports
from IPython.config.configurable import LoggingConfigurable
from IPython.utils.importstring import import_item
from IPython.utils.localinterfaces import LOCAL_IPS
from IPython.utils.traitlets import (
    Any, Instance, Unicode, List, Bool, Type, DottedObjectName
)
from IPython.kernel import (
    make_ipkernel_cmd,
    launch_kernel,
)
from .connect import ConnectionFileMixin
from .zmq.session import Session
from .managerabc import (
    KernelManagerABC
)

#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

_socket_types = {
    'hb' : zmq.REQ,
    'shell' : zmq.DEALER,
    'iopub' : zmq.SUB,
    'stdin' : zmq.DEALER,
    'control': zmq.DEALER,
}

class KernelManager(LoggingConfigurable, ConnectionFileMixin):
    """Manages a single kernel in a subprocess on this host.

    This version starts kernels with Popen.
    """

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context)
    def _context_default(self):
        return zmq.Context.instance()

    # The Session to use for communication with the kernel.
    session = Instance(Session)
    def _session_default(self):
        return Session(config=self.config)

    # the class to create with our `client` method
    client_class = DottedObjectName('IPython.kernel.client.KernelClient')
    client_factory = Type()
    def _client_class_changed(self, name, old, new):
        self.client_factory = import_item(str(new))

    # The kernel process with which the KernelManager is communicating.
    # generally a Popen instance
    kernel = Any()

    kernel_cmd = List(Unicode, config=True,
        help="""The Popen Command to launch the kernel.
        Override this if you have a custom
        """
    )

    def _kernel_cmd_changed(self, name, old, new):
        self.ipython_kernel = False

    ipython_kernel = Bool(True)

    # Protected traits
    _launch_args = Any()
    _control_socket = Any()

    _restarter = Any()

    autorestart = Bool(False, config=True,
        help="""Should we autorestart the kernel if it dies."""
    )

    def __del__(self):
        self._close_control_socket()
        self.cleanup_connection_file()

    #--------------------------------------------------------------------------
    # Kernel restarter
    #--------------------------------------------------------------------------

    def start_restarter(self):
        pass

    def stop_restarter(self):
        pass

    #--------------------------------------------------------------------------
    # create a Client connected to our Kernel
    #--------------------------------------------------------------------------

    def client(self, **kwargs):
        """Create a client configured to connect to our kernel"""
        if self.client_factory is None:
            self.client_factory = import_item(self.client_class)

        kw = {}
        kw.update(self.get_connection_info())
        kw.update(dict(
            connection_file=self.connection_file,
            session=self.session,
            config=self.config,
        ))

        # add kwargs last, for manual overrides
        kw.update(kwargs)
        return self.client_factory(**kw)

    #--------------------------------------------------------------------------
    # Connection info
    #--------------------------------------------------------------------------

    def _make_url(self, channel):
        """Make a ZeroMQ URL for a given channel."""
        transport = self.transport
        ip = self.ip
        port = getattr(self, '%s_port' % channel)

        if transport == 'tcp':
            return "tcp://%s:%i" % (ip, port)
        else:
            return "%s://%s-%s" % (transport, ip, port)

    def _create_connected_socket(self, channel, identity=None):
        """Create a zmq Socket and connect it to the kernel."""
        url = self._make_url(channel)
        socket_type = _socket_types[channel]
        self.log.info("Connecting to: %s" % url)
        sock = self.context.socket(socket_type)
        if identity:
            sock.identity = identity
        sock.connect(url)
        return sock

    def connect_iopub(self, identity=None):
        """return zmq Socket connected to the IOPub channel"""
        sock = self._create_connected_socket('iopub', identity=identity)
        sock.setsockopt(zmq.SUBSCRIBE, b'')
        return sock

    def connect_shell(self, identity=None):
        """return zmq Socket connected to the Shell channel"""
        return self._create_connected_socket('shell', identity=identity)

    def connect_stdin(self, identity=None):
        """return zmq Socket connected to the StdIn channel"""
        return self._create_connected_socket('stdin', identity=identity)

    def connect_hb(self, identity=None):
        """return zmq Socket connected to the Heartbeat channel"""
        return self._create_connected_socket('hb', identity=identity)

    def connect_control(self, identity=None):
        """return zmq Socket connected to the Heartbeat channel"""
        return self._create_connected_socket('control', identity=identity)

    #--------------------------------------------------------------------------
    # Kernel management
    #--------------------------------------------------------------------------

    def format_kernel_cmd(self, **kw):
        """format templated args (e.g. {connection_file})"""
        if self.kernel_cmd:
            cmd = self.kernel_cmd
        else:
            cmd = make_ipkernel_cmd(
                'from IPython.kernel.zmq.kernelapp import main; main()',
                **kw
            )
        ns = dict(connection_file=self.connection_file)
        ns.update(self._launch_args)
        return [ c.format(**ns) for c in cmd ]

    def _launch_kernel(self, kernel_cmd, **kw):
        """actually launch the kernel

        override in a subclass to launch kernel subprocesses differently
        """
        return launch_kernel(kernel_cmd, **kw)

    # Control socket used for polite kernel shutdown

    def _connect_control_socket(self):
        if self._control_socket is None:
            self._control_socket = self.connect_control()
            self._control_socket.linger = 100

    def _close_control_socket(self):
        if self._control_socket is None:
            return
        self._control_socket.close()
        self._control_socket = None

    def start_kernel(self, **kw):
        """Starts a kernel on this host in a separate process.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.

        Parameters:
        -----------
        **kw : optional
             keyword arguments that are passed down to build the kernel_cmd
             and launching the kernel (e.g. Popen kwargs).
        """
        if self.transport == 'tcp' and self.ip not in LOCAL_IPS:
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s"%LOCAL_IPS
                               )

        # write connection file / get default ports
        self.write_connection_file()

        # save kwargs for use in restart
        self._launch_args = kw.copy()
        # build the Popen cmd
        kernel_cmd = self.format_kernel_cmd(**kw)
        # launch the kernel subprocess
        self.kernel = self._launch_kernel(kernel_cmd,
                                    ipython_kernel=self.ipython_kernel,
                                    **kw)
        self.start_restarter()
        self._connect_control_socket()

    def _send_shutdown_request(self, restart=False):
        """TODO: send a shutdown request via control channel"""
        content = dict(restart=restart)
        msg = self.session.msg("shutdown_request", content=content)
        self.session.send(self._control_socket, msg)

    def shutdown_kernel(self, now=False, restart=False):
        """Attempts to the stop the kernel process cleanly.

        This attempts to shutdown the kernels cleanly by:

        1. Sending it a shutdown message over the shell channel.
        2. If that fails, the kernel is shutdown forcibly by sending it
           a signal.

        Parameters:
        -----------
        now : bool
            Should the kernel be forcible killed *now*. This skips the
            first, nice shutdown attempt.
        restart: bool
            Will this kernel be restarted after it is shutdown. When this
            is True, connection files will not be cleaned up.
        """
        # Stop monitoring for restarting while we shutdown.
        self.stop_restarter()

        # FIXME: Shutdown does not work on Windows due to ZMQ errors!
        if sys.platform == 'win32':
            self._kill_kernel()
            return

        if now:
            if self.has_kernel:
                self._kill_kernel()
        else:
            # Don't send any additional kernel kill messages immediately, to give
            # the kernel a chance to properly execute shutdown actions. Wait for at
            # most 1s, checking every 0.1s.
            self._send_shutdown_request(restart=restart)
            for i in range(10):
                if self.is_alive():
                    time.sleep(0.1)
                else:
                    break
            else:
                # OK, we've waited long enough.
                if self.has_kernel:
                    self._kill_kernel()

        if not restart:
            self.cleanup_connection_file()
            self.cleanup_ipc_files()
        else:
            self.cleanup_ipc_files()

    def restart_kernel(self, now=False, **kw):
        """Restarts a kernel with the arguments that were used to launch it.

        If the old kernel was launched with random ports, the same ports will be
        used for the new kernel. The same connection file is used again.

        Parameters
        ----------
        now : bool, optional
            If True, the kernel is forcefully restarted *immediately*, without
            having a chance to do any cleanup action.  Otherwise the kernel is
            given 1s to clean up before a forceful restart is issued.

            In all cases the kernel is restarted, the only difference is whether
            it is given a chance to perform a clean shutdown or not.

        **kw : optional
            Any options specified here will overwrite those used to launch the
            kernel.
        """
        if self._launch_args is None:
            raise RuntimeError("Cannot restart the kernel. "
                               "No previous call to 'start_kernel'.")
        else:
            # Stop currently running kernel.
            self.shutdown_kernel(now=now, restart=True)

            # Start new kernel.
            self._launch_args.update(kw)
            self.start_kernel(**self._launch_args)

            # FIXME: Messages get dropped in Windows due to probable ZMQ bug
            # unless there is some delay here.
            if sys.platform == 'win32':
                time.sleep(0.2)

    @property
    def has_kernel(self):
        """Has a kernel been started that we are managing."""
        return self.kernel is not None

    def _kill_kernel(self):
        """Kill the running kernel.

        This is a private method, callers should use shutdown_kernel(now=True).
        """
        if self.has_kernel:

            # Signal the kernel to terminate (sends SIGKILL on Unix and calls
            # TerminateProcess() on Win32).
            try:
                self.kernel.kill()
            except OSError as e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if sys.platform == 'win32':
                    if e.winerror != 5:
                        raise
                # On Unix, we may get an ESRCH error if the process has already
                # terminated. Ignore it.
                else:
                    from errno import ESRCH
                    if e.errno != ESRCH:
                        raise

            # Block until the kernel terminates.
            self.kernel.wait()
            self.kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def interrupt_kernel(self):
        """Interrupts the kernel by sending it a signal.

        Unlike ``signal_kernel``, this operation is well supported on all
        platforms.
        """
        if self.has_kernel:
            if sys.platform == 'win32':
                from .zmq.parentpoller import ParentPollerWindows as Poller
                Poller.send_interrupt(self.kernel.win32_interrupt_event)
            else:
                self.kernel.send_signal(signal.SIGINT)
        else:
            raise RuntimeError("Cannot interrupt kernel. No kernel is running!")

    def signal_kernel(self, signum):
        """Sends a signal to the kernel.

        Note that since only SIGTERM is supported on Windows, this function is
        only useful on Unix systems.
        """
        if self.has_kernel:
            self.kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    def is_alive(self):
        """Is the kernel process still running?"""
        if self.has_kernel:
            if self.kernel.poll() is None:
                return True
            else:
                return False
        else:
            # we don't have a kernel
            return False


#-----------------------------------------------------------------------------
# ABC Registration
#-----------------------------------------------------------------------------

KernelManagerABC.register(KernelManager)


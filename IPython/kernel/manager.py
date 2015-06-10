"""Base class to manage a running kernel"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

from contextlib import contextmanager
import os
import re
import signal
import sys
import time
import warnings
try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

import zmq

from IPython.utils.importstring import import_item
from IPython.utils.localinterfaces import is_local_ip, local_ips
from IPython.utils.path import get_ipython_dir
from IPython.utils.traitlets import (
    Any, Instance, Unicode, List, Bool, Type, DottedObjectName
)
from IPython.kernel import (
    launch_kernel,
    kernelspec,
)
from .connect import ConnectionFileMixin
from .zmq.session import Session
from .managerabc import (
    KernelManagerABC
)


class KernelManager(ConnectionFileMixin):
    """Manages a single kernel in a subprocess on this host.

    This version starts kernels with Popen.
    """

    # The PyZMQ Context to use for communication with the kernel.
    context = Instance(zmq.Context)
    def _context_default(self):
        return zmq.Context.instance()

    # the class to create with our `client` method
    client_class = DottedObjectName('IPython.kernel.blocking.BlockingKernelClient')
    client_factory = Type()
    def _client_class_changed(self, name, old, new):
        self.client_factory = import_item(str(new))

    # The kernel process with which the KernelManager is communicating.
    # generally a Popen instance
    kernel = Any()
    
    kernel_spec_manager = Instance(kernelspec.KernelSpecManager)
    
    def _kernel_spec_manager_default(self):
        return kernelspec.KernelSpecManager(ipython_dir=self.ipython_dir)
    
    kernel_name = Unicode(kernelspec.NATIVE_KERNEL_NAME)
    
    kernel_spec = Instance(kernelspec.KernelSpec)
    
    def _kernel_spec_default(self):
        return self.kernel_spec_manager.get_kernel_spec(self.kernel_name)
    
    def _kernel_name_changed(self, name, old, new):
        if new == 'python':
            self.kernel_name = kernelspec.NATIVE_KERNEL_NAME
            # This triggered another run of this function, so we can exit now
            return
        self.kernel_spec = self.kernel_spec_manager.get_kernel_spec(new)
        self.ipython_kernel = new in {'python', 'python2', 'python3'}

    kernel_cmd = List(Unicode, config=True,
        help="""DEPRECATED: Use kernel_name instead.
        
        The Popen Command to launch the kernel.
        Override this if you have a custom kernel.
        If kernel_cmd is specified in a configuration file,
        IPython does not pass any arguments to the kernel,
        because it cannot make any assumptions about the 
        arguments that the kernel understands. In particular,
        this means that the kernel does not receive the
        option --debug if it given on the IPython command line.
        """
    )

    def _kernel_cmd_changed(self, name, old, new):
        warnings.warn("Setting kernel_cmd is deprecated, use kernel_spec to "
                      "start different kernels.")
        self.ipython_kernel = False

    ipython_kernel = Bool(True)
    
    ipython_dir = Unicode()
    def _ipython_dir_default(self):
        return get_ipython_dir()

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

    def add_restart_callback(self, callback, event='restart'):
        """register a callback to be called when a kernel is restarted"""
        if self._restarter is None:
            return
        self._restarter.add_callback(callback, event)

    def remove_restart_callback(self, callback, event='restart'):
        """unregister a callback to be called when a kernel is restarted"""
        if self._restarter is None:
            return
        self._restarter.remove_callback(callback, event)

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
            parent=self,
        ))

        # add kwargs last, for manual overrides
        kw.update(kwargs)
        return self.client_factory(**kw)

    #--------------------------------------------------------------------------
    # Kernel management
    #--------------------------------------------------------------------------

    def format_kernel_cmd(self, extra_arguments=None):
        """replace templated args (e.g. {connection_file})"""
        extra_arguments = extra_arguments or []
        if self.kernel_cmd:
            cmd = self.kernel_cmd + extra_arguments
        else:
            cmd = self.kernel_spec.argv + extra_arguments

        ns = dict(connection_file=self.connection_file)
        ns.update(self._launch_args)
        
        pat = re.compile(r'\{([A-Za-z0-9_]+)\}')
        def from_ns(match):
            """Get the key out of ns if it's there, otherwise no change."""
            return ns.get(match.group(1), match.group())
        
        return [ pat.sub(from_ns, arg) for arg in cmd ]

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

        Parameters
        ----------
        **kw : optional
             keyword arguments that are passed down to build the kernel_cmd
             and launching the kernel (e.g. Popen kwargs).
        """
        if self.transport == 'tcp' and not is_local_ip(self.ip):
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s" % local_ips()
                               )

        # write connection file / get default ports
        self.write_connection_file()

        # save kwargs for use in restart
        self._launch_args = kw.copy()
        # build the Popen cmd
        extra_arguments = kw.pop('extra_arguments', [])
        kernel_cmd = self.format_kernel_cmd(extra_arguments=extra_arguments)
        env = os.environ.copy()
        # Don't allow PYTHONEXECUTABLE to be passed to kernel process.
        # If set, it can bork all the things.
        env.pop('PYTHONEXECUTABLE', None)
        if not self.kernel_cmd:
            # If kernel_cmd has been set manually, don't refer to a kernel spec
            env.update(self.kernel_spec.env or {})
        # launch the kernel subprocess
        self.kernel = self._launch_kernel(kernel_cmd, env=env,
                                    **kw)
        self.start_restarter()
        self._connect_control_socket()

    def request_shutdown(self, restart=False):
        """Send a shutdown request via control channel
        
        On Windows, this just kills kernels instead, because the shutdown
        messages don't work.
        """
        content = dict(restart=restart)
        msg = self.session.msg("shutdown_request", content=content)
        self.session.send(self._control_socket, msg)

    def finish_shutdown(self, waittime=1, pollinterval=0.1):
        """Wait for kernel shutdown, then kill process if it doesn't shutdown.
        
        This does not send shutdown requests - use :meth:`request_shutdown`
        first.
        """
        for i in range(int(waittime/pollinterval)):
            if self.is_alive():
                time.sleep(pollinterval)
            else:
                break
        else:
            # OK, we've waited long enough.
            if self.has_kernel:
                self._kill_kernel()

    def cleanup(self, connection_file=True):
        """Clean up resources when the kernel is shut down"""
        if connection_file:
            self.cleanup_connection_file()

        self.cleanup_ipc_files()
        self._close_control_socket()

    def shutdown_kernel(self, now=False, restart=False):
        """Attempts to the stop the kernel process cleanly.

        This attempts to shutdown the kernels cleanly by:

        1. Sending it a shutdown message over the shell channel.
        2. If that fails, the kernel is shutdown forcibly by sending it
           a signal.

        Parameters
        ----------
        now : bool
            Should the kernel be forcible killed *now*. This skips the
            first, nice shutdown attempt.
        restart: bool
            Will this kernel be restarted after it is shutdown. When this
            is True, connection files will not be cleaned up.
        """
        # Stop monitoring for restarting while we shutdown.
        self.stop_restarter()

        if now:
            self._kill_kernel()
        else:
            self.request_shutdown(restart=restart)
            # Don't send any additional kernel kill messages immediately, to give
            # the kernel a chance to properly execute shutdown actions. Wait for at
            # most 1s, checking every 0.1s.
            self.finish_shutdown()

        self.cleanup(connection_file=not restart)

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


KernelManagerABC.register(KernelManager)


def start_new_kernel(startup_timeout=60, kernel_name='python', **kwargs):
    """Start a new kernel, and return its Manager and Client"""
    km = KernelManager(kernel_name=kernel_name)
    km.start_kernel(**kwargs)
    kc = km.client()
    kc.start_channels()
    kc.wait_for_ready()

    return km, kc

@contextmanager
def run_kernel(**kwargs):
    """Context manager to create a kernel in a subprocess.
    
    The kernel is shut down when the context exits.
    
    Returns
    -------
    kernel_client: connected KernelClient instance
    """
    km, kc = start_new_kernel(**kwargs)
    try:
        yield kc
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)

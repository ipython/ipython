"""KernelStarter class that intercepts Control Queue messages, and handles process management.

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from zmq.eventloop import ioloop

from IPython.zmq.session import Session

class KernelStarter(object):
    """Object for resetting/killing the Kernel."""
    
    
    def __init__(self, session, upstream, downstream, *kernel_args, **kernel_kwargs):
        self.session = session
        self.upstream = upstream
        self.downstream = downstream
        self.kernel_args = kernel_args
        self.kernel_kwargs = kernel_kwargs
        self.handlers = {}
        for method in 'shutdown_request shutdown_reply'.split():
            self.handlers[method] = getattr(self, method)
    
    def start(self):
        self.upstream.on_recv(self.dispatch_request)
        self.downstream.on_recv(self.dispatch_reply)
        
    #--------------------------------------------------------------------------
    # Dispatch methods
    #--------------------------------------------------------------------------
    
    def dispatch_request(self, raw_msg):
        idents, msg = self.session.feed_identities()
        try:
            msg = self.session.unserialize(msg, content=False)
        except:
            print ("bad msg: %s"%msg)
        
        msgtype = msg['header']['msg_type']
        handler = self.handlers.get(msgtype, None)
        if handler is None:
            self.downstream.send_multipart(raw_msg, copy=False)
        else:
            handler(msg)
        
    def dispatch_reply(self, raw_msg):
        idents, msg = self.session.feed_identities()
        try:
            msg = self.session.unserialize(msg, content=False)
        except:
            print ("bad msg: %s"%msg)
        
        msgtype = msg['header']['msg_type']
        handler = self.handlers.get(msgtype, None)
        if handler is None:
            self.upstream.send_multipart(raw_msg, copy=False)
        else:
            handler(msg)
    
    #--------------------------------------------------------------------------
    # Handlers
    #--------------------------------------------------------------------------
    
    def shutdown_request(self, msg):
        """"""
        self.downstream.send_multipart(msg)
    
    #--------------------------------------------------------------------------
    # Kernel process management methods, from KernelManager:
    #--------------------------------------------------------------------------
    
    def _check_local(addr):
        if isinstance(addr, tuple):
            addr = addr[0]
        return addr in LOCAL_IPS
    
    def start_kernel(self, **kw):
        """Starts a kernel process and configures the manager to use it.

        If random ports (port=0) are being used, this method must be called
        before the channels are created.

        Parameters:
        -----------
        ipython : bool, optional (default True)
             Whether to use an IPython kernel instead of a plain Python kernel.
        """
        self.kernel = Process(target=make_kernel, args=self.kernel_args,
                                            kwargs=self.kernel_kwargs)

    def shutdown_kernel(self, restart=False):
        """ Attempts to the stop the kernel process cleanly. If the kernel
        cannot be stopped, it is killed, if possible.
        """
        # FIXME: Shutdown does not work on Windows due to ZMQ errors!
        if sys.platform == 'win32':
            self.kill_kernel()
            return

        # Don't send any additional kernel kill messages immediately, to give
        # the kernel a chance to properly execute shutdown actions. Wait for at
        # most 1s, checking every 0.1s.
        self.xreq_channel.shutdown(restart=restart)
        for i in range(10):
            if self.is_alive:
                time.sleep(0.1)
            else:
                break
        else:
            # OK, we've waited long enough.
            if self.has_kernel:
                self.kill_kernel()
    
    def restart_kernel(self, now=False):
        """Restarts a kernel with the same arguments that were used to launch
        it. If the old kernel was launched with random ports, the same ports
        will be used for the new kernel.

        Parameters
        ----------
        now : bool, optional
          If True, the kernel is forcefully restarted *immediately*, without
          having a chance to do any cleanup action.  Otherwise the kernel is
          given 1s to clean up before a forceful restart is issued.

          In all cases the kernel is restarted, the only difference is whether
          it is given a chance to perform a clean shutdown or not.
        """
        if self._launch_args is None:
            raise RuntimeError("Cannot restart the kernel. "
                               "No previous call to 'start_kernel'.")
        else:
            if self.has_kernel:
                if now:
                    self.kill_kernel()
                else:
                    self.shutdown_kernel(restart=True)
            self.start_kernel(**self._launch_args)

            # FIXME: Messages get dropped in Windows due to probable ZMQ bug
            # unless there is some delay here.
            if sys.platform == 'win32':
                time.sleep(0.2)

    @property
    def has_kernel(self):
        """Returns whether a kernel process has been specified for the kernel
        manager.
        """
        return self.kernel is not None

    def kill_kernel(self):
        """ Kill the running kernel. """
        if self.has_kernel:
            # Pause the heart beat channel if it exists.
            if self._hb_channel is not None:
                self._hb_channel.pause()

            # Attempt to kill the kernel.
            try:
                self.kernel.kill()
            except OSError, e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if not (sys.platform == 'win32' and e.winerror == 5):
                    raise
            self.kernel = None
        else:
            raise RuntimeError("Cannot kill kernel. No kernel is running!")

    def interrupt_kernel(self):
        """ Interrupts the kernel. Unlike ``signal_kernel``, this operation is
        well supported on all platforms.
        """
        if self.has_kernel:
            if sys.platform == 'win32':
                from parentpoller import ParentPollerWindows as Poller
                Poller.send_interrupt(self.kernel.win32_interrupt_event)
            else:
                self.kernel.send_signal(signal.SIGINT)
        else:
            raise RuntimeError("Cannot interrupt kernel. No kernel is running!")

    def signal_kernel(self, signum):
        """ Sends a signal to the kernel. Note that since only SIGTERM is
        supported on Windows, this function is only useful on Unix systems.
        """
        if self.has_kernel:
            self.kernel.send_signal(signum)
        else:
            raise RuntimeError("Cannot signal kernel. No kernel is running!")

    @property
    def is_alive(self):
        """Is the kernel process still running?"""
        # FIXME: not using a heartbeat means this method is broken for any
        # remote kernel, it's only capable of handling local kernels.
        if self.has_kernel:
            if self.kernel.poll() is None:
                return True
            else:
                return False
        else:
            # We didn't start the kernel with this KernelManager so we don't
            # know if it is running. We should use a heartbeat for this case.
            return True


def make_starter(up_addr, down_addr, *args, **kwargs):
    """entry point function for launching a kernelstarter in a subprocess"""
    loop = ioloop.IOLoop.instance()
    ctx = zmq.Context()
    session = Session()
    upstream = zmqstream.ZMQStream(ctx.socket(zmq.DEALER),loop)
    upstream.connect(up_addr)
    downstream = zmqstream.ZMQStream(ctx.socket(zmq.DEALER),loop)
    downstream.connect(down_addr)
    
    starter = KernelStarter(session, upstream, downstream, *args, **kwargs)
    starter.start()
    loop.start()
    

#!/usr/bin/env python
"""An Application for launching a kernel

Authors
-------
* MinRK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
import os
import sys

# System library imports.
import zmq

# IPython imports.
from IPython.core.ultratb import FormattedTB
from IPython.core.newapplication import (
    BaseIPythonApplication, base_flags, base_aliases
)
from IPython.utils import io
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.traitlets import Any, Instance, Dict, Unicode, Int, Bool
from IPython.utils.importstring import import_item
# local imports
from IPython.zmq.heartbeat import Heartbeat
from IPython.zmq.parentpoller import ParentPollerUnix, ParentPollerWindows
from IPython.zmq.session import Session


#-----------------------------------------------------------------------------
# Flags and Aliases
#-----------------------------------------------------------------------------

kernel_aliases = dict(base_aliases)
kernel_aliases.update({
    'ip' : 'KernelApp.ip',
    'hb' : 'KernelApp.hb_port',
    'shell' : 'KernelApp.shell_port',
    'iopub' : 'KernelApp.iopub_port',
    'stdin' : 'KernelApp.stdin_port',
    'parent': 'KernelApp.parent',
})
if sys.platform.startswith('win'):
    kernel_aliases['interrupt'] = 'KernelApp.interrupt'

kernel_flags = dict(base_flags)
kernel_flags.update({
    'no-stdout' : (
            {'KernelApp' : {'no_stdout' : True}},
            "redirect stdout to the null device"),
    'no-stderr' : (
            {'KernelApp' : {'no_stderr' : True}},
            "redirect stderr to the null device"),
})


#-----------------------------------------------------------------------------
# Application class for starting a Kernel
#-----------------------------------------------------------------------------

class KernelApp(BaseIPythonApplication):
    name='pykernel'
    aliases = Dict(kernel_aliases)
    flags = Dict(kernel_flags)

    # the kernel class, as an importstring
    kernel_class = Unicode('IPython.zmq.pykernel.Kernel')
    kernel = Any()
    poller = Any() # don't restrict this even though current pollers are all Threads
    heartbeat = Instance(Heartbeat)
    session = Instance('IPython.zmq.session.Session')
    ports = Dict()

    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="Set the IP or interface on which the kernel will listen.")
    hb_port = Int(0, config=True, help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True, help="set the shell (XREP) port [default: random]")
    iopub_port = Int(0, config=True, help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True, help="set the stdin (XREQ) port [default: random]")

    # streams, etc.
    no_stdout = Bool(False, config=True, help="redirect stdout to the null device")
    no_stderr = Bool(False, config=True, help="redirect stderr to the null device")
    outstream_class = Unicode('IPython.zmq.iostream.OutStream', config=True,
        help="The importstring for the OutStream factory")
    displayhook_class = Unicode('IPython.zmq.displayhook.DisplayHook', config=True,
        help="The importstring for the DisplayHook factory")

    # polling
    parent = Int(0, config=True,
        help="""kill this process if its parent dies.  On Windows, the argument
        specifies the HANDLE of the parent process, otherwise it is simply boolean.
        """)
    interrupt = Int(0, config=True,
        help="""ONLY USED ON WINDOWS
        Interrupt this process when the parent is signalled.
        """)

    def init_crash_handler(self):
        # Install minimal exception handling
        sys.excepthook = FormattedTB(mode='Verbose', color_scheme='NoColor',
                                     ostream=sys.__stdout__)

    def init_poller(self):
        if sys.platform == 'win32':
            if self.interrupt or self.parent:
                self.poller = ParentPollerWindows(self.interrupt, self.parent)
        elif self.parent:
            self.poller = ParentPollerUnix()

    def _bind_socket(self, s, port):
        iface = 'tcp://%s' % self.ip
        if port <= 0:
            port = s.bind_to_random_port(iface)
        else:
            s.bind(iface + ':%i'%port)
        return port

    def init_sockets(self):
        # Create a context, a session, and the kernel sockets.
        io.raw_print("Starting the kernel at pid:", os.getpid())
        context = zmq.Context.instance()
        # Uncomment this to try closing the context.
        # atexit.register(context.term)

        self.shell_socket = context.socket(zmq.XREP)
        self.shell_port = self._bind_socket(self.shell_socket, self.shell_port)
        self.log.debug("shell XREP Channel on port: %i"%self.shell_port)

        self.iopub_socket = context.socket(zmq.PUB)
        self.iopub_port = self._bind_socket(self.iopub_socket, self.iopub_port)
        self.log.debug("iopub PUB Channel on port: %i"%self.iopub_port)

        self.stdin_socket = context.socket(zmq.XREQ)
        self.stdin_port = self._bind_socket(self.stdin_socket, self.stdin_port)
        self.log.debug("stdin XREQ Channel on port: %i"%self.stdin_port)

        self.heartbeat = Heartbeat(context, (self.ip, self.hb_port))
        self.hb_port = self.heartbeat.port
        self.log.debug("Heartbeat REP Channel on port: %i"%self.hb_port)

        # Helper to make it easier to connect to an existing kernel, until we have
        # single-port connection negotiation fully implemented.
        self.log.info("To connect another client to this kernel, use:")
        self.log.info("--external shell={0} iopub={1} stdin={2} hb={3}".format(
            self.shell_port, self.iopub_port, self.stdin_port, self.hb_port))


        self.ports = dict(shell=self.shell_port, iopub=self.iopub_port,
                                stdin=self.stdin_port, hb=self.hb_port)

    def init_session(self):
        """create our session object"""
        self.session = Session(username=u'kernel')

    def init_io(self):
        """redirects stdout/stderr, and installs a display hook"""
        # Re-direct stdout/stderr, if necessary.
        if self.no_stdout or self.no_stderr:
            blackhole = file(os.devnull, 'w')
            if self.no_stdout:
                sys.stdout = sys.__stdout__ = blackhole
            if self.no_stderr:
                sys.stderr = sys.__stderr__ = blackhole

        # Redirect input streams and set a display hook.

        if self.outstream_class:
            outstream_factory = import_item(str(self.outstream_class))
            sys.stdout = outstream_factory(self.session, self.iopub_socket, u'stdout')
            sys.stderr = outstream_factory(self.session, self.iopub_socket, u'stderr')
        if self.displayhook_class:
            displayhook_factory = import_item(str(self.displayhook_class))
            sys.displayhook = displayhook_factory(self.session, self.iopub_socket)

    def init_kernel(self):
        """Create the Kernel object itself"""
        kernel_factory = import_item(str(self.kernel_class))
        self.kernel = kernel_factory(config=self.config, session=self.session,
                                shell_socket=self.shell_socket,
                                iopub_socket=self.iopub_socket,
                                stdin_socket=self.stdin_socket,
        )
        self.kernel.record_ports(self.ports)

    def initialize(self, argv=None):
        super(KernelApp, self).initialize(argv)
        self.init_session()
        self.init_poller()
        self.init_sockets()
        self.init_io()
        self.init_kernel()

    def start(self):
        self.heartbeat.start()
        if self.poller is not None:
            self.poller.start()
        try:
            self.kernel.start()
        except KeyboardInterrupt:
            pass

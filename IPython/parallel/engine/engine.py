"""A simple engine that talks to a controller over 0MQ.
it handles registration, etc. and launches a kernel
connected to the Controller's Schedulers.

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

import sys
import time
from getpass import getpass

import zmq
from zmq.eventloop import ioloop, zmqstream

from IPython.external.ssh import tunnel
# internal
from IPython.utils.traitlets import (
    Instance, Dict, Integer, Type, CFloat, Unicode, CBytes, Bool
)
from IPython.utils.py3compat import cast_bytes

from IPython.parallel.controller.heartmonitor import Heart
from IPython.parallel.factory import RegistrationFactory
from IPython.parallel.util import disambiguate_url

from IPython.zmq.session import Message
from IPython.zmq.ipkernel import Kernel

class EngineFactory(RegistrationFactory):
    """IPython engine"""

    # configurables:
    out_stream_factory=Type('IPython.zmq.iostream.OutStream', config=True,
        help="""The OutStream for handling stdout/err.
        Typically 'IPython.zmq.iostream.OutStream'""")
    display_hook_factory=Type('IPython.zmq.displayhook.ZMQDisplayHook', config=True,
        help="""The class for handling displayhook.
        Typically 'IPython.zmq.displayhook.ZMQDisplayHook'""")
    location=Unicode(config=True,
        help="""The location (an IP address) of the controller.  This is
        used for disambiguating URLs, to determine whether
        loopback should be used to connect or the public address.""")
    timeout=CFloat(2,config=True,
        help="""The time (in seconds) to wait for the Controller to respond
        to registration requests before giving up.""")
    sshserver=Unicode(config=True,
        help="""The SSH server to use for tunneling connections to the Controller.""")
    sshkey=Unicode(config=True,
        help="""The SSH private key file to use when tunneling connections to the Controller.""")
    paramiko=Bool(sys.platform == 'win32', config=True,
        help="""Whether to use paramiko instead of openssh for tunnels.""")

    # not configurable:
    user_ns=Dict()
    id=Integer(allow_none=True)
    registrar=Instance('zmq.eventloop.zmqstream.ZMQStream')
    kernel=Instance(Kernel)

    bident = CBytes()
    ident = Unicode()
    def _ident_changed(self, name, old, new):
        self.bident = cast_bytes(new)
    using_ssh=Bool(False)


    def __init__(self, **kwargs):
        super(EngineFactory, self).__init__(**kwargs)
        self.ident = self.session.session

    def init_connector(self):
        """construct connection function, which handles tunnels."""
        self.using_ssh = bool(self.sshkey or self.sshserver)

        if self.sshkey and not self.sshserver:
            # We are using ssh directly to the controller, tunneling localhost to localhost
            self.sshserver = self.url.split('://')[1].split(':')[0]

        if self.using_ssh:
            if tunnel.try_passwordless_ssh(self.sshserver, self.sshkey, self.paramiko):
                password=False
            else:
                password = getpass("SSH Password for %s: "%self.sshserver)
        else:
            password = False

        def connect(s, url):
            url = disambiguate_url(url, self.location)
            if self.using_ssh:
                self.log.debug("Tunneling connection to %s via %s"%(url, self.sshserver))
                return tunnel.tunnel_connection(s, url, self.sshserver,
                            keyfile=self.sshkey, paramiko=self.paramiko,
                            password=password,
                )
            else:
                return s.connect(url)

        def maybe_tunnel(url):
            """like connect, but don't complete the connection (for use by heartbeat)"""
            url = disambiguate_url(url, self.location)
            if self.using_ssh:
                self.log.debug("Tunneling connection to %s via %s"%(url, self.sshserver))
                url,tunnelobj = tunnel.open_tunnel(url, self.sshserver,
                            keyfile=self.sshkey, paramiko=self.paramiko,
                            password=password,
                )
            return url
        return connect, maybe_tunnel

    def register(self):
        """send the registration_request"""

        self.log.info("Registering with controller at %s"%self.url)
        ctx = self.context
        connect,maybe_tunnel = self.init_connector()
        reg = ctx.socket(zmq.DEALER)
        reg.setsockopt(zmq.IDENTITY, self.bident)
        connect(reg, self.url)
        self.registrar = zmqstream.ZMQStream(reg, self.loop)


        content = dict(queue=self.ident, heartbeat=self.ident, control=self.ident)
        self.registrar.on_recv(lambda msg: self.complete_registration(msg, connect, maybe_tunnel))
        # print (self.session.key)
        self.session.send(self.registrar, "registration_request",content=content)

    def complete_registration(self, msg, connect, maybe_tunnel):
        # print msg
        self._abort_dc.stop()
        ctx = self.context
        loop = self.loop
        identity = self.bident
        idents,msg = self.session.feed_identities(msg)
        msg = Message(self.session.unserialize(msg))

        if msg.content.status == 'ok':
            self.id = int(msg.content.id)

            # launch heartbeat
            hb_addrs = msg.content.heartbeat

            # possibly forward hb ports with tunnels
            hb_addrs = [ maybe_tunnel(addr) for addr in hb_addrs ]
            heart = Heart(*map(str, hb_addrs), heart_id=identity)
            heart.start()

            # create Shell Streams (MUX, Task, etc.):
            queue_addr = msg.content.mux
            shell_addrs = [ str(queue_addr) ]
            task_addr = msg.content.task
            if task_addr:
                shell_addrs.append(str(task_addr))

            # Uncomment this to go back to two-socket model
            # shell_streams = []
            # for addr in shell_addrs:
            #     stream = zmqstream.ZMQStream(ctx.socket(zmq.ROUTER), loop)
            #     stream.setsockopt(zmq.IDENTITY, identity)
            #     stream.connect(disambiguate_url(addr, self.location))
            #     shell_streams.append(stream)

            # Now use only one shell stream for mux and tasks
            stream = zmqstream.ZMQStream(ctx.socket(zmq.ROUTER), loop)
            stream.setsockopt(zmq.IDENTITY, identity)
            shell_streams = [stream]
            for addr in shell_addrs:
                connect(stream, addr)
            # end single stream-socket

            # control stream:
            control_addr = str(msg.content.control)
            control_stream = zmqstream.ZMQStream(ctx.socket(zmq.ROUTER), loop)
            control_stream.setsockopt(zmq.IDENTITY, identity)
            connect(control_stream, control_addr)

            # create iopub stream:
            iopub_addr = msg.content.iopub
            iopub_socket = ctx.socket(zmq.PUB)
            iopub_socket.setsockopt(zmq.IDENTITY, identity)
            connect(iopub_socket, iopub_addr)

            # disable history:
            self.config.HistoryManager.hist_file = ':memory:'
            
            # Redirect input streams and set a display hook.
            if self.out_stream_factory:
                sys.stdout = self.out_stream_factory(self.session, iopub_socket, u'stdout')
                sys.stdout.topic = cast_bytes('engine.%i.stdout' % self.id)
                sys.stderr = self.out_stream_factory(self.session, iopub_socket, u'stderr')
                sys.stderr.topic = cast_bytes('engine.%i.stderr' % self.id)
            if self.display_hook_factory:
                sys.displayhook = self.display_hook_factory(self.session, iopub_socket)
                sys.displayhook.topic = cast_bytes('engine.%i.pyout' % self.id)

            self.kernel = Kernel(config=self.config, int_id=self.id, ident=self.ident, session=self.session,
                    control_stream=control_stream, shell_streams=shell_streams, iopub_socket=iopub_socket,
                    loop=loop, user_ns=self.user_ns, log=self.log)
            self.kernel.shell.display_pub.topic = cast_bytes('engine.%i.displaypub' % self.id)
            self.kernel.start()


        else:
            self.log.fatal("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)

        self.log.info("Completed registration with id %i"%self.id)


    def abort(self):
        self.log.fatal("Registration timed out after %.1f seconds"%self.timeout)
        if self.url.startswith('127.'):
            self.log.fatal("""
            If the controller and engines are not on the same machine,
            you will have to instruct the controller to listen on an external IP (in ipcontroller_config.py):
                c.HubFactory.ip='*' # for all interfaces, internal and external
                c.HubFactory.ip='192.168.1.101' # or any interface that the engines can see
            or tunnel connections via ssh.
            """)
        self.session.send(self.registrar, "unregistration_request", content=dict(id=self.id))
        time.sleep(1)
        sys.exit(255)

    def start(self):
        dc = ioloop.DelayedCallback(self.register, 0, self.loop)
        dc.start()
        self._abort_dc = ioloop.DelayedCallback(self.abort, self.timeout*1000, self.loop)
        self._abort_dc.start()


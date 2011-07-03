#!/usr/bin/env python
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

import zmq
from zmq.eventloop import ioloop, zmqstream

# internal
from IPython.utils.traitlets import Instance, Dict, Int, Type, CFloat, Unicode, CBytes
# from IPython.utils.localinterfaces import LOCALHOST 

from IPython.parallel.controller.heartmonitor import Heart
from IPython.parallel.factory import RegistrationFactory
from IPython.parallel.util import disambiguate_url, asbytes

from IPython.zmq.session import Message

from .streamkernel import Kernel

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
    
    # not configurable:
    user_ns=Dict()
    id=Int(allow_none=True)
    registrar=Instance('zmq.eventloop.zmqstream.ZMQStream')
    kernel=Instance(Kernel)
    
    bident = CBytes()
    ident = Unicode()
    def _ident_changed(self, name, old, new):
        self.bident = asbytes(new)
    
    
    def __init__(self, **kwargs):
        super(EngineFactory, self).__init__(**kwargs)
        self.ident = self.session.session
        ctx = self.context
        
        reg = ctx.socket(zmq.XREQ)
        reg.setsockopt(zmq.IDENTITY, self.bident)
        reg.connect(self.url)
        self.registrar = zmqstream.ZMQStream(reg, self.loop)
        
    def register(self):
        """send the registration_request"""
        
        self.log.info("Registering with controller at %s"%self.url)
        content = dict(queue=self.ident, heartbeat=self.ident, control=self.ident)
        self.registrar.on_recv(self.complete_registration)
        # print (self.session.key)
        self.session.send(self.registrar, "registration_request",content=content)
    
    def complete_registration(self, msg):
        # print msg
        self._abort_dc.stop()
        ctx = self.context
        loop = self.loop
        identity = self.bident
        idents,msg = self.session.feed_identities(msg)
        msg = Message(self.session.unpack_message(msg))
        
        if msg.content.status == 'ok':
            self.id = int(msg.content.id)
            
            # create Shell Streams (MUX, Task, etc.):
            queue_addr = msg.content.mux
            shell_addrs = [ str(queue_addr) ]
            task_addr = msg.content.task
            if task_addr:
                shell_addrs.append(str(task_addr))
            
            # Uncomment this to go back to two-socket model
            # shell_streams = []
            # for addr in shell_addrs:
            #     stream = zmqstream.ZMQStream(ctx.socket(zmq.XREP), loop)
            #     stream.setsockopt(zmq.IDENTITY, identity)
            #     stream.connect(disambiguate_url(addr, self.location))
            #     shell_streams.append(stream)
            
            # Now use only one shell stream for mux and tasks
            stream = zmqstream.ZMQStream(ctx.socket(zmq.XREP), loop)
            stream.setsockopt(zmq.IDENTITY, identity)
            shell_streams = [stream]
            for addr in shell_addrs:
                stream.connect(disambiguate_url(addr, self.location))
            # end single stream-socket
            
            # control stream:
            control_addr = str(msg.content.control)
            control_stream = zmqstream.ZMQStream(ctx.socket(zmq.XREP), loop)
            control_stream.setsockopt(zmq.IDENTITY, identity)
            control_stream.connect(disambiguate_url(control_addr, self.location))
            
            # create iopub stream:
            iopub_addr = msg.content.iopub
            iopub_stream = zmqstream.ZMQStream(ctx.socket(zmq.PUB), loop)
            iopub_stream.setsockopt(zmq.IDENTITY, identity)
            iopub_stream.connect(disambiguate_url(iopub_addr, self.location))
            
            # launch heartbeat
            hb_addrs = msg.content.heartbeat
            # print (hb_addrs)
            
            # # Redirect input streams and set a display hook.
            if self.out_stream_factory:
                sys.stdout = self.out_stream_factory(self.session, iopub_stream, u'stdout')
                sys.stdout.topic = 'engine.%i.stdout'%self.id
                sys.stderr = self.out_stream_factory(self.session, iopub_stream, u'stderr')
                sys.stderr.topic = 'engine.%i.stderr'%self.id
            if self.display_hook_factory:
                sys.displayhook = self.display_hook_factory(self.session, iopub_stream)
                sys.displayhook.topic = 'engine.%i.pyout'%self.id

            self.kernel = Kernel(config=self.config, int_id=self.id, ident=self.ident, session=self.session, 
                    control_stream=control_stream, shell_streams=shell_streams, iopub_stream=iopub_stream, 
                    loop=loop, user_ns = self.user_ns, log=self.log)
            self.kernel.start()
            hb_addrs = [ disambiguate_url(addr, self.location) for addr in hb_addrs ]
            heart = Heart(*map(str, hb_addrs), heart_id=identity)
            heart.start()
            
            
        else:
            self.log.fatal("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        self.log.info("Completed registration with id %i"%self.id)
    
    
    def abort(self):
        self.log.fatal("Registration timed out after %.1f seconds"%self.timeout)
        self.session.send(self.registrar, "unregistration_request", content=dict(id=self.id))
        time.sleep(1)
        sys.exit(255)
    
    def start(self):
        dc = ioloop.DelayedCallback(self.register, 0, self.loop)
        dc.start()
        self._abort_dc = ioloop.DelayedCallback(self.abort, self.timeout*1000, self.loop)
        self._abort_dc.start()


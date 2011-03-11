#!/usr/bin/env python
"""A simple engine that talks to a controller over 0MQ.
it handles registration, etc. and launches a kernel
connected to the Controller's Schedulers.
"""
from __future__ import print_function

import sys
import time

import zmq
from zmq.eventloop import ioloop, zmqstream

# internal
from IPython.utils.traitlets import Instance, Str, Dict, Int, Type, CFloat
# from IPython.utils.localinterfaces import LOCALHOST 

from . import heartmonitor
from .factory import RegistrationFactory
from .streamkernel import Kernel
from .streamsession import Message
from .util import disambiguate_url

class EngineFactory(RegistrationFactory):
    """IPython engine"""
    
    # configurables:
    user_ns=Dict(config=True)
    out_stream_factory=Type('IPython.zmq.iostream.OutStream', config=True)
    display_hook_factory=Type('IPython.zmq.displayhook.DisplayHook', config=True)
    location=Str(config=True)
    timeout=CFloat(2,config=True)
    
    # not configurable:
    id=Int(allow_none=True)
    registrar=Instance('zmq.eventloop.zmqstream.ZMQStream')
    kernel=Instance(Kernel)
    
    
    def __init__(self, **kwargs):
        super(EngineFactory, self).__init__(**kwargs)
        ctx = self.context
        
        reg = ctx.socket(zmq.PAIR)
        reg.setsockopt(zmq.IDENTITY, self.ident)
        reg.connect(self.url)
        self.registrar = zmqstream.ZMQStream(reg, self.loop)
        
    def register(self):
        """send the registration_request"""
        
        self.log.info("registering")
        content = dict(queue=self.ident, heartbeat=self.ident, control=self.ident)
        self.registrar.on_recv(self.complete_registration)
        # print (self.session.key)
        self.session.send(self.registrar, "registration_request",content=content)
    
    def complete_registration(self, msg):
        # print msg
        self._abort_dc.stop()
        ctx = self.context
        loop = self.loop
        identity = self.ident
        
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
            shell_streams = []
            for addr in shell_addrs:
                stream = zmqstream.ZMQStream(ctx.socket(zmq.PAIR), loop)
                stream.setsockopt(zmq.IDENTITY, identity)
                stream.connect(disambiguate_url(addr, self.location))
                shell_streams.append(stream)
            
            # control stream:
            control_addr = str(msg.content.control)
            control_stream = zmqstream.ZMQStream(ctx.socket(zmq.PAIR), loop)
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
                    loop=loop, user_ns = self.user_ns, logname=self.log.name)
            self.kernel.start()
            hb_addrs = [ disambiguate_url(addr, self.location) for addr in hb_addrs ]
            heart = heartmonitor.Heart(*map(str, hb_addrs), heart_id=identity)
            # ioloop.DelayedCallback(heart.start, 1000, self.loop).start()
            heart.start()
            
            
        else:
            self.log.fatal("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        self.log.info("Completed registration with id %i"%self.id)
    
    
    def abort(self):
        self.log.fatal("Registration timed out")
        self.session.send(self.registrar, "unregistration_request", content=dict(id=self.id))
        time.sleep(1)
        sys.exit(255)
    
    def start(self):
        dc = ioloop.DelayedCallback(self.register, 0, self.loop)
        dc.start()
        self._abort_dc = ioloop.DelayedCallback(self.abort, self.timeout*1000, self.loop)
        self._abort_dc.start()


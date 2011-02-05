#!/usr/bin/env python
"""A simple engine that talks to a controller over 0MQ.
it handles registration, etc. and launches a kernel
connected to the Controller's queue(s).
"""
from __future__ import print_function
import sys
import time
import traceback
import uuid
import logging
from pprint import pprint

import zmq
from zmq.eventloop import ioloop, zmqstream

# internal
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance, Str, Dict, Int, Type
# from IPython.utils.localinterfaces import LOCALHOST 

from factory import RegistrationFactory

from streamsession import Message, StreamSession
from streamkernel import Kernel, make_kernel
import heartmonitor
from entry_point import (make_base_argument_parser, connect_engine_logger, parse_url,
                        local_logger)
# import taskthread

def printer(*msg):
    # print (logging.handlers, file=sys.__stdout__)
    logging.info(str(msg))

class EngineFactory(RegistrationFactory):
    """IPython engine"""
    
    # configurables:
    user_ns=Dict(config=True)
    out_stream_factory=Type('IPython.zmq.iostream.OutStream', config=True)
    display_hook_factory=Type('IPython.zmq.displayhook.DisplayHook', config=True)
    
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
        
        logging.info("registering")
        content = dict(queue=self.ident, heartbeat=self.ident, control=self.ident)
        self.registrar.on_recv(self.complete_registration)
        # print (self.session.key)
        self.session.send(self.registrar, "registration_request",content=content)
    
    def complete_registration(self, msg):
        # print msg
        ctx = self.context
        loop = self.loop
        identity = self.ident
        print (identity)
        
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
                stream.connect(addr)
                shell_streams.append(stream)
            
            # control stream:
            control_addr = str(msg.content.control)
            control_stream = zmqstream.ZMQStream(ctx.socket(zmq.PAIR), loop)
            control_stream.setsockopt(zmq.IDENTITY, identity)
            control_stream.connect(control_addr)
            
            # create iopub stream:
            iopub_addr = msg.content.iopub
            iopub_stream = zmqstream.ZMQStream(ctx.socket(zmq.PUB), loop)
            iopub_stream.setsockopt(zmq.IDENTITY, identity)
            iopub_stream.connect(iopub_addr)
            
            # launch heartbeat
            hb_addrs = msg.content.heartbeat
            # print (hb_addrs)
            
            # # Redirect input streams and set a display hook.
            # if self.out_stream_factory:
            #     sys.stdout = self.out_stream_factory(self.session, iopub_stream, u'stdout')
            #     sys.stdout.topic = 'engine.%i.stdout'%self.id
            #     sys.stderr = self.out_stream_factory(self.session, iopub_stream, u'stderr')
            #     sys.stderr.topic = 'engine.%i.stderr'%self.id
            # if self.display_hook_factory:
            #     sys.displayhook = self.display_hook_factory(self.session, iopub_stream)
            #     sys.displayhook.topic = 'engine.%i.pyout'%self.id
            
            # ioloop.DelayedCallback(self.heart.start, 1000, self.loop).start()
            self.kernel = Kernel(int_id=self.id, ident=self.ident, session=self.session, 
                    control_stream=control_stream,
                    shell_streams=shell_streams, iopub_stream=iopub_stream, loop=loop,
                    user_ns = self.user_ns, config=self.config)
            self.kernel.start()
            
            heart = heartmonitor.Heart(*map(str, hb_addrs), heart_id=identity)
            heart.start()
            
            
        else:
            logging.error("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        logging.info("Completed registration with id %i"%self.id)
    
    
    def unregister(self):
        self.session.send(self.registrar, "unregistration_request", content=dict(id=self.id))
        time.sleep(1)
        sys.exit(0)
    
    def start(self):
        dc = ioloop.DelayedCallback(self.register, 0, self.loop)
        dc.start()



def main(argv=None, user_ns=None):
    """DO NOT USE ME ANYMORE"""
    parser = make_base_argument_parser()
    
    args = parser.parse_args(argv)
    
    parse_url(args)
    
    iface="%s://%s"%(args.transport,args.ip)+':%i'
    
    loop = ioloop.IOLoop.instance()
    session = StreamSession(keyfile=args.execkey)
    # print (session.key)
    ctx = zmq.Context()

    # setup logging
    
    reg_conn = iface % args.regport
    print (reg_conn, file=sys.__stdout__)
    print ("Starting the engine...", file=sys.__stderr__)
    
    reg = ctx.socket(zmq.PAIR)
    reg.connect(reg_conn)
    reg = zmqstream.ZMQStream(reg, loop)
    
    e = Engine(context=ctx, loop=loop, session=session, registrar=reg, 
            ident=args.ident or '', user_ns=user_ns)
    if args.logport:
        print ("connecting logger to %s"%(iface%args.logport), file=sys.__stdout__)
        connect_engine_logger(ctx, iface%args.logport, e, loglevel=args.loglevel)
    else:
        local_logger(args.loglevel)
    
    dc = ioloop.DelayedCallback(e.start, 0, loop)
    dc.start()
    try:
        loop.start()
    except KeyboardInterrupt:
        print ("interrupted, exiting...", file=sys.__stderr__)

# Execution as a script
if __name__ == '__main__':
    main()

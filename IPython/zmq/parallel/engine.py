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
from IPython.utils.traitlets import Instance, Str, Dict
# from IPython.utils.localinterfaces import LOCALHOST 

from streamsession import Message, StreamSession
from streamkernel import Kernel, make_kernel
import heartmonitor
from entry_point import (make_base_argument_parser, connect_engine_logger, parse_url,
                        local_logger)
# import taskthread
logger = logging.getLogger()

def printer(*msg):
    # print (logger.handlers, file=sys.__stdout__)
    logger.info(str(msg))

class Engine(Configurable):
    """IPython engine"""
    
    kernel=None
    id=None
    
    # configurables:
    context=Instance(zmq.Context)
    loop=Instance(ioloop.IOLoop)
    session=Instance(StreamSession)
    ident=Str()
    registrar=Instance(zmqstream.ZMQStream)
    user_ns=Dict()
    
    def __init__(self, **kwargs):
        super(Engine, self).__init__(**kwargs)
        if not self.ident:
            self.ident =  str(uuid.uuid4())
        self.registrar.on_send(printer)
        
    def register(self):
        
        content = dict(queue=self.ident, heartbeat=self.ident, control=self.ident)
        self.registrar.on_recv(self.complete_registration)
        # print (self.session.key)
        self.session.send(self.registrar, "registration_request",content=content)
    
    def complete_registration(self, msg):
        # print msg
        idents,msg = self.session.feed_identities(msg)
        msg = Message(self.session.unpack_message(msg))
        if msg.content.status == 'ok':
            self.id = int(msg.content.id)
            self.session.username = 'engine-%i'%self.id
            queue_addr = msg.content.mux
            shell_addrs = [ str(queue_addr) ]
            control_addr = str(msg.content.control)
            task_addr = msg.content.task
            iopub_addr = msg.content.iopub
            if task_addr:
                shell_addrs.append(str(task_addr))
            
            hb_addrs = msg.content.heartbeat
            # ioloop.DelayedCallback(self.heart.start, 1000, self.loop).start()
            k = make_kernel(self.id, self.ident, control_addr, shell_addrs, iopub_addr,
                            hb_addrs, client_addr=None, loop=self.loop,
                            context=self.context, key=self.session.key)[-1]
            self.kernel = k
            if self.user_ns is not None:
                self.user_ns.update(self.kernel.user_ns)
                self.kernel.user_ns = self.user_ns
            
        else:
            logger.error("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        logger.info("completed registration with id %i"%self.id)
        
        # logger.info(str(msg))
    
    def unregister(self):
        self.session.send(self.registrar, "unregistration_request", content=dict(id=int(self.session.username)))
        time.sleep(1)
        sys.exit(0)
    
    def start(self):
        logger.info("registering")
        self.register()

        

def main(argv=None, user_ns=None):
    
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
    loop.start()

# Execution as a script
if __name__ == '__main__':
    main()

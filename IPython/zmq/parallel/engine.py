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
from pprint import pprint

import zmq
from zmq.eventloop import ioloop, zmqstream

from IPython.utils.traitlets import HasTraits
from IPython.utils.localinterfaces import LOCALHOST 

from streamsession import Message, StreamSession
from client import Client
from streamkernel import Kernel, make_kernel
import heartmonitor
from entry_point import make_base_argument_parser, connect_logger, parse_url
# import taskthread
# from log import logger


def printer(*msg):
    pprint(msg)

class Engine(object):
    """IPython engine"""
    
    id=None
    context=None
    loop=None
    session=None
    ident=None
    registrar=None
    heart=None
    kernel=None
    
    def __init__(self, context, loop, session, registrar, client=None, ident=None):
        self.context = context
        self.loop = loop
        self.session = session
        self.registrar = registrar
        self.client = client
        self.ident = ident if ident else str(uuid.uuid4())
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
            self.session.username = str(msg.content.id)
            queue_addr = msg.content.queue
            shell_addrs = [str(queue_addr)]
            control_addr = str(msg.content.control)
            task_addr = msg.content.task
            if task_addr:
                shell_addrs.append(str(task_addr))
            
            hb_addrs = msg.content.heartbeat
            # ioloop.DelayedCallback(self.heart.start, 1000, self.loop).start()
            
            # placeholder for no, since pub isn't hooked up:
            sub = self.context.socket(zmq.SUB)
            sub = zmqstream.ZMQStream(sub, self.loop)
            sub.on_recv(lambda *a: None)
            port = sub.bind_to_random_port("tcp://%s"%LOCALHOST)
            iopub_addr = "tcp://%s:%i"%(LOCALHOST,12345)
            make_kernel(self.ident, control_addr, shell_addrs, iopub_addr, hb_addrs, 
                        client_addr=None, loop=self.loop, context=self.context, key=self.session.key)
            
        else:
            # logger.error("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        # logger.info("engine::completed registration with id %s"%self.session.username)
        
        print (msg)
    
    def unregister(self):
        self.session.send(self.registrar, "unregistration_request", content=dict(id=int(self.session.username)))
        time.sleep(1)
        sys.exit(0)
    
    def start(self):
        print ("registering")
        self.register()

        

def main():
    
    parser = make_base_argument_parser()
    
    args = parser.parse_args()
    
    parse_url(args)
    
    iface="%s://%s"%(args.transport,args.ip)+':%i'
    
    loop = ioloop.IOLoop.instance()
    session = StreamSession(keyfile=args.execkey)
    # print (session.key)
    ctx = zmq.Context()

    # setup logging
    connect_logger(ctx, iface%args.logport, root="engine", loglevel=args.loglevel)
    
    reg_conn = iface % args.regport
    print (reg_conn)
    print ("Starting the engine...", file=sys.__stderr__)
    
    reg = ctx.socket(zmq.PAIR)
    reg.connect(reg_conn)
    reg = zmqstream.ZMQStream(reg, loop)
    client = None
    
    e = Engine(ctx, loop, session, reg, client, args.ident)
    dc = ioloop.DelayedCallback(e.start, 100, loop)
    dc.start()
    loop.start()
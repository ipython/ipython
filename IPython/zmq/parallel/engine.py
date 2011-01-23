#!/usr/bin/env python
"""A simple engine that talks to a controller over 0MQ.
it handles registration, etc. and launches a kernel
connected to the Controller's queue(s).
"""
import sys
import time
import traceback
import uuid

import zmq
from zmq.eventloop import ioloop, zmqstream

from streamsession import Message, StreamSession
from client import Client
import streamkernel as kernel
import heartmonitor
# import taskthread
# from log import logger


def printer(*msg):
    print msg

class Engine(object):
    """IPython engine"""
    
    id=None
    context=None
    loop=None
    session=None
    queue_id=None
    control_id=None
    heart_id=None
    registrar=None
    heart=None
    kernel=None
    
    def __init__(self, context, loop, session, registrar, client, queue_id=None, heart_id=None):
        self.context = context
        self.loop = loop
        self.session = session
        self.registrar = registrar
        self.client = client
        self.queue_id = queue_id or str(uuid.uuid4())
        self.heart_id = heart_id or self.queue_id
        self.registrar.on_send(printer)
        
    def register(self):
        
        content = dict(queue=self.queue_id, heartbeat=self.heart_id)
        self.registrar.on_recv(self.complete_registration)
        self.session.send(self.registrar, "registration_request",content=content)
    
    def complete_registration(self, msg):
        # print msg
        idents,msg = self.session.feed_identities(msg)
        msg = Message(self.session.unpack_message(msg))
        if msg.content.status == 'ok':
            self.session.username = str(msg.content.id)
            queue_addr = msg.content.queue
            if queue_addr:
                queue = self.context.socket(zmq.PAIR)
                queue.setsockopt(zmq.IDENTITY, self.queue_id)
                queue.connect(str(queue_addr))
                self.queue = zmqstream.ZMQStream(queue, self.loop)
            
            control_addr = msg.content.control
            if control_addr:
                control = self.context.socket(zmq.PAIR)
                control.setsockopt(zmq.IDENTITY, self.queue_id)
                control.connect(str(control_addr))
                self.control = zmqstream.ZMQStream(control, self.loop)
            
            task_addr = msg.content.task
            print task_addr
            if task_addr:
                # task as stream:
                task = self.context.socket(zmq.PAIR)
                task.connect(str(task_addr))
                self.task_stream = zmqstream.ZMQStream(task, self.loop)
                # TaskThread:
                # mon_addr = msg.content.monitor
                # task = taskthread.TaskThread(zmq.PAIR, zmq.PUB, self.queue_id)
                # task.connect_in(str(task_addr))
                # task.connect_out(str(mon_addr))
                # self.task_stream = taskthread.QueueStream(*task.queues)
                # task.start()
            
            hbs = msg.content.heartbeat
            self.heart = heartmonitor.Heart(*map(str, hbs), heart_id=self.heart_id)
            self.heart.start()
            # ioloop.DelayedCallback(self.heart.start, 1000, self.loop).start()
            # placeholder for now:
            pub = self.context.socket(zmq.PUB)
            pub = zmqstream.ZMQStream(pub, self.loop)
            # create and start the kernel
            self.kernel = kernel.Kernel(self.session, self.control, self.queue, pub, self.task_stream, self.client)
            self.kernel.start()
        else:
            # logger.error("Registration Failed: %s"%msg)
            raise Exception("Registration Failed: %s"%msg)
        
        # logger.info("engine::completed registration with id %s"%self.session.username)
        
        print msg
    
    def unregister(self):
        self.session.send(self.registrar, "unregistration_request", content=dict(id=int(self.session.username)))
        time.sleep(1)
        sys.exit(0)
    
    def start(self):
        print "registering"
        self.register()
        

if __name__ == '__main__':
    
    loop = ioloop.IOLoop.instance()
    session = StreamSession()
    ctx = zmq.Context()

    ip = '127.0.0.1'
    reg_port = 10101
    connection = ('tcp://%s' % ip) + ':%i'
    reg_conn = connection % reg_port
    print reg_conn
    print >>sys.__stdout__, "Starting the engine..."
    
    reg = ctx.socket(zmq.PAIR)
    reg.connect(reg_conn)
    reg = zmqstream.ZMQStream(reg, loop)
    client = Client(reg_conn)
    if len(sys.argv) > 1:
        queue_id=sys.argv[1]
    else:
        queue_id = None
    
    e = Engine(ctx, loop, session, reg, client, queue_id)
    dc = ioloop.DelayedCallback(e.start, 500, loop)
    dc.start()
    loop.start()
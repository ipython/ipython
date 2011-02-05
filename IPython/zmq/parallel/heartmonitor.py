#!/usr/bin/env python
"""
A multi-heart Heartbeat system using PUB and XREP sockets. pings are sent out on the PUB,
and hearts are tracked based on their XREQ identities.
"""

from __future__ import print_function
import time
import uuid
import logging

import zmq
from zmq.devices import ProcessDevice,ThreadDevice
from zmq.eventloop import ioloop, zmqstream

class Heart(object):
    """A basic heart object for responding to a HeartMonitor.
    This is a simple wrapper with defaults for the most common
    Device model for responding to heartbeats.
    
    It simply builds a threadsafe zmq.FORWARDER Device, defaulting to using 
    SUB/XREQ for in/out.
    
    You can specify the XREQ's IDENTITY via the optional heart_id argument."""
    device=None
    id=None
    def __init__(self, in_addr, out_addr, in_type=zmq.SUB, out_type=zmq.XREQ, heart_id=None):
        self.device = ThreadDevice(zmq.FORWARDER, in_type, out_type)
        self.device.daemon=True
        self.device.connect_in(in_addr)
        self.device.connect_out(out_addr)
        if in_type == zmq.SUB:
            self.device.setsockopt_in(zmq.SUBSCRIBE, "")
        if heart_id is None:
            heart_id = str(uuid.uuid4())
        self.device.setsockopt_out(zmq.IDENTITY, heart_id)
        self.id = heart_id
    
    def start(self):
        return self.device.start()
        
class HeartMonitor(object):
    """A basic HeartMonitor class
    pingstream: a PUB stream
    pongstream: an XREP stream
    period: the period of the heartbeat in milliseconds"""
    loop=None
    pingstream=None
    pongstream=None
    period=None
    hearts=None
    on_probation=None
    last_ping=None
    # debug=False
    
    def __init__(self, loop, pingstream, pongstream, period=1000):
        self.loop = loop
        self.period = period
        
        self.pingstream = pingstream
        self.pongstream = pongstream
        self.pongstream.on_recv(self.handle_pong)
        
        self.hearts = set()
        self.responses = set()
        self.on_probation = set()
        self.lifetime = 0
        self.tic = time.time()
        
        self._new_handlers = set()
        self._failure_handlers = set()
    
    def start(self):
        self.caller = ioloop.PeriodicCallback(self.beat, self.period, self.loop)
        self.caller.start()
    
    def add_new_heart_handler(self, handler):
        """add a new handler for new hearts"""
        logging.debug("heartbeat::new_heart_handler: %s"%handler)
        self._new_handlers.add(handler)
        
    def add_heart_failure_handler(self, handler):
        """add a new handler for heart failure"""
        logging.debug("heartbeat::new heart failure handler: %s"%handler)
        self._failure_handlers.add(handler)
            
    def beat(self):
        self.pongstream.flush() 
        self.last_ping = self.lifetime
        
        toc = time.time()
        self.lifetime += toc-self.tic
        self.tic = toc
        # logging.debug("heartbeat::%s"%self.lifetime)
        goodhearts = self.hearts.intersection(self.responses)
        missed_beats = self.hearts.difference(goodhearts)
        heartfailures = self.on_probation.intersection(missed_beats)
        newhearts = self.responses.difference(goodhearts)
        map(self.handle_new_heart, newhearts)
        map(self.handle_heart_failure, heartfailures)
        self.on_probation = missed_beats.intersection(self.hearts)
        self.responses = set()
        # print self.on_probation, self.hearts
        # logging.debug("heartbeat::beat %.3f, %i beating hearts"%(self.lifetime, len(self.hearts)))
        self.pingstream.send(str(self.lifetime))
    
    def handle_new_heart(self, heart):
        if self._new_handlers:
            for handler in self._new_handlers:
                handler(heart)
        else:
            logging.info("heartbeat::yay, got new heart %s!"%heart)
        self.hearts.add(heart)
    
    def handle_heart_failure(self, heart):
        if self._failure_handlers:
            for handler in self._failure_handlers:
                try:
                    handler(heart)
                except Exception as e:
                    logging.error("heartbeat::Bad Handler! %s"%handler, exc_info=True)
                    pass
        else:
            logging.info("heartbeat::Heart %s failed :("%heart)
        self.hearts.remove(heart)
        
    
    def handle_pong(self, msg):
        "a heart just beat"
        if msg[1] == str(self.lifetime):
            delta = time.time()-self.tic
            # logging.debug("heartbeat::heart %r took %.2f ms to respond"%(msg[0], 1000*delta))
            self.responses.add(msg[0])
        elif msg[1] == str(self.last_ping):
            delta = time.time()-self.tic + (self.lifetime-self.last_ping)
            logging.warn("heartbeat::heart %r missed a beat, and took %.2f ms to respond"%(msg[0], 1000*delta))
            self.responses.add(msg[0])
        else:
            logging.warn("heartbeat::got bad heartbeat (possibly old?): %s (current=%.3f)"%
            (msg[1],self.lifetime))


if __name__ == '__main__':
    loop = ioloop.IOLoop.instance()
    context = zmq.Context()
    pub = context.socket(zmq.PUB)
    pub.bind('tcp://127.0.0.1:5555')
    xrep = context.socket(zmq.XREP)
    xrep.bind('tcp://127.0.0.1:5556')
    
    outstream = zmqstream.ZMQStream(pub, loop)
    instream = zmqstream.ZMQStream(xrep, loop)
    
    hb = HeartMonitor(loop, outstream, instream)
    
    loop.start()

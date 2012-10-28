#!/usr/bin/env python
"""
A multi-heart Heartbeat system using PUB and ROUTER sockets. pings are sent out on the PUB,
and hearts are tracked based on their DEALER identities.

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
import time
import uuid

import zmq
from zmq.devices import ThreadDevice, ThreadMonitoredQueue
from zmq.eventloop import ioloop, zmqstream

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import Set, Instance, CFloat, Integer

from IPython.parallel.util import log_errors

class Heart(object):
    """A basic heart object for responding to a HeartMonitor.
    This is a simple wrapper with defaults for the most common
    Device model for responding to heartbeats.

    It simply builds a threadsafe zmq.FORWARDER Device, defaulting to using
    SUB/DEALER for in/out.

    You can specify the DEALER's IDENTITY via the optional heart_id argument."""
    device=None
    id=None
    def __init__(self, in_addr, out_addr, mon_addr=None, in_type=zmq.SUB, out_type=zmq.DEALER, mon_type=zmq.PUB, heart_id=None):
        if mon_addr is None:
            self.device = ThreadDevice(zmq.FORWARDER, in_type, out_type)
        else:
            self.device = ThreadMonitoredQueue(in_type, out_type, mon_type, in_prefix=b"", out_prefix=b"")
        # do not allow the device to share global Context.instance,
        # which is the default behavior in pyzmq > 2.1.10
        self.device.context_factory = zmq.Context
        
        self.device.daemon=True
        self.device.connect_in(in_addr)
        self.device.connect_out(out_addr)
        if mon_addr is not None:
            self.device.connect_mon(mon_addr)
        if in_type == zmq.SUB:
            self.device.setsockopt_in(zmq.SUBSCRIBE, b"")
        if heart_id is None:
            heart_id = uuid.uuid4().bytes
        self.device.setsockopt_out(zmq.IDENTITY, heart_id)
        self.id = heart_id

    def start(self):
        return self.device.start()


class HeartMonitor(LoggingConfigurable):
    """A basic HeartMonitor class
    pingstream: a PUB stream
    pongstream: an ROUTER stream
    period: the period of the heartbeat in milliseconds"""

    period = Integer(3000, config=True,
        help='The frequency at which the Hub pings the engines for heartbeats '
        '(in ms)',
    )

    pingstream=Instance('zmq.eventloop.zmqstream.ZMQStream')
    pongstream=Instance('zmq.eventloop.zmqstream.ZMQStream')
    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        return ioloop.IOLoop.instance()

    # not settable:
    hearts=Set()
    responses=Set()
    on_probation=Set()
    last_ping=CFloat(0)
    _new_handlers = Set()
    _failure_handlers = Set()
    lifetime = CFloat(0)
    tic = CFloat(0)

    def __init__(self, **kwargs):
        super(HeartMonitor, self).__init__(**kwargs)

        self.pongstream.on_recv(self.handle_pong)

    def start(self):
        self.tic = time.time()
        self.caller = ioloop.PeriodicCallback(self.beat, self.period, self.loop)
        self.caller.start()

    def add_new_heart_handler(self, handler):
        """add a new handler for new hearts"""
        self.log.debug("heartbeat::new_heart_handler: %s", handler)
        self._new_handlers.add(handler)

    def add_heart_failure_handler(self, handler):
        """add a new handler for heart failure"""
        self.log.debug("heartbeat::new heart failure handler: %s", handler)
        self._failure_handlers.add(handler)

    def beat(self):
        self.pongstream.flush()
        self.last_ping = self.lifetime

        toc = time.time()
        self.lifetime += toc-self.tic
        self.tic = toc
        self.log.debug("heartbeat::sending %s", self.lifetime)
        goodhearts = self.hearts.intersection(self.responses)
        missed_beats = self.hearts.difference(goodhearts)
        heartfailures = self.on_probation.intersection(missed_beats)
        newhearts = self.responses.difference(goodhearts)
        map(self.handle_new_heart, newhearts)
        map(self.handle_heart_failure, heartfailures)
        self.on_probation = missed_beats.intersection(self.hearts)
        self.responses = set()
        #print self.on_probation, self.hearts
        # self.log.debug("heartbeat::beat %.3f, %i beating hearts", self.lifetime, len(self.hearts))
        self.pingstream.send(str_to_bytes(str(self.lifetime)))
        # flush stream to force immediate socket send
        self.pingstream.flush()

    def handle_new_heart(self, heart):
        if self._new_handlers:
            for handler in self._new_handlers:
                handler(heart)
        else:
            self.log.info("heartbeat::yay, got new heart %s!", heart)
        self.hearts.add(heart)

    def handle_heart_failure(self, heart):
        if self._failure_handlers:
            for handler in self._failure_handlers:
                try:
                    handler(heart)
                except Exception as e:
                    self.log.error("heartbeat::Bad Handler! %s", handler, exc_info=True)
                    pass
        else:
            self.log.info("heartbeat::Heart %s failed :(", heart)
        self.hearts.remove(heart)


    @log_errors
    def handle_pong(self, msg):
        "a heart just beat"
        current = str_to_bytes(str(self.lifetime))
        last = str_to_bytes(str(self.last_ping))
        if msg[1] == current:
            delta = time.time()-self.tic
            # self.log.debug("heartbeat::heart %r took %.2f ms to respond"%(msg[0], 1000*delta))
            self.responses.add(msg[0])
        elif msg[1] == last:
            delta = time.time()-self.tic + (self.lifetime-self.last_ping)
            self.log.warn("heartbeat::heart %r missed a beat, and took %.2f ms to respond", msg[0], 1000*delta)
            self.responses.add(msg[0])
        else:
            self.log.warn("heartbeat::got bad heartbeat (possibly old?): %s (current=%.3f)", msg[1], self.lifetime)


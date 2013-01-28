"""
A simple logger object that consolidates messages incoming from ipcluster processes.

Authors:

* MinRK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import logging
import sys

import zmq
from zmq.eventloop import ioloop, zmqstream

from IPython.config.configurable import LoggingConfigurable
from IPython.utils.localinterfaces import LOCALHOST
from IPython.utils.traitlets import Int, Unicode, Instance, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class LogWatcher(LoggingConfigurable):
    """A simple class that receives messages on a SUB socket, as published
    by subclasses of `zmq.log.handlers.PUBHandler`, and logs them itself.
    
    This can subscribe to multiple topics, but defaults to all topics.
    """
    
    # configurables
    topics = List([''], config=True,
        help="The ZMQ topics to subscribe to. Default is to subscribe to all messages")
    url = Unicode('tcp://%s:20202' % LOCALHOST, config=True,
        help="ZMQ url on which to listen for log messages")
    
    # internals
    stream = Instance('zmq.eventloop.zmqstream.ZMQStream')
    
    context = Instance(zmq.Context)
    def _context_default(self):
        return zmq.Context.instance()
    
    loop = Instance(zmq.eventloop.ioloop.IOLoop)
    def _loop_default(self):
        return ioloop.IOLoop.instance()
    
    def __init__(self, **kwargs):
        super(LogWatcher, self).__init__(**kwargs)
        s = self.context.socket(zmq.SUB)
        s.bind(self.url)
        self.stream = zmqstream.ZMQStream(s, self.loop)
        self.subscribe()
        self.on_trait_change(self.subscribe, 'topics')
    
    def start(self):
        self.stream.on_recv(self.log_message)
    
    def stop(self):
        self.stream.stop_on_recv()
    
    def subscribe(self):
        """Update our SUB socket's subscriptions."""
        self.stream.setsockopt(zmq.UNSUBSCRIBE, '')
        if '' in self.topics:
            self.log.debug("Subscribing to: everything")
            self.stream.setsockopt(zmq.SUBSCRIBE, '')
        else:
            for topic in self.topics:
                self.log.debug("Subscribing to: %r"%(topic))
                self.stream.setsockopt(zmq.SUBSCRIBE, topic)
    
    def _extract_level(self, topic_str):
        """Turn 'engine.0.INFO.extra' into (logging.INFO, 'engine.0.extra')"""
        topics = topic_str.split('.')
        for idx,t in enumerate(topics):
            level = getattr(logging, t, None)
            if level is not None:
                break
        
        if level is None:
            level = logging.INFO
        else:
            topics.pop(idx)
        
        return level, '.'.join(topics)
            
            
    def log_message(self, raw):
        """receive and parse a message, then log it."""
        if len(raw) != 2 or '.' not in raw[0]:
            self.log.error("Invalid log message: %s"%raw)
            return
        else:
            topic, msg = raw
            # don't newline, since log messages always newline:
            topic,level_name = topic.rsplit('.',1)
            level,topic = self._extract_level(topic)
            if msg[-1] == '\n':
                msg = msg[:-1]
            self.log.log(level, "[%s] %s" % (topic, msg))


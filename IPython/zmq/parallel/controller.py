#!/usr/bin/env python
"""The IPython Controller with 0MQ
This is a collection of one Hub and several Schedulers.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import logging
from multiprocessing import Process

import zmq

# internal:
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Int, Str, Instance, List, Bool

from entry_point import signal_children


from scheduler import launch_scheduler
from hub import Hub, HubFactory

#-----------------------------------------------------------------------------
# Configurable
#-----------------------------------------------------------------------------


class ControllerFactory(HubFactory):
    """Configurable for setting up a Hub and Schedulers."""
    
    usethreads = Bool(False, config=True)
    
    # internal
    children = List()
    mq_class = Str('zmq.devices.ProcessMonitoredQueue')
    
    def _usethreads_changed(self, name, old, new):
        self.mq_class = 'zmq.devices.%sMonitoredQueue'%('Thread' if new else 'Process')
        
    def __init__(self, **kwargs):
        super(ControllerFactory, self).__init__(**kwargs)
        self.subconstructors.append(self.construct_schedulers)
    
    def start(self):
        super(ControllerFactory, self).start()
        for child in self.children:
            child.start()
        if not self.usethreads:
            signal_children([ getattr(c, 'launcher', c) for c in self.children ])
        
    
    def construct_schedulers(self):
        children = self.children
        mq = import_item(self.mq_class)
        
        # IOPub relay (in a Process)
        q = mq(zmq.PUB, zmq.SUB, zmq.PUB, 'N/A','iopub')
        q.bind_in(self.client_info['iopub'])
        q.bind_out(self.engine_info['iopub'])
        q.setsockopt_out(zmq.SUBSCRIBE, '')
        q.connect_mon(self.monitor_url)
        q.daemon=True
        children.append(q)

        # Multiplexer Queue (in a Process)
        q = mq(zmq.XREP, zmq.XREP, zmq.PUB, 'in', 'out')
        q.bind_in(self.client_info['mux'])
        q.bind_out(self.engine_info['mux'])
        q.connect_mon(self.monitor_url)
        q.daemon=True
        children.append(q)

        # Control Queue (in a Process)
        q = mq(zmq.XREP, zmq.XREP, zmq.PUB, 'incontrol', 'outcontrol')
        q.bind_in(self.client_info['control'])
        q.bind_out(self.engine_info['control'])
        q.connect_mon(self.monitor_url)
        q.daemon=True
        children.append(q)
        # Task Queue (in a Process)
        if self.scheme == 'pure':
            self.log.warn("task::using pure XREQ Task scheduler")
            q = mq(zmq.XREP, zmq.XREQ, zmq.PUB, 'intask', 'outtask')
            q.bind_in(self.client_info['task'][1])
            q.bind_out(self.engine_info['task'])
            q.connect_mon(self.monitor_url)
            q.daemon=True
            children.append(q)
        elif self.scheme == 'none':
            self.log.warn("task::using no Task scheduler")
            
        else:
            self.log.info("task::using Python %s Task scheduler"%self.scheme)
            sargs = (self.client_info['task'][1], self.engine_info['task'], self.monitor_url, self.client_info['notification'])
            kwargs = dict(scheme=self.scheme,logname=self.log.name, loglevel=self.log.level, config=self.config)
            q = Process(target=launch_scheduler, args=sargs, kwargs=kwargs)
            q.daemon=True
            children.append(q)


"""Base config factories."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import logging
import os

import zmq
from zmq.eventloop.ioloop import IOLoop

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Int, Instance, Unicode

from IPython.parallel.util import select_random_ports
from IPython.zmq.session import Session

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class LoggingFactory(Configurable):
    """A most basic class, that has a `log` (type:`Logger`) attribute, set via a `logname` Trait."""
    log = Instance('logging.Logger', ('ZMQ', logging.WARN))
    logname = Unicode('ZMQ')
    def _logname_changed(self, name, old, new):
        self.log = logging.getLogger(new)
    

class SessionFactory(LoggingFactory):
    """The Base factory from which every factory in IPython.parallel inherits"""
    
    # not configurable:
    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()
    
    session = Instance('IPython.zmq.session.Session')
    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return IOLoop.instance()
    
    
    def __init__(self, **kwargs):
        super(SessionFactory, self).__init__(**kwargs)
        
        # construct the session
        self.session = Session(**kwargs)
    

class RegistrationFactory(SessionFactory):
    """The Base Configurable for objects that involve registration."""
    
    url = Unicode('', config=True,
        help="""The 0MQ url used for registration. This sets transport, ip, and port
        in one variable. For example: url='tcp://127.0.0.1:12345' or
        url='epgm://*:90210'""") # url takes precedence over ip,regport,transport
    transport = Unicode('tcp', config=True,
        help="""The 0MQ transport for communications.  This will likely be
        the default of 'tcp', but other values include 'ipc', 'epgm', 'inproc'.""")
    ip = Unicode('127.0.0.1', config=True,
        help="""The IP address for registration.  This is generally either
        '127.0.0.1' for loopback only or '*' for all interfaces.
        [default: '127.0.0.1']""")
    regport = Int(config=True,
        help="""The port on which the Hub listens for registration.""")
    def _regport_default(self):
        return select_random_ports(1)[0]
    
    def __init__(self, **kwargs):
        super(RegistrationFactory, self).__init__(**kwargs)
        self._propagate_url()
        self._rebuild_url()
        self.on_trait_change(self._propagate_url, 'url')
        self.on_trait_change(self._rebuild_url, 'ip')
        self.on_trait_change(self._rebuild_url, 'transport')
        self.on_trait_change(self._rebuild_url, 'regport')
    
    def _rebuild_url(self):
        self.url = "%s://%s:%i"%(self.transport, self.ip, self.regport)
        
    def _propagate_url(self):
        """Ensure self.url contains full transport://interface:port"""
        if self.url:
            iface = self.url.split('://',1)
            if len(iface) == 2:
                self.transport,iface = iface
            iface = iface.split(':')
            self.ip = iface[0]
            if iface[1]:
                self.regport = int(iface[1])

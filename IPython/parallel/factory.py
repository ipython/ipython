"""Base config factories.

Authors:

* Min RK
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import localhost
from IPython.utils.traitlets import Integer, Unicode

from IPython.parallel.util import select_random_ports
from IPython.kernel.zmq.session import SessionFactory

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class RegistrationFactory(SessionFactory):
    """The Base Configurable for objects that involve registration."""
    
    url = Unicode('', config=True,
        help="""The 0MQ url used for registration. This sets transport, ip, and port
        in one variable. For example: url='tcp://127.0.0.1:12345' or
        url='epgm://*:90210'"""
        ) # url takes precedence over ip,regport,transport
    transport = Unicode('tcp', config=True,
        help="""The 0MQ transport for communications.  This will likely be
        the default of 'tcp', but other values include 'ipc', 'epgm', 'inproc'.""")
    ip = Unicode(config=True,
        help="""The IP address for registration.  This is generally either
        '127.0.0.1' for loopback only or '*' for all interfaces.
        """)
    def _ip_default(self):
        return localhost()
    regport = Integer(config=True,
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

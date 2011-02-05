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


import os
import logging

import uuid

from zmq.eventloop.ioloop import IOLoop

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Str,Int,Instance, CUnicode, CStr
from IPython.utils.importstring import import_item

from IPython.zmq.parallel.entry_point import select_random_ports
import IPython.zmq.parallel.streamsession as ss

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class SessionFactory(Configurable):
    """The Base factory from which every factory in IPython.zmq.parallel inherits"""
    
    packer = Str('',config=True)
    unpacker = Str('',config=True)
    ident = CStr('',config=True)
    def _ident_default(self):
        return str(uuid.uuid4())
    username = Str(os.environ.get('USER','username'),config=True)
    exec_key = CUnicode('',config=True)
    
    # not configurable:
    context = Instance('zmq.Context', (), {})
    session = Instance('IPython.zmq.parallel.streamsession.StreamSession')
    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        return IOLoop.instance()
    
    def __init__(self, **kwargs):
        super(SessionFactory, self).__init__(**kwargs)
        
        keyfile = self.exec_key or None
        
        # set the packers:
        if not self.packer:
            packer_f = unpacker_f = None
        elif self.packer.lower() == 'json':
            packer_f = ss.json_packer
            unpacker_f = ss.json_unpacker
        elif self.packer.lower() == 'pickle':
            packer_f = ss.pickle_packer
            unpacker_f = ss.pickle_unpacker
        else:
            packer_f = import_item(self.packer)
            unpacker_f = import_item(self.unpacker)
        
        # construct the session
        self.session = ss.StreamSession(self.username, self.ident, packer=packer_f, unpacker=unpacker_f, keyfile=keyfile)
    

class RegistrationFactory(SessionFactory):
    """The Base Configurable for objects that involve registration."""
    
    url = Str('', config=True) # url takes precedence over ip,regport,transport
    transport = Str('tcp', config=True)
    ip = Str('127.0.0.1', config=True)
    regport = Instance(int, config=True)
    def _regport_default(self):
        return 10101
        # return select_random_ports(1)[0]
    
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

#-----------------------------------------------------------------------------
# argparse argument extenders
#-----------------------------------------------------------------------------


def add_session_arguments(parser):
    paa = parser.add_argument
    paa('--ident',
        type=str, dest='SessionFactory.ident', 
        help='set the ZMQ and session identity [default: random uuid]',
        metavar='identity')
    # paa('--execkey',
    #     type=str, dest='SessionFactory.exec_key', 
    #     help='path to a file containing an execution key.',
    #     metavar='execkey')
    paa('--packer',
        type=str, dest='SessionFactory.packer', 
        help='method to serialize messages: {json,pickle} [default: json]',
        metavar='packer')
    paa('--unpacker',
        type=str, dest='SessionFactory.unpacker', 
        help='inverse function of `packer`.  Only necessary when using something other than json|pickle',
        metavar='packer')

def add_registration_arguments(parser):
    paa = parser.add_argument
    paa('--ip',
        type=str, dest='RegistrationFactory.ip',
        help="The IP used for registration [default: localhost]",
        metavar='ip')
    paa('--transport',
        type=str, dest='RegistrationFactory.transport',
        help="The ZeroMQ transport used for registration [default: tcp]",
        metavar='transport')
    paa('--url',
        type=str, dest='RegistrationFactory.url', 
        help='set transport,ip,regport in one go, e.g. tcp://127.0.0.1:10101',
        metavar='url')
    paa('--regport',
        type=int, dest='RegistrationFactory.regport',
        help="The port used for registration [default: 10101]",
        metavar='ip')

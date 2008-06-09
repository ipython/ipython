# encoding: utf-8

"""A class that manages the engines connection to the controller."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import cPickle as pickle

from twisted.python import log

from IPython.kernel.fcutil import find_furl
from IPython.kernel.enginefc import IFCEngine

#-------------------------------------------------------------------------------
# The ClientConnector class
#-------------------------------------------------------------------------------

class EngineConnector(object):
    """Manage an engines connection to a controller.
    
    This class takes a foolscap `Tub` and provides a `connect_to_controller` 
    method that will use the `Tub` to connect to a controller and register
    the engine with the controller.
    """
    
    def __init__(self, tub):
        self.tub = tub
        
    def connect_to_controller(self, engine_service, furl_or_file):
        """
        Make a connection to a controller specified by a furl.
        
        This method takes an `IEngineBase` instance and a foolcap URL and uses
        the `tub` attribute to make a connection to the controller.  The 
        foolscap URL contains all the information needed to connect to the 
        controller, including the ip and port as well as any encryption and 
        authentication information needed for the connection.
        
        After getting a reference to the controller, this method calls the 
        `register_engine` method of the controller to actually register the 
        engine.
        
        :Parameters:
            engine_service : IEngineBase
                An instance of an `IEngineBase` implementer
            furl_or_file : str
                A furl or a filename containing a furl
        """
        if not self.tub.running:
            self.tub.startService()
        self.engine_service = engine_service
        self.engine_reference = IFCEngine(self.engine_service)
        self.furl = find_furl(furl_or_file)
        d = self.tub.getReference(self.furl)
        d.addCallbacks(self._register, self._log_failure)
        return d
    
    def _log_failure(self, reason):
        log.err('engine registration failed:')
        log.err(reason)
        return reason

    def _register(self, rr):
        self.remote_ref = rr
        # Now register myself with the controller
        desired_id = self.engine_service.id
        d = self.remote_ref.callRemote('register_engine', self.engine_reference, 
            desired_id, os.getpid(), pickle.dumps(self.engine_service.properties,2))
        return d.addCallbacks(self._reference_sent, self._log_failure)

    def _reference_sent(self, registration_dict):
        self.engine_service.id = registration_dict['id']
        log.msg("engine registration succeeded, got id: %r" % self.engine_service.id)
        return self.engine_service.id


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

from twisted.python import log, failure
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue

from IPython.kernel.fcutil import find_furl
from IPython.kernel.enginefc import IFCEngine
from IPython.kernel.twistedutil import sleep_deferred

#-------------------------------------------------------------------------------
# The ClientConnector class
#-------------------------------------------------------------------------------


class EngineConnectorError(Exception):
    pass


class EngineConnector(object):
    """Manage an engines connection to a controller.
    
    This class takes a foolscap `Tub` and provides a `connect_to_controller` 
    method that will use the `Tub` to connect to a controller and register
    the engine with the controller.
    """
    
    def __init__(self, tub):
        self.tub = tub

    def connect_to_controller(self, engine_service, furl_or_file,
                              delay=0.1, max_tries=10):
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

        This method will try to connect to the controller multiple times with
        a delay in between.  Each time the FURL file is read anew.

        Parameters
        __________
        engine_service : IEngineBase
            An instance of an `IEngineBase` implementer
        furl_or_file : str
            A furl or a filename containing a furl
        delay : float
            The intial time to wait between connection attempts.  Subsequent
            attempts have increasing delays.
        max_tries : int
            The maximum number of connection attempts.
        """
        if not self.tub.running:
            self.tub.startService()
        self.engine_service = engine_service
        self.engine_reference = IFCEngine(self.engine_service)

        d = self._try_to_connect(furl_or_file, delay, max_tries, attempt=0)
        return d

    @inlineCallbacks
    def _try_to_connect(self, furl_or_file, delay, max_tries, attempt):
        """Try to connect to the controller with retry logic."""
        if attempt < max_tries:
            log.msg("Attempting to connect to controller [%r]: %s" % \
                (attempt, furl_or_file))
            try:
                self.furl = find_furl(furl_or_file)
                # Uncomment this to see the FURL being tried.
                # log.msg("FURL: %s" % self.furl)
                rr = yield self.tub.getReference(self.furl)
            except:
                if attempt==max_tries-1:
                    # This will propagate the exception all the way to the top
                    # where it can be handled.
                    raise
                else:
                    yield sleep_deferred(delay)
                    yield self._try_to_connect(
                        furl_or_file, 1.5*delay, max_tries, attempt+1
                    )
            else:
                result = yield self._register(rr)
                returnValue(result)
        else:
            raise EngineConnectorError(
                'Could not connect to controller, max_tries (%r) exceeded. '
                'This usually means that i) the controller was not started, '
                'or ii) a firewall was blocking the engine from connecting '
                'to the controller.' % max_tries
            )

    def _register(self, rr):
        self.remote_ref = rr
        # Now register myself with the controller
        desired_id = self.engine_service.id
        d = self.remote_ref.callRemote('register_engine', self.engine_reference, 
            desired_id, os.getpid(), pickle.dumps(self.engine_service.properties,2))
        return d.addCallback(self._reference_sent)

    def _reference_sent(self, registration_dict):
        self.engine_service.id = registration_dict['id']
        log.msg("engine registration succeeded, got id: %r" % self.engine_service.id)
        return self.engine_service.id


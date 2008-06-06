# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_enginepb -*-

"""
Expose the IPython EngineService using the Foolscap network protocol.

Foolscap is a high-performance and secure network protocol.
"""
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

import os, time
import cPickle as pickle

from twisted.python import components, log, failure
from twisted.python.failure import Failure
from twisted.internet import defer, reactor, threads
from twisted.internet.interfaces import IProtocolFactory
from zope.interface import Interface, implements, Attribute

from twisted.internet.base import DelayedCall
DelayedCall.debug = True

from foolscap import Referenceable, DeadReferenceError
from foolscap.referenceable import RemoteReference

from IPython.kernel.pbutil import packageFailure, unpackageFailure
from IPython.kernel.util import printer
from IPython.kernel.twistedutil import gatherBoth
from IPython.kernel import newserialized
from IPython.kernel.error import  ProtocolError
from IPython.kernel import controllerservice
from IPython.kernel.controllerservice import IControllerBase
from IPython.kernel.engineservice import \
    IEngineBase, \
    IEngineQueued, \
    EngineService, \
    StrictDict
from IPython.kernel.pickleutil import \
    can, \
    canDict, \
    canSequence, \
    uncan, \
    uncanDict, \
    uncanSequence


#-------------------------------------------------------------------------------
# The client (Engine) side of things
#-------------------------------------------------------------------------------

# Expose a FC interface to the EngineService
     
class IFCEngine(Interface):
    """An interface that exposes an EngineService over Foolscap.
    
    The methods in this interface are similar to those from IEngine, 
    but their arguments and return values slightly different to reflect
    that FC cannot send arbitrary objects.  We handle this by pickling/
    unpickling that the two endpoints.
    
    If a remote or local exception is raised, the appropriate Failure
    will be returned instead.
    """
    pass
    

class FCEngineReferenceFromService(Referenceable, object):
    """Adapt an `IEngineBase` to an `IFCEngine` implementer.
    
    This exposes an `IEngineBase` to foolscap by adapting it to a
    `foolscap.Referenceable`.
    
    See the documentation of the `IEngineBase` methods for more details.
    """
        
    implements(IFCEngine)
    
    def __init__(self, service):
        assert IEngineBase.providedBy(service), \
            "IEngineBase is not provided by" + repr(service)
        self.service = service
        self.collectors = {}
    
    def remote_get_id(self):
        return self.service.id
    
    def remote_set_id(self, id):
        self.service.id = id
    
    def _checkProperties(self, result):
        dosync = self.service.properties.modified
        self.service.properties.modified = False
        return (dosync and pickle.dumps(self.service.properties, 2)), result
    
    def remote_execute(self, lines):
        d = self.service.execute(lines)
        d.addErrback(packageFailure)
        d.addCallback(self._checkProperties)
        d.addErrback(packageFailure)
        #d.addCallback(lambda r: log.msg("Got result: " + str(r)))
        return d
        
    #---------------------------------------------------------------------------
    # Old version of push
    #---------------------------------------------------------------------------
        
    def remote_push(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            return self.service.push(namespace).addErrback(packageFailure)
    
    #---------------------------------------------------------------------------
    # pull
    #---------------------------------------------------------------------------     
    
    def remote_pull(self, keys):
        d = self.service.pull(keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(packageFailure)
        return d
    
    #---------------------------------------------------------------------------
    # push/pullFuction
    #---------------------------------------------------------------------------
    
    def remote_push_function(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            # The usage of globals() here is an attempt to bind any pickled functions
            # to the globals of this module.  What we really want is to have it bound
            # to the globals of the callers module.  This will require walking the 
            # stack.  BG 10/3/07.
            namespace = uncanDict(namespace, globals())
            return self.service.push_function(namespace).addErrback(packageFailure)
    
    def remote_pull_function(self, keys):
        d = self.service.pull_function(keys)
        if len(keys)>1:
            d.addCallback(canSequence)
        elif len(keys)==1:
            d.addCallback(can)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(packageFailure)
        return d

    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def remote_get_result(self, i=None):
        return self.service.get_result(i).addErrback(packageFailure)
    
    def remote_reset(self):
        return self.service.reset().addErrback(packageFailure)
    
    def remote_kill(self):
        return self.service.kill().addErrback(packageFailure)
    
    def remote_keys(self):
        return self.service.keys().addErrback(packageFailure)
    
    #---------------------------------------------------------------------------
    # push/pull_serialized
    #---------------------------------------------------------------------------
    
    def remote_push_serialized(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            d = self.service.push_serialized(namespace)
            return d.addErrback(packageFailure)
    
    def remote_pull_serialized(self, keys):
        d = self.service.pull_serialized(keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(packageFailure)
        return d
    
    #---------------------------------------------------------------------------
    # Properties interface
    #---------------------------------------------------------------------------
    
    def remote_set_properties(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            return self.service.set_properties(namespace).addErrback(packageFailure)
    
    def remote_get_properties(self, keys=None):
        d = self.service.get_properties(keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(packageFailure)
        return d
    
    def remote_has_properties(self, keys):
        d = self.service.has_properties(keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(packageFailure)
        return d
    
    def remote_del_properties(self, keys):
        d = self.service.del_properties(keys)
        d.addErrback(packageFailure)
        return d
    
    def remote_clear_properties(self):
        d = self.service.clear_properties()
        d.addErrback(packageFailure)
        return d
    

components.registerAdapter(FCEngineReferenceFromService,
                           IEngineBase,
                           IFCEngine)


#-------------------------------------------------------------------------------
# Now the server (Controller) side of things
#-------------------------------------------------------------------------------

class EngineFromReference(object):
    """Adapt a `RemoteReference` to an `IEngineBase` implementing object.
    
    When an engine connects to a controller, it calls the `register_engine`
    method of the controller and passes the controller a `RemoteReference` to
    itself.  This class is used to adapt this `RemoteReference` to an object
    that implements the full `IEngineBase` interface.
    
    See the documentation of `IEngineBase` for details on the methods.
    """
    
    implements(IEngineBase)
    
    def __init__(self, reference):
        self.reference = reference
        self._id = None
        self._properties = StrictDict()
        self.currentCommand = None
    
    def callRemote(self, *args, **kwargs):
        try:
            return self.reference.callRemote(*args, **kwargs)
        except DeadReferenceError:
            self.notifier()
            self.stopNotifying(self.notifier)
            return defer.fail()
    
    def get_id(self):
        """Return the Engines id."""
        return self._id
    
    def set_id(self, id):
        """Set the Engines id."""
        self._id = id
        return self.callRemote('set_id', id)
    
    id = property(get_id, set_id)
    
    def syncProperties(self, r):
        try:
            psync, result = r
        except (ValueError, TypeError):
            return r
        else:
            if psync:
                log.msg("sync properties")
                pick = self.checkReturnForFailure(psync)
                if isinstance(pick, failure.Failure):
                    self.properties = pick
                    return pick
                else:
                    self.properties = pickle.loads(pick)
            return result
    
    def _set_properties(self, dikt):
        self._properties.clear()
        self._properties.update(dikt)
    
    def _get_properties(self):
        if isinstance(self._properties, failure.Failure):
            self._properties.raiseException()
        return self._properties
    
    properties = property(_get_properties, _set_properties)
    
    #---------------------------------------------------------------------------
    # Methods from IEngine
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # execute
    #---------------------------------------------------------------------------
    
    def execute(self, lines):
        # self._needProperties = True
        d = self.callRemote('execute', lines)
        d.addCallback(self.syncProperties)
        return d.addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # push
    #---------------------------------------------------------------------------
    
    def push(self, namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('push', package)
                return d.addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # pull
    #---------------------------------------------------------------------------
    
    def pull(self, keys):
        d = self.callRemote('pull', keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    #---------------------------------------------------------------------------
    # push/pull_function
    #---------------------------------------------------------------------------
    
    def push_function(self, namespace):
        try:
            package = pickle.dumps(canDict(namespace), 2)
        except:
            return defer.fail(failure.Failure())
        else:
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('push_function', package)
                return d.addCallback(self.checkReturnForFailure)    
    
    def pull_function(self, keys):
        d = self.callRemote('pull_function', keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        # The usage of globals() here is an attempt to bind any pickled functions
        # to the globals of this module.  What we really want is to have it bound
        # to the globals of the callers module.  This will require walking the 
        # stack.  BG 10/3/07.
        if len(keys)==1:
            d.addCallback(uncan, globals())
        elif len(keys)>1:
            d.addCallback(uncanSequence, globals())            
        return d
    
    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def get_result(self, i=None):
        return self.callRemote('get_result', i).addCallback(self.checkReturnForFailure)
    
    def reset(self):
        self._refreshProperties = True
        d = self.callRemote('reset')
        d.addCallback(self.syncProperties)
        return d.addCallback(self.checkReturnForFailure)
    
    def kill(self):
        #this will raise pb.PBConnectionLost on success
        d = self.callRemote('kill')
        d.addCallback(self.syncProperties)
        d.addCallback(self.checkReturnForFailure)
        d.addErrback(self.killBack)
        return d
    
    def killBack(self, f):
        log.msg('filling engine: %s' % f)
        return None
    
    def keys(self):
        return self.callRemote('keys').addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # Properties methods
    #---------------------------------------------------------------------------
    
    def set_properties(self, properties):
        try:
            package = pickle.dumps(properties, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('set_properties', package)
                return d.addCallback(self.checkReturnForFailure)
        return d
    
    def get_properties(self, keys=None):
        d = self.callRemote('get_properties', keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def has_properties(self, keys):
        d = self.callRemote('has_properties', keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def del_properties(self, keys):
        d = self.callRemote('del_properties', keys)
        d.addCallback(self.checkReturnForFailure)
        # d.addCallback(pickle.loads)
        return d
    
    def clear_properties(self):
        d = self.callRemote('clear_properties')
        d.addCallback(self.checkReturnForFailure)
        return d
    
    #---------------------------------------------------------------------------
    # push/pull_serialized
    #---------------------------------------------------------------------------
    
    def push_serialized(self, namespace):
        """Older version of pushSerialize."""
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('push_serialized', package)
                return d.addCallback(self.checkReturnForFailure)
    
    def pull_serialized(self, keys):
        d = self.callRemote('pull_serialized', keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    #---------------------------------------------------------------------------
    # Misc
    #---------------------------------------------------------------------------
     
    def checkReturnForFailure(self, r):
        """See if a returned value is a pickled Failure object.
        
        To distinguish between general pickled objects and pickled Failures, the
        other side should prepend the string FAILURE: to any pickled Failure.
        """
        return unpackageFailure(r)
    

components.registerAdapter(EngineFromReference,
    RemoteReference,
    IEngineBase)


#-------------------------------------------------------------------------------
# Now adapt an IControllerBase to incoming FC connections
#-------------------------------------------------------------------------------


class IFCControllerBase(Interface):
    """
    Interface that tells how an Engine sees a Controller.
    
    In our architecture, the Controller listens for Engines to connect
    and register.  This interface defines that registration method as it is 
    exposed over the Foolscap network protocol
    """
    
    def remote_register_engine(self, engineReference, id=None, pid=None, pproperties=None):
        """
        Register new engine on the controller.
        
        Engines must call this upon connecting to the controller if they
        want to do work for the controller.
        
        See the documentation of `IControllerCore` for more details.
        """
    

class FCRemoteEngineRefFromService(Referenceable):
    """
    Adapt an `IControllerBase` to an `IFCControllerBase`.
    """
    
    implements(IFCControllerBase)
    
    def __init__(self, service):
        assert IControllerBase.providedBy(service), \
            "IControllerBase is not provided by " + repr(service)
        self.service = service
    
    def remote_register_engine(self, engine_reference, id=None, pid=None, pproperties=None):
        # First adapt the engine_reference to a basic non-queued engine
        engine = IEngineBase(engine_reference)
        if pproperties:
            engine.properties = pickle.loads(pproperties)
        # Make it an IQueuedEngine before registration
        remote_engine = IEngineQueued(engine)
        # Get the ip/port of the remote side
        peer_address = engine_reference.tracker.broker.transport.getPeer()
        ip = peer_address.host
        port = peer_address.port
        reg_dict = self.service.register_engine(remote_engine, id, ip, port, pid)
        # Now setup callback for disconnect and unregistering the engine
        def notify(*args):
            return self.service.unregister_engine(reg_dict['id'])
        engine_reference.tracker.broker.notifyOnDisconnect(notify)
        
        engine.notifier = notify
        engine.stopNotifying = engine_reference.tracker.broker.dontNotifyOnDisconnect
        
        return reg_dict


components.registerAdapter(FCRemoteEngineRefFromService,
                        IControllerBase,
                        IFCControllerBase)

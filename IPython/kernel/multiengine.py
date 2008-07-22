# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_multiengine -*-

"""Adapt the IPython ControllerServer to IMultiEngine.

This module provides classes that adapt a ControllerService to the 
IMultiEngine interface.  This interface is a basic interactive interface
for working with a set of engines where it is desired to have explicit 
access to each registered engine.  

The classes here are exposed to the network in files like:

* multienginevanilla.py
* multienginepb.py
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

from new import instancemethod
from types import FunctionType

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, components, failure
from zope.interface import Interface, implements, Attribute

from IPython.tools import growl
from IPython.kernel.util import printer
from IPython.kernel.twistedutil import gatherBoth
from IPython.kernel import map as Map
from IPython.kernel import error
from IPython.kernel.pendingdeferred import PendingDeferredManager, two_phase
from IPython.kernel.controllerservice import \
    ControllerAdapterBase, \
    ControllerService, \
    IControllerBase


#-------------------------------------------------------------------------------
# Interfaces for the MultiEngine representation of a controller
#-------------------------------------------------------------------------------

class IEngineMultiplexer(Interface):
    """Interface to multiple engines implementing IEngineCore/Serialized/Queued.
    
    This class simply acts as a multiplexer of methods that are in the 
    various IEngines* interfaces.  Thus the methods here are jut like those 
    in the IEngine* interfaces, but with an extra first argument, targets.  
    The targets argument can have the following forms:
    
    * targets = 10            # Engines are indexed by ints
    * targets = [0,1,2,3]     # A list of ints
    * targets = 'all'         # A string to indicate all targets
    
    If targets is bad in any way, an InvalidEngineID will be raised.  This
    includes engines not being registered.
    
    All IEngineMultiplexer multiplexer methods must return a Deferred to a list 
    with length equal to the number of targets.  The elements of the list will 
    correspond to the return of the corresponding IEngine method.
    
    Failures are aggressive, meaning that if an action fails for any target, 
    the overall action will fail immediately with that Failure.
    
    :Parameters:
        targets : int, list of ints, or 'all'
            Engine ids the action will apply to.
    
    :Returns: Deferred to a list of results for each engine.
    
    :Exception:
        InvalidEngineID
            If the targets argument is bad or engines aren't registered.
        NoEnginesRegistered
            If there are no engines registered and targets='all'
    """
        
    #---------------------------------------------------------------------------
    # Mutiplexed methods
    #---------------------------------------------------------------------------
     
    def execute(lines, targets='all'):
        """Execute lines of Python code on targets.
              
        See the class docstring for information about targets and possible
        exceptions this method can raise.
              
        :Parameters:
            lines : str
                String of python code to be executed on targets.
        """
            
    def push(namespace, targets='all'):
        """Push dict namespace into the user's namespace on targets.
        
        See the class docstring for information about targets and possible
        exceptions this method can raise.
        
        :Parameters:
            namspace : dict
                Dict of key value pairs to be put into the users namspace.
        """
        
    def pull(keys, targets='all'):
        """Pull values out of the user's namespace on targets by keys.
        
        See the class docstring for information about targets and possible
        exceptions this method can raise.
        
        :Parameters:
            keys : tuple of strings
                Sequence of keys to be pulled from user's namespace.
        """
          
    def push_function(namespace, targets='all'):
        """"""
        
    def pull_function(keys, targets='all'):
        """"""
                
    def get_result(i=None, targets='all'):
        """Get the result for command i from targets.
        
        See the class docstring for information about targets and possible
        exceptions this method can raise.
        
        :Parameters:
            i : int or None
                Command index or None to indicate most recent command.                
        """
        
    def reset(targets='all'):
        """Reset targets.
        
        This clears the users namespace of the Engines, but won't cause
        modules to be reloaded.
        """
        
    def keys(targets='all'):
        """Get variable names defined in user's namespace on targets."""
        
    def kill(controller=False, targets='all'):
        """Kill the targets Engines and possibly the controller.
        
        :Parameters:
            controller : boolean
                Should the controller be killed as well.  If so all the 
                engines will be killed first no matter what targets is.
        """
        
    def push_serialized(namespace, targets='all'):
        """Push a namespace of Serialized objects to targets.
        
        :Parameters:
            namespace : dict
                A dict whose keys are the variable names and whose values
                are serialized version of the objects.
        """
        
    def pull_serialized(keys, targets='all'):
        """Pull Serialized objects by keys from targets.
        
        :Parameters:
            keys : tuple of strings
                Sequence of variable names to pull as serialized objects.
        """
        
    def clear_queue(targets='all'):
        """Clear the queue of pending command for targets."""
        
    def queue_status(targets='all'):
        """Get the status of the queue on the targets."""
    
    def set_properties(properties, targets='all'):
        """set properties by key and value"""
    
    def get_properties(keys=None, targets='all'):
        """get a list of properties by `keys`, if no keys specified, get all"""
    
    def del_properties(keys, targets='all'):
        """delete properties by `keys`"""
    
    def has_properties(keys, targets='all'):
        """get a list of bool values for whether `properties` has `keys`"""
    
    def clear_properties(targets='all'):
        """clear the properties dict"""


class IMultiEngine(IEngineMultiplexer):
    """A controller that exposes an explicit interface to all of its engines.
    
    This is the primary inteface for interactive usage.
    """
    
    def get_ids():
        """Return list of currently registered ids.
                
        :Returns:  A Deferred to a list of registered engine ids.
        """



#-------------------------------------------------------------------------------
# Implementation of the core MultiEngine classes
#-------------------------------------------------------------------------------

class MultiEngine(ControllerAdapterBase):
    """The representation of a ControllerService as a IMultiEngine.
    
    Although it is not implemented currently, this class would be where a
    client/notification API is implemented.  It could inherit from something
    like results.NotifierParent and then use the notify method to send
    notifications.
    """
    
    implements(IMultiEngine)
    
    def __init(self, controller):
        ControllerAdapterBase.__init__(self, controller)
    
    #---------------------------------------------------------------------------
    # Helper methods
    #---------------------------------------------------------------------------
    
    def engineList(self, targets):
        """Parse the targets argument into a list of valid engine objects.
        
        :Parameters:
            targets : int, list of ints or 'all'
                The targets argument to be parsed.
                
        :Returns: List of engine objects.
        
        :Exception:
            InvalidEngineID
                If targets is not valid or if an engine is not registered.
        """
        if isinstance(targets, int):
            if targets not in self.engines.keys():
                log.msg("Engine with id %i is not registered" % targets)
                raise error.InvalidEngineID("Engine with id %i is not registered" % targets)
            else: 
                return [self.engines[targets]]
        elif isinstance(targets, (list, tuple)):
            for id in targets:
                if id not in self.engines.keys():
                    log.msg("Engine with id %r is not registered" % id)
                    raise error.InvalidEngineID("Engine with id %r is not registered" % id)  
            return map(self.engines.get, targets)
        elif targets == 'all':
            eList = self.engines.values()
            if len(eList) == 0:
                msg = """There are no engines registered.
                     Check the logs in ~/.ipython/log if you think there should have been."""
                raise error.NoEnginesRegistered(msg)
            else:
                return eList
        else:
            raise error.InvalidEngineID("targets argument is not an int, list of ints or 'all': %r"%targets)
    
    def _performOnEngines(self, methodName, *args, **kwargs):
        """Calls a method on engines and returns deferred to list of results.
        
        :Parameters:
            methodName : str
                Name of the method to be called.
            targets : int, list of ints, 'all'
                The targets argument to be parsed into a list of engine objects.
            args
                The positional keyword arguments to be passed to the engines.
            kwargs
                The keyword arguments passed to the method
                
        :Returns: List of deferreds to the results on each engine
        
        :Exception:
            InvalidEngineID
                If the targets argument is bad in any way.
            AttributeError
                If the method doesn't exist on one of the engines.
        """
        targets = kwargs.pop('targets')
        log.msg("Performing %s on %r" % (methodName, targets))
        # log.msg("Performing %s(%r, %r) on %r" % (methodName, args, kwargs, targets))
        # This will and should raise if targets is not valid!
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            meth = getattr(e, methodName, None)
            if meth is not None:
                dList.append(meth(*args, **kwargs))
            else:
                raise AttributeError("Engine %i does not have method %s" % (e.id, methodName))
        return dList
        
    def _performOnEnginesAndGatherBoth(self, methodName, *args, **kwargs):
        """Called _performOnEngines and wraps result/exception into deferred."""
        try:
            dList = self._performOnEngines(methodName, *args, **kwargs)
        except (error.InvalidEngineID, AttributeError, KeyError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())
        else:
            # Having fireOnOneErrback is causing problems with the determinacy
            # of the system.  Basically, once a single engine has errbacked, this
            # method returns.  In some cases, this will cause client to submit
            # another command.  Because the previous command is still running
            # on some engines, this command will be queued.  When those commands
            # then errback, the second command will raise QueueCleared.  Ahhh!
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, methodName)
            return d
              
    #---------------------------------------------------------------------------
    # General IMultiEngine methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        return defer.succeed(self.engines.keys())
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer methods
    #---------------------------------------------------------------------------
        
    def execute(self, lines, targets='all'):
        return self._performOnEnginesAndGatherBoth('execute', lines, targets=targets)
    
    def push(self, ns, targets='all'):
        return self._performOnEnginesAndGatherBoth('push', ns, targets=targets)
        
    def pull(self, keys, targets='all'):
        return self._performOnEnginesAndGatherBoth('pull', keys, targets=targets)
    
    def push_function(self, ns, targets='all'):
        return self._performOnEnginesAndGatherBoth('push_function', ns, targets=targets)
        
    def pull_function(self, keys, targets='all'):
        return self._performOnEnginesAndGatherBoth('pull_function', keys, targets=targets)
    
    def get_result(self, i=None, targets='all'):
        return self._performOnEnginesAndGatherBoth('get_result', i, targets=targets)
    
    def reset(self, targets='all'):
        return self._performOnEnginesAndGatherBoth('reset', targets=targets)
    
    def keys(self, targets='all'):
        return self._performOnEnginesAndGatherBoth('keys', targets=targets)
    
    def kill(self, controller=False, targets='all'):
        if controller:
            targets = 'all'
        d = self._performOnEnginesAndGatherBoth('kill', targets=targets)
        if controller:
            log.msg("Killing controller")
            d.addCallback(lambda _: reactor.callLater(2.0, reactor.stop))
            # Consume any weird stuff coming back
            d.addBoth(lambda _: None)
        return d
    
    def push_serialized(self, namespace, targets='all'):
        for k, v in namespace.iteritems():
            log.msg("Pushed object %s is %f MB" % (k, v.getDataSize()))
        d = self._performOnEnginesAndGatherBoth('push_serialized', namespace, targets=targets)      
        return d
        
    def pull_serialized(self, keys, targets='all'):
        try:
            dList = self._performOnEngines('pull_serialized', keys, targets=targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())
        else:
            for d in dList:
                d.addCallback(self._logSizes)
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'pull_serialized')
            return d  
                              
    def _logSizes(self, listOfSerialized):
        if isinstance(listOfSerialized, (list, tuple)):
            for s in listOfSerialized:
                log.msg("Pulled object is %f MB" % s.getDataSize())
        else:
            log.msg("Pulled object is %f MB" % listOfSerialized.getDataSize())
        return listOfSerialized
    
    def clear_queue(self, targets='all'):
        return self._performOnEnginesAndGatherBoth('clear_queue', targets=targets)         
    
    def queue_status(self, targets='all'):
        log.msg("Getting queue status on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = []
            for e in engines:
                dList.append(e.queue_status().addCallback(lambda s:(e.id, s)))
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'queue_status')
            return d 
    
    def get_properties(self, keys=None, targets='all'):
        log.msg("Getting properties on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = [e.get_properties(keys) for e in engines]
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'get_properties')
            return d
    
    def set_properties(self, properties, targets='all'):
        log.msg("Setting properties on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = [e.set_properties(properties) for e in engines]
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'set_properties')
            return d
    
    def has_properties(self, keys, targets='all'):
        log.msg("Checking properties on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = [e.has_properties(keys) for e in engines]
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'has_properties')
            return d
    
    def del_properties(self, keys, targets='all'):
        log.msg("Deleting properties on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = [e.del_properties(keys) for e in engines]
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'del_properties')
            return d
    
    def clear_properties(self, targets='all'):
        log.msg("Clearing properties on %r" % targets)
        try:
            engines = self.engineList(targets)
        except (error.InvalidEngineID, AttributeError, error.NoEnginesRegistered):
            return defer.fail(failure.Failure())            
        else:
            dList = [e.clear_properties() for e in engines]
            d = gatherBoth(dList, 
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            d.addCallback(error.collect_exceptions, 'clear_properties')
            return d


components.registerAdapter(MultiEngine,
                           IControllerBase, 
                           IMultiEngine)


#-------------------------------------------------------------------------------
# Interfaces for the Synchronous MultiEngine
#-------------------------------------------------------------------------------

class ISynchronousEngineMultiplexer(Interface):
    pass


class ISynchronousMultiEngine(ISynchronousEngineMultiplexer):
    """Synchronous, two-phase version of IMultiEngine.
    
    Methods in this interface are identical to those of IMultiEngine, but they
    take one additional argument:
    
    execute(lines, targets='all') -> execute(lines, targets='all, block=True)
    
    :Parameters:
        block : boolean
            Should the method return a deferred to a deferredID or the 
            actual result.  If block=False a deferred to a deferredID is 
            returned and the user must call `get_pending_deferred` at a later
            point.  If block=True, a deferred to the actual result comes back.
    """
    def get_pending_deferred(deferredID, block=True):
        """"""
    
    def clear_pending_deferreds():
        """"""


#-------------------------------------------------------------------------------
# Implementation of the Synchronous MultiEngine
#-------------------------------------------------------------------------------

class SynchronousMultiEngine(PendingDeferredManager):
    """Adapt an `IMultiEngine` -> `ISynchronousMultiEngine`
    
    Warning, this class uses a decorator that currently uses **kwargs.  
    Because of this block must be passed as a kwarg, not positionally.
    """
    
    implements(ISynchronousMultiEngine)
    
    def __init__(self, multiengine):
        self.multiengine = multiengine
        PendingDeferredManager.__init__(self)
    
    #---------------------------------------------------------------------------
    # Decorated pending deferred methods
    #---------------------------------------------------------------------------
    
    @two_phase
    def execute(self, lines, targets='all'):
        d = self.multiengine.execute(lines, targets)
        return d
    
    @two_phase
    def push(self, namespace, targets='all'):
        return self.multiengine.push(namespace, targets)
    
    @two_phase
    def pull(self, keys, targets='all'):
        d = self.multiengine.pull(keys, targets)
        return d
    
    @two_phase
    def push_function(self, namespace, targets='all'):
        return self.multiengine.push_function(namespace, targets)
    
    @two_phase
    def pull_function(self, keys, targets='all'):
        d = self.multiengine.pull_function(keys, targets)
        return d
    
    @two_phase
    def get_result(self, i=None, targets='all'):
        return self.multiengine.get_result(i, targets='all')
    
    @two_phase
    def reset(self, targets='all'):
        return self.multiengine.reset(targets)
    
    @two_phase
    def keys(self, targets='all'):
        return self.multiengine.keys(targets)
    
    @two_phase
    def kill(self, controller=False, targets='all'):
        return self.multiengine.kill(controller, targets)
    
    @two_phase
    def push_serialized(self, namespace, targets='all'):
        return self.multiengine.push_serialized(namespace, targets)
    
    @two_phase
    def pull_serialized(self, keys, targets='all'):
        return self.multiengine.pull_serialized(keys, targets)
    
    @two_phase
    def clear_queue(self, targets='all'):
        return self.multiengine.clear_queue(targets)
    
    @two_phase
    def queue_status(self, targets='all'):
        return self.multiengine.queue_status(targets)
    
    @two_phase
    def set_properties(self, properties, targets='all'):
        return self.multiengine.set_properties(properties, targets)
    
    @two_phase
    def get_properties(self, keys=None, targets='all'):
        return self.multiengine.get_properties(keys, targets)
    
    @two_phase
    def has_properties(self, keys, targets='all'):
        return self.multiengine.has_properties(keys, targets)
    
    @two_phase
    def del_properties(self, keys, targets='all'):
        return self.multiengine.del_properties(keys, targets)
    
    @two_phase
    def clear_properties(self, targets='all'):
        return self.multiengine.clear_properties(targets)
    
    #---------------------------------------------------------------------------
    # IMultiEngine methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        """Return a list of registered engine ids.
        
        Never use the two phase block/non-block stuff for this.
        """
        return self.multiengine.get_ids()


components.registerAdapter(SynchronousMultiEngine, IMultiEngine, ISynchronousMultiEngine)


#-------------------------------------------------------------------------------
# Various high-level interfaces that can be used as MultiEngine mix-ins
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# IMultiEngineCoordinator
#-------------------------------------------------------------------------------

class IMultiEngineCoordinator(Interface):
    """Methods that work on multiple engines explicitly."""
       
    def scatter(key, seq, dist='b', flatten=False, targets='all'):
        """Partition and distribute a sequence to targets."""
        
    def gather(key, dist='b', targets='all'):
        """Gather object key from targets."""
    
    def raw_map(func, seqs, dist='b', targets='all'):
        """
        A parallelized version of Python's builtin `map` function.
        
        This has a slightly different syntax than the builtin `map`.
        This is needed because we need to have keyword arguments and thus
        can't use *args to capture all the sequences.  Instead, they must
        be passed in a list or tuple.
        
        The equivalence is:
        
        raw_map(func, seqs) -> map(func, seqs[0], seqs[1], ...)
        
        Most users will want to use parallel functions or the `mapper`
        and `map` methods for an API that follows that of the builtin
        `map`.
        """


class ISynchronousMultiEngineCoordinator(IMultiEngineCoordinator):
    """Methods that work on multiple engines explicitly."""

    def scatter(key, seq, dist='b', flatten=False, targets='all', block=True):
        """Partition and distribute a sequence to targets."""
        
    def gather(key, dist='b', targets='all', block=True):
        """Gather object key from targets"""
    
    def raw_map(func, seqs, dist='b', targets='all', block=True):
        """
        A parallelized version of Python's builtin map.
        
        This has a slightly different syntax than the builtin `map`.
        This is needed because we need to have keyword arguments and thus
        can't use *args to capture all the sequences.  Instead, they must
        be passed in a list or tuple.
        
        raw_map(func, seqs) -> map(func, seqs[0], seqs[1], ...)
        
        Most users will want to use parallel functions or the `mapper`
        and `map` methods for an API that follows that of the builtin
        `map`.
        """


#-------------------------------------------------------------------------------
# IMultiEngineExtras
#-------------------------------------------------------------------------------

class IMultiEngineExtras(Interface):
    
    def zip_pull(targets, keys):
        """
        Pull, but return results in a different format from `pull`.
        
        This method basically returns zip(pull(targets, *keys)), with a few 
        edge cases handled differently.  Users of chainsaw will find this format 
        familiar.
        """
    
    def run(targets, fname):
        """Run a .py file on targets."""


class ISynchronousMultiEngineExtras(IMultiEngineExtras):
    def zip_pull(targets, keys, block=True):
        """
        Pull, but return results in a different format from `pull`.
        
        This method basically returns zip(pull(targets, *keys)), with a few 
        edge cases handled differently.  Users of chainsaw will find this format 
        familiar.
        """
    
    def run(targets, fname, block=True):
        """Run a .py file on targets."""

#-------------------------------------------------------------------------------
# The full MultiEngine interface
#-------------------------------------------------------------------------------

class IFullMultiEngine(IMultiEngine, 
    IMultiEngineCoordinator, 
    IMultiEngineExtras):
    pass


class IFullSynchronousMultiEngine(ISynchronousMultiEngine, 
    ISynchronousMultiEngineCoordinator,
    ISynchronousMultiEngineExtras):
    pass


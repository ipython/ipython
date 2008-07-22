# encoding: utf-8

"""
Expose the multiengine controller over the Foolscap network protocol.
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

import cPickle as pickle
from types import FunctionType

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure, log

from foolscap import Referenceable

from IPython.kernel import error 
from IPython.kernel.util import printer
from IPython.kernel import map as Map
from IPython.kernel.parallelfunction import ParallelFunction
from IPython.kernel.mapper import (
    MultiEngineMapper, 
    IMultiEngineMapperFactory,
    IMapper
)
from IPython.kernel.twistedutil import gatherBoth
from IPython.kernel.multiengine import (MultiEngine,
    IMultiEngine,
    IFullSynchronousMultiEngine,
    ISynchronousMultiEngine)
from IPython.kernel.multiengineclient import wrapResultList
from IPython.kernel.pendingdeferred import PendingDeferredManager
from IPython.kernel.pickleutil import (can, canDict,
    canSequence, uncan, uncanDict, uncanSequence)

from IPython.kernel.clientinterfaces import (
    IFCClientInterfaceProvider, 
    IBlockingClientAdaptor
)

# Needed to access the true globals from __main__.__dict__ 
import __main__

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

def packageResult(wrappedMethod):
    
    def wrappedPackageResult(self, *args, **kwargs):
        d = wrappedMethod(self, *args, **kwargs)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    return wrappedPackageResult


class IFCSynchronousMultiEngine(Interface):
    """Foolscap interface to `ISynchronousMultiEngine`.  
    
    The methods in this interface are similar to those of 
    `ISynchronousMultiEngine`, but their arguments and return values are pickled
    if they are not already simple Python types that can be send over XML-RPC.
    
    See the documentation of `ISynchronousMultiEngine` and `IMultiEngine` for 
    documentation about the methods.
    
    Most methods in this interface act like the `ISynchronousMultiEngine`
    versions and can be called in blocking or non-blocking mode.
    """
    pass


class FCSynchronousMultiEngineFromMultiEngine(Referenceable):
    """Adapt `IMultiEngine` -> `ISynchronousMultiEngine` -> `IFCSynchronousMultiEngine`.
    """
    
    implements(IFCSynchronousMultiEngine, IFCClientInterfaceProvider)
    
    addSlash = True
    
    def __init__(self, multiengine):
        # Adapt the raw multiengine to `ISynchronousMultiEngine` before saving
        # it.  This allow this class to do two adaptation steps.
        self.smultiengine = ISynchronousMultiEngine(multiengine)
        self._deferredIDCallbacks = {}
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageFailure(self, f):
        f.cleanFailure()
        return self.packageSuccess(f)
    
    def packageSuccess(self, obj):
        serial = pickle.dumps(obj, 2)
        return serial
    
    #---------------------------------------------------------------------------
    # Things related to PendingDeferredManager
    #---------------------------------------------------------------------------
    
    @packageResult
    def remote_get_pending_deferred(self, deferredID, block):
        d = self.smultiengine.get_pending_deferred(deferredID, block)
        try:
            callback = self._deferredIDCallbacks.pop(deferredID)
        except KeyError:
            callback = None
        if callback is not None:
            d.addCallback(callback[0], *callback[1], **callback[2])
        return d
       
    @packageResult
    def remote_clear_pending_deferreds(self):
        return defer.maybeDeferred(self.smultiengine.clear_pending_deferreds)
    
    def _addDeferredIDCallback(self, did, callback, *args, **kwargs):
        self._deferredIDCallbacks[did] = (callback, args, kwargs)
        return did
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    @packageResult
    def remote_execute(self, lines, targets, block):
        return self.smultiengine.execute(lines, targets=targets, block=block)
    
    @packageResult    
    def remote_push(self, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push(namespace, targets=targets, block=block)
        return d
    
    @packageResult
    def remote_pull(self, keys, targets, block):
        d = self.smultiengine.pull(keys, targets=targets, block=block)
        return d
    
    @packageResult    
    def remote_push_function(self, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS)
        except:
            d = defer.fail(failure.Failure())
        else:
            namespace = uncanDict(namespace)
            d = self.smultiengine.push_function(namespace, targets=targets, block=block)
        return d
    
    def _canMultipleKeys(self, result):
        return [canSequence(r) for r in result]
    
    @packageResult
    def remote_pull_function(self, keys, targets, block):
        def can_functions(r, keys):
            if len(keys)==1 or isinstance(keys, str):
                result = canSequence(r)
            elif len(keys)>1:
                result = [canSequence(s) for s in r]
            return result
        d = self.smultiengine.pull_function(keys, targets=targets, block=block)
        if block:
            d.addCallback(can_functions, keys)
        else:
            d.addCallback(lambda did: self._addDeferredIDCallback(did, can_functions, keys))
        return d
    
    @packageResult    
    def remote_push_serialized(self, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push_serialized(namespace, targets=targets, block=block)
        return d
    
    @packageResult
    def remote_pull_serialized(self, keys, targets, block):
        d = self.smultiengine.pull_serialized(keys, targets=targets, block=block)
        return d
    
    @packageResult
    def remote_get_result(self, i, targets, block):
        if i == 'None':
            i = None
        return self.smultiengine.get_result(i, targets=targets, block=block)
    
    @packageResult
    def remote_reset(self, targets, block):
        return self.smultiengine.reset(targets=targets, block=block)
    
    @packageResult
    def remote_keys(self, targets, block):
        return self.smultiengine.keys(targets=targets, block=block)
    
    @packageResult
    def remote_kill(self, controller, targets, block):
        return self.smultiengine.kill(controller, targets=targets, block=block)
    
    @packageResult
    def remote_clear_queue(self, targets, block):
        return self.smultiengine.clear_queue(targets=targets, block=block)
    
    @packageResult
    def remote_queue_status(self, targets, block):
        return self.smultiengine.queue_status(targets=targets, block=block)
    
    @packageResult
    def remote_set_properties(self, binaryNS, targets, block):
        try:
            ns = pickle.loads(binaryNS)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.set_properties(ns, targets=targets, block=block)
        return d
    
    @packageResult
    def remote_get_properties(self, keys, targets, block):
        if keys=='None':
            keys=None
        return self.smultiengine.get_properties(keys, targets=targets, block=block)
    
    @packageResult
    def remote_has_properties(self, keys, targets, block):
        return self.smultiengine.has_properties(keys, targets=targets, block=block)
    
    @packageResult
    def remote_del_properties(self, keys, targets, block):
        return self.smultiengine.del_properties(keys, targets=targets, block=block)
    
    @packageResult
    def remote_clear_properties(self, targets, block):
        return self.smultiengine.clear_properties(targets=targets, block=block)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def remote_get_ids(self):
        """Get the ids of the registered engines.
        
        This method always blocks.
        """
        return self.smultiengine.get_ids()
    
    #---------------------------------------------------------------------------
    # IFCClientInterfaceProvider related methods
    #---------------------------------------------------------------------------
    
    def remote_get_client_name(self):
        return 'IPython.kernel.multienginefc.FCFullSynchronousMultiEngineClient'


# The __init__ method of `FCMultiEngineFromMultiEngine` first adapts the
# `IMultiEngine` to `ISynchronousMultiEngine` so this is actually doing a
# two phase adaptation.
components.registerAdapter(FCSynchronousMultiEngineFromMultiEngine,
            IMultiEngine, IFCSynchronousMultiEngine)


#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------


class FCFullSynchronousMultiEngineClient(object):
    
    implements(
        IFullSynchronousMultiEngine, 
        IBlockingClientAdaptor,
        IMultiEngineMapperFactory,
        IMapper
    )
    
    def __init__(self, remote_reference):
        self.remote_reference = remote_reference
        self._deferredIDCallbacks = {}
        # This class manages some pending deferreds through this instance.  This
        # is required for methods like gather/scatter as it enables us to
        # create our own pending deferreds for composite operations.
        self.pdm = PendingDeferredManager()
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
                 
    def unpackage(self, r):
        return pickle.loads(r)
    
    #---------------------------------------------------------------------------
    # Things related to PendingDeferredManager
    #---------------------------------------------------------------------------
    
    def get_pending_deferred(self, deferredID, block=True):
        
        # Because we are managing some pending deferreds locally (through
        # self.pdm) and some remotely (on the controller), we first try the 
        # local one and then the remote one.
        if self.pdm.quick_has_id(deferredID):
            d = self.pdm.get_pending_deferred(deferredID, block)
            return d
        else:
            d = self.remote_reference.callRemote('get_pending_deferred', deferredID, block)
            d.addCallback(self.unpackage)
            try:
                callback = self._deferredIDCallbacks.pop(deferredID)
            except KeyError:
                callback = None
            if callback is not None:
                d.addCallback(callback[0], *callback[1], **callback[2])
            return d
    
    def clear_pending_deferreds(self):
        
        # This clear both the local (self.pdm) and remote pending deferreds
        self.pdm.clear_pending_deferreds()
        d2 = self.remote_reference.callRemote('clear_pending_deferreds')
        d2.addCallback(self.unpackage)
        return d2
    
    def _addDeferredIDCallback(self, did, callback, *args, **kwargs):
        self._deferredIDCallbacks[did] = (callback, args, kwargs)
        return did
       
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, lines, targets='all', block=True):
        d = self.remote_reference.callRemote('execute', lines, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def push(self, namespace, targets='all', block=True):
        serial = pickle.dumps(namespace, 2)
        d =  self.remote_reference.callRemote('push', serial, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull(self, keys, targets='all', block=True):
        d = self.remote_reference.callRemote('pull', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def push_function(self, namespace, targets='all', block=True):
        cannedNamespace = canDict(namespace)
        serial = pickle.dumps(cannedNamespace, 2)
        d = self.remote_reference.callRemote('push_function', serial, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull_function(self, keys, targets='all', block=True):
        def uncan_functions(r, keys):
            if len(keys)==1 or isinstance(keys, str):
                return uncanSequence(r)
            elif len(keys)>1:
                return [uncanSequence(s) for s in r]
        d = self.remote_reference.callRemote('pull_function', keys, targets, block)
        if block:
            d.addCallback(self.unpackage)
            d.addCallback(uncan_functions, keys)
        else:
            d.addCallback(self.unpackage)
            d.addCallback(lambda did: self._addDeferredIDCallback(did, uncan_functions, keys))
        return d
    
    def push_serialized(self, namespace, targets='all', block=True):
        cannedNamespace = canDict(namespace)
        serial = pickle.dumps(cannedNamespace, 2)
        d =  self.remote_reference.callRemote('push_serialized', serial, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull_serialized(self, keys, targets='all', block=True):
        d = self.remote_reference.callRemote('pull_serialized', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
        
    def get_result(self, i=None, targets='all', block=True):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        d = self.remote_reference.callRemote('get_result', i, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def reset(self, targets='all', block=True):
        d = self.remote_reference.callRemote('reset', targets, block)
        d.addCallback(self.unpackage)
        return d        
    
    def keys(self, targets='all', block=True):
        d = self.remote_reference.callRemote('keys', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def kill(self, controller=False, targets='all', block=True):
        d = self.remote_reference.callRemote('kill', controller, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def clear_queue(self, targets='all', block=True):
        d = self.remote_reference.callRemote('clear_queue', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def queue_status(self, targets='all', block=True):
        d = self.remote_reference.callRemote('queue_status', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def set_properties(self, properties, targets='all', block=True):
        serial = pickle.dumps(properties, 2)
        d = self.remote_reference.callRemote('set_properties', serial, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def get_properties(self, keys=None, targets='all', block=True):
        if keys==None:
            keys='None'
        d = self.remote_reference.callRemote('get_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def has_properties(self, keys, targets='all', block=True):
        d = self.remote_reference.callRemote('has_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def del_properties(self, keys, targets='all', block=True):
        d = self.remote_reference.callRemote('del_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def clear_properties(self, targets='all', block=True):
        d = self.remote_reference.callRemote('clear_properties', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        d = self.remote_reference.callRemote('get_ids')
        return d
    
    #---------------------------------------------------------------------------
    # ISynchronousMultiEngineCoordinator related methods
    #---------------------------------------------------------------------------

    def _process_targets(self, targets):
        def create_targets(ids):
            if isinstance(targets, int):
                engines = [targets]
            elif targets=='all':
                engines = ids
            elif isinstance(targets, (list, tuple)):
                engines = targets
            for t in engines:
                if not t in ids:
                    raise error.InvalidEngineID("engine with id %r does not exist"%t)
            return engines
        
        d = self.get_ids()
        d.addCallback(create_targets)
        return d
    
    def scatter(self, key, seq, dist='b', flatten=False, targets='all', block=True):
        
        # Note: scatter and gather handle pending deferreds locally through self.pdm.
        # This enables us to collect a bunch fo deferred ids and make a secondary 
        # deferred id that corresponds to the entire group.  This logic is extremely
        # difficult to get right though.
        def do_scatter(engines):
            nEngines = len(engines)
            mapClass = Map.dists[dist]
            mapObject = mapClass()
            d_list = []
            # Loop through and push to each engine in non-blocking mode.
            # This returns a set of deferreds to deferred_ids
            for index, engineid in enumerate(engines):
                partition = mapObject.getPartition(seq, index, nEngines)
                if flatten and len(partition) == 1:
                    d = self.push({key: partition[0]}, targets=engineid, block=False)
                else:
                    d = self.push({key: partition}, targets=engineid, block=False)
                d_list.append(d)
            # Collect the deferred to deferred_ids
            d = gatherBoth(d_list,
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            # Now d has a list of deferred_ids or Failures coming
            d.addCallback(error.collect_exceptions, 'scatter')
            def process_did_list(did_list):
                """Turn a list of deferred_ids into a final result or failure."""
                new_d_list = [self.get_pending_deferred(did, True) for did in did_list]
                final_d = gatherBoth(new_d_list,
                                     fireOnOneErrback=0,
                                     consumeErrors=1,
                                     logErrors=0)
                final_d.addCallback(error.collect_exceptions, 'scatter')
                final_d.addCallback(lambda lop: [i[0] for i in lop])
                return final_d
            # Now, depending on block, we need to handle the list deferred_ids
            # coming down the pipe diferently.
            if block:
                # If we are blocking register a callback that will transform the
                # list of deferred_ids into the final result.
                d.addCallback(process_did_list)
                return d
            else:
                # Here we are going to use a _local_ PendingDeferredManager.
                deferred_id = self.pdm.get_deferred_id()
                # This is the deferred we will return to the user that will fire
                # with the local deferred_id AFTER we have received the list of 
                # primary deferred_ids
                d_to_return = defer.Deferred()
                def do_it(did_list):
                    """Produce a deferred to the final result, but first fire the
                    deferred we will return to the user that has the local
                    deferred id."""
                    d_to_return.callback(deferred_id)
                    return process_did_list(did_list)
                d.addCallback(do_it)
                # Now save the deferred to the final result
                self.pdm.save_pending_deferred(d, deferred_id)
                return d_to_return

        d = self._process_targets(targets)
        d.addCallback(do_scatter)
        return d

    def gather(self, key, dist='b', targets='all', block=True):
        
        # Note: scatter and gather handle pending deferreds locally through self.pdm.
        # This enables us to collect a bunch fo deferred ids and make a secondary 
        # deferred id that corresponds to the entire group.  This logic is extremely
        # difficult to get right though.
        def do_gather(engines):
            nEngines = len(engines)
            mapClass = Map.dists[dist]
            mapObject = mapClass()
            d_list = []
            # Loop through and push to each engine in non-blocking mode.
            # This returns a set of deferreds to deferred_ids
            for index, engineid in enumerate(engines):
                d = self.pull(key, targets=engineid, block=False)
                d_list.append(d)
            # Collect the deferred to deferred_ids
            d = gatherBoth(d_list,
                           fireOnOneErrback=0,
                           consumeErrors=1,
                           logErrors=0)
            # Now d has a list of deferred_ids or Failures coming
            d.addCallback(error.collect_exceptions, 'scatter')
            def process_did_list(did_list):
                """Turn a list of deferred_ids into a final result or failure."""
                new_d_list = [self.get_pending_deferred(did, True) for did in did_list]
                final_d = gatherBoth(new_d_list,
                                     fireOnOneErrback=0,
                                     consumeErrors=1,
                                     logErrors=0)
                final_d.addCallback(error.collect_exceptions, 'gather')
                final_d.addCallback(lambda lop: [i[0] for i in lop])
                final_d.addCallback(mapObject.joinPartitions)
                return final_d
            # Now, depending on block, we need to handle the list deferred_ids
            # coming down the pipe diferently.
            if block:
                # If we are blocking register a callback that will transform the
                # list of deferred_ids into the final result.
                d.addCallback(process_did_list)
                return d
            else:
                # Here we are going to use a _local_ PendingDeferredManager.
                deferred_id = self.pdm.get_deferred_id()
                # This is the deferred we will return to the user that will fire
                # with the local deferred_id AFTER we have received the list of 
                # primary deferred_ids
                d_to_return = defer.Deferred()
                def do_it(did_list):
                    """Produce a deferred to the final result, but first fire the
                    deferred we will return to the user that has the local
                    deferred id."""
                    d_to_return.callback(deferred_id)
                    return process_did_list(did_list)
                d.addCallback(do_it)
                # Now save the deferred to the final result
                self.pdm.save_pending_deferred(d, deferred_id)
                return d_to_return

        d = self._process_targets(targets)
        d.addCallback(do_gather)
        return d

    def raw_map(self, func, sequences, dist='b', targets='all', block=True):
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
        if not isinstance(sequences, (list, tuple)):
            raise TypeError('sequences must be a list or tuple')
        max_len = max(len(s) for s in sequences)
        for s in sequences:
            if len(s)!=max_len:
                raise ValueError('all sequences must have equal length')
        if isinstance(func, FunctionType):
            d = self.push_function(dict(_ipython_map_func=func), targets=targets, block=False)
            d.addCallback(lambda did: self.get_pending_deferred(did, True))
            sourceToRun = '_ipython_map_seq_result = map(_ipython_map_func, *zip(*_ipython_map_seq))'
        elif isinstance(func, str):
            d = defer.succeed(None)
            sourceToRun = \
                '_ipython_map_seq_result = map(%s, *zip(*_ipython_map_seq))' % func
        else:
            raise TypeError("func must be a function or str")
        
        d.addCallback(lambda _: self.scatter('_ipython_map_seq', zip(*sequences), dist, targets=targets))
        d.addCallback(lambda _: self.execute(sourceToRun, targets=targets, block=False))
        d.addCallback(lambda did: self.get_pending_deferred(did, True))
        d.addCallback(lambda _: self.gather('_ipython_map_seq_result', dist, targets=targets, block=block))
        return d

    def map(self, func, *sequences):
        """
        A parallel version of Python's builtin `map` function.
        
        This method applies a function to sequences of arguments.  It 
        follows the same syntax as the builtin `map`.
        
        This method creates a mapper objects by calling `self.mapper` with
        no arguments and then uses that mapper to do the mapping.  See
        the documentation of `mapper` for more details.
        """
        return self.mapper().map(func, *sequences)
    
    def mapper(self, dist='b', targets='all', block=True):
        """
        Create a mapper object that has a `map` method.
        
        This method returns an object that implements the `IMapper` 
        interface.  This method is a factory that is used to control how 
        the map happens.
        
        :Parameters:
            dist : str
                What decomposition to use, 'b' is the only one supported
                currently
            targets : str, int, sequence of ints
                Which engines to use for the map
            block : boolean
                Should calls to `map` block or not
        """
        return MultiEngineMapper(self, dist, targets, block)

    def parallel(self, dist='b', targets='all', block=True):
        """
        A decorator that turns a function into a parallel function.
        
        This can be used as:
        
        @parallel()
        def f(x, y)
            ...
        
        f(range(10), range(10))
        
        This causes f(0,0), f(1,1), ... to be called in parallel.
        
        :Parameters:
            dist : str
                What decomposition to use, 'b' is the only one supported
                currently
            targets : str, int, sequence of ints
                Which engines to use for the map
            block : boolean
                Should calls to `map` block or not
        """
        mapper = self.mapper(dist, targets, block)
        pf = ParallelFunction(mapper)
        return pf
    
    #---------------------------------------------------------------------------
    # ISynchronousMultiEngineExtras related methods
    #---------------------------------------------------------------------------
    
    def _transformPullResult(self, pushResult, multitargets, lenKeys):
        if not multitargets:
            result = pushResult[0]
        elif lenKeys > 1:
            result = zip(*pushResult)
        elif lenKeys is 1:
            result = list(pushResult)
        return result
    
    def zip_pull(self, keys, targets='all', block=True):
        multitargets = not isinstance(targets, int) and len(targets) > 1
        lenKeys = len(keys)
        d = self.pull(keys, targets=targets, block=block)
        if block:
            d.addCallback(self._transformPullResult, multitargets, lenKeys)
        else:
            d.addCallback(lambda did: self._addDeferredIDCallback(did, self._transformPullResult, multitargets, lenKeys))
        return d
    
    def run(self, fname, targets='all', block=True):
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        try:
            code = compile(source,fname,'exec')
        except:
            return defer.fail(failure.Failure()) 
        # Now run the code
        d = self.execute(source, targets=targets, block=block)
        return d
    
    #---------------------------------------------------------------------------
    # IBlockingClientAdaptor related methods
    #---------------------------------------------------------------------------
    
    def adapt_to_blocking_client(self):
        from IPython.kernel.multiengineclient import IFullBlockingMultiEngineClient
        return IFullBlockingMultiEngineClient(self)

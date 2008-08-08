# encoding: utf-8
# -*- test-case-name: IPython.kernel.tests.test_engineservice -*-

"""A Twisted Service Representation of the IPython core.

The IPython Core exposed to the network is called the Engine.  Its
representation in Twisted in the EngineService.  Interfaces and adapters
are used to abstract out the details of the actual network protocol used.
The EngineService is an Engine that knows nothing about the actual protocol
used.

The EngineService is exposed with various network protocols in modules like:

enginepb.py
enginevanilla.py

As of 12/12/06 the classes in this module have been simplified greatly.  It was 
felt that we had over-engineered things.  To improve the maintainability of the
code we have taken out the ICompleteEngine interface and the completeEngine
method that automatically added methods to engines.

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

import os, sys, copy
import cPickle as pickle
from new import instancemethod

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, failure, components
import zope.interface as zi

from IPython.kernel.core.interpreter import Interpreter
from IPython.kernel import newserialized, error, util
from IPython.kernel.util import printer
from IPython.kernel.twistedutil import gatherBoth, DeferredList
from IPython.kernel import codeutil


#-------------------------------------------------------------------------------
# Interface specification for the Engine
#-------------------------------------------------------------------------------

class IEngineCore(zi.Interface):
    """The minimal required interface for the IPython Engine.
    
    This interface provides a formal specification of the IPython core.
    All these methods should return deferreds regardless of what side of a
    network connection they are on.
    
    In general, this class simply wraps a shell class and wraps its return
    values as Deferred objects.  If the underlying shell class method raises
    an exception, this class should convert it to a twisted.failure.Failure
    that will be propagated along the Deferred's errback chain.
    
    In addition, Failures are aggressive.  By this, we mean that if a method
    is performing multiple actions (like pulling multiple object) if any
    single one fails, the entire method will fail with that Failure.  It is
    all or nothing. 
    """
    
    id = zi.interface.Attribute("the id of the Engine object")
    properties = zi.interface.Attribute("A dict of properties of the Engine")
    
    def execute(lines):
        """Execute lines of Python code.
        
        Returns a dictionary with keys (id, number, stdin, stdout, stderr)
        upon success.
        
        Returns a failure object if the execution of lines raises an exception.
        """
    
    def push(namespace):
        """Push dict namespace into the user's namespace.
        
        Returns a deferred to None or a failure.
        """
    
    def pull(keys):
        """Pulls values out of the user's namespace by keys.
        
        Returns a deferred to a tuple objects or a single object.
        
        Raises NameError if any one of objects doess not exist.
        """
    
    def push_function(namespace):
        """Push a dict of key, function pairs into the user's namespace.
        
        Returns a deferred to None or a failure."""
    
    def pull_function(keys):
        """Pulls functions out of the user's namespace by keys.
        
        Returns a deferred to a tuple of functions or a single function.
        
        Raises NameError if any one of the functions does not exist.
        """
    
    def get_result(i=None):
        """Get the stdin/stdout/stderr of command i.
        
        Returns a deferred to a dict with keys
        (id, number, stdin, stdout, stderr).
        
        Raises IndexError if command i does not exist.
        Raises TypeError if i in not an int.
        """
    
    def reset():
        """Reset the shell.
        
        This clears the users namespace.  Won't cause modules to be
        reloaded.  Should also re-initialize certain variables like id.
        """
    
    def kill():
        """Kill the engine by stopping the reactor."""
    
    def keys():
        """Return the top level variables in the users namspace.
        
        Returns a deferred to a dict."""
    

class IEngineSerialized(zi.Interface):
    """Push/Pull methods that take Serialized objects.  
    
    All methods should return deferreds.
    """
    
    def push_serialized(namespace):
        """Push a dict of keys and Serialized objects into the user's namespace."""
    
    def pull_serialized(keys):
        """Pull objects by key from the user's namespace as Serialized.
        
        Returns a list of or one Serialized.
        
        Raises NameError is any one of the objects does not exist.
        """
    

class IEngineProperties(zi.Interface):
    """Methods for access to the properties object of an Engine"""
    
    properties = zi.Attribute("A StrictDict object, containing the properties")
    
    def set_properties(properties):
        """set properties by key and value"""
    
    def get_properties(keys=None):
        """get a list of properties by `keys`, if no keys specified, get all"""
    
    def del_properties(keys):
        """delete properties by `keys`"""
    
    def has_properties(keys):
        """get a list of bool values for whether `properties` has `keys`"""

    def clear_properties():
        """clear the properties dict"""
    
class IEngineBase(IEngineCore, IEngineSerialized, IEngineProperties):
    """The basic engine interface that EngineService will implement.
    
    This exists so it is easy to specify adapters that adapt to and from the
    API that the basic EngineService implements.
    """
    pass

class IEngineQueued(IEngineBase):
    """Interface for adding a queue to an IEngineBase.  
    
    This interface extends the IEngineBase interface to add methods for managing
    the engine's queue.  The implicit details of this interface are that the 
    execution of all methods declared in IEngineBase should appropriately be
    put through a queue before execution. 
    
    All methods should return deferreds.
    """
    
    def clear_queue():
        """Clear the queue."""
    
    def queue_status():
        """Get the queued and pending commands in the queue."""
    
    def register_failure_observer(obs):
        """Register an observer of pending Failures.
        
        The observer must implement IFailureObserver.
        """
    
    def unregister_failure_observer(obs):
        """Unregister an observer of pending Failures."""
    

class IEngineThreaded(zi.Interface):
    """A place holder for threaded commands.  
    
    All methods should return deferreds.
    """
    pass


#-------------------------------------------------------------------------------
# Functions and classes to implement the EngineService
#-------------------------------------------------------------------------------


class StrictDict(dict):
    """This is a strict copying dictionary for use as the interface to the 
    properties of an Engine.

    :IMPORTANT:
        This object copies the values you set to it, and returns copies to you
        when you request them.  The only way to change properties os explicitly
        through the setitem and getitem of the dictionary interface.

    Example:
        >>> e = get_engine(id)
        >>> L = [1,2,3]
        >>> e.properties['L'] = L
        >>> L == e.properties['L']
        True
        >>> L.append(99)
        >>> L == e.properties['L']
        False
        
        Note that getitem copies, so calls to methods of objects do not affect
        the properties, as seen here:
        
        >>> e.properties[1] = range(2)
        >>> print e.properties[1]
        [0, 1]
        >>> e.properties[1].append(2)
        >>> print e.properties[1]
        [0, 1]
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.modified = True
    
    def __getitem__(self, key):
        return copy.deepcopy(dict.__getitem__(self, key))
    
    def __setitem__(self, key, value):
        # check if this entry is valid for transport around the network
        # and copying
        try:
            pickle.dumps(key, 2)
            pickle.dumps(value, 2)
            newvalue = copy.deepcopy(value)
        except:
            raise error.InvalidProperty(value)
        dict.__setitem__(self, key, newvalue)
        self.modified = True
    
    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.modified = True
    
    def update(self, dikt):
        for k,v in dikt.iteritems():
            self[k] = v
    
    def pop(self, key):
        self.modified = True
        return dict.pop(self, key)
    
    def popitem(self):
        self.modified = True
        return dict.popitem(self)
    
    def clear(self):
        self.modified = True
        dict.clear(self)
    
    def subDict(self, *keys):
        d = {}
        for key in keys:
            d[key] = self[key]
        return d
    


class EngineAPI(object):
    """This is the object through which the user can edit the `properties`
    attribute of an Engine.
    The Engine Properties object copies all object in and out of itself.
    See the EngineProperties object for details.
    """
    _fix=False
    def __init__(self, id):
        self.id = id
        self.properties = StrictDict()
        self._fix=True
    
    def __setattr__(self, k,v):
        if self._fix:
            raise error.KernelError("I am protected!")
        else:
            object.__setattr__(self, k, v)
    
    def __delattr__(self, key):
        raise error.KernelError("I am protected!")
    

_apiDict = {}

def get_engine(id):
    """Get the Engine API object, whcih currently just provides the properties 
    object, by ID"""
    global _apiDict
    if not _apiDict.get(id):
        _apiDict[id] = EngineAPI(id)
    return _apiDict[id]

def drop_engine(id):
    """remove an engine"""
    global _apiDict
    if _apiDict.has_key(id):
        del _apiDict[id]

class EngineService(object, service.Service):
    """Adapt a IPython shell into a IEngine implementing Twisted Service."""
    
    zi.implements(IEngineBase)
    name = 'EngineService'
    
    def __init__(self, shellClass=Interpreter, mpi=None):
        """Create an EngineService.
        
        shellClass: something that implements IInterpreter or core1
        mpi:        an mpi module that has rank and size attributes
        """
        self.shellClass = shellClass
        self.shell = self.shellClass()
        self.mpi = mpi
        self.id = None
        self.properties = get_engine(self.id).properties
        if self.mpi is not None:
            log.msg("MPI started with rank = %i and size = %i" % 
                (self.mpi.rank, self.mpi.size))
            self.id = self.mpi.rank
        self._seedNamespace()
    
    # Make id a property so that the shell can get the updated id
        
    def _setID(self, id):
        self._id = id
        self.properties = get_engine(id).properties
        self.shell.push({'id': id})
    
    def _getID(self):
        return self._id
    
    id = property(_getID, _setID)
    
    def _seedNamespace(self):
        self.shell.push({'mpi': self.mpi, 'id' : self.id})
    
    def executeAndRaise(self, msg, callable, *args, **kwargs):
        """Call a method of self.shell and wrap any exception."""
        d = defer.Deferred()
        try:
            result = callable(*args, **kwargs)
        except:
            # This gives the following:
            # et=exception class
            # ev=exception class instance
            # tb=traceback object
            et,ev,tb = sys.exc_info()
            # This call adds attributes to the exception value
            et,ev,tb = self.shell.formatTraceback(et,ev,tb,msg)
            # Add another attribute
            ev._ipython_engine_info = msg
            f = failure.Failure(ev,et,None)
            d.errback(f)
        else:
            d.callback(result)
            
        return d
    
    
    # The IEngine methods.  See the interface for documentation.
    
    def execute(self, lines):
        msg = {'engineid':self.id,
               'method':'execute',
               'args':[lines]}
        d = self.executeAndRaise(msg, self.shell.execute, lines)
        d.addCallback(self.addIDToResult)
        return d
    
    def addIDToResult(self, result):
        result['id'] = self.id
        return result
    
    def push(self, namespace):
        msg = {'engineid':self.id,
               'method':'push',
               'args':[repr(namespace.keys())]}
        d = self.executeAndRaise(msg, self.shell.push, namespace)
        return d
    
    def pull(self, keys):
        msg = {'engineid':self.id,
               'method':'pull',
               'args':[repr(keys)]}
        d = self.executeAndRaise(msg, self.shell.pull, keys)
        return d
    
    def push_function(self, namespace):
        msg = {'engineid':self.id,
               'method':'push_function',
               'args':[repr(namespace.keys())]}
        d = self.executeAndRaise(msg, self.shell.push_function, namespace)
        return d
    
    def pull_function(self, keys):
        msg = {'engineid':self.id,
               'method':'pull_function',
               'args':[repr(keys)]}
        d = self.executeAndRaise(msg, self.shell.pull_function, keys)
        return d
    
    def get_result(self, i=None):
        msg = {'engineid':self.id,
               'method':'get_result',
               'args':[repr(i)]}
        d = self.executeAndRaise(msg, self.shell.getCommand, i)
        d.addCallback(self.addIDToResult)
        return d
    
    def reset(self):
        msg = {'engineid':self.id,
               'method':'reset',
               'args':[]}
        del self.shell
        self.shell = self.shellClass()
        self.properties.clear()
        d = self.executeAndRaise(msg, self._seedNamespace)
        return d
    
    def kill(self):
        drop_engine(self.id)
        try:
            reactor.stop()
        except RuntimeError:
            log.msg('The reactor was not running apparently.')
            return defer.fail()
        else:
            return defer.succeed(None)
    
    def keys(self):
        """Return a list of variables names in the users top level namespace.
        
        This used to return a dict of all the keys/repr(values) in the 
        user's namespace.  This was too much info for the ControllerService
        to handle so it is now just a list of keys.
        """
        
        remotes = []
        for k in self.shell.user_ns.iterkeys():
            if k not in ['__name__', '_ih', '_oh', '__builtins__',
                         'In', 'Out', '_', '__', '___', '__IP', 'input', 'raw_input']:
                remotes.append(k)
        return defer.succeed(remotes)
    
    def set_properties(self, properties):
        msg = {'engineid':self.id,
               'method':'set_properties',
               'args':[repr(properties.keys())]}
        return self.executeAndRaise(msg, self.properties.update, properties)
    
    def get_properties(self, keys=None):
        msg = {'engineid':self.id,
               'method':'get_properties',
               'args':[repr(keys)]}
        if keys is None:
            keys = self.properties.keys()
        return self.executeAndRaise(msg, self.properties.subDict, *keys)
    
    def _doDel(self, keys):
        for key in keys:
            del self.properties[key]
    
    def del_properties(self, keys):
        msg = {'engineid':self.id,
               'method':'del_properties',
               'args':[repr(keys)]}
        return self.executeAndRaise(msg, self._doDel, keys)
    
    def _doHas(self, keys):
        return [self.properties.has_key(key) for key in keys]
    
    def has_properties(self, keys):
        msg = {'engineid':self.id,
               'method':'has_properties',
               'args':[repr(keys)]}
        return self.executeAndRaise(msg, self._doHas, keys)
    
    def clear_properties(self):
        msg = {'engineid':self.id,
               'method':'clear_properties',
               'args':[]}
        return self.executeAndRaise(msg, self.properties.clear)
    
    def push_serialized(self, sNamespace):
        msg = {'engineid':self.id,
               'method':'push_serialized',
               'args':[repr(sNamespace.keys())]}       
        ns = {}
        for k,v in sNamespace.iteritems():
            try:
                unserialized = newserialized.IUnSerialized(v)
                ns[k] = unserialized.getObject()
            except:
                return defer.fail()
        return self.executeAndRaise(msg, self.shell.push, ns)
    
    def pull_serialized(self, keys):
        msg = {'engineid':self.id,
               'method':'pull_serialized',
               'args':[repr(keys)]}
        if isinstance(keys, str):
            keys = [keys]
        if len(keys)==1:
            d = self.executeAndRaise(msg, self.shell.pull, keys)
            d.addCallback(newserialized.serialize)
            return d
        elif len(keys)>1:
            d = self.executeAndRaise(msg, self.shell.pull, keys)         
            @d.addCallback
            def packThemUp(values):
                serials = []
                for v in values:
                    try:
                        serials.append(newserialized.serialize(v))
                    except:
                        return defer.fail(failure.Failure())
                return serials
            return packThemUp


def queue(methodToQueue):
    def queuedMethod(this, *args, **kwargs):
        name = methodToQueue.__name__
        return this.submitCommand(Command(name, *args, **kwargs))
    return queuedMethod
    
class QueuedEngine(object):
    """Adapt an IEngineBase to an IEngineQueued by wrapping it.
    
    The resulting object will implement IEngineQueued which extends
    IEngineCore which extends (IEngineBase, IEngineSerialized). 
    
    This seems like the best way of handling it, but I am not sure.  The
    other option is to have the various base interfaces be used like
    mix-in intefaces.  The problem I have with this is adpatation is
    more difficult and complicated because there can be can multiple
    original and final Interfaces. 
    """
    
    zi.implements(IEngineQueued)
    
    def __init__(self, engine):
        """Create a QueuedEngine object from an engine
        
        engine:       An implementor of IEngineCore and IEngineSerialized
        keepUpToDate: whether to update the remote status when the 
                      queue is empty.  Defaults to False.
        """
        
        # This is the right way to do these tests rather than 
        # IEngineCore in list(zi.providedBy(engine)) which will only 
        # picks of the interfaces that are directly declared by engine.
        assert IEngineBase.providedBy(engine), \
            "engine passed to QueuedEngine doesn't provide IEngineBase"
            
        self.engine = engine
        self.id = engine.id
        self.queued = []
        self.history = {}
        self.engineStatus = {}
        self.currentCommand = None
        self.failureObservers = []
    
    def _get_properties(self):
        return self.engine.properties
    
    properties = property(_get_properties, lambda self, _: None)
    # Queue management methods.  You should not call these directly
    
    def submitCommand(self, cmd):
        """Submit command to queue."""
        
        d = defer.Deferred()
        cmd.setDeferred(d)
        if self.currentCommand is not None:
            if self.currentCommand.finished:
                # log.msg("Running command immediately: %r" % cmd)
                self.currentCommand = cmd
                self.runCurrentCommand()
            else:  # command is still running  
                # log.msg("Command is running: %r" % self.currentCommand)
                # log.msg("Queueing: %r" % cmd)
                self.queued.append(cmd)
        else:
            # log.msg("No current commands, running: %r" % cmd)
            self.currentCommand = cmd
            self.runCurrentCommand()
        return d
    
    def runCurrentCommand(self):
        """Run current command."""
        
        cmd = self.currentCommand
        f = getattr(self.engine, cmd.remoteMethod, None)
        if f:
            d = f(*cmd.args, **cmd.kwargs)
            if cmd.remoteMethod is 'execute':
                d.addCallback(self.saveResult)
            d.addCallback(self.finishCommand)
            d.addErrback(self.abortCommand)
        else:
            return defer.fail(AttributeError(cmd.remoteMethod))
    
    def _flushQueue(self):
        """Pop next command in queue and run it."""
        
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()
    
    def saveResult(self, result):
        """Put the result in the history."""
        self.history[result['number']] = result
        return result
    
    def finishCommand(self, result):
        """Finish currrent command."""
        
        # The order of these commands is absolutely critical.
        self.currentCommand.handleResult(result)
        self.currentCommand.finished = True
        self._flushQueue()
        return result
    
    def abortCommand(self, reason):
        """Abort current command.
        
        This eats the Failure but first passes it onto the Deferred that the 
        user has.
        
        It also clear out the queue so subsequence commands don't run.
        """

        # The order of these 3 commands is absolutely critical.  The currentCommand
        # must first be marked as finished BEFORE the queue is cleared and before
        # the current command is sent the failure.
        # Also, the queue must be cleared BEFORE the current command is sent the Failure
        # otherwise the errback chain could trigger new commands to be added to the 
        # queue before we clear it.  We should clear ONLY the commands that were in
        # the queue when the error occured. 
        self.currentCommand.finished = True
        s = "%r %r %r" % (self.currentCommand.remoteMethod, self.currentCommand.args, self.currentCommand.kwargs)
        self.clear_queue(msg=s)
        self.currentCommand.handleError(reason)
        
        return None
    
    #---------------------------------------------------------------------------
    # IEngineCore methods
    #---------------------------------------------------------------------------
    
    @queue
    def execute(self, lines):
        pass

    @queue
    def push(self, namespace):
        pass      
    
    @queue
    def pull(self, keys):
        pass
        
    @queue
    def push_function(self, namespace):
        pass      
    
    @queue
    def pull_function(self, keys):
        pass        

    def get_result(self, i=None):
        if i is None:
            i = max(self.history.keys()+[None])

        cmd = self.history.get(i, None)
        # Uncomment this line to disable chaching of results
        #cmd = None
        if cmd is None:
            return self.submitCommand(Command('get_result', i))
        else:
            return defer.succeed(cmd)
        
    def reset(self):
        self.clear_queue()
        self.history = {}  # reset the cache - I am not sure we should do this
        return self.submitCommand(Command('reset'))
    
    def kill(self):
        self.clear_queue()
        return self.submitCommand(Command('kill'))
    
    @queue
    def keys(self):
        pass
    
    #---------------------------------------------------------------------------
    # IEngineSerialized methods
    #---------------------------------------------------------------------------

    @queue
    def push_serialized(self, namespace):
        pass
        
    @queue
    def pull_serialized(self, keys):
        pass
    
    #---------------------------------------------------------------------------
    # IEngineProperties methods
    #---------------------------------------------------------------------------

    @queue
    def set_properties(self, namespace):
        pass
        
    @queue
    def get_properties(self, keys=None):
        pass
    
    @queue
    def del_properties(self, keys):
        pass
    
    @queue
    def has_properties(self, keys):
        pass
    
    @queue
    def clear_properties(self):
        pass
    
    #---------------------------------------------------------------------------
    # IQueuedEngine methods
    #---------------------------------------------------------------------------
    
    def clear_queue(self, msg=''):
        """Clear the queue, but doesn't cancel the currently running commmand."""
        
        for cmd in self.queued:
            cmd.deferred.errback(failure.Failure(error.QueueCleared(msg)))
        self.queued = []
        return defer.succeed(None)
    
    def queue_status(self):
        if self.currentCommand is not None:
            if self.currentCommand.finished:
                pending = repr(None)
            else:
                pending = repr(self.currentCommand)
        else:
            pending = repr(None)
        dikt = {'queue':map(repr,self.queued), 'pending':pending}
        return defer.succeed(dikt)
        
    def register_failure_observer(self, obs):
        self.failureObservers.append(obs)
    
    def unregister_failure_observer(self, obs):
        self.failureObservers.remove(obs)
    

# Now register QueuedEngine as an adpater class that makes an IEngineBase into a
# IEngineQueued.  
components.registerAdapter(QueuedEngine, IEngineBase, IEngineQueued)
    

class Command(object):
    """A command object that encapslates queued commands.
    
    This class basically keeps track of a command that has been queued
    in a QueuedEngine.  It manages the deferreds and hold the method to be called
    and the arguments to that method.
    """
    
    
    def __init__(self, remoteMethod, *args, **kwargs):
        """Build a new Command object."""
        
        self.remoteMethod = remoteMethod
        self.args = args
        self.kwargs = kwargs
        self.finished = False
    
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""  
          
        self.deferred = d
    
    def __repr__(self):
        if not self.args:
            args = ''
        else:
            args = str(self.args)[1:-2]  #cut off (...,)
        for k,v in self.kwargs.iteritems():
            if args:
                args += ', '
            args += '%s=%r' %(k,v)
        return "%s(%s)" %(self.remoteMethod, args)
    
    def handleResult(self, result):
        """When the result is ready, relay it to self.deferred."""
        
        self.deferred.callback(result)
    
    def handleError(self, reason):
        """When an error has occured, relay it to self.deferred."""
        
        self.deferred.errback(reason)

class ThreadedEngineService(EngineService):
    """An EngineService subclass that defers execute commands to a separate 
    thread.
    
    ThreadedEngineService uses twisted.internet.threads.deferToThread to 
    defer execute requests to a separate thread. GUI frontends may want to 
    use ThreadedEngineService as the engine in an 
    IPython.frontend.frontendbase.FrontEndBase subclass to prevent
    block execution from blocking the GUI thread.
    """
    
    zi.implements(IEngineBase)

    def __init__(self, shellClass=Interpreter, mpi=None):
        EngineService.__init__(self, shellClass, mpi)
    
    def wrapped_execute(self, msg, lines):
        """Wrap self.shell.execute to add extra information to tracebacks"""
        
        try:
            result = self.shell.execute(lines)
        except Exception,e:
            # This gives the following:
            # et=exception class
            # ev=exception class instance
            # tb=traceback object
            et,ev,tb = sys.exc_info()
            # This call adds attributes to the exception value
            et,ev,tb = self.shell.formatTraceback(et,ev,tb,msg)
            # Add another attribute
            
            # Create a new exception with the new attributes
            e = et(ev._ipython_traceback_text)
            e._ipython_engine_info = msg
            
            # Re-raise
            raise e
        
        return result
    
    
    def execute(self, lines):
        # Only import this if we are going to use this class
        from twisted.internet import threads
        
        msg = {'engineid':self.id,
               'method':'execute',
               'args':[lines]}
        
        d = threads.deferToThread(self.wrapped_execute, msg, lines)
        d.addCallback(self.addIDToResult)
        return d

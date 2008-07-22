# encoding: utf-8
# -*- test-case-name: IPython.kernel.tests.test_taskxmlrpc -*-
"""A Foolscap interface to a TaskController.

This class lets Foolscap clients talk to a TaskController.
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
import xmlrpclib, copy

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure

from foolscap import Referenceable

from IPython.kernel.twistedutil import blockingCallFromThread
from IPython.kernel import error, task as taskmodule, taskclient
from IPython.kernel.pickleutil import can, uncan
from IPython.kernel.clientinterfaces import (
    IFCClientInterfaceProvider, 
    IBlockingClientAdaptor
)
from IPython.kernel.mapper import (
    TaskMapper,
    ITaskMapperFactory,
    IMapper
)
from IPython.kernel.parallelfunction import (
    ParallelFunction, 
    ITaskParallelDecorator
)

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------


class IFCTaskController(Interface):
    """Foolscap interface to task controller.
        
    See the documentation of `ITaskController` for more information.
    """
    def remote_run(binTask):
        """"""
    
    def remote_abort(taskid):
        """"""
        
    def remote_get_task_result(taskid, block=False):
        """"""
        
    def remote_barrier(taskids):
        """"""
    
    def remote_spin():
        """"""
    
    def remote_queue_status(verbose):
        """"""
    
    def remote_clear():
        """"""


class FCTaskControllerFromTaskController(Referenceable):
    """
    Adapt a `TaskController` to an `IFCTaskController`
    
    This class is used to expose a `TaskController` over the wire using
    the Foolscap network protocol.
    """
    
    implements(IFCTaskController, IFCClientInterfaceProvider)
    
    def __init__(self, taskController):
        self.taskController = taskController
    
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
    # ITaskController related methods
    #---------------------------------------------------------------------------
    
    def remote_run(self, ptask):
        try:
            task = pickle.loads(ptask)
            task.uncan_task()
        except:
            d = defer.fail(pickle.UnpickleableError("Could not unmarshal task"))
        else:
            d = self.taskController.run(task)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_abort(self, taskid):
        d = self.taskController.abort(taskid)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_get_task_result(self, taskid, block=False):
        d = self.taskController.get_task_result(taskid, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_barrier(self, taskids):
        d = self.taskController.barrier(taskids)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d        
    
    def remote_spin(self):
        d = self.taskController.spin()
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d        
    
    def remote_queue_status(self, verbose):
        d = self.taskController.queue_status(verbose)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_clear(self):
        return self.taskController.clear()
    
    def remote_get_client_name(self):
        return 'IPython.kernel.taskfc.FCTaskClient'
    
components.registerAdapter(FCTaskControllerFromTaskController,
            taskmodule.ITaskController, IFCTaskController)


#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class FCTaskClient(object):
    """
    Client class for Foolscap exposed `TaskController`.
    
    This class is an adapter that makes a `RemoteReference` to a 
    `TaskController` look like an actual `ITaskController` on the client side.

    This class also implements `IBlockingClientAdaptor` so that clients can 
    automatically get a blocking version of this class.
    """
    
    implements(
        taskmodule.ITaskController, 
        IBlockingClientAdaptor,
        ITaskMapperFactory,
        IMapper,
        ITaskParallelDecorator
    )
    
    def __init__(self, remote_reference):
        self.remote_reference = remote_reference
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def unpackage(self, r):
        return pickle.loads(r)
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    def run(self, task):
        """Run a task on the `TaskController`.
        
        See the documentation of the `MapTask` and `StringTask` classes for 
        details on how to build a task of different types.
        
        :Parameters:
            task : an `ITask` implementer
        
        :Returns: The int taskid of the submitted task.  Pass this to 
            `get_task_result` to get the `TaskResult` object.
        """
        assert isinstance(task, taskmodule.BaseTask), "task must be a Task object!"
        task.can_task()
        ptask = pickle.dumps(task, 2)
        task.uncan_task()
        d = self.remote_reference.callRemote('run', ptask)
        d.addCallback(self.unpackage)
        return d
    
    def get_task_result(self, taskid, block=False):
        """
        Get a task result by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be retrieved.
            block : boolean
                Should I block until the task is done?
        
        :Returns: A `TaskResult` object that encapsulates the task result.
        """
        d = self.remote_reference.callRemote('get_task_result', taskid, block)
        d.addCallback(self.unpackage)
        return d 
    
    def abort(self, taskid):
        """
        Abort a task by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be aborted.
        """
        d = self.remote_reference.callRemote('abort', taskid)
        d.addCallback(self.unpackage)
        return d 
        
    def barrier(self, taskids):
        """Block until a set of tasks are completed.
        
        :Parameters:
            taskids : list, tuple
                A sequence of taskids to block on.
        """
        d = self.remote_reference.callRemote('barrier', taskids)
        d.addCallback(self.unpackage)
        return d 
    
    def spin(self):
        """
        Touch the scheduler, to resume scheduling without submitting a task.
        
        This method only needs to be called in unusual situations where the
        scheduler is idle for some reason.
        """
        d = self.remote_reference.callRemote('spin')
        d.addCallback(self.unpackage)
        return d
    
    def queue_status(self, verbose=False):
        """
        Get a dictionary with the current state of the task queue.
        
        :Parameters:
            verbose : boolean
                If True, return a list of taskids.  If False, simply give
                the number of tasks with each status.
        
        :Returns:
            A dict with the queue status.
        """
        d = self.remote_reference.callRemote('queue_status', verbose)
        d.addCallback(self.unpackage)
        return d
    
    def clear(self):
        """
        Clear all previously run tasks from the task controller.
        
        This is needed because the task controller keep all task results
        in memory.  This can be a problem is there are many completed
        tasks.  Users should call this periodically to clean out these
        cached task results.
        """
        d = self.remote_reference.callRemote('clear')
        return d
    
    def adapt_to_blocking_client(self):
        """
        Wrap self in a blocking version that implements `IBlockingTaskClient.
        """
        from IPython.kernel.taskclient import IBlockingTaskClient
        return IBlockingTaskClient(self)
    
    def map(self, func, *sequences):
        """
        Apply func to *sequences elementwise.  Like Python's builtin map.
        
        This version is load balanced.
        """
        return self.mapper().map(func, *sequences)
    
    def mapper(self, clear_before=False, clear_after=False, retries=0, 
                recovery_task=None, depend=None, block=True):
        """
        Create an `IMapper` implementer with a given set of arguments.
        
        The `IMapper` created using a task controller is load balanced.
        
        See the documentation for `IPython.kernel.task.BaseTask` for 
        documentation on the arguments to this method.
        """
        return TaskMapper(self, clear_before=clear_before, 
            clear_after=clear_after, retries=retries, 
            recovery_task=recovery_task, depend=depend, block=block)
    
    def parallel(self, clear_before=False, clear_after=False, retries=0, 
        recovery_task=None, depend=None, block=True):
        mapper = self.mapper(clear_before, clear_after, retries,
            recovery_task, depend, block)
        pf = ParallelFunction(mapper)
        return pf


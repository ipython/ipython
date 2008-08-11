# encoding: utf-8
# -*- test-case-name: IPython.kernel.tests.test_taskcontrollerxmlrpc -*-

"""
A blocking version of the task client.
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

from zope.interface import Interface, implements
from twisted.python import components, log

from IPython.kernel.twistedutil import blockingCallFromThread
from IPython.kernel import task, error
from IPython.kernel.mapper import (
    SynchronousTaskMapper,
    ITaskMapperFactory,
    IMapper
)
from IPython.kernel.parallelfunction import (
    ParallelFunction, 
    ITaskParallelDecorator
)

#-------------------------------------------------------------------------------
# The task client
#-------------------------------------------------------------------------------

class IBlockingTaskClient(Interface):
    """
    A vague interface of the blocking task client
    """
    pass

class BlockingTaskClient(object):
    """
    A blocking task client that adapts a non-blocking one.
    """
    
    implements(
        IBlockingTaskClient, 
        ITaskMapperFactory,
        IMapper,
        ITaskParallelDecorator
    )
    
    def __init__(self, task_controller):
        self.task_controller = task_controller
        self.block = True
        
    def run(self, task, block=False):
        """Run a task on the `TaskController`.
        
        See the documentation of the `MapTask` and `StringTask` classes for 
        details on how to build a task of different types.
        
        :Parameters:
            task : an `ITask` implementer
        
        :Returns: The int taskid of the submitted task.  Pass this to 
            `get_task_result` to get the `TaskResult` object.
        """
        tid = blockingCallFromThread(self.task_controller.run, task)
        if block:
            return self.get_task_result(tid, block=True)
        else:
            return tid
    
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
        return blockingCallFromThread(self.task_controller.get_task_result,
            taskid, block)
    
    def abort(self, taskid):
        """
        Abort a task by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be aborted.
        """
        return blockingCallFromThread(self.task_controller.abort, taskid)
    
    def barrier(self, taskids):
        """Block until a set of tasks are completed.
        
        :Parameters:
            taskids : list, tuple
                A sequence of taskids to block on.
        """
        return blockingCallFromThread(self.task_controller.barrier, taskids)
    
    def spin(self):
        """
        Touch the scheduler, to resume scheduling without submitting a task.
        
        This method only needs to be called in unusual situations where the
        scheduler is idle for some reason. 
        """
        return blockingCallFromThread(self.task_controller.spin)
    
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
        return blockingCallFromThread(self.task_controller.queue_status, verbose)
    
    def clear(self):
        """
        Clear all previously run tasks from the task controller.
        
        This is needed because the task controller keep all task results
        in memory.  This can be a problem is there are many completed
        tasks.  Users should call this periodically to clean out these
        cached task results.
        """
        return blockingCallFromThread(self.task_controller.clear)
    
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
        return SynchronousTaskMapper(self, clear_before=clear_before, 
            clear_after=clear_after, retries=retries, 
            recovery_task=recovery_task, depend=depend, block=block)
    
    def parallel(self, clear_before=False, clear_after=False, retries=0, 
        recovery_task=None, depend=None, block=True):
        mapper = self.mapper(clear_before, clear_after, retries,
            recovery_task, depend, block)
        pf = ParallelFunction(mapper)
        return pf

components.registerAdapter(BlockingTaskClient,
            task.ITaskController, IBlockingTaskClient)



# encoding: utf-8
# -*- test-case-name: IPython.kernel.tests.test_taskcontrollerxmlrpc -*-

"""The Generic Task Client object.  

This must be subclassed based on your connection method.
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

#-------------------------------------------------------------------------------
# Connecting Task Client
#-------------------------------------------------------------------------------

class InteractiveTaskClient(object):
    
    def irun(self, *args, **kwargs):
        """Run a task on the `TaskController`.
        
        This method is a shorthand for run(task) and its arguments are simply
        passed onto a `Task` object:
        
        irun(*args, **kwargs) -> run(Task(*args, **kwargs))

        :Parameters:
            expression : str
                A str that is valid python code that is the task.
            pull : str or list of str 
                The names of objects to be pulled as results.
            push : dict
                A dict of objects to be pushed into the engines namespace before
                execution of the expression.
            clear_before : boolean
                Should the engine's namespace be cleared before the task is run.
                Default=False.
            clear_after : boolean 
                Should the engine's namespace be cleared after the task is run.
                Default=False.
            retries : int
                The number of times to resumbit the task if it fails.  Default=0.
            options : dict
                Any other keyword options for more elaborate uses of tasks
            
        :Returns: A `TaskResult` object.      
        """
        block = kwargs.pop('block', False)
        if len(args) == 1 and isinstance(args[0], task.Task):
            t = args[0]
        else:
            t = task.Task(*args, **kwargs)
        taskid = self.run(t)
        print "TaskID = %i"%taskid
        if block:
            return self.get_task_result(taskid, block)
        else:
            return taskid

class IBlockingTaskClient(Interface):
    """
    An interface for blocking task clients.
    """
    pass


class BlockingTaskClient(InteractiveTaskClient):
    """
    This class provides a blocking task client.
    """
    
    implements(IBlockingTaskClient)
    
    def __init__(self, task_controller):
        self.task_controller = task_controller
        self.block = True
        
    def run(self, task):
        """
        Run a task and return a task id that can be used to get the task result.
        
        :Parameters:
            task : `Task`
                The `Task` object to run
        """
        return blockingCallFromThread(self.task_controller.run, task)
    
    def get_task_result(self, taskid, block=False):
        """
        Get or poll for a task result.
        
        :Parameters:
            taskid : int
                The id of the task whose result to get
            block : boolean
                If True, wait until the task is done and then result the
                `TaskResult` object.  If False, just poll for the result and
                return None if the task is not done.
        """
        return blockingCallFromThread(self.task_controller.get_task_result,
            taskid, block)
    
    def abort(self, taskid):
        """
        Abort a task by task id if it has not been started.
        """
        return blockingCallFromThread(self.task_controller.abort, taskid)
    
    def barrier(self, taskids):
        """
        Wait for a set of tasks to finish.
        
        :Parameters:
            taskids : list of ints
                A list of task ids to wait for.
        """
        return blockingCallFromThread(self.task_controller.barrier, taskids)
    
    def spin(self):
        """
        Cause the scheduler to schedule tasks.
        
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


components.registerAdapter(BlockingTaskClient,
            task.ITaskController, IBlockingTaskClient)



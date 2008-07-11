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

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------


class IFCTaskController(Interface):
    """Foolscap interface to task controller.
        
    See the documentation of ITaskController for documentation about the methods.
    """
    def remote_run(request, binTask):
        """"""
    
    def remote_abort(request, taskid):
        """"""
        
    def remote_get_task_result(request, taskid, block=False):
        """"""
        
    def remote_barrier(request, taskids):
        """"""
    
    def remote_spin(request):
        """"""
    
    def remote_queue_status(request, verbose):
        """"""


class FCTaskControllerFromTaskController(Referenceable):
    """XML-RPC attachmeot for controller.
        
    See IXMLRPCTaskController and ITaskController (and its children) for documentation. 
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
            ctask = pickle.loads(ptask)
            task = taskmodule.uncan_task(ctask)
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
    
    def remote_get_client_name(self):
        return 'IPython.kernel.taskfc.FCTaskClient'
    
components.registerAdapter(FCTaskControllerFromTaskController,
            taskmodule.ITaskController, IFCTaskController)


#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class FCTaskClient(object):
    """XML-RPC based TaskController client that implements ITaskController.
        
    :Parameters:
        addr : (ip, port)
            The ip (str) and port (int) tuple of the `TaskController`.  
    """
    implements(taskmodule.ITaskController, IBlockingClientAdaptor)
    
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
        
        :Parameters:
            task : a `Task` object
        
        The Task object is created using the following signature:
        
        Task(expression, pull=None, push={}, clear_before=False, 
            clear_after=False, retries=0, **options):)
        
        The meaning of the arguments is as follows:
        
        :Task Parameters:
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
            
        :Returns: The int taskid of the submitted task.  Pass this to 
            `get_task_result` to get the `TaskResult` object.
        """
        assert isinstance(task, taskmodule.Task), "task must be a Task object!"
        ctask = taskmodule.can_task(task) # handles arbitrary function in .depend
                                # as well as arbitrary recovery_task chains
        ptask = pickle.dumps(ctask, 2)
        d = self.remote_reference.callRemote('run', ptask)
        d.addCallback(self.unpackage)
        return d
    
    def get_task_result(self, taskid, block=False):
        """The task result by taskid.
        
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
        """Abort a task by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be aborted.
            block : boolean
                Should I block until the task is aborted.        
        """
        d = self.remote_reference.callRemote('abort', taskid)
        d.addCallback(self.unpackage)
        return d 
        
    def barrier(self, taskids):
        """Block until all tasks are completed.
        
        :Parameters:
            taskids : list, tuple
                A sequence of taskids to block on.
        """
        d = self.remote_reference.callRemote('barrier', taskids)
        d.addCallback(self.unpackage)
        return d 
    
    def spin(self):
        """touch the scheduler, to resume scheduling without submitting
        a task.
        """
        d = self.remote_reference.callRemote('spin')
        d.addCallback(self.unpackage)
        return d
    
    def queue_status(self, verbose=False):
        """Return a dict with the status of the task queue."""
        d = self.remote_reference.callRemote('queue_status', verbose)
        d.addCallback(self.unpackage)
        return d
    
    def adapt_to_blocking_client(self):
        from IPython.kernel.taskclient import IBlockingTaskClient
        return IBlockingTaskClient(self)


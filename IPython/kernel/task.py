# encoding: utf-8
# -*- test-case-name: IPython.kernel.tests.test_task -*-

"""Task farming representation of the ControllerService."""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import copy, time
from types import FunctionType

import zope.interface as zi, string
from twisted.internet import defer, reactor
from twisted.python import components, log, failure

from IPython.kernel.util import printer
from IPython.kernel import engineservice as es, error
from IPython.kernel import controllerservice as cs
from IPython.kernel.twistedutil import gatherBoth, DeferredList

from IPython.kernel.pickleutil import can, uncan, CannedFunction

#-----------------------------------------------------------------------------
# Definition of the Task objects
#-----------------------------------------------------------------------------

time_format = '%Y/%m/%d %H:%M:%S'

class ITask(zi.Interface):
    """
    This interface provides a generic definition of what constitutes a task.
    
    There are two sides to a task.  First a task needs to take input from
    a user to determine what work is performed by the task.  Second, the
    task needs to have the logic that knows how to turn that information
    info specific calls to a worker, through the `IQueuedEngine` interface.
    
    Many method in this class get two things passed to them: a Deferred
    and an IQueuedEngine implementer.  Such methods should register callbacks
    on the Deferred that use the IQueuedEngine to accomplish something.  See
    the existing task objects for examples.
    """
    
    zi.Attribute('retries','How many times to retry the task')
    zi.Attribute('recovery_task','A task to try if the initial one fails')
    zi.Attribute('taskid','the id of the task')
    
    def start_time(result):
        """
        Do anything needed to start the timing of the task.
        
        Must simply return the result after starting the timers.
        """
    
    def stop_time(result):
        """
        Do anything needed to stop the timing of the task.
        
        Must simply return the result after stopping the timers.  This 
        method will usually set attributes that are used by `process_result`
        in building result of the task.
        """
    
    def pre_task(d, queued_engine):
        """Do something with the queued_engine before the task is run.
        
        This method should simply add callbacks to the input Deferred
        that do something with the `queued_engine` before the task is run.
        
        :Parameters:
            d : Deferred
                The deferred that actions should be attached to
            queued_engine : IQueuedEngine implementer
                The worker that has been allocated to perform the task
        """
    
    def post_task(d, queued_engine):
        """Do something with the queued_engine after the task is run.
        
        This method should simply add callbacks to the input Deferred
        that do something with the `queued_engine` before the task is run.
        
        :Parameters:
            d : Deferred
                The deferred that actions should be attached to
            queued_engine : IQueuedEngine implementer
                The worker that has been allocated to perform the task
        """
    
    def submit_task(d, queued_engine):
        """Submit a task using the `queued_engine` we have been allocated.
        
        When a task is ready to run, this method is called.  This method
        must take the internal information of the task and make suitable
        calls on the queued_engine to have the actual work done.
        
        This method should simply add callbacks to the input Deferred
        that do something with the `queued_engine` before the task is run.
        
        :Parameters:
            d : Deferred
                The deferred that actions should be attached to
            queued_engine : IQueuedEngine implementer
                The worker that has been allocated to perform the task
        """

    def process_result(d, result, engine_id):
        """Take a raw task result.
        
        Objects that implement `ITask` can choose how the result of running
        the task is presented.  This method takes the raw result and 
        does this logic.  Two example are the `MapTask` which simply returns
        the raw result or a `Failure` object and the `StringTask` which
        returns a `TaskResult` object.
        
        :Parameters:
            d : Deferred
                The deferred that actions should be attached to
            result : object
                The raw task result that needs to be wrapped
            engine_id : int
                The id of the engine that did the task
        
        :Returns:
            The result, as a tuple of the form: (success, result).
            Here, success is a boolean indicating if the task
            succeeded or failed and result is the result.
        """
        
    def check_depend(properties):
        """Check properties to see if the task should be run.
        
        :Parameters:
            properties : dict
                A dictionary of properties that an engine has set
        
        :Returns:
            True if the task should be run, False otherwise
        """
    
    def can_task(self):
        """Serialize (can) any functions in the task for pickling.
        
        Subclasses must override this method and make sure that all 
        functions in the task are canned by calling `can` on the 
        function.
        """
    
    def uncan_task(self):
        """Unserialize (uncan) any canned function in the task."""

class BaseTask(object):
    """
    Common fuctionality for all objects implementing `ITask`.
    """
    
    zi.implements(ITask)
    
    def __init__(self, clear_before=False, clear_after=False, retries=0,
            recovery_task=None, depend=None):
        """
        Make a generic task.
        
        :Parameters:
            clear_before : boolean
                Should the engines namespace be cleared before the task
                is run
            clear_after : boolean
                Should the engines namespace be clear after the task is run
            retries : int
                The number of times a task should be retries upon failure
            recovery_task : any task object
                If a task fails and it has a recovery_task, that is run
                upon a retry
            depend : FunctionType
                A function that is called to test for properties.  This function
                must take one argument, the properties dict and return a boolean
        """
        self.clear_before = clear_before
        self.clear_after = clear_after
        self.retries = retries
        self.recovery_task = recovery_task
        self.depend = depend
        self.taskid = None
    
    def start_time(self, result):
        """
        Start the basic timers.
        """
        self.start = time.time()
        self.start_struct = time.localtime()
        return result
    
    def stop_time(self, result):
        """
        Stop the basic timers.
        """
        self.stop = time.time()
        self.stop_struct = time.localtime()
        self.duration = self.stop - self.start 
        self.submitted = time.strftime(time_format, self.start_struct)
        self.completed = time.strftime(time_format)
        return result
    
    def pre_task(self, d, queued_engine):
        """
        Clear the engine before running the task if clear_before is set.
        """
        if self.clear_before:
            d.addCallback(lambda r: queued_engine.reset())
    
    def post_task(self, d, queued_engine):
        """
        Clear the engine after running the task if clear_after is set.
        """
        def reseter(result):
            queued_engine.reset()
            return result
        if self.clear_after:
            d.addBoth(reseter)
    
    def submit_task(self, d, queued_engine):
        raise NotImplementedError('submit_task must be implemented in a subclass')
    
    def process_result(self, result, engine_id):
        """
        Process a task result.
        
        This is the default `process_result` that just returns the raw
        result or a `Failure`.
        """
        if isinstance(result, failure.Failure):
            return (False, result)
        else:
            return (True, result)
    
    def check_depend(self, properties):
        """
        Calls self.depend(properties) to see if a task should be run.
        """
        if self.depend is not None:
            return self.depend(properties)
        else:
            return True

    def can_task(self):
        self.depend = can(self.depend)
        if isinstance(self.recovery_task, BaseTask):
            self.recovery_task.can_task()
            
    def uncan_task(self):
        self.depend = uncan(self.depend)
        if isinstance(self.recovery_task, BaseTask):
            self.recovery_task.uncan_task()

class MapTask(BaseTask):
    """
    A task that consists of a function and arguments.
    """
    
    zi.implements(ITask)
    
    def __init__(self, function, args=None, kwargs=None, clear_before=False, 
            clear_after=False, retries=0, recovery_task=None, depend=None):
        """
        Create a task based on a function, args and kwargs.
        
        This is a simple type of task that consists of calling:
        function(*args, **kwargs) and wrapping the result in a `TaskResult`.
        
        The return value of the function, or a `Failure` wrapping an 
        exception is the task result for this type of task.
        """
        BaseTask.__init__(self, clear_before, clear_after, retries, 
            recovery_task, depend)
        if not isinstance(function, FunctionType):
            raise TypeError('a task function must be a FunctionType')
        self.function = function
        if args is None:
            self.args = ()
        else:
            self.args = args
        if not isinstance(self.args, (list, tuple)):
            raise TypeError('a task args must be a list or tuple')
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs
        if not isinstance(self.kwargs, dict):
            raise TypeError('a task kwargs must be a dict')
    
    def submit_task(self, d, queued_engine):
        d.addCallback(lambda r: queued_engine.push_function(
            dict(_ipython_task_function=self.function))
        )
        d.addCallback(lambda r: queued_engine.push(
            dict(_ipython_task_args=self.args,_ipython_task_kwargs=self.kwargs))
        )
        d.addCallback(lambda r: queued_engine.execute(
            '_ipython_task_result = _ipython_task_function(*_ipython_task_args,**_ipython_task_kwargs)')
        )
        d.addCallback(lambda r: queued_engine.pull('_ipython_task_result'))
    
    def can_task(self):
        self.function = can(self.function)
        BaseTask.can_task(self)
    
    def uncan_task(self):
        self.function = uncan(self.function)
        BaseTask.uncan_task(self)


class StringTask(BaseTask):
    """
    A task that consists of a string of Python code to run.
    """

    def __init__(self, expression, pull=None, push=None,
            clear_before=False, clear_after=False, retries=0, 
            recovery_task=None, depend=None):
        """
        Create a task based on a Python expression and variables
        
        This type of task lets you push a set of variables to the engines
        namespace, run a Python string in that namespace and then bring back
        a different set of Python variables as the result.
        
        Because this type of task can return many results (through the
        `pull` keyword argument) it returns a special `TaskResult` object
        that wraps the pulled variables, statistics about the run and
        any exceptions raised.
        """
        if not isinstance(expression, str):
            raise TypeError('a task expression must be a string')
        self.expression = expression
        
        if pull==None:
            self.pull = ()
        elif isinstance(pull, str):
            self.pull = (pull,)
        elif isinstance(pull, (list, tuple)):
            self.pull = pull
        else:
            raise TypeError('pull must be str or a sequence of strs')
        
        if push==None:
            self.push = {}
        elif isinstance(push, dict):
            self.push = push
        else:
            raise TypeError('push must be a dict')
        
        BaseTask.__init__(self, clear_before, clear_after, retries, 
            recovery_task, depend)

    def submit_task(self, d, queued_engine):
        if self.push is not None:
            d.addCallback(lambda r: queued_engine.push(self.push))
        
        d.addCallback(lambda r: queued_engine.execute(self.expression))
        
        if self.pull is not None:
            d.addCallback(lambda r: queued_engine.pull(self.pull))
        else:
            d.addCallback(lambda r: None)    
    
    def process_result(self, result, engine_id):
        if isinstance(result, failure.Failure):
            tr = TaskResult(result, engine_id)
        else:
            if self.pull is None:
                resultDict = {}
            elif len(self.pull) == 1:
                resultDict = {self.pull[0]:result}
            else:
                resultDict = dict(zip(self.pull, result))
            tr = TaskResult(resultDict, engine_id)
        # Assign task attributes
        tr.submitted = self.submitted
        tr.completed = self.completed
        tr.duration = self.duration
        if hasattr(self,'taskid'):
            tr.taskid = self.taskid
        else:
            tr.taskid = None
        if isinstance(result, failure.Failure):
            return (False, tr)
        else:
            return (True, tr)

class ResultNS(object):
    """
    A dict like object for holding the results of a task.
    
    The result namespace object for use in `TaskResult` objects as tr.ns.
    It builds an object from a dictionary, such that it has attributes
    according to the key,value pairs of the dictionary.
    
    This works by calling setattr on ALL key,value pairs in the dict.  If a user
    chooses to overwrite the `__repr__` or `__getattr__` attributes, they can.
    This can be a bad idea, as it may corrupt standard behavior of the
    ns object.
    
    Example
    --------
    
    >>> ns = ResultNS({'a':17,'foo':range(3)})
    >>> print ns
    NS{'a': 17, 'foo': [0, 1, 2]}
    >>> ns.a
    17
    >>> ns['foo']
    [0, 1, 2]
    """
    def __init__(self, dikt):
        for k,v in dikt.iteritems():
            setattr(self,k,v)
    
    def __repr__(self):
        l = dir(self)
        d = {}
        for k in l:
            # do not print private objects
            if k[:2] != '__' and k[-2:] != '__':
                d[k] = getattr(self, k)
        return "NS"+repr(d)
    
    def __getitem__(self, key):
        return getattr(self, key)

class TaskResult(object):
    """
    An object for returning task results for certain types of tasks.
        
    This object encapsulates the results of a task.  On task
    success it will have a keys attribute that will have a list
    of the variables that have been pulled back.  These variables
    are accessible as attributes of this class as well.  On 
    success the failure attribute will be None.
        
    In task failure, keys will be empty, but failure will contain
    the failure object that encapsulates the remote exception.
    One can also simply call the `raise_exception` method of 
    this class to re-raise any remote exception in the local
    session.
        
    The `TaskResult` has a `.ns` member, which is a property for access
    to the results.  If the Task had pull=['a', 'b'], then the 
    Task Result will have attributes `tr.ns.a`, `tr.ns.b` for those values.
    Accessing `tr.ns` will raise the remote failure if the task failed.
        
    The `engineid` attribute should have the `engineid` of the engine
    that ran the task.  But, because engines can come and go, 
    the `engineid` may not continue to be
    valid or accurate.
        
    The `taskid` attribute simply gives the `taskid` that the task
    is tracked under.
    """
    taskid = None
    
    def _getNS(self):
        if isinstance(self.failure, failure.Failure):
            return self.failure.raiseException()
        else:
            return self._ns
    
    def _setNS(self, v):
        raise Exception("the ns attribute cannot be changed")
    
    ns = property(_getNS, _setNS)
    
    def __init__(self, results, engineid):
        self.engineid = engineid
        if isinstance(results, failure.Failure):
            self.failure = results
            self.results = {}
        else:
            self.results = results
            self.failure = None
        
        self._ns = ResultNS(self.results)
        
        self.keys = self.results.keys()
    
    def __repr__(self):
        if self.failure is not None:
            contents = self.failure
        else:
            contents = self.results
        return "TaskResult[ID:%r]:%r"%(self.taskid, contents)
    
    def __getitem__(self, key):
        if self.failure is not None:
            self.raise_exception()
        return self.results[key]
    
    def raise_exception(self):
        """Re-raise any remote exceptions in the local python session."""
        if self.failure is not None:
            self.failure.raiseException()


#-----------------------------------------------------------------------------
# The controller side of things
#-----------------------------------------------------------------------------

class IWorker(zi.Interface):
    """The Basic Worker Interface. 
    
    A worked is a representation of an Engine that is ready to run tasks.
    """
    
    zi.Attribute("workerid", "the id of the worker")
    
    def run(task):
        """Run task in worker's namespace.
        
        :Parameters:
            task : a `Task` object
        
        :Returns: `Deferred` to a tuple of (success, result) where
            success if a boolean that signifies success or failure
            and result is the task result.
        """


class WorkerFromQueuedEngine(object):
    """Adapt an `IQueuedEngine` to an `IWorker` object"""
    
    zi.implements(IWorker)
    
    def __init__(self, qe):
        self.queuedEngine = qe
        self.workerid = None
    
    def _get_properties(self):
        return self.queuedEngine.properties
    
    properties = property(_get_properties, lambda self, _:None)
    
    def run(self, task):
        """Run task in worker's namespace.
        
        This takes a task and calls methods on the task that actually
        cause `self.queuedEngine` to do the task.  See the methods of
        `ITask` for more information about how these methods are called.
        
        :Parameters:
            task : a `Task` object
        
        :Returns: `Deferred` to a tuple of (success, result) where
            success if a boolean that signifies success or failure
            and result is the task result.
        """
        d = defer.succeed(None)
        d.addCallback(task.start_time)
        task.pre_task(d, self.queuedEngine)
        task.submit_task(d, self.queuedEngine)
        task.post_task(d, self.queuedEngine)
        d.addBoth(task.stop_time)
        d.addBoth(task.process_result, self.queuedEngine.id)
        # At this point, there will be (success, result) coming down the line
        return d


components.registerAdapter(WorkerFromQueuedEngine, es.IEngineQueued, IWorker)

class IScheduler(zi.Interface):
    """The interface for a Scheduler.
    """
    zi.Attribute("nworkers", "the number of unassigned workers")
    zi.Attribute("ntasks", "the number of unscheduled tasks")
    zi.Attribute("workerids", "a list of the worker ids")
    zi.Attribute("taskids", "a list of the task ids")
    
    def add_task(task, **flags):
        """Add a task to the queue of the Scheduler.
        
        :Parameters:
            task : an `ITask` implementer
                The task to be queued.
            flags : dict
                General keywords for more sophisticated scheduling
        """
    
    def pop_task(id=None):
        """Pops a task object from the queue.
        
        This gets the next task to be run.  If no `id` is requested, the highest priority
        task is returned.
        
        :Parameters:
            id
                The id of the task to be popped.  The default (None) is to return 
                the highest priority task.
                
        :Returns: an `ITask` implementer
        
        :Exceptions:
            IndexError : raised if no taskid in queue
        """
    
    def add_worker(worker, **flags):
        """Add a worker to the worker queue.
        
        :Parameters:
            worker : an `IWorker` implementer
            flags : dict
                General keywords for more sophisticated scheduling
        """
    
    def pop_worker(id=None):
        """Pops an IWorker object that is ready to do work.
        
        This gets the next IWorker that is ready to do work. 
        
        :Parameters:
            id : if specified, will pop worker with workerid=id, else pops
                 highest priority worker.  Defaults to None.
        
        :Returns:
            an IWorker object
        
        :Exceptions:
            IndexError : raised if no workerid in queue
        """
    
    def ready():
        """Returns True if there is something to do, False otherwise"""
    
    def schedule():
        """Returns (worker,task) pair for the next task to be run."""
    

class FIFOScheduler(object):
    """
    A basic First-In-First-Out (Queue) Scheduler.
    
    This is the default Scheduler for the `TaskController`.
    See the docstrings for `IScheduler` for interface details.
    """
    
    zi.implements(IScheduler)
    
    def __init__(self):
        self.tasks = []
        self.workers = []
    
    def _ntasks(self):
        return len(self.tasks)
    
    def _nworkers(self):
        return len(self.workers)
    
    ntasks = property(_ntasks, lambda self, _:None)
    nworkers = property(_nworkers, lambda self, _:None)
    
    def _taskids(self):
        return [t.taskid for t in self.tasks]
    
    def _workerids(self):
        return [w.workerid for w in self.workers]
    
    taskids = property(_taskids, lambda self,_:None)
    workerids = property(_workerids, lambda self,_:None)
    
    def add_task(self, task, **flags):    
        self.tasks.append(task)
    
    def pop_task(self, id=None):
        if id is None:
            return self.tasks.pop(0)
        else:
            for i in range(len(self.tasks)):
                taskid = self.tasks[i].taskid
                if id == taskid:
                    return self.tasks.pop(i)
            raise IndexError("No task #%i"%id)
    
    def add_worker(self, worker, **flags):
        self.workers.append(worker)
    
    def pop_worker(self, id=None):
        if id is None:
            return self.workers.pop(0)
        else:
            for i in range(len(self.workers)):
                workerid = self.workers[i].workerid
                if id == workerid:
                    return self.workers.pop(i)
            raise IndexError("No worker #%i"%id)
    
    def schedule(self):
        for t in self.tasks:
            for w in self.workers:
                try:# do not allow exceptions to break this
                    # Allow the task to check itself using its
                    # check_depend method.
                    cando = t.check_depend(w.properties)
                except:
                    cando = False
                if cando:
                    return self.pop_worker(w.workerid), self.pop_task(t.taskid)
        return None, None
    


class LIFOScheduler(FIFOScheduler):
    """
    A Last-In-First-Out (Stack) Scheduler.
    
    This scheduler should naively reward fast engines by giving 
    them more jobs.  This risks starvation, but only in cases with 
    low load, where starvation does not really matter.
    """
    
    def add_task(self, task, **flags):
        # self.tasks.reverse()
        self.tasks.insert(0, task)
        # self.tasks.reverse()
    
    def add_worker(self, worker, **flags):
        # self.workers.reverse()
        self.workers.insert(0, worker)
        # self.workers.reverse()
    

class ITaskController(cs.IControllerBase):
    """
    The Task based interface to a `ControllerService` object
    
    This adapts a `ControllerService` to the ITaskController interface.
    """
    
    def run(task):
        """
        Run a task.
        
        :Parameters:
            task : an IPython `Task` object
        
        :Returns: the integer ID of the task
        """
    
    def get_task_result(taskid, block=False):
        """
        Get the result of a task by its ID.
        
        :Parameters:
            taskid : int
                the id of the task whose result is requested
        
        :Returns: `Deferred` to the task result if the task is done, and None
            if not.
        
        :Exceptions:
            actualResult will be an `IndexError` if no such task has been submitted
        """
    
    def abort(taskid):
        """Remove task from queue if task is has not been submitted.
        
        If the task has already been submitted, wait for it to finish and discard 
        results and prevent resubmission.
        
        :Parameters:
            taskid : the id of the task to be aborted
        
        :Returns:
            `Deferred` to abort attempt completion.  Will be None on success.
        
        :Exceptions:
            deferred will fail with `IndexError` if no such task has been submitted
            or the task has already completed.
        """
    
    def barrier(taskids):
        """
        Block until the list of taskids are completed.
        
        Returns None on success.
        """
    
    def spin():
        """
        Touch the scheduler, to resume scheduling without submitting a task.
        """
    
    def queue_status(verbose=False):
        """
        Get a dictionary with the current state of the task queue.
        
        If verbose is True, then return lists of taskids, otherwise, 
        return the number of tasks with each status.
        """
    
    def clear():
        """
        Clear all previously run tasks from the task controller.
        
        This is needed because the task controller keep all task results
        in memory.  This can be a problem is there are many completed
        tasks.  Users should call this periodically to clean out these
        cached task results.
        """
    

class TaskController(cs.ControllerAdapterBase):
    """The Task based interface to a Controller object.
    
    If you want to use a different scheduler, just subclass this and set
    the `SchedulerClass` member to the *class* of your chosen scheduler.
    """
    
    zi.implements(ITaskController)
    SchedulerClass = FIFOScheduler
    
    timeout = 30
    
    def __init__(self, controller):
        self.controller = controller
        self.controller.on_register_engine_do(self.registerWorker, True)
        self.controller.on_unregister_engine_do(self.unregisterWorker, True)
        self.taskid = 0
        self.failurePenalty = 1 # the time in seconds to penalize
                                # a worker for failing a task
        self.pendingTasks = {} # dict of {workerid:(taskid, task)}
        self.deferredResults = {} # dict of {taskid:deferred}
        self.finishedResults = {} # dict of {taskid:actualResult}
        self.workers = {} # dict of {workerid:worker}
        self.abortPending = [] # dict of {taskid:abortDeferred}
        self.idleLater = None # delayed call object for timeout
        self.scheduler = self.SchedulerClass()
        
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
                self.workers[id].workerid = id
                self.schedule.add_worker(self.workers[id])
    
    def registerWorker(self, id):
        """Called by controller.register_engine."""
        if self.workers.get(id):
            raise ValueError("worker with id %s already exists.  This should not happen." % id)
        self.workers[id] = IWorker(self.controller.engines[id])
        self.workers[id].workerid = id
        if not self.pendingTasks.has_key(id):# if not working
            self.scheduler.add_worker(self.workers[id])
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """Called by controller.unregister_engine"""
        
        if self.workers.has_key(id):
            try:
                self.scheduler.pop_worker(id)
            except IndexError:
                pass
            self.workers.pop(id)
    
    def _pendingTaskIDs(self):
        return [t.taskid for t in self.pendingTasks.values()]
    
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------
    
    def run(self, task):
        """
        Run a task and return `Deferred` to its taskid.
        """
        task.taskid = self.taskid
        task.start = time.localtime()
        self.taskid += 1
        d = defer.Deferred()
        self.scheduler.add_task(task)
        log.msg('Queuing task: %i' % task.taskid)
        
        self.deferredResults[task.taskid] = []
        self.distributeTasks()
        return defer.succeed(task.taskid)
    
    def get_task_result(self, taskid, block=False):
        """
        Returns a `Deferred` to the task result, or None.
        """
        log.msg("Getting task result: %i" % taskid)
        if self.finishedResults.has_key(taskid):
            tr = self.finishedResults[taskid]
            return defer.succeed(tr)
        elif self.deferredResults.has_key(taskid):
            if block:
                d = defer.Deferred()
                self.deferredResults[taskid].append(d)
                return d
            else:
                return defer.succeed(None)
        else:
            return defer.fail(IndexError("task ID not registered: %r" % taskid))
    
    def abort(self, taskid):
        """
        Remove a task from the queue if it has not been run already.
        """
        if not isinstance(taskid, int):
            return defer.fail(failure.Failure(TypeError("an integer task id expected: %r" % taskid)))
        try:
            self.scheduler.pop_task(taskid)
        except IndexError, e:
            if taskid in self.finishedResults.keys():
                d = defer.fail(IndexError("Task Already Completed"))
            elif taskid in self.abortPending:
                d = defer.fail(IndexError("Task Already Aborted"))
            elif taskid in self._pendingTaskIDs():# task is pending
                self.abortPending.append(taskid)
                d = defer.succeed(None)
            else:
                d = defer.fail(e)
        else:
            d = defer.execute(self._doAbort, taskid)
        
        return d
    
    def barrier(self, taskids):
        dList = []
        if isinstance(taskids, int):
            taskids = [taskids]
        for id in taskids:
            d = self.get_task_result(id, block=True)
            dList.append(d)
        d = DeferredList(dList, consumeErrors=1)
        d.addCallbacks(lambda r: None)
        return d
    
    def spin(self):
        return defer.succeed(self.distributeTasks())
    
    def queue_status(self, verbose=False):
        pending = self._pendingTaskIDs()
        failed = []
        succeeded = []
        for k,v in self.finishedResults.iteritems():
            if not isinstance(v, failure.Failure):
                if hasattr(v,'failure'):
                    if v.failure is None:
                        succeeded.append(k)
                    else:
                        failed.append(k)
        scheduled = self.scheduler.taskids
        if verbose:
            result = dict(pending=pending, failed=failed, 
                succeeded=succeeded, scheduled=scheduled)
        else:
            result = dict(pending=len(pending),failed=len(failed),
                succeeded=len(succeeded),scheduled=len(scheduled))
        return defer.succeed(result)
    
    #---------------------------------------------------------------------------
    # Queue methods
    #---------------------------------------------------------------------------
    
    def _doAbort(self, taskid):
        """
        Helper function for aborting a pending task.
        """
        log.msg("Task aborted: %i" % taskid)
        result = failure.Failure(error.TaskAborted())
        self._finishTask(taskid, result)
        if taskid in self.abortPending:
            self.abortPending.remove(taskid)
    
    def _finishTask(self, taskid, result):
        dlist = self.deferredResults.pop(taskid)
        # result.taskid = taskid   # The TaskResult should save the taskid
        self.finishedResults[taskid] = result
        for d in dlist:
            d.callback(result)
    
    def distributeTasks(self):
        """
        Distribute tasks while self.scheduler has things to do.
        """
        log.msg("distributing Tasks")
        worker, task = self.scheduler.schedule()
        if not worker and not task:
            if self.idleLater and self.idleLater.called:# we are inside failIdle
                self.idleLater = None
            else:
                self.checkIdle()
            return False
        # else something to do:
        while worker and task:
            # get worker and task
            # add to pending
            self.pendingTasks[worker.workerid] = task
            # run/link callbacks
            d = worker.run(task)
            log.msg("Running task %i on worker %i" %(task.taskid, worker.workerid))
            d.addBoth(self.taskCompleted, task.taskid, worker.workerid)
            worker, task = self.scheduler.schedule()
        # check for idle timeout:
        self.checkIdle()
        return True
    
    def checkIdle(self):
        if self.idleLater and not self.idleLater.called:
            self.idleLater.cancel()
        if self.scheduler.ntasks and self.workers and \
                    self.scheduler.nworkers == len(self.workers):
            self.idleLater = reactor.callLater(self.timeout, self.failIdle)
        else:
            self.idleLater = None
    
    def failIdle(self):
        if not self.distributeTasks():
            while self.scheduler.ntasks:
                t = self.scheduler.pop_task()
                msg = "task %i failed to execute due to unmet dependencies"%t.taskid
                msg += " for %i seconds"%self.timeout
                log.msg("Task aborted by timeout: %i" % t.taskid)
                f = failure.Failure(error.TaskTimeout(msg))
                self._finishTask(t.taskid, f)
        self.idleLater = None
                
    
    def taskCompleted(self, success_and_result, taskid, workerid):
        """This is the err/callback for a completed task."""
        success, result = success_and_result
        try:
            task = self.pendingTasks.pop(workerid)
        except:
            # this should not happen
            log.msg("Tried to pop bad pending task %i from worker %i"%(taskid, workerid))
            log.msg("Result: %r"%result)
            log.msg("Pending tasks: %s"%self.pendingTasks)
            return
        
        # Check if aborted while pending
        aborted = False
        if taskid in self.abortPending:
            self._doAbort(taskid)
            aborted = True
        
        if not aborted:
            if not success:
                log.msg("Task %i failed on worker %i"% (taskid, workerid))
                if task.retries > 0: # resubmit
                    task.retries -= 1
                    self.scheduler.add_task(task)
                    s = "Resubmitting task %i, %i retries remaining" %(taskid, task.retries)
                    log.msg(s)
                    self.distributeTasks()
                elif isinstance(task.recovery_task, BaseTask) and \
                                    task.recovery_task.retries > -1:
                    # retries = -1 is to prevent infinite recovery_task loop
                    task.retries = -1 
                    task.recovery_task.taskid = taskid
                    task = task.recovery_task
                    self.scheduler.add_task(task)
                    s = "Recovering task %i, %i retries remaining" %(taskid, task.retries)
                    log.msg(s)
                    self.distributeTasks()
                else: # done trying
                    self._finishTask(taskid, result)
                # wait a second before readmitting a worker that failed
                # it may have died, and not yet been unregistered
                reactor.callLater(self.failurePenalty, self.readmitWorker, workerid)
            else: # we succeeded
                log.msg("Task completed: %i"% taskid)
                self._finishTask(taskid, result)
                self.readmitWorker(workerid)
        else: # we aborted the task
            if not success:
                reactor.callLater(self.failurePenalty, self.readmitWorker, workerid)
            else:
                self.readmitWorker(workerid)
    
    def readmitWorker(self, workerid):
        """
        Readmit a worker to the scheduler.  
        
        This is outside `taskCompleted` because of the `failurePenalty` being 
        implemented through `reactor.callLater`.
        """
        
        if workerid in self.workers.keys() and workerid not in self.pendingTasks.keys():
            self.scheduler.add_worker(self.workers[workerid])
            self.distributeTasks()
    
    def clear(self):
        """
        Clear all previously run tasks from the task controller.
        
        This is needed because the task controller keep all task results
        in memory.  This can be a problem is there are many completed
        tasks.  Users should call this periodically to clean out these
        cached task results.
        """
        self.finishedResults = {}
        return defer.succeed(None)
        
    
components.registerAdapter(TaskController, cs.IControllerBase, ITaskController)

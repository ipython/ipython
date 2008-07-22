# encoding: utf-8

"""A parallelized version of Python's builtin map."""

__docformat__ = "restructuredtext en"

#----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#----------------------------------------------------------------------------

#----------------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------------

from types import FunctionType
from zope.interface import Interface, implements
from IPython.kernel.task import MapTask
from IPython.kernel.twistedutil import DeferredList, gatherBoth
from IPython.kernel.util import printer
from IPython.kernel.error import collect_exceptions

#----------------------------------------------------------------------------
# Code
#----------------------------------------------------------------------------

class IMapper(Interface):
    """The basic interface for a Mapper.
    
    This defines a generic interface for mapping.  The idea of this is 
    similar to that of Python's builtin `map` function, which applies a function
    elementwise to a sequence.
    """
    
    def map(func, *seqs):
        """Do map in parallel.
        
        Equivalent to map(func, *seqs) or:
        
        [func(seqs[0][0], seqs[1][0],...), func(seqs[0][1], seqs[1][1],...),...]
        
        :Parameters:
            func : FunctionType
                The function to apply to the sequence
            sequences : tuple of iterables
                A sequence of iterables that are used for sucessive function
                arguments.  This work just like map
        """

class IMultiEngineMapperFactory(Interface):
    """
    An interface for something that creates `IMapper` instances.
    """
    
    def mapper(dist='b', targets='all', block=True):
        """
        Create an `IMapper` implementer with a given set of arguments.
        
        The `IMapper` created using a multiengine controller is 
        not load balanced.
        """

class ITaskMapperFactory(Interface):
    """
    An interface for something that creates `IMapper` instances.
    """
    
    def mapper(clear_before=False, clear_after=False, retries=0, 
                recovery_task=None, depend=None, block=True):
        """
        Create an `IMapper` implementer with a given set of arguments.
        
        The `IMapper` created using a task controller is load balanced.
        
        See the documentation for `IPython.kernel.task.BaseTask` for 
        documentation on the arguments to this method.
        """


class MultiEngineMapper(object):
    """
    A Mapper for `IMultiEngine` implementers.
    """
    
    implements(IMapper)
    
    def __init__(self, multiengine, dist='b', targets='all', block=True):
        """
        Create a Mapper for a multiengine.
        
        The value of all arguments are used for all calls to `map`.  This
        class allows these arguemnts to be set for a series of map calls.
        
        :Parameters:
            multiengine : `IMultiEngine` implementer
                The multiengine to use for running the map commands
            dist : str
                The type of decomposition to use.  Only block ('b') is
                supported currently
            targets : (str, int, tuple of ints)
                The engines to use in the map
            block : boolean
                Whether to block when the map is applied
        """
        self.multiengine = multiengine
        self.dist = dist
        self.targets = targets
        self.block = block
    
    def map(self, func, *sequences):
        """
        Apply func to *sequences elementwise.  Like Python's builtin map.
        
        This version is not load balanced.
        """
        max_len = max(len(s) for s in sequences)
        for s in sequences:
            if len(s)!=max_len:
                raise ValueError('all sequences must have equal length')
        assert isinstance(func, (str, FunctionType)), "func must be a fuction or str"
        return self.multiengine.raw_map(func, sequences, dist=self.dist,
            targets=self.targets, block=self.block)

class TaskMapper(object):
    """
    Make an `ITaskController` look like an `IMapper`.
    
    This class provides a load balanced version of `map`.
    """
    
    def __init__(self, task_controller, clear_before=False, clear_after=False, retries=0, 
            recovery_task=None, depend=None, block=True):
        """
        Create a `IMapper` given a `TaskController` and arguments.
        
        The additional arguments are those that are common to all types of 
        tasks and are described in the documentation for 
        `IPython.kernel.task.BaseTask`.
        
        :Parameters:
            task_controller : an `IBlockingTaskClient` implementer
                The `TaskController` to use for calls to `map`
        """
        self.task_controller = task_controller
        self.clear_before = clear_before
        self.clear_after = clear_after
        self.retries = retries
        self.recovery_task = recovery_task
        self.depend = depend
        self.block = block
    
    def map(self, func, *sequences):
        """
        Apply func to *sequences elementwise.  Like Python's builtin map.
        
        This version is load balanced.
        """
        max_len = max(len(s) for s in sequences)
        for s in sequences:
            if len(s)!=max_len:
                raise ValueError('all sequences must have equal length')
        task_args = zip(*sequences)
        task_ids = []
        dlist = []
        for ta in task_args:
            task = MapTask(func, ta, clear_before=self.clear_before,
                clear_after=self.clear_after, retries=self.retries,
                recovery_task=self.recovery_task, depend=self.depend)
            dlist.append(self.task_controller.run(task))
        dlist = gatherBoth(dlist, consumeErrors=1)
        dlist.addCallback(collect_exceptions,'map')
        if self.block:
            def get_results(task_ids):
                d = self.task_controller.barrier(task_ids)
                d.addCallback(lambda _: gatherBoth([self.task_controller.get_task_result(tid) for tid in task_ids], consumeErrors=1))
                d.addCallback(collect_exceptions, 'map')
                return d
            dlist.addCallback(get_results)
        return dlist

class SynchronousTaskMapper(object):
    """
    Make an `IBlockingTaskClient` look like an `IMapper`.
    
    This class provides a load balanced version of `map`.
    """
    
    def __init__(self, task_controller, clear_before=False, clear_after=False, retries=0, 
            recovery_task=None, depend=None, block=True):
        """
        Create a `IMapper` given a `IBlockingTaskClient` and arguments.
        
        The additional arguments are those that are common to all types of 
        tasks and are described in the documentation for 
        `IPython.kernel.task.BaseTask`.
        
        :Parameters:
            task_controller : an `IBlockingTaskClient` implementer
                The `TaskController` to use for calls to `map`
        """
        self.task_controller = task_controller
        self.clear_before = clear_before
        self.clear_after = clear_after
        self.retries = retries
        self.recovery_task = recovery_task
        self.depend = depend
        self.block = block
    
    def map(self, func, *sequences):
        """
        Apply func to *sequences elementwise.  Like Python's builtin map.
        
        This version is load balanced.
        """
        max_len = max(len(s) for s in sequences)
        for s in sequences:
            if len(s)!=max_len:
                raise ValueError('all sequences must have equal length')
        task_args = zip(*sequences)
        task_ids = []
        for ta in task_args:
            task = MapTask(func, ta, clear_before=self.clear_before,
                clear_after=self.clear_after, retries=self.retries,
                recovery_task=self.recovery_task, depend=self.depend)
            task_ids.append(self.task_controller.run(task))
        if self.block:
            self.task_controller.barrier(task_ids)
            task_results = [self.task_controller.get_task_result(tid) for tid in task_ids]
            return task_results
        else:
            return task_ids
# encoding: utf-8

"""A parallelized function that does scatter/execute/gather."""

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

from types import FunctionType
from zope.interface import Interface, implements


class IMultiEngineParallelDecorator(Interface):
    """A decorator that creates a parallel function."""
    
    def parallel(dist='b', targets=None, block=None):
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

class ITaskParallelDecorator(Interface):
    """A decorator that creates a parallel function."""
    
    def parallel(clear_before=False, clear_after=False, retries=0, 
        recovery_task=None, depend=None, block=True):
        """
        A decorator that turns a function into a parallel function.
        
        This can be used as:
        
        @parallel()
        def f(x, y)
            ...
        
        f(range(10), range(10))
        
        This causes f(0,0), f(1,1), ... to be called in parallel.
        
        See the documentation for `IPython.kernel.task.BaseTask` for 
        documentation on the arguments to this method.
        """

class IParallelFunction(Interface):
    pass

class ParallelFunction(object):
    """
    The implementation of a parallel function.
    
    A parallel function is similar to Python's map function: 
    
    map(func, *sequences) -> pfunc(*sequences)
    
    Parallel functions should be created by using the @parallel decorator.
    """
    
    implements(IParallelFunction)
    
    def __init__(self, mapper):
        """
        Create a parallel function from an `IMapper`.
        
        :Parameters:
            mapper : an `IMapper` implementer.
                The mapper to use for the parallel function
        """
        self.mapper = mapper
        
    def __call__(self, func):
        """
        Decorate a function to make it run in parallel.
        """
        assert isinstance(func, (str, FunctionType)), "func must be a fuction or str"
        self.func = func
        def call_function(*sequences):
            return self.mapper.map(self.func, *sequences)
        return call_function

    
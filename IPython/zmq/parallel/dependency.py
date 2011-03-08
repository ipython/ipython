"""Dependency utilities"""

from IPython.external.decorator import decorator

from .asyncresult import AsyncResult
from .error import UnmetDependency


class depend(object):
    """Dependency decorator, for use with tasks.
    
    `@depend` lets you define a function for engine dependencies
    just like you use `apply` for tasks.
    
    
    Examples
    --------
    ::
    
        @depend(df, a,b, c=5)
        def f(m,n,p)
        
        view.apply(f, 1,2,3)
    
    will call df(a,b,c=5) on the engine, and if it returns False or
    raises an UnmetDependency error, then the task will not be run
    and another engine will be tried.
    """
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs
    
    def __call__(self, f):
        return dependent(f, self.f, *self.args, **self.kwargs)

class dependent(object):
    """A function that depends on another function.
    This is an object to prevent the closure used
    in traditional decorators, which are not picklable.
    """

    def __init__(self, f, df, *dargs, **dkwargs):
        self.f = f
        self.func_name = getattr(f, '__name__', 'f')
        self.df = df
        self.dargs = dargs
        self.dkwargs = dkwargs

    def __call__(self, *args, **kwargs):
        if self.df(*self.dargs, **self.dkwargs) is False:
            raise UnmetDependency()
        return self.f(*args, **kwargs)
    
    @property
    def __name__(self):
        return self.func_name

def _require(*names):
    """Helper for @require decorator."""
    for name in names:
        try:
            __import__(name)
        except ImportError:
            return False
    return True

def require(*names):
    """Simple decorator for requiring names to be importable.
    
    Examples
    --------
    
    In [1]: @require('numpy')
       ...: def norm(a):
       ...:     import numpy
       ...:     return numpy.linalg.norm(a,2)
    """
    return depend(_require, *names)

class Dependency(set):
    """An object for representing a set of msg_id dependencies.
    
    Subclassed from set().
    
    Parameters
    ----------
    dependencies: list/set of msg_ids or AsyncResult objects or output of Dependency.as_dict()
        The msg_ids to depend on
    all : bool [default True]
        Whether the dependency should be considered met when *all* depending tasks have completed
        or only when *any* have been completed.
    success_only : bool [default True]
        Whether to consider only successes for Dependencies, or consider failures as well.
        If `all=success_only=True`, then this task will fail with an ImpossibleDependency
        as soon as the first depended-upon task fails.
    """
    
    all=True
    success_only=True
    
    def __init__(self, dependencies=[], all=True, success_only=True):
        if isinstance(dependencies, dict):
            # load from dict
            all = dependencies.get('all', True)
            success_only = dependencies.get('success_only', success_only)
            dependencies = dependencies.get('dependencies', [])
        ids = []
        if isinstance(dependencies, AsyncResult):
            ids.extend(AsyncResult.msg_ids)
        else:
            for d in dependencies:
                if isinstance(d, basestring):
                    ids.append(d)
                elif isinstance(d, AsyncResult):
                    ids.extend(d.msg_ids)
                else:
                    raise TypeError("invalid dependency type: %r"%type(d))
        set.__init__(self, ids)
        self.all = all
        self.success_only=success_only
    
    def check(self, completed, failed=None):
        if failed is not None and not self.success_only:
            completed = completed.union(failed)
        if len(self) == 0:
            return True
        if self.all:
            return self.issubset(completed)
        else:
            return not self.isdisjoint(completed)
    
    def unreachable(self, failed):
        if len(self) == 0 or len(failed) == 0 or not self.success_only:
            return False
        # print self, self.success_only, self.all, failed
        if self.all:
            return not self.isdisjoint(failed)
        else:
            return self.issubset(failed)
        
    
    def as_dict(self):
        """Represent this dependency as a dict. For json compatibility."""
        return dict(
            dependencies=list(self),
            all=self.all,
            success_only=self.success_only,
        )
    

__all__ = ['depend', 'require', 'dependent', 'Dependency']


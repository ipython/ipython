"""Dependency utilities

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from types import ModuleType

from IPython.parallel.client.asyncresult import AsyncResult
from IPython.parallel.error import UnmetDependency
from IPython.parallel.util import interactive
from IPython.utils import py3compat
from IPython.utils.pickleutil import can, uncan

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
    
    def check_dependency(self):
        if self.df(*self.dargs, **self.dkwargs) is False:
            raise UnmetDependency()
    
    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)
    
    if not py3compat.PY3:
        @property
        def __name__(self):
            return self.func_name

@interactive
def _require(*modules, **mapping):
    """Helper for @require decorator."""
    from IPython.parallel.error import UnmetDependency
    from IPython.utils.pickleutil import uncan
    user_ns = globals()
    for name in modules:
        try:
            exec 'import %s' % name in user_ns
        except ImportError:
            raise UnmetDependency(name)
            
    for name, cobj in mapping.items():
        user_ns[name] = uncan(cobj, user_ns)
    return True

def require(*objects, **mapping):
    """Simple decorator for requiring local objects and modules to be available
    when the decorated function is called on the engine.
    
    Modules specified by name or passed directly will be imported
    prior to calling the decorated function.
    
    Objects other than modules will be pushed as a part of the task.
    Functions can be passed positionally,
    and will be pushed to the engine with their __name__.
    Other objects can be passed by keyword arg.
    
    Examples
    --------
    
    In [1]: @require('numpy')
       ...: def norm(a):
       ...:     return numpy.linalg.norm(a,2)

    In [2]: foo = lambda x: x*x
    In [3]: @require(foo)
       ...: def bar(a):
       ...:     return foo(1-a)
    """
    names = []
    for obj in objects:
        if isinstance(obj, ModuleType):
            obj = obj.__name__
        
        if isinstance(obj, basestring):
            names.append(obj)
        elif hasattr(obj, '__name__'):
            mapping[obj.__name__] = obj
        else:
            raise TypeError("Objects other than modules and functions "
                "must be passed by kwarg, but got: %s" % type(obj)
            )
    
    for name, obj in mapping.items():
        mapping[name] = can(obj)
    return depend(_require, *names, **mapping)

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
    success : bool [default True]
        Whether to consider successes as fulfilling dependencies.
    failure : bool [default False]
        Whether to consider failures as fulfilling dependencies.
    
    If `all=success=True` and `failure=False`, then the task will fail with an ImpossibleDependency
        as soon as the first depended-upon task fails.
    """
    
    all=True
    success=True
    failure=True
    
    def __init__(self, dependencies=[], all=True, success=True, failure=False):
        if isinstance(dependencies, dict):
            # load from dict
            all = dependencies.get('all', True)
            success = dependencies.get('success', success)
            failure = dependencies.get('failure', failure)
            dependencies = dependencies.get('dependencies', [])
        ids = []
        
        # extract ids from various sources:
        if isinstance(dependencies, (basestring, AsyncResult)):
            dependencies = [dependencies]
        for d in dependencies:
            if isinstance(d, basestring):
                ids.append(d)
            elif isinstance(d, AsyncResult):
                ids.extend(d.msg_ids)
            else:
                raise TypeError("invalid dependency type: %r"%type(d))
        
        set.__init__(self, ids)
        self.all = all
        if not (success or failure):
            raise ValueError("Must depend on at least one of successes or failures!")
        self.success=success
        self.failure = failure
    
    def check(self, completed, failed=None):
        """check whether our dependencies have been met."""
        if len(self) == 0:
            return True
        against = set()
        if self.success:
            against = completed
        if failed is not None and self.failure:
            against = against.union(failed)
        if self.all:
            return self.issubset(against)
        else:
            return not self.isdisjoint(against)
    
    def unreachable(self, completed, failed=None):
        """return whether this dependency has become impossible."""
        if len(self) == 0:
            return False
        against = set()
        if not self.success:
            against = completed
        if failed is not None and not self.failure:
            against = against.union(failed)
        if self.all:
            return not self.isdisjoint(against)
        else:
            return self.issubset(against)
        
    
    def as_dict(self):
        """Represent this dependency as a dict. For json compatibility."""
        return dict(
            dependencies=list(self),
            all=self.all,
            success=self.success,
            failure=self.failure
        )


__all__ = ['depend', 'require', 'dependent', 'Dependency']


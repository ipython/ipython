"""Dependency utilities"""

from IPython.external.decorator import decorator
from error import UnmetDependency


# flags
ALL = 1 << 0
ANY = 1 << 1
HERE = 1 << 2
ANYWHERE = 1 << 3


class depend(object):
    """Dependency decorator, for use with tasks."""
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
    for name in names:
        try:
            __import__(name)
        except ImportError:
            return False
    return True

def require(*names):
    return depend(_require, *names)

class Dependency(set):
    """An object for representing a set of msg_id dependencies.
    
    Subclassed from set()."""
    
    mode='all'
    success_only=True
    
    def __init__(self, dependencies=[], mode='all', success_only=True):
        if isinstance(dependencies, dict):
            # load from dict
            mode = dependencies.get('mode', mode)
            success_only = dependencies.get('success_only', success_only)
            dependencies = dependencies.get('dependencies', [])
        set.__init__(self, dependencies)
        self.mode = mode.lower()
        self.success_only=success_only
        if self.mode not in ('any', 'all'):
            raise NotImplementedError("Only any|all supported, not %r"%mode)
    
    def check(self, completed, failed=None):
        if failed is not None and not self.success_only:
            completed = completed.union(failed)
        if len(self) == 0:
            return True
        if self.mode == 'all':
            return self.issubset(completed)
        elif self.mode == 'any':
            return not self.isdisjoint(completed)
        else:
            raise NotImplementedError("Only any|all supported, not %r"%mode)
    
    def unreachable(self, failed):
        if len(self) == 0 or len(failed) == 0 or not self.success_only:
            return False
        print self, self.success_only, self.mode, failed
        if self.mode == 'all':
            return not self.isdisjoint(failed)
        elif self.mode == 'any':
            return self.issubset(failed)
        else:
            raise NotImplementedError("Only any|all supported, not %r"%mode)
        
    
    def as_dict(self):
        """Represent this dependency as a dict. For json compatibility."""
        return dict(
            dependencies=list(self),
            mode=self.mode,
            success_only=self.success_only,
        )
    

__all__ = ['depend', 'require', 'Dependency']


"""Dependency utilities"""

from IPython.external.decorator import decorator

# flags
ALL = 1 << 0
ANY = 1 << 1
HERE = 1 << 2
ANYWHERE = 1 << 3

class UnmetDependency(Exception):
    pass

class depend2(object):
    """dependency decorator"""
    def __init__(self, f, *args, **kwargs):
        print "Inside __init__()"
        self.dependency = (f,args,kwargs)
    
    def __call__(self, f, *args, **kwargs):
        f._dependency = self.dependency
        return decorator(_depend_wrapper, f)
    
class depend(object):
    """Dependency decorator, for use with tasks."""
    def __init__(self, f, *args, **kwargs):
        print "Inside __init__()"
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
        self.func_name = self.f.func_name
        self.df = df
        self.dargs = dargs
        self.dkwargs = dkwargs

    def __call__(self, *args, **kwargs):
        if self.df(*self.dargs, **self.dkwargs) is False:
            raise UnmetDependency()
        return self.f(*args, **kwargs)

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
    """An object for representing a set of dependencies.
    
    Subclassed from set()."""
    
    mode='all'
    
    def __init__(self, dependencies=[], mode='all'):
        if isinstance(dependencies, dict):
            # load from dict
            dependencies = dependencies.get('dependencies', [])
            mode = dependencies.get('mode', mode)
        set.__init__(self, dependencies)
        self.mode = mode.lower()
        if self.mode not in ('any', 'all'):
            raise NotImplementedError("Only any|all supported, not %r"%mode)
    
    def check(self, completed):
        if len(self) == 0:
            return True
        if self.mode == 'all':
            for dep in self:
                if dep not in completed:
                    return False
            return True
        elif self.mode == 'any':
            for com in completed:
                if com in self.dependencies:
                    return True
            return False
    
    def as_dict(self):
        """Represent this dependency as a dict. For json compatibility."""
        return dict(
            dependencies=list(self),
            mode=self.mode
        )
    

__all__ = ['UnmetDependency', 'depend', 'require', 'Dependency']


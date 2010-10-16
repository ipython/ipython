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

def evaluate_dependency(deps):
    """Evaluate wheter dependencies are met.
    
    Parameters
    ----------
    deps : dict
    """
    pass

def _check_dependency(flag):
    pass


__all__ = ['UnmetDependency', 'depend', 'evaluate_dependencies']
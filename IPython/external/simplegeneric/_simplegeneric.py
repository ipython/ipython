#Name: simplegeneric
#Version: 0.6
#Summary: Simple generic functions (similar to Python's own len(), pickle.dump(), etc.)
#Home-page: http://cheeseshop.python.org/pypi/simplegeneric
#Author: Phillip J. Eby
#Author-email: peak@eby-sarna.com
#License: PSF or ZPL

# This is version 0.6 of Philip J. Eby's simplegeneric module
# (http://cheeseshop.python.org/pypi/simplegeneric) patched to work
# with Python 2.3 (which doesn't support assigning to __name__)

__all__ = ["generic"]


from types import ClassType, InstanceType
classtypes = type, ClassType

def generic(func):
    """Create a simple generic function"""

    _sentinel = object()

    def _by_class(*args, **kw):
        cls = args[0].__class__
        for t in type(cls.__name__, (cls,object), {}).__mro__:
            f = _gbt(t, _sentinel)
            if f is not _sentinel:
                return f(*args, **kw)
        else:
            return func(*args, **kw)

    _by_type = {object: func, InstanceType: _by_class}
    _gbt = _by_type.get

    def when_type(t):
        """Decorator to add a method that will be called for type `t`"""
        if not isinstance(t, classtypes):
            raise TypeError(
                "%r is not a type or class" % (t,)
            )
        def decorate(f):
            if _by_type.setdefault(t,f) is not f:
                raise TypeError(
                    "%r already has method for type %r" % (func, t)
                )
            return f
        return decorate






    _by_object = {}
    _gbo = _by_object.get

    def when_object(o):
        """Decorator to add a method that will be called for object `o`"""
        def decorate(f):
            if _by_object.setdefault(id(o), (o,f))[1] is not f:
                raise TypeError(
                    "%r already has method for object %r" % (func, o)
                )
            return f
        return decorate


    def dispatch(*args, **kw):
        f = _gbo(id(args[0]), _sentinel)
        if f is _sentinel:
            for t in type(args[0]).__mro__:
                f = _gbt(t, _sentinel)
                if f is not _sentinel:
                    return f(*args, **kw)
            else:
                return func(*args, **kw)
        else:
            return f[1](*args, **kw)

    try:
        dispatch.__name__       = func.__name__
    except TypeError:
        pass
    dispatch.__dict__       = func.__dict__.copy()
    dispatch.__doc__        = func.__doc__
    dispatch.__module__     = func.__module__

    dispatch.when_type = when_type
    dispatch.when_object = when_object
    dispatch.default = func
    dispatch.has_object = lambda o: id(o) in _by_object
    dispatch.has_type   = lambda t: t in _by_type
    return dispatch




def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'README.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )




































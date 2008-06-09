"""Parametric testing on top of twisted.trial.unittest.

"""

__all__ = ['parametric','Parametric']

from twisted.trial.unittest import TestCase

def partial(f, *partial_args, **partial_kwargs):
    """Generate a partial class method.

    """
    def partial_func(self, *args, **kwargs):
        dikt = dict(kwargs)
        dikt.update(partial_kwargs)
        return f(self, *(partial_args+args), **dikt)

    return partial_func

def parametric(f):
    """Mark f as a parametric test.

    """
    f._parametric = True
    return classmethod(f)

def Parametric(cls):
    """Register parametric tests with a class.

    """
    # Walk over all tests marked with @parametric
    test_generators = [getattr(cls,f) for f in dir(cls)
                    if f.startswith('test')]
    test_generators = [m for m in test_generators if hasattr(m,'_parametric')]
    for test_gen in test_generators:
        test_name = test_gen.func_name

        # Insert a new test for each parameter
        for n,test_and_params in enumerate(test_gen()):
            test_method = test_and_params[0]
            test_params = test_and_params[1:]

            # Here we use partial (defined above), which returns a
            # class method of type ``types.FunctionType``, unlike
            # functools.partial which returns a function of type
            # ``functools.partial``.
            partial_func = partial(test_method,*test_params)
            # rename the test to look like a testcase
            partial_func.__name__ = 'test_' + partial_func.__name__

            # insert the new function into the class as a test
            setattr(cls, test_name + '_%s' % n, partial_func)

        # rename test generator so it isn't called again by nose
        test_gen.im_func.func_name = '__done_' + test_name

try:
    from numpy.testing import *
    from numpy.testing import dec
    from numpy.testing.noseclasses import KnownFailure
except ImportError:
    from ._decorators import *
    try:
        from ._numpy_testing_noseclasses import KnownFailure
    except ImportError:
        pass

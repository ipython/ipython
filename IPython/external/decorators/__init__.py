try:
    from numpy.testing.decorators import *
    from numpy.testing.noseclasses import KnownFailure
except ImportError:
    from _decorators import *
    # KnownFailure imported in _decorators from local version of
    # noseclasses which is in _numpy_testing_noseclasses

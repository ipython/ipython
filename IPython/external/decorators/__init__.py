try:
    from numpy.testing.noseclasses import KnownFailure, knownfailureif
except ImportError:
    from ._decorators import knownfailureif
    try:
        from ._numpy_testing_noseclasses import KnownFailure
    except ImportError:
        pass

try:
    from pickleshare import *
except ImportError:
    from ._pickleshare import *

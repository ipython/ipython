from IPython.utils.version import check_version
try:
    import argparse
    # don't use system argparse if older than 1.1:
    if not check_version(argparse.__version__, '1.1'):
        raise ImportError
    else:
        from argparse import *
        from argparse import SUPPRESS
except (ImportError, AttributeError):
    from _argparse import *
    from _argparse import SUPPRESS

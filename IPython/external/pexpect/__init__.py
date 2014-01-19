import sys
if sys.platform != 'cli':
    try:
        import pexpect
        from pexpect import *
    except ImportError:
        from ._pexpect import *
del sys

try:
    import pexpect
    from pexpect import *
    # pexpect-u-2.5 has a spawnb, but version 2.5 excludes it from __all__,
    # so we must explicitly fetch it
    if hasattr(pexpect, 'spawnb'):
        spawnb = pexpect.spawnb
except ImportError:
    from _pexpect import *

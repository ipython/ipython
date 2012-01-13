"""
Run this script in the qtconsole with one of:

    %loadpy hb_gil.py

or
    %run hb_gil.py

Holding the GIL for too long could disrupt the heartbeat.

See Issue #1260: https://github.com/ipython/ipython/issues/1260

"""

import sys
import time

from cython import inline

def gilsleep(t):
    """gil-holding sleep with cython.inline"""
    code = '\n'.join([
        'from posix cimport unistd',
        'unistd.sleep(t)',
    ])
    while True:
        inline(code, quiet=True, t=t)
        print time.time()
        sys.stdout.flush() # this is important

gilsleep(5)

# encoding: utf-8
"""
Enables gevent to be used interactively.

Authors: Dave Foster <daf@minuslab.net>
"""

# learn more about gevent's monkeypatching:
# http://www.gevent.org/intro.html#monkey-patching
from gevent import monkey, sleep; monkey.patch_all()

import os
import sys
from IPython.lib.inputhook import stdin_ready

def inputhook_gevent():
    try:
        while not stdin_ready():
            sleep(0.05)
    except KeyboardInterrupt:
        pass

    return 0

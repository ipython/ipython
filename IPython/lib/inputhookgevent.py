# encoding: utf-8
"""
Enables gevent to be used interactively.

Authors: Dave Foster <daf@minuslab.net>
"""

import gevent
from gevent import monkey; monkey.patch_all()

import os
import sys

if os.name == 'posix':
    import select

    def stdin_ready():
        infds, outfds, erfds = select.select([sys.stdin],[],[],0)
        if infds:
            return True
        else:
            return False
else:
    raise RuntimeError("Not supported")

def inputhook_gevent():
    try:
        while not stdin_ready():
            gevent.sleep(0.05)
    except KeyboardInterrupt:
        pass

    return 0

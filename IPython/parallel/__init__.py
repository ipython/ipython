"""The IPython ZMQ-based parallel computing interface.

Authors:

* MinRK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import warnings

import zmq

from IPython.zmq import check_for_zmq

if os.name == 'nt':
    min_pyzmq = '2.1.7'
else:
    min_pyzmq = '2.1.4'

check_for_zmq(min_pyzmq, 'IPython.parallel')

from IPython.utils.pickleutil import Reference

from .client.asyncresult import *
from .client.client import Client
from .client.remotefunction import *
from .client.view import *
from .controller.dependency import *



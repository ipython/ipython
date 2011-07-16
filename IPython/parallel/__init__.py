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


if os.name == 'nt':
    if zmq.__version__ < '2.1.7':
        raise ImportError("IPython.parallel requires pyzmq/0MQ >= 2.1.7 on Windows, "
        "and you appear to have %s"%zmq.__version__)
elif zmq.__version__ < '2.1.4':
    raise ImportError("IPython.parallel requires pyzmq/0MQ >= 2.1.4, you appear to have %s"%zmq.__version__)

if zmq.zmq_version() >= '3.0.0':
    warnings.warn("""libzmq 3 detected.
    It is unlikely that IPython's zmq code will work properly.
    Please install libzmq stable, which is 2.1.x or 2.2.x""",
    RuntimeWarning)


from IPython.utils.pickleutil import Reference

from .client.asyncresult import *
from .client.client import Client
from .client.remotefunction import *
from .client.view import *
from .controller.dependency import *



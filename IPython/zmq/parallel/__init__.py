"""The IPython ZMQ-based parallel computing interface."""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import zmq

if zmq.__version__ < '2.1.3':
    raise ImportError("IPython.zmq.parallel requires pyzmq/0MQ >= 2.1.3, you appear to have %s"%zmq.__version__)

from .asyncresult import *
from .client import Client
from .dependency import *
from .remotefunction import *
from .view import *



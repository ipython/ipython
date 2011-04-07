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

if zmq.__version__ < '2.1.4':
    raise ImportError("IPython.parallel requires pyzmq/0MQ >= 2.1.4, you appear to have %s"%zmq.__version__)

from IPython.utils.pickleutil import Reference

from .client.asyncresult import *
from .client.client import Client
from .client.remotefunction import *
from .client.view import *
from .controller.dependency import *



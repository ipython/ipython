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

import os
import zmq


if os.name == 'nt':
    if zmq.__version__ < '2.1dev':
        raise ImportError("On Windows, IPython.parallel depends on bugfixes only "
        "in current git master of pyzmq, you appear to have %s"%zmq.__version__)
elif zmq.__version__ < '2.1.4':
    raise ImportError("IPython.parallel requires pyzmq/0MQ >= 2.1.4, you appear to have %s"%zmq.__version__)

from IPython.utils.pickleutil import Reference

from .client.asyncresult import *
from .client.client import Client
from .client.remotefunction import *
from .client.view import *
from .controller.dependency import *



#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.4
#-----------------------------------------------------------------------------

import warnings

minimum_pyzmq_version = "2.1.4"

try:
    import zmq
except ImportError:
    raise ImportError("IPython.zmq requires pyzmq >= %s"%minimum_pyzmq_version)

pyzmq_version = zmq.__version__

if pyzmq_version < minimum_pyzmq_version:
    raise ImportError("IPython.zmq requires pyzmq >= %s, but you have %s"%(
                    minimum_pyzmq_version, pyzmq_version))

del pyzmq_version

if zmq.zmq_version() >= '3.0.0':
    warnings.warn("""libzmq 3 detected.
    It is unlikely that IPython's zmq code will work properly.
    Please install libzmq stable, which is 2.1.x or 2.2.x""",
    RuntimeWarning)


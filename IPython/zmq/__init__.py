#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.0.10
#-----------------------------------------------------------------------------

minimum_pyzmq_version = "2.0.10"

try:
    import zmq
except ImportError:
    raise ImportError("IPython.zmq requires pyzmq >= %s"%minimum_pyzmq_version)

pyzmq_version = zmq.__version__

if pyzmq_version < minimum_pyzmq_version:
    raise ImportError("IPython.zmq requires pyzmq >= %s, but you have %s"%(
                    minimum_pyzmq_version, pyzmq_version))

del pyzmq_version

""" An embedded (in-process) kernel. """

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Local imports.
from IPython.zmq.ipkernel import Kernel

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class EmbeddedKernel(Kernel):
    pass

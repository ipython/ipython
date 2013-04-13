#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Verify zmq version dependency >= 2.1.11
#-----------------------------------------------------------------------------

from IPython.utils.zmqrelated import check_for_zmq

check_for_zmq('2.1.11', 'IPython.kernel.zmq')

from .session import Session


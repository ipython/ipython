# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# Verify zmq version dependency

from IPython.utils.zmqrelated import check_for_zmq

check_for_zmq('13', 'IPython.kernel.zmq')

from .session import Session


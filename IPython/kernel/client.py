# encoding: utf-8

"""This module contains blocking clients for the controller interfaces.

Unlike the clients in `asyncclient.py`, the clients in this module are fully
blocking.  This means that methods on the clients return the actual results
rather than a deferred to the result.  Also, we manage the Twisted reactor
for you.  This is done by running the reactor in a thread.

The main classes in this module are:

    * MultiEngineClient
    * TaskClient
    * Task
    * CompositeError
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys

# from IPython.tools import growl
# growl.start("IPython1 Client")


from twisted.internet import reactor
from IPython.kernel.clientconnector import ClientConnector
from IPython.kernel.twistedutil import ReactorInThread
from IPython.kernel.twistedutil import blockingCallFromThread

# These enable various things 
from IPython.kernel import codeutil
import IPython.kernel.magic

# Other things that the user will need
from IPython.kernel.task import MapTask, StringTask
from IPython.kernel.error import CompositeError

#-------------------------------------------------------------------------------
# Code
#-------------------------------------------------------------------------------

_client_tub = ClientConnector()


def get_multiengine_client(furl_or_file=''):
    """Get the blocking MultiEngine client.
    
    :Parameters:
        furl_or_file : str
            A furl or a filename containing a furl.  If empty, the
            default furl_file will be used
            
    :Returns:
        The connected MultiEngineClient instance
    """
    client = blockingCallFromThread(_client_tub.get_multiengine_client, 
        furl_or_file)
    return client.adapt_to_blocking_client()

def get_task_client(furl_or_file=''):
    """Get the blocking Task client.
    
    :Parameters:
        furl_or_file : str
            A furl or a filename containing a furl.  If empty, the
            default furl_file will be used
            
    :Returns:
        The connected TaskClient instance
    """
    client = blockingCallFromThread(_client_tub.get_task_client, 
        furl_or_file)
    return client.adapt_to_blocking_client()


MultiEngineClient = get_multiengine_client
TaskClient = get_task_client



# Now we start the reactor in a thread
rit = ReactorInThread()
rit.setDaemon(True)
rit.start()
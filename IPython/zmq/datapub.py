"""Publishing
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config import Configurable
from IPython.embedded.socket import SocketABC
from IPython.utils.jsonutil import json_clean
from IPython.utils.traitlets import Instance, Dict, CBytes
from IPython.zmq.serialize import serialize_object
from IPython.zmq.session import Session, extract_header

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class ZMQDataPublisher(Configurable):

    topic = topic = CBytes(b'datapub')
    session = Instance(Session)
    pub_socket = Instance(SocketABC)
    parent_header = Dict({})

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)
    
    def publish_data(self, data):
        """publish a data_message on the IOPub channel
    
        Parameters
        ----------
    
        data : dict
            The data to be published. Think of it as a namespace.
        """
        session = self.session
        buffers = serialize_object(data,
            buffer_threshold=session.buffer_threshold,
            item_threshold=session.item_threshold,
        )
        content = json_clean(dict(keys=data.keys()))
        session.send(self.pub_socket, 'data_message', content=content,
            parent=self.parent_header,
            buffers=buffers,
            ident=self.topic,
        )


def publish_data(data):
    """publish a data_message on the IOPub channel
    
    Parameters
    ----------
    
    data : dict
        The data to be published. Think of it as a namespace.
    """
    from IPython.zmq.zmqshell import ZMQInteractiveShell
    ZMQInteractiveShell.instance().data_pub.publish_data(data)

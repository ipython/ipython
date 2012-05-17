"""A module that allows custom user messages to be sent from the kernel.

This module provides a :class:`UserMessage` class that allows a user to send
custom messages from the kernel to a given pub socket.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class UserMessage(object):
    """An object that lets the user send user messages to a 0MQ PUB socket."""

    topic=None

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def send(self,content):
        if not isinstance(content, dict):
            raise ValueError("Message must be a dictionary")
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            msg = self.session.send(self.pub_socket, u'user', content=content,
                                    parent=self.parent_header, ident=self.topic)


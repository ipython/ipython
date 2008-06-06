# encoding: utf-8

"""Storage for the responses from the interpreter."""

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


class IMessageCache(object):
    """ Storage for the response from the interpreter.
    """

    def add_message(self, i, message):
        """ Add a message dictionary to the cache.

        Parameters
        ----------
        i : int
        message : dict
        """

    def get_message(self, i=None):
        """ Get the message from the cache.

        Parameters
        ----------
        i : int, optional
            The number of the message. If not provided, return the
            highest-numbered message.

        Returns
        -------
        message : dict

        Raises
        ------
        IndexError if the message does not exist in the cache.
        """


class SimpleMessageCache(object):
    """ Simple dictionary-based, in-memory storage of the responses from the
    interpreter.
    """

    def __init__(self):
        self.cache = {}

    def add_message(self, i, message):
        """ Add a message dictionary to the cache.

        Parameters
        ----------
        i : int
        message : dict
        """

        self.cache[i] = message

    def get_message(self, i=None):
        """ Get the message from the cache.

        Parameters
        ----------
        i : int, optional
            The number of the message. If not provided, return the
            highest-numbered message.

        Returns
        -------
        message : dict

        Raises
        ------
        IndexError if the message does not exist in the cache.
        """
        if i is None:
            keys = self.cache.keys()
            if len(keys) == 0:
                raise IndexError("index %r out of range" % i)
            else:
                i = max(self.cache.keys())
        try:
            return self.cache[i]
        except KeyError:
            # IndexError is more appropriate, here.
            raise IndexError("index %r out of range" % i)


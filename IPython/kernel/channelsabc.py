"""Abstract base classes for kernel client channels"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import abc

from IPython.utils.py3compat import with_metaclass


class ChannelABC(with_metaclass(abc.ABCMeta, object)):
    """A base class for all channel ABCs."""

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def is_alive(self):
        pass


class ShellChannelABC(ChannelABC):
    """ShellChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.channels.ShellChannel`
    """


class IOPubChannelABC(ChannelABC):
    """IOPubChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.channels.IOPubChannel`
    """

    @abc.abstractmethod
    def flush(self, timeout=1.0):
        pass


class StdInChannelABC(ChannelABC):
    """StdInChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.channels.StdInChannel`
    """



class HBChannelABC(ChannelABC):
    """HBChannel ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.channels.HBChannel`
    """

    @abc.abstractproperty
    def time_to_dead(self):
        pass

    @abc.abstractmethod
    def pause(self):
        pass

    @abc.abstractmethod
    def unpause(self):
        pass

    @abc.abstractmethod
    def is_beating(self):
        pass

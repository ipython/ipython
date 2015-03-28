"""Base classes to manage a Client's interaction with a running kernel"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

import atexit
import errno
from threading import Thread
import time

import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError

from IPython.core.release import kernel_protocol_version_info

from .channelsabc import HBChannelABC

#-----------------------------------------------------------------------------
# Constants and exceptions
#-----------------------------------------------------------------------------

major_protocol_version = kernel_protocol_version_info[0]

class InvalidPortNumber(Exception):
    pass

class HBChannel(Thread):
    """The heartbeat channel which monitors the kernel heartbeat.

    Note that the heartbeat channel is paused by default. As long as you start
    this channel, the kernel manager will ensure that it is paused and un-paused
    as appropriate.
    """
    context = None
    session = None
    socket = None
    address = None
    _exiting = False

    time_to_dead = 1.
    poller = None
    _running = None
    _pause = None
    _beating = None

    def __init__(self, context=None, session=None, address=None):
        """Create the heartbeat monitor thread.

        Parameters
        ----------
        context : :class:`zmq.Context`
            The ZMQ context to use.
        session : :class:`session.Session`
            The session to use.
        address : zmq url
            Standard (ip, port) tuple that the kernel is listening on.
        """
        super(HBChannel, self).__init__()
        self.daemon = True

        self.context = context
        self.session = session
        if isinstance(address, tuple):
            if address[1] == 0:
                message = 'The port number for a channel cannot be 0.'
                raise InvalidPortNumber(message)
            address = "tcp://%s:%i" % address
        self.address = address
        atexit.register(self._notice_exit)

        self._running = False
        self._pause = True
        self.poller = zmq.Poller()

    def _notice_exit(self):
        self._exiting = True

    def _create_socket(self):
        if self.socket is not None:
            # close previous socket, before opening a new one
            self.poller.unregister(self.socket)
            self.socket.close()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.linger = 1000
        self.socket.connect(self.address)

        self.poller.register(self.socket, zmq.POLLIN)

    def _poll(self, start_time):
        """poll for heartbeat replies until we reach self.time_to_dead.

        Ignores interrupts, and returns the result of poll(), which
        will be an empty list if no messages arrived before the timeout,
        or the event tuple if there is a message to receive.
        """

        until_dead = self.time_to_dead - (time.time() - start_time)
        # ensure poll at least once
        until_dead = max(until_dead, 1e-3)
        events = []
        while True:
            try:
                events = self.poller.poll(1000 * until_dead)
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    # ignore interrupts during heartbeat
                    # this may never actually happen
                    until_dead = self.time_to_dead - (time.time() - start_time)
                    until_dead = max(until_dead, 1e-3)
                    pass
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break
        return events

    def run(self):
        """The thread's main activity.  Call start() instead."""
        self._create_socket()
        self._running = True
        self._beating = True

        while self._running:
            if self._pause:
                # just sleep, and skip the rest of the loop
                time.sleep(self.time_to_dead)
                continue

            since_last_heartbeat = 0.0
            # io.rprint('Ping from HB channel') # dbg
            # no need to catch EFSM here, because the previous event was
            # either a recv or connect, which cannot be followed by EFSM
            self.socket.send(b'ping')
            request_time = time.time()
            ready = self._poll(request_time)
            if ready:
                self._beating = True
                # the poll above guarantees we have something to recv
                self.socket.recv()
                # sleep the remainder of the cycle
                remainder = self.time_to_dead - (time.time() - request_time)
                if remainder > 0:
                    time.sleep(remainder)
                continue
            else:
                # nothing was received within the time limit, signal heart failure
                self._beating = False
                since_last_heartbeat = time.time() - request_time
                self.call_handlers(since_last_heartbeat)
                # and close/reopen the socket, because the REQ/REP cycle has been broken
                self._create_socket()
                continue

    def pause(self):
        """Pause the heartbeat."""
        self._pause = True

    def unpause(self):
        """Unpause the heartbeat."""
        self._pause = False

    def is_beating(self):
        """Is the heartbeat running and responsive (and not paused)."""
        if self.is_alive() and not self._pause and self._beating:
            return True
        else:
            return False

    def stop(self):
        """Stop the channel's event loop and join its thread."""
        self._running = False
        self.join()
        self.close()

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None

    def call_handlers(self, since_last_heartbeat):
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        pass


HBChannelABC.register(HBChannel)

# -*- coding: utf-8 -*-
"""
    sockjs.tornado.sessioncontainer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple heapq-based session implementation with sliding expiration window
    support.
"""

from heapq import heappush, heappop
from time import time
from hashlib import md5
from random import random


def _random_key():
    """Return random session key"""
    i = md5()
    i.update('%s%s' % (random(), time()))
    return i.hexdigest()


class SessionMixin(object):
    """Represents one session object stored in the session container.
    Derive from this object to store additional data.
    """

    def __init__(self, session_id=None, expiry=None):
        """Constructor.

        ``session_id``
            Optional session id. If not provided, will generate
            new session id.
        ``expiry``
            Expiration time. If not provided, will never expire.
        """
        self.session_id = session_id or _random_key()
        self.promoted = None
        self.expiry = expiry

        if self.expiry is not None:
            self.expiry_date = time() + self.expiry

    def is_alive(self):
        """Check if session is still alive"""
        return self.expiry_date > time()

    def promote(self):
        """Mark object as alive, so it won't be collected during next
        run of the garbage collector.
        """
        if self.expiry is not None:
            self.promoted = time() + self.expiry

    def on_delete(self, forced):
        """Triggered when object was expired or deleted."""
        pass

    def __cmp__(self, other):
        return cmp(self.expiry_date, other.expiry_date)

    def __repr__(self):
        return '%f %s %d' % (getattr(self, 'expiry_date', -1),
                             self.session_id,
                             self.promoted or 0)


class SessionContainer(object):
    """Session container object.

    If we will implement sessions with Tornado timeouts, for polling transports
    it will be nightmare - if load will be high, number of discarded timeouts
    will be huge and will be huge performance hit, as Tornado will have to
    clean them up all the time.
    """
    def __init__(self):
        self._items = dict()
        self._queue = []

    def add(self, session):
        """Add session to the container.

        `session`
            Session object
        """
        self._items[session.session_id] = session

        if session.expiry is not None:
            heappush(self._queue, session)

    def get(self, session_id):
        """Return session object or None if it is not available

        `session_id`
            Session identifier
        """
        return self._items.get(session_id, None)

    def remove(self, session_id):
        """Remove session object from the container

        `session_id`
            Session identifier
        """
        session = self._items.get(session_id, None)

        if session is not None:
            session.promoted = -1
            session.on_delete(True)
            del self._items[session_id]
            return True

        return False

    def expire(self, current_time=None):
        """Expire any old entries

        `current_time`
            Optional time to be used to clean up queue (can be used in unit tests)
        """
        if not self._queue:
            return

        if current_time is None:
            current_time = time()

        while self._queue:
            # Get top most item
            top = self._queue[0]

            # Early exit if item was not promoted and its expiration time
            # is greater than now.
            if top.promoted is None and top.expiry_date > current_time:
                break

            # Pop item from the stack
            top = heappop(self._queue)

            need_reschedule = (top.promoted is not None
                               and top.promoted > current_time)

            # Give chance to reschedule
            if not need_reschedule:
                top.promoted = None
                top.on_delete(False)

                need_reschedule = (top.promoted is not None
                                   and top.promoted > current_time)

            # If item is promoted and expiration time somewhere in future
            # just reschedule it
            if need_reschedule:
                top.expiry_date = top.promoted
                top.promoted = None
                heappush(self._queue, top)
            else:
                del self._items[top.session_id]

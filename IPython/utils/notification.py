# encoding: utf-8
"""
The IPython Core Notification Center.

See docs/source/development/notification_blueprint.txt for an overview of the
notification module.

Authors:

* Barry Wark
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class NotificationError(Exception):
    pass


class NotificationCenter(object):
    """Synchronous notification center.

    Examples
    --------
    Here is a simple example of how to use this::

        import IPython.util.notification as notification
        def callback(ntype, theSender, args={}):
            print ntype,theSender,args

        notification.sharedCenter.add_observer(callback, 'NOTIFICATION_TYPE', None)
        notification.sharedCenter.post_notification('NOTIFICATION_TYPE', object()) # doctest:+ELLIPSIS
        NOTIFICATION_TYPE ...
    """
    def __init__(self):
        super(NotificationCenter, self).__init__()
        self._init_observers()

    def _init_observers(self):
        """Initialize observer storage"""

        self.registered_types = set() #set of types that are observed
        self.registered_senders = set() #set of senders that are observed
        self.observers = {} #map (type,sender) => callback (callable)

    def post_notification(self, ntype, sender, *args, **kwargs):
        """Post notification to all registered observers.

        The registered callback will be called as::

            callback(ntype, sender, *args, **kwargs)

        Parameters
        ----------
        ntype : hashable
            The notification type.
        sender : hashable
            The object sending the notification.
        *args : tuple
            The positional arguments to be passed to the callback.
        **kwargs : dict
            The keyword argument to be passed to the callback.

        Notes
        -----
        * If no registered observers, performance is O(1).
        * Notificaiton order is undefined.
        * Notifications are posted synchronously.
        """

        if(ntype==None or sender==None):
            raise NotificationError(
                "Notification type and sender are required.")

        # If there are no registered observers for the type/sender pair
        if((ntype not in self.registered_types and
                None not in self.registered_types) or
            (sender not in self.registered_senders and
                None not in self.registered_senders)):
            return

        for o in self._observers_for_notification(ntype, sender):
            o(ntype, sender, *args, **kwargs)

    def _observers_for_notification(self, ntype, sender):
        """Find all registered observers that should recieve notification"""

        keys = (
                   (ntype,sender),
                   (ntype, None),
                   (None, sender),
                   (None,None)
               )

        obs = set()
        for k in keys:
            obs.update(self.observers.get(k, set()))

        return obs

    def add_observer(self, callback, ntype, sender):
        """Add an observer callback to this notification center.

        The given callback will be called upon posting of notifications of
        the given type/sender and will receive any additional arguments passed
        to post_notification.

        Parameters
        ----------
        callback : callable
            The callable that will be called by :meth:`post_notification`
            as ``callback(ntype, sender, *args, **kwargs)
        ntype : hashable
            The notification type. If None, all notifications from sender
            will be posted.
        sender : hashable
            The notification sender. If None, all notifications of ntype
            will be posted.
        """
        assert(callback != None)
        self.registered_types.add(ntype)
        self.registered_senders.add(sender)
        self.observers.setdefault((ntype,sender), set()).add(callback)

    def remove_all_observers(self):
        """Removes all observers from this notification center"""

        self._init_observers()



shared_center = NotificationCenter()

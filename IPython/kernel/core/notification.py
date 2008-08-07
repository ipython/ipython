# encoding: utf-8

"""The IPython Core Notification Center.

See docs/source/development/notification_blueprint.txt for an overview of the
notification module.
"""

__docformat__ = "restructuredtext en"
                                                                              
#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team                           
#                                                                             
#  Distributed under the terms of the BSD License.  The full license is in    
#  the file COPYING, distributed as part of this software.                    
#-----------------------------------------------------------------------------


class NotificationCenter(object):
    """Synchronous notification center
    
    Example
    -------
    >>> import IPython.kernel.core.notification as notification
    >>> def callback(theType, theSender, args={}):
    ...     print theType,theSender,args
    ...     
    >>> notification.sharedCenter.add_observer(callback, 'NOTIFICATION_TYPE', None)
    >>> notification.sharedCenter.post_notification('NOTIFICATION_TYPE', object()) # doctest:+ELLIPSIS
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
    
    
    def post_notification(self, theType, sender, **kwargs):
        """Post notification (type,sender,**kwargs) to all registered
        observers. 
        
        Implementation
        --------------
        * If no registered observers, performance is O(1).
        * Notificaiton order is undefined.
        * Notifications are posted synchronously.
        """
        
        if(theType==None or sender==None):
            raise Exception("NotificationCenter.post_notification requires \
                type and sender.")
        
        # If there are no registered observers for the type/sender pair
        if((theType not in self.registered_types and 
                None not in self.registered_types) or
            (sender not in self.registered_senders and 
                None not in self.registered_senders)):
            return
        
        for o in self._observers_for_notification(theType, sender):
            o(theType, sender, args=kwargs)
    
        
    def _observers_for_notification(self, theType, sender):
        """Find all registered observers that should recieve notification"""
        
        keys = (
                    (theType,sender),
                    (theType, None),
                    (None, sender),  
                    (None,None)
                )
        
        
        obs = set()
        for k in keys:
            obs.update(self.observers.get(k, set()))
        
        return obs
    
    
    def add_observer(self, callback, theType, sender):
        """Add an observer callback to this notification center.
        
        The given callback will be called upon posting of notifications of
        the given type/sender and will receive any additional kwargs passed
        to post_notification.
        
        Parameters
        ----------
        observerCallback : callable
            Callable. Must take at least two arguments::
                observerCallback(type, sender, args={})
        
        theType : hashable
            The notification type. If None, all notifications from sender
            will be posted.
        
        sender : hashable
            The notification sender. If None, all notifications of theType
            will be posted.
        """
        assert(callback != None)
        self.registered_types.add(theType)
        self.registered_senders.add(sender)
        self.observers.setdefault((theType,sender), set()).add(callback)
    
    def remove_all_observers(self):
        """Removes all observers from this notification center"""
        
        self._init_observers()
    


sharedCenter = NotificationCenter()
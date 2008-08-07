# encoding: utf-8

"""This file contains unittests for the notification.py module."""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team                           
#                                                                             
#  Distributed under the terms of the BSD License.  The full license is in    
#  the file COPYING, distributed as part of this software.                    
#-----------------------------------------------------------------------------
                                                                              
#-----------------------------------------------------------------------------
# Imports                                                                     
#-----------------------------------------------------------------------------

import unittest
import IPython.kernel.core.notification as notification
from nose.tools import timed

#
# Supporting test classes
#

class Observer(object):
    """docstring for Observer"""
    def __init__(self, expectedType, expectedSender, 
                    center=notification.sharedCenter, **kwargs):
        super(Observer, self).__init__()
        self.expectedType = expectedType
        self.expectedSender = expectedSender
        self.expectedKwArgs = kwargs
        self.recieved = False
        center.add_observer(self.callback, 
                            self.expectedType, 
                            self.expectedSender)
    
    
    def callback(self, theType, sender, args={}):
        """callback"""
        
        assert(theType == self.expectedType or
                self.expectedType == None)
        assert(sender == self.expectedSender or
                self.expectedSender == None)
        assert(args == self.expectedKwArgs)
        self.recieved = True
    
    
    def verify(self):
        """verify"""
        
        assert(self.recieved)
    
    def reset(self):
        """reset"""
        
        self.recieved = False
    


class Notifier(object):
    """docstring for Notifier"""
    def __init__(self, theType, **kwargs):
        super(Notifier, self).__init__()
        self.theType = theType
        self.kwargs = kwargs
    
    def post(self, center=notification.sharedCenter):
        """fire"""
        
        center.post_notification(self.theType, self,
            **self.kwargs)
    

#
# Test Cases
#

class NotificationTests(unittest.TestCase):
    """docstring for NotificationTests"""
    
    def tearDown(self):
        notification.sharedCenter.remove_all_observers()
    
    def test_notification_delivered(self):
        """Test that notifications are delivered"""
        expectedType = 'EXPECTED_TYPE'
        sender = Notifier(expectedType)
        observer = Observer(expectedType, sender)
        
        sender.post()
        
        observer.verify()
    
    
    def test_type_specificity(self):
        """Test that observers are registered by type"""
        
        expectedType = 1
        unexpectedType = "UNEXPECTED_TYPE"
        sender = Notifier(expectedType)
        unexpectedSender = Notifier(unexpectedType)
        observer = Observer(expectedType, sender)
    
        sender.post()
        unexpectedSender.post()
    
        observer.verify()
    
    
    def test_sender_specificity(self):
        """Test that observers are registered by sender"""
        
        expectedType = "EXPECTED_TYPE"
        sender1 = Notifier(expectedType)
        sender2 = Notifier(expectedType)
        observer = Observer(expectedType, sender1)
        
        sender1.post()
        sender2.post()
        
        observer.verify()
    
    
    def test_remove_all_observers(self):
        """White-box test for remove_all_observers"""
        
        for i in xrange(10):
            Observer('TYPE', None, center=notification.sharedCenter)
        
        self.assert_(len(notification.sharedCenter.observers[('TYPE',None)]) >= 10, 
            "observers registered")
        
        notification.sharedCenter.remove_all_observers()
        
        self.assert_(len(notification.sharedCenter.observers) == 0, "observers removed")
    
    
    def test_any_sender(self):
        """test_any_sender"""
        
        expectedType = "EXPECTED_TYPE"
        sender1 = Notifier(expectedType)
        sender2 = Notifier(expectedType)
        observer = Observer(expectedType, None)
        
        
        sender1.post()
        observer.verify()
        
        observer.reset()
        sender2.post()
        observer.verify()
        
    
    @timed(.01)
    def test_post_performance(self):
        """Test that post_notification, even with many registered irrelevant
        observers is fast"""
        
        for i in xrange(10):
            Observer("UNRELATED_TYPE", None)
        
        o = Observer('EXPECTED_TYPE', None)
        
        notification.sharedCenter.post_notification('EXPECTED_TYPE', self)
        
        o.verify()
    

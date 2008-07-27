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

from IPython.kernel.core.notification import NotificationCenter,\
                                            sharedCenter

#
# Supporting test classes
#

class Observer(object):
    """docstring for Observer"""
    def __init__(self, expectedType, expectedSender, **kwargs):
        super(Observer, self).__init__()
        self.expectedType = expectedType
        self.expectedSender = expectedSender
        self.expectedKwArgs = kwargs
        self.recieved = False
        sharedCenter.add_observer(self.callback, 
                                    self.expectedType, 
                                    self.expectedSender)
    
    
    def callback(self, theType, sender, args={}):
        """callback"""
        
        assert(theType == self.expectedType)
        assert(sender == self.expectedSender)
        assert(args == self.expectedKwArgs)
        self.recieved = True
    
    
    def verify(self):
        """verify"""
        
        assert(self.recieved)
    


class Notifier(object):
    """docstring for Notifier"""
    def __init__(self, theType, **kwargs):
        super(Notifier, self).__init__()
        self.theType = theType
        self.kwargs = kwargs
    
    def post(self, center=sharedCenter):
        """fire"""
        
        center.post_notification(self.theType, self,
            **self.kwargs)
    

#
# Test Cases
#


def test_notification_delivered():
    """Test that notifications are delivered"""
    expectedType = 'EXPECTED_TYPE'
    sender = Notifier(expectedType)
    observer = Observer(expectedType, sender)
    
    sender.post()
    
    observer.verify()


def test_type_specificity():
    """Test that observers are registered by type"""
    
    expectedType = 1
    unexpectedType = "UNEXPECTED_TYPE"
    sender = Notifier(expectedType)
    unexpectedSender = Notifier(unexpectedType)
    observer = Observer(expectedType, sender)
    
    sender.post()
    unexpectedSender.post()
    
    observer.verify()


def test_sender_specificity():
    """Test that observers are registered by sender"""
    
    expectedType = "EXPECTED_TYPE"
    sender1 = Notifier(expectedType)
    sender2 = Notifier(expectedType)
    observer = Observer(expectedType, sender1)
    
    sender1.post()
    sender2.post()
    
    observer.verify()


def test_complexity_with_no_observers():
    """Test that the notification center's algorithmic complexity is O(1)
    with no registered observers (for the given notification type)
    """
    
    assert(False) #I'm not sure how to test this yet

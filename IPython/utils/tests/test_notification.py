# encoding: utf-8

"""This file contains unittests for the notification.py module."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import unittest

from IPython.utils.notification import shared_center

#-----------------------------------------------------------------------------
# Support Classes
#-----------------------------------------------------------------------------


class Observer(object):

    def __init__(self, expected_ntype, expected_sender,
                    center=shared_center, *args, **kwargs):
        super(Observer, self).__init__()
        self.expected_ntype = expected_ntype
        self.expected_sender = expected_sender
        self.expected_args = args
        self.expected_kwargs = kwargs
        self.recieved = False
        center.add_observer(self.callback,
                            self.expected_ntype,
                            self.expected_sender)

    def callback(self, ntype, sender, *args, **kwargs):
        assert(ntype == self.expected_ntype or
                self.expected_ntype == None)
        assert(sender == self.expected_sender or
                self.expected_sender == None)
        assert(args == self.expected_args)
        assert(kwargs == self.expected_kwargs)
        self.recieved = True

    def verify(self):
        assert(self.recieved)

    def reset(self):
        self.recieved = False


class Notifier(object):

    def __init__(self, ntype, **kwargs):
        super(Notifier, self).__init__()
        self.ntype = ntype
        self.kwargs = kwargs

    def post(self, center=shared_center):

        center.post_notification(self.ntype, self,
            **self.kwargs)


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


class NotificationTests(unittest.TestCase):

    def tearDown(self):
        shared_center.remove_all_observers()

    def test_notification_delivered(self):
        """Test that notifications are delivered"""

        expected_ntype = 'EXPECTED_TYPE'
        sender = Notifier(expected_ntype)
        observer = Observer(expected_ntype, sender)

        sender.post()
        observer.verify()

    def test_type_specificity(self):
        """Test that observers are registered by type"""

        expected_ntype = 1
        unexpected_ntype = "UNEXPECTED_TYPE"
        sender = Notifier(expected_ntype)
        unexpected_sender = Notifier(unexpected_ntype)
        observer = Observer(expected_ntype, sender)

        sender.post()
        unexpected_sender.post()
        observer.verify()

    def test_sender_specificity(self):
        """Test that observers are registered by sender"""

        expected_ntype = "EXPECTED_TYPE"
        sender1 = Notifier(expected_ntype)
        sender2 = Notifier(expected_ntype)
        observer = Observer(expected_ntype, sender1)

        sender1.post()
        sender2.post()

        observer.verify()

    def test_remove_all_observers(self):
        """White-box test for remove_all_observers"""

        for i in xrange(10):
            Observer('TYPE', None, center=shared_center)

        self.assert_(len(shared_center.observers[('TYPE',None)]) >= 10,
            "observers registered")

        shared_center.remove_all_observers()
        self.assert_(len(shared_center.observers) == 0, "observers removed")

    def test_any_sender(self):
        expected_ntype = "EXPECTED_TYPE"
        sender1 = Notifier(expected_ntype)
        sender2 = Notifier(expected_ntype)
        observer = Observer(expected_ntype, None)

        sender1.post()
        observer.verify()

        observer.reset()
        sender2.post()
        observer.verify()

    def test_post_performance(self):
        """Test that post_notification, even with many registered irrelevant
        observers is fast"""

        for i in xrange(10):
            Observer("UNRELATED_TYPE", None)

        o = Observer('EXPECTED_TYPE', None)
        shared_center.post_notification('EXPECTED_TYPE', self)
        o.verify()



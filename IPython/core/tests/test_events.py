import unittest
try:  # Python 3.3 +
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from IPython.core import events
import IPython.testing.tools as tt

def ping_received():
    pass

class CallbackTests(unittest.TestCase):
    def setUp(self):
        self.em = events.EventManager(get_ipython(), {'ping_received': ping_received})
    
    def test_register_unregister(self):
        cb = Mock()

        self.em.register('ping_received', cb)        
        self.em.trigger('ping_received')
        self.assertEqual(cb.call_count, 1)
        
        self.em.unregister('ping_received', cb)
        self.em.trigger('ping_received')
        self.assertEqual(cb.call_count, 1)
    
    def test_reset(self):
        cb = Mock()
        self.em.register('ping_received', cb)
        self.em.reset('ping_received')
        self.em.trigger('ping_received')
        assert not cb.called
    
    def test_reset_all(self):
        cb = Mock()
        self.em.register('ping_received', cb)
        self.em.reset_all()
        self.em.trigger('ping_received')
        assert not cb.called
    
    def test_cb_error(self):
        cb = Mock(side_effect=ValueError)
        self.em.register('ping_received', cb)
        with tt.AssertPrints("Error in callback"):
            self.em.trigger('ping_received')
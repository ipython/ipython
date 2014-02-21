import unittest
try:  # Python 3.3 +
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from IPython.core import callbacks
import IPython.testing.tools as tt

def ping_received():
    pass

class CallbackTests(unittest.TestCase):
    def setUp(self):
        self.cbm = callbacks.CallbackManager(get_ipython(), {'ping_received': ping_received})
    
    def test_register_unregister(self):
        cb = Mock()

        self.cbm.register('ping_received', cb)        
        self.cbm.fire('ping_received')
        self.assertEqual(cb.call_count, 1)
        
        self.cbm.unregister('ping_received', cb)
        self.cbm.fire('ping_received')
        self.assertEqual(cb.call_count, 1)
    
    def test_reset(self):
        cb = Mock()
        self.cbm.register('ping_received', cb)
        self.cbm.reset('ping_received')
        self.cbm.fire('ping_received')
        assert not cb.called
    
    def test_reset_all(self):
        cb = Mock()
        self.cbm.register('ping_received', cb)
        self.cbm.reset_all()
        self.cbm.fire('ping_received')
        assert not cb.called
    
    def test_cb_error(self):
        cb = Mock(side_effect=ValueError)
        self.cbm.register('ping_received', cb)
        with tt.AssertPrints("Error in callback"):
            self.cbm.fire('ping_received')
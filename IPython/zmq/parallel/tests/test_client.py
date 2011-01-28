import time

from IPython.zmq.parallel.view import LoadBalancedView, DirectView

from clienttest import ClusterTestCase

class TestClient(ClusterTestCase):
    
    def test_ids(self):
        self.assertEquals(len(self.client.ids), 1)
        self.add_engines(3)
        self.wait_on_engines()
        self.assertEquals(self.client.ids, set(range(4)))
    
    def test_segfault(self):
        def segfault():
            import ctypes
            ctypes.memset(-1,0,1)
        self.client[0].apply(segfault)
        while 0 in self.client.ids:
            time.sleep(.01)
            self.client.spin()
    
    def test_view_indexing(self):
        self.add_engines(7)
        self.wait_on_engines()
        targets = self.client._build_targets('all')[-1]
        v = self.client[:]
        self.assertEquals(v.targets, targets)
        v =self.client[2]
        self.assertEquals(v.targets, 2)
        v =self.client[1,2]
        self.assertEquals(v.targets, [1,2])
        v =self.client[::2]
        self.assertEquals(v.targets, targets[::2])
        v =self.client[1::3]
        self.assertEquals(v.targets, targets[1::3])
        v =self.client[:-3]
        self.assertEquals(v.targets, targets[:-3])
        v =self.client[None]
        self.assert_(isinstance(v, LoadBalancedView))
        
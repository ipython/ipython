import time
from signal import SIGINT
from multiprocessing import Process

from zmq.tests import BaseZMQTestCase

from IPython.zmq.parallel.ipcluster import launch_process
from IPython.zmq.parallel.entry_point import select_random_ports
from IPython.zmq.parallel.client import Client
from IPython.zmq.parallel.tests import cluster_logs,add_engine


class ClusterTestCase(BaseZMQTestCase):
    
    def add_engines(self, n=1):
        """add multiple engines to our cluster"""
        for i in range(n):
            self.engines.append(add_engine())
    
    def wait_on_engines(self):
        """wait for our engines to connect."""
        while len(self.client.ids) < len(self.engines)+self.base_engine_count:
            time.sleep(0.1)
    
    def start_cluster(self, n=1):
        """start a cluster"""
        raise NotImplementedError("Don't use this anymore")
        rport = select_random_ports(1)[0]
        args = [ '--regport', str(rport), '--ip', '127.0.0.1' ]
        cp = launch_process('controller', args)
        eps = [ launch_process('engine', args+['--ident', 'engine-%i'%i]) for i in range(n) ]
        return rport, args, cp, eps
    
    def connect_client(self, port=None):
        """connect a client with my Context, and track its sockets for cleanup"""
        if port is None:
            port = cluster_logs['regport']
            c = Client('tcp://127.0.0.1:%i'%port,context=self.context)
        for name in filter(lambda n:n.endswith('socket'), dir(c)):
            self.sockets.append(getattr(c, name))
        return c
    
    def setUp(self):
        BaseZMQTestCase.setUp(self)
        self.client = self.connect_client()
        self.base_engine_count=len(self.client.ids)
        self.engines=[]
    
    def tearDown(self):
        [ e.terminate() for e in filter(lambda e: e.poll() is None, self.engines) ]
        # while len(self.client.ids) > self.base_engine_count:
        #     time.sleep(.1)
        del self.engines
        BaseZMQTestCase.tearDown(self)
        
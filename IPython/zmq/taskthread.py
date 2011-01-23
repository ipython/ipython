"""Thread for popping Tasks from zmq to Python Queue"""


import time
from threading import Thread

try:
    from queue import Queue
except:
    from Queue import Queue

import zmq
from zmq.core.poll import _poll as poll
from zmq.devices import ThreadDevice
from IPython.zmq import streamsession as ss


class QueueStream(object):
    def __init__(self, in_queue, out_queue):
        self.in_queue = in_queue
        self.out_queue = out_queue
    
    def send_multipart(self, *args, **kwargs):
        while self.out_queue.full():
            time.sleep(1e-3)
        self.out_queue.put(('send_multipart', args, kwargs))
    
    def send(self, *args, **kwargs):
        while self.out_queue.full():
            time.sleep(1e-3)
        self.out_queue.put(('send', args, kwargs))
    
    def recv_multipart(self):
        return self.in_queue.get()
    
    def empty(self):
        return self.in_queue.empty()

class TaskThread(ThreadDevice):
    """Class for popping Tasks from C-ZMQ->Python Queue"""
    max_qsize = 100
    in_socket = None
    out_socket = None
    # queue = None
    
    def __init__(self, queue_type, mon_type, engine_id, max_qsize=100):
        ThreadDevice.__init__(self, 0, queue_type, mon_type)
        self.session = ss.StreamSession(username='TaskNotifier[%s]'%engine_id)
        self.engine_id = engine_id
        self.in_queue = Queue(max_qsize)
        self.out_queue = Queue(max_qsize)
        self.max_qsize = max_qsize
    
    @property
    def queues(self):
        return self.in_queue, self.out_queue
    
    @property
    def can_recv(self):
        # print self.in_queue.full(), poll((self.queue_socket, zmq.POLLIN),1e-3)
        return (not self.in_queue.full()) and poll([(self.queue_socket, zmq.POLLIN)], 1e-3 )
    
    @property
    def can_send(self):
        return not self.out_queue.empty()
    
    def run(self):
        print 'running'
        self.queue_socket,self.mon_socket = self._setup_sockets()
        print 'setup'
        
        while True:
            while not self.can_send and not self.can_recv:
                # print 'idle'
                # nothing to do, wait
                time.sleep(1e-3)
            while self.can_send:
                # flush out queue
                print 'flushing...'
                meth, args, kwargs = self.out_queue.get()
                getattr(self.queue_socket, meth)(*args, **kwargs)
                print 'flushed'
            
            if self.can_recv:
                print 'recving'
                # get another job from zmq
                msg = self.queue_socket.recv_multipart(0, copy=False)
                # put it in the Queue
                self.in_queue.put(msg)
                idents,msg = self.session.feed_identities(msg, copy=False)
                msg = self.session.unpack_message(msg, content=False, copy=False)
                # notify the Controller that we got it
                self.mon_socket.send('tracktask', zmq.SNDMORE)
                header = msg['header']
                msg_id = header['msg_id']
                content = dict(engine_id=self.engine_id, msg_id = msg_id)
                self.session.send(self.mon_socket, 'task_receipt', content=content)
                print 'recvd'
            
    
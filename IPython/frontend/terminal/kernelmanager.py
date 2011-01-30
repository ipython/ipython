# -*- coding: utf-8 -*-

from Queue import Queue
from IPython.zmq.session import Session, Message, extract_header
from IPython.utils.traitlets import Type, HasTraits, TraitType
from IPython.zmq.kernelmanager import KernelManager, SubSocketChannel, \
XReqSocketChannel, RepSocketChannel, HBSocketChannel
MetaHasTraits = type(HasTraits)


class SubSocketChannel2p(SubSocketChannel):
    #---------------------------------------------------------------------------
    # 'SubSocketChannel' interface
    #---------------------------------------------------------------------------
    _msg = None
    queue = Queue(-1)
    def call_handlers(self, msg):  
      self.queue.put(Message(msg))
        
    def get_msg(self):
      return self.queue.get()
    
    def was_called(self):
      return not self.queue.empty()

class XReqSocketChannel2p(XReqSocketChannel):
   #---------------------------------------------------------------------------
   # 'XReqSocketChannel' interface
   #---------------------------------------------------------------------------
    _msg = None
    _called = False
    def call_handlers(self, msg):
        self._called = True
        self._msg = Message(msg)
        
    def get_msg(self):
       self._called = False
       return self._msg
    
    def was_called(self):
       return self._called
       
class RepSocketChannel2p(RepSocketChannel):
   #---------------------------------------------------------------------------
   # 'XReqSocketChannel' interface
   #---------------------------------------------------------------------------
    _msg = None
    _called = False
    def call_handlers(self, msg):
        self._called = True
        self._msg = Message(msg)
        
    def get_msg(self):
       self._called = False
       return self._msg
    
    def was_called(self):
       return self._called
   
class HBSocketChannel2p(HBSocketChannel):
   #---------------------------------------------------------------------------
   # 'XReqSocketChannel' interface
   #---------------------------------------------------------------------------
    _msg = None
    _called = False
    def call_handlers(self, msg):
        self._called = True
        self._msg = Message(msg)
        
    def get_msg(self):
       self._called = False
       return self._msg
    
    def was_called(self):
       return self._called

class KernelManager2p(KernelManager):
      sub_channel_class = Type(SubSocketChannel2p)
      xreq_channel_class = Type(XReqSocketChannel2p)
      rep_channel_class = Type(RepSocketChannel2p)
      hb_channel_class = Type(HBSocketChannel2p)
      
      def start_kernel(self, *args, **kw):
          """ Reimplemented for proper heartbeat management.
          """
          if self._xreq_channel is not None:
              self._xreq_channel.reset_first_reply()
          super(KernelManager2p, self).start_kernel(*args, **kw)

    

      
      
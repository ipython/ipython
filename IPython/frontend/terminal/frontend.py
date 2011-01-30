# -*- coding: utf-8 -*-
"""Frontend of ipython working with python-zmq

Ipython's frontend, is a ipython interface that send request to kernel and proccess the kernel's outputs.

For more details, see the ipython-zmq design
"""
#-----------------------------------------------------------------------------
# Copyright (C) 2010 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
from contextlib import nested
import time
import sys
import os
import signal
import uuid
import cPickle as pickle
import code
import zmq
import rlcompleter
import time


#-----------------------------------------------------------------------------
# Imports from ipython
#-----------------------------------------------------------------------------
from IPython.external.argparse import ArgumentParser
from IPython.utils.traitlets import (
Int, Str, CBool, CaselessStrEnum, Enum, List, Unicode
)
from IPython.core.interactiveshell import get_default_colors
from IPython.core.excolors import exception_colors
from IPython.utils import PyColorize
from IPython.core.inputsplitter import InputSplitter
from IPython.frontend.terminal.kernelmanager import KernelManager2p as KernelManager
from IPython.zmq.session import Session
from IPython.zmq import completer
#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS
class Frontend(object):
   """ this class is a simple frontend to ipython-zmq 
       
      NOTE: this class use kernelmanager to manipulate sockets
      
      Parameters:
      -----------
      kernelmanager : object
        instantiated object from class KernelManager in module kernelmanager
        
   """

   def __init__(self,kernelmanager):
       self.km = kernelmanager
       self.session = kernelmanager.session
       self.request_socket = self.km.xreq_channel.socket
       self.sub_socket = self.km.sub_channel.socket
       self.reply_socket = self.km.rep_channel.socket
            
       
       self.completer = completer.ClientCompleter(self,self.session,self.request_socket)
       rlcompleter.readline.parse_and_bind("tab: complete")
       rlcompleter.readline.parse_and_bind('set show-all-if-ambiguous on')
       rlcompleter.Completer = self.completer.complete
       
       history_path = os.path.expanduser('~/.ipython/history')
       if os.path.isfile(history_path):
           rlcompleter.readline.read_history_file(history_path)
       else:
           print("history file can not be readed.")   

       self.messages = {}
       self.prompt_count = 0
       self.backgrounded = 0
       self._splitter = InputSplitter()
        
   def interact(self):
       """ let you get input from console using inputsplitter, then
       while you enter code it can indent and set index id to any input

       """    
       try:
           self._splitter.push(raw_input('In[%i]:'%self.prompt_count))
           while self._splitter.push_accepts_more():
              code = raw_input('.....:'+' '*self._splitter.indent_spaces)
              self._splitter.push(' '*self._splitter.indent_spaces+code)
           self._execute(self._splitter.source,False)
           self._splitter.reset()
       except  KeyboardInterrupt:
            print('\nKeyboardInterrupt\n')    
            pass  
       
   def start(self):
       """ init a bucle that call interact method to get code.
       
       """
       while True:
           try:
               self.interact()    
           except EOFError:
               answer = ''    
               while True:
                   answer = raw_input('\nDo you really want to exit ([y]/n)?')
                   if answer == 'y' or answer == '' :
		       self.km.shutdown_kernel()
                       sys.exit()
                   elif answer == 'n':
                       break
   def _execute(self, source, hidden = True):
       """ Execute 'source'. If 'hidden', do not show any output.

        See parent class :meth:`execute` docstring for full details.
       """
       msg_id = self.km.xreq_channel.execute(source, hidden)  
       if self.km.xreq_channel.was_called():
         msg_xreq =  self.km.xreq_channel.get_msg()
         print "xreq not implemented yet"
        
       if self.km.rep_channel.was_called():
         msg_rep = self.km.rep_channel.get_msg()
         print "rep hadler not implemented yet" 
        
       while True:
         if not self.km.sub_channel.was_called():
            break
       print "calles sub0"
       sub_msg = self.km.sub_channel.get_msg()
       if self.km.session.username == sub_msg['parent_header']['username'] and self.km.session.session == sub_msg['parent_header']['session']:
         print "calles sub1"
 

   def handle_sub_msg(self,msg):
		 if msg['content'] == '':
			 pass
       
def start_frontend():
    """ Entry point for application.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    kgroup = parser.add_argument_group('kernel options')
    kgroup.add_argument('-e', '--existing', action='store_true',
                        help='connect to an existing kernel')
    kgroup.add_argument('--ip', type=str, default=LOCALHOST,
                        help=\
            "set the kernel\'s IP address [default localhost].\
            If the IP address is something other than localhost, then \
            Consoles on other machines will be able to connect\
            to the Kernel, so be careful!")
    kgroup.add_argument('--xreq', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    kgroup.add_argument('--sub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    kgroup.add_argument('--rep', type=int, metavar='PORT', default=0,
                        help='set the REP channel port [default random]')
    kgroup.add_argument('--hb', type=int, metavar='PORT', default=0,
                        help='set the heartbeat port [default random]')

    egroup = kgroup.add_mutually_exclusive_group()
    egroup.add_argument('--pure', action='store_true', help = \
                        'use a pure Python kernel instead of an IPython kernel')
    egroup.add_argument('--pylab', type=str, metavar='GUI', nargs='?', 
                       const='auto', help = \
        "Pre-load matplotlib and numpy for interactive use. If GUI is not \
         given, the GUI backend is matplotlib's, otherwise use one of: \
         ['tk', 'gtk', 'qt', 'wx', 'inline'].")
    egroup.add_argument('--colors', type=str,
                        help="Set the color scheme (LightBG,Linux,NoColor). This is guessed\
                        based on the pygments style if not set.")

    args = parser.parse_args()

    # parse the colors arg down to current known labels
    if args.colors:
        colors=args.colors.lower()
        if colors in ('lightbg', 'light'):
            colors='lightbg'
        elif colors in ('dark', 'linux'):
            colors='linux'
        else:
            colors='nocolor'
    else:
        colors=None

    # Create a KernelManager and start a kernel.
    kernel_manager = KernelManager(xreq_address=(args.ip, args.xreq),
                                     sub_address=(args.ip, args.sub),
                                     rep_address=(args.ip, args.rep),
                                     hb_address=(args.ip, args.hb))
    if not args.existing:
        # if not args.ip in LOCAL_IPS+ALL_ALIAS:
        #     raise ValueError("Must bind a local ip, such as: %s"%LOCAL_IPS)

        kwargs = dict(ip=args.ip)
        if args.pure:
            kwargs['ipython']=False
        else:
            kwargs['colors']=colors
            if args.pylab:
                kwargs['pylab']=args.pylab
        kernel_manager.start_kernel(**kwargs)

    
    kernel_manager.start_channels()
    time.sleep(4)
 
    frontend=Frontend(kernel_manager)
    return frontend

if __name__ == "__main__" :
     frontend=start_frontend()
     frontend.start()
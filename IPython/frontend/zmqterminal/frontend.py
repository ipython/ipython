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
from __future__ import print_function

import __builtin__
import sys
import os
from Queue import Empty
import readline
import rlcompleter

#-----------------------------------------------------------------------------
# Imports from ipython
#-----------------------------------------------------------------------------
from IPython.external.argparse import ArgumentParser
from IPython.core.inputsplitter import IPythonInputSplitter
from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager
from IPython.frontend.zmqterminal.completer import ClientCompleter2p 

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS
class Frontend(object):
    """This class is a simple frontend to ipython-zmq 
       
      NOTE: this class uses kernelmanager to manipulate sockets
      
      Parameters:
      -----------
      kernelmanager : object
        instantiated object from class KernelManager in module kernelmanager
        
    """

    def __init__(self, kernelmanager):
       self.km = kernelmanager
       self.session_id = self.km.session.session
       self.completer = ClientCompleter2p(self, self.km)
       readline.parse_and_bind("tab: complete")
       readline.parse_and_bind('set show-all-if-ambiguous on')
       readline.set_completer(self.completer.complete)

       history_path = os.path.expanduser('~/.ipython/history')
       if os.path.isfile(history_path):
           rlcompleter.readline.read_history_file(history_path)
       else:
           print("history file cannot be read.")   

       self.messages = {}

       self._splitter = IPythonInputSplitter()
       self.code = ""
 
       self.prompt_count = 0
       self._get_initial_prompt()
 
    def _get_initial_prompt(self):
       self._execute('', hidden=True)
   
    def interact(self):
       """Gets input from console using inputsplitter, then
       while you enter code it can indent and set index id to any input
       """    
       
       try:
           print()
           self._splitter.push(raw_input('In [%i]: '%self.prompt_count+self.code))
           while self._splitter.push_accepts_more():
              self.code = raw_input('.....: '+' '*self._splitter.indent_spaces)
              self._splitter.push(' '*self._splitter.indent_spaces+self.code)
           self._execute(self._splitter.source,False)
           self._splitter.reset()
       except KeyboardInterrupt:
           print('\nKeyboardInterrupt\n')
           pass
          
       
    def start(self):
       """Start the interaction loop, calling the .interact() method for each
       input cell.
       """
       while True:
           try:
               self.interact()
           except KeyboardInterrupt:
                print('\nKeyboardInterrupt\n')
                pass
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
        msg_id = self.km.shell_channel.execute(source, hidden)
        while not self.km.shell_channel.msg_ready():
            try:
                self.handle_stdin_channel(timeout=0.1)
            except Empty:
                pass
        self.handle_execute_reply(msg_id)

    def handle_execute_reply(self, msg_id):
        msg = self.km.shell_channel.get_msg()
        if msg["parent_header"]["msg_id"] == msg_id:
            if msg["content"]["status"] == 'ok' :
                self.handle_sub_channel()
               
            elif msg["content"]["status"] == 'error':
                for frame in msg["content"]["traceback"]:
                    print(frame, file=sys.stderr)
            
            self.prompt_count = msg["content"]["execution_count"] + 1


    def handle_sub_channel(self):
       """ Method to procces subscribe channel's messages

           This method reads a message and processes the content in different
           outputs like stdout, stderr, pyout and status

           Arguments:
           sub_msg:  message receive from kernel in the sub socket channel
                     capture by kernel manager.
       """
       while self.km.sub_channel.msg_ready():
           sub_msg = self.km.sub_channel.get_msg()
           if self.session_id == sub_msg['parent_header']['session']:
               if sub_msg['msg_type'] == 'status' :
                    if sub_msg["content"]["execution_state"] == "busy" :
                        pass

               elif sub_msg['msg_type'] == 'stream' :
                  if sub_msg["content"]["name"] == "stdout":
                    print(sub_msg["content"]["data"], file=sys.stdout, end="")
                    sys.stdout.flush()
                  elif sub_msg["content"]["name"] == "stderr" :
                    print(sub_msg["content"]["data"], file=sys.stderr, end="")
                    sys.stderr.flush()
                
               elif sub_msg['msg_type'] == 'pyout' :
                    print("Out[%i]:"%sub_msg["content"]["execution_count"],
                            sub_msg["content"]["data"]["text/plain"],
                            file=sys.stdout)
                    sys.stdout.flush()

    def handle_stdin_channel(self, timeout=0.1):
        """ Method to capture raw_input
        """
        msg_rep = self.km.stdin_channel.get_msg(timeout=timeout)
        if self.session_id == msg_rep["parent_header"]["session"] :
            raw_data = raw_input(msg_rep["content"]["prompt"])
            self.km.stdin_channel.input(raw_data)
             
       

       
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
    kgroup.add_argument('--shell', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    kgroup.add_argument('--iopub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    kgroup.add_argument('--stdin', type=int, metavar='PORT', default=0,
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
    kernel_manager = KernelManager(shell_address=(args.ip, args.shell),
                                     sub_address=(args.ip, args.iopub),
                                     stdin_address=(args.ip, args.stdin),
                                     hb_address=(args.ip, args.hb))
    if not args.existing:
        # if not args.ip in LOCAL_IPS+ALL_ALIAS:
        #     raise ValueError("Must bind a local ip, such as: %s"%LOCAL_IPS)

        kwargs = dict(ip=args.ip, ipython=True)
        kernel_manager.start_kernel(**kwargs)

    
    kernel_manager.start_channels()
 
    frontend=Frontend(kernel_manager)
    return frontend

if __name__ == "__main__" :
     frontend=start_frontend()
     frontend.start()

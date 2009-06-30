# encoding: utf-8
"""
Object for encapsulating process execution by using callbacks for stdout, 
stderr and stdin.
"""
__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
from killableprocess import Popen, PIPE
from threading import Thread
from time import sleep
import os

class PipedProcess(Thread):
    """ Class that encapsulates process execution by using callbacks for
        stdout, stderr and stdin, and providing a reliable way of
        killing it.
    """

    def __init__(self, command_string, out_callback, 
                        end_callback=None,):
        """ command_string: the command line executed to start the
        process. 

        out_callback: the python callable called on stdout/stderr.

        end_callback: an optional callable called when the process
        finishes.

        These callbacks are called from a different thread as the
        thread from which is started.
        """
        self.command_string = command_string
        self.out_callback = out_callback
        self.end_callback = end_callback
        Thread.__init__(self)
    

    def run(self):
        """ Start the process and hook up the callbacks.
        """
        env = os.environ
        env['TERM'] = 'xterm'
        process = Popen(self.command_string + ' 2>&1', shell=True,
                                env=env,
                                universal_newlines=True,
                                stdout=PIPE, stdin=PIPE, )
        self.process = process
        while True:
            out_char = process.stdout.read(1)
            if out_char == '':
                if process.poll() is not None:
                    # The process has finished
                    break
                else:
                    # The process is not giving any interesting
                    # output. No use polling it immediatly.
                    sleep(0.1)
            else:
                self.out_callback(out_char)

        if self.end_callback is not None:
            self.end_callback()
    


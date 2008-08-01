"""
Frontend class that uses IPython0 to prefilter the inputs.

Using the IPython0 mechanism gives us access to the magics.
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
import sys

from linefrontendbase import LineFrontEndBase, common_prefix

from IPython.ipmaker import make_IPython
from IPython.ipapi import IPApi
from IPython.kernel.core.redirector_output_trap import RedirectorOutputTrap

from IPython.genutils import Term
import pydoc

#-------------------------------------------------------------------------------
# Utility functions (temporary, should be moved out of here)
#-------------------------------------------------------------------------------
import os
def xterm_system(command):
    """ Run a command in a separate console window.
    """
    os.system(("""xterm -title "%s" -e \'/bin/sh -c "%s ; """
               """echo; echo press enter to close ; """
#               """echo \\"\x1b]0;%s (finished -- press enter to close)\x07\\" ;
               """read foo;"\' """)  % (command, command) )

#-------------------------------------------------------------------------------
# Frontend class using ipython0 to do the prefiltering. 
#-------------------------------------------------------------------------------
class PrefilterFrontEnd(LineFrontEndBase):
    
    def __init__(self, *args, **kwargs):
        LineFrontEndBase.__init__(self, *args, **kwargs)
        # Instanciate an IPython0 interpreter to be able to use the
        # prefiltering.
        self.ipython0 = make_IPython()
        # Set the pager:
        self.ipython0.set_hook('show_in_pager', 
                    lambda s, string: self.write("\n"+string))
        self.ipython0.write = self.write
        self._ip = _ip = IPApi(self.ipython0)
        # XXX: Hack: mix the two namespaces
        self.shell.user_ns = self.ipython0.user_ns
        self.shell.user_global_ns = self.ipython0.user_global_ns
        # Make sure the raw system call doesn't get called, as we don't
        # have a stdin accessible.
        self._ip.system = xterm_system
        self.shell.output_trap = RedirectorOutputTrap(
                            out_callback=self.write,
                            err_callback=self.write,
                                            )
        # Capture and release the outputs, to make sure all the
        # shadow variables are set
        self.capture_output()
        self.release_output()

    
    def prefilter_input(self, input_string):
        """ Using IPython0 to prefilter the commands.
        """
        input_string = LineFrontEndBase.prefilter_input(self, input_string)
        filtered_lines = []
        # The IPython0 prefilters sometime produce output. We need to
        # capture it.
        self.capture_output()
        self.last_result = dict(number=self.prompt_number)
        try:
            for line in input_string.split('\n'):
                filtered_lines.append(self.ipython0.prefilter(line, False))
        except:
            # XXX: probably not the right thing to do.
            self.ipython0.showsyntaxerror()
            self.after_execute()
        finally:
            self.release_output()

        filtered_string = '\n'.join(filtered_lines)
        return filtered_string


    def show_traceback(self):
        self.capture_output()
        self.ipython0.showtraceback()
        self.release_output()


    def execute(self, python_string, raw_string=None):
        self.capture_output()
        LineFrontEndBase.execute(self, python_string,
                                    raw_string=raw_string)
        self.release_output()


    def capture_output(self):
        """ Capture all the output mechanisms we can think of.
        """
        self.__old_cout_write = Term.cout.write
        self.__old_err_write = Term.cerr.write
        Term.cout.write = self.write
        Term.cerr.write = self.write
        self.__old_stdout = sys.stdout
        self.__old_stderr= sys.stderr
        sys.stdout = Term.cout
        sys.stderr = Term.cerr
        self.__old_help_output = pydoc.help.output
        pydoc.help.output = self.shell.output_trap.out


    def release_output(self):
        """ Release all the different captures we have made.
        """
        Term.cout.write = self.__old_cout_write
        Term.cerr.write = self.__old_err_write
        sys.stdout = self.__old_stdout
        sys.stderr = self.__old_stderr
        pydoc.help.output = self.__old_help_output 


    def complete(self, line):
        word = line.split('\n')[-1].split(' ')[-1]
        completions = self.ipython0.complete(word)
        # FIXME: The proper sort should be done in the complete method.
        key = lambda x: x.replace('_', '')
        completions.sort(key=key)
        if completions:
            prefix = common_prefix(completions) 
            line = line[:-len(word)] + prefix
        return line, completions 
 

    def do_exit(self):
        """ Exit the shell, cleanup and save the history.
        """
        self.ipython0.atexit_operations()


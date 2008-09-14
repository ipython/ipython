"""
Frontend class that uses IPython0 to prefilter the inputs.

Using the IPython0 mechanism gives us access to the magics.

This is a transitory class, used here to do the transition between
ipython0 and ipython1. This class is meant to be short-lived as more
functionnality is abstracted out of ipython0 in reusable functions and
is added on the interpreter. This class can be a used to guide this
refactoring.
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
from frontendbase import FrontEndBase

from IPython.ipmaker import make_IPython
from IPython.ipapi import IPApi
from IPython.kernel.core.redirector_output_trap import RedirectorOutputTrap

from IPython.kernel.core.sync_traceback_trap import SyncTracebackTrap

from IPython.genutils import Term
import pydoc
import os
import sys


def mk_system_call(system_call_function, command):
    """ given a os.system replacement, and a leading string command,
        returns a function that will execute the command with the given
        argument string.
    """
    def my_system_call(args):
        system_call_function("%s %s" % (command, args))
    return my_system_call

#-------------------------------------------------------------------------------
# Frontend class using ipython0 to do the prefiltering. 
#-------------------------------------------------------------------------------
class PrefilterFrontEnd(LineFrontEndBase):
    """ Class that uses ipython0 to do prefilter the input, do the
    completion and the magics.

    The core trick is to use an ipython0 instance to prefilter the
    input, and share the namespace between the interpreter instance used
    to execute the statements and the ipython0 used for code
    completion...
    """

    debug = False
    
    def __init__(self, ipython0=None, *args, **kwargs):
        """ Parameters:
            -----------

            ipython0: an optional ipython0 instance to use for command
            prefiltering and completion.
        """
        LineFrontEndBase.__init__(self, *args, **kwargs)
        self.shell.output_trap = RedirectorOutputTrap(
                            out_callback=self.write,
                            err_callback=self.write,
                                            )
        self.shell.traceback_trap = SyncTracebackTrap(
                        formatters=self.shell.traceback_trap.formatters,
                            )

        # Start the ipython0 instance:
        self.save_output_hooks()
        if ipython0 is None:
            # Instanciate an IPython0 interpreter to be able to use the
            # prefiltering.
            # XXX: argv=[] is a bit bold.
            ipython0 = make_IPython(argv=[], 
                                    user_ns=self.shell.user_ns,
                                    user_global_ns=self.shell.user_global_ns)
        self.ipython0 = ipython0
        # Set the pager:
        self.ipython0.set_hook('show_in_pager', 
                    lambda s, string: self.write("\n" + string))
        self.ipython0.write = self.write
        self._ip = _ip = IPApi(self.ipython0)
        # Make sure the raw system call doesn't get called, as we don't
        # have a stdin accessible.
        self._ip.system = self.system_call
        # XXX: Muck around with magics so that they work better
        # in our environment
        self.ipython0.magic_ls = mk_system_call(self.system_call, 
                                                            'ls -CF')
        # And now clean up the mess created by ipython0
        self.release_output()


        if not 'banner' in kwargs and self.banner is None:
            self.banner = self.ipython0.BANNER + """
This is the wx frontend, by Gael Varoquaux. This is EXPERIMENTAL code."""

        self.start()

    #--------------------------------------------------------------------------
    # FrontEndBase interface 
    #--------------------------------------------------------------------------

    def show_traceback(self):
        """ Use ipython0 to capture the last traceback and display it.
        """
        self.capture_output()
        self.ipython0.showtraceback(tb_offset=-1)
        self.release_output()


    def execute(self, python_string, raw_string=None):
        if self.debug:
            print 'Executing Python code:', repr(python_string)
        self.capture_output()
        LineFrontEndBase.execute(self, python_string,
                                    raw_string=raw_string)
        self.release_output()


    def save_output_hooks(self):
        """ Store all the output hooks we can think of, to be able to
        restore them. 
        
        We need to do this early, as starting the ipython0 instance will
        screw ouput hooks.
        """
        self.__old_cout_write = Term.cout.write
        self.__old_cerr_write = Term.cerr.write
        self.__old_stdout = sys.stdout
        self.__old_stderr= sys.stderr
        self.__old_help_output = pydoc.help.output
        self.__old_display_hook = sys.displayhook


    def capture_output(self):
        """ Capture all the output mechanisms we can think of.
        """
        self.save_output_hooks()
        Term.cout.write = self.write
        Term.cerr.write = self.write
        sys.stdout = Term.cout
        sys.stderr = Term.cerr
        pydoc.help.output = self.shell.output_trap.out


    def release_output(self):
        """ Release all the different captures we have made.
        """
        Term.cout.write = self.__old_cout_write
        Term.cerr.write = self.__old_cerr_write
        sys.stdout = self.__old_stdout
        sys.stderr = self.__old_stderr
        pydoc.help.output = self.__old_help_output 
        sys.displayhook = self.__old_display_hook 


    def complete(self, line):
        # FIXME: This should be factored out in the linefrontendbase
        # method.
        word = line.split('\n')[-1].split(' ')[-1]
        completions = self.ipython0.complete(word)
        # FIXME: The proper sort should be done in the complete method.
        key = lambda x: x.replace('_', '')
        completions.sort(key=key)
        if completions:
            prefix = common_prefix(completions) 
            line = line[:-len(word)] + prefix
        return line, completions 
 
    
    #--------------------------------------------------------------------------
    # LineFrontEndBase interface 
    #--------------------------------------------------------------------------

    def prefilter_input(self, input_string):
        """ Using IPython0 to prefilter the commands to turn them
        in executable statements that are valid Python strings.
        """
        input_string = LineFrontEndBase.prefilter_input(self, input_string)
        filtered_lines = []
        # The IPython0 prefilters sometime produce output. We need to
        # capture it.
        self.capture_output()
        self.last_result = dict(number=self.prompt_number)
        
        ## try:
        ##     for line in input_string.split('\n'):
        ##         filtered_lines.append(
        ##                 self.ipython0.prefilter(line, False).rstrip())
        ## except:
        ##     # XXX: probably not the right thing to do.
        ##     self.ipython0.showsyntaxerror()
        ##     self.after_execute()
        ## finally:
        ##     self.release_output()


        try:
            try:
                for line in input_string.split('\n'):
                    filtered_lines.append(
                            self.ipython0.prefilter(line, False).rstrip())
            except:
                # XXX: probably not the right thing to do.
                self.ipython0.showsyntaxerror()
                self.after_execute()
        finally:
            self.release_output()



        # Clean up the trailing whitespace, to avoid indentation errors
        filtered_string = '\n'.join(filtered_lines)
        return filtered_string


    #--------------------------------------------------------------------------
    # PrefilterFrontEnd interface 
    #--------------------------------------------------------------------------
 
    def system_call(self, command_string):
        """ Allows for frontend to define their own system call, to be
            able capture output and redirect input.
        """
        return os.system(command_string)


    def do_exit(self):
        """ Exit the shell, cleanup and save the history.
        """
        self.ipython0.atexit_operations()


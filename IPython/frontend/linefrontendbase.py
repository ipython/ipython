"""
Base front end class for all line-oriented frontends.

Currently this focuses on synchronous frontends.
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
import re

import IPython


from frontendbase import FrontEndBase
from IPython.kernel.core.interpreter import Interpreter

#-------------------------------------------------------------------------------
# Base class for the line-oriented front ends
#-------------------------------------------------------------------------------
class LineFrontEndBase(FrontEndBase):
    
    # We need to keep the prompt number, to be able to increment
    # it when there is an exception.
    prompt_number = 1


    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------

    def __init__(self, shell=None, history=None):
        if shell is None:
            shell = Interpreter()
        FrontEndBase.__init__(self, shell=shell, history=history)
        
        #FIXME: print banner.
        banner = """IPython1 %s -- An enhanced Interactive Python.""" \
                            % IPython.__version__


    def complete(self, token):
        """Complete token in engine's user_ns
        
        Parameters
        ----------
        token : string
        
        Result
        ------
        Deferred result of 
        IPython.kernel.engineservice.IEngineBase.complete
        """
        
        return self.shell.complete(token)
 

    def render_result(self, result):
        if 'stdout' in result and result['stdout']:
            self.write('\n' + result['stdout'])
        if 'display' in result and result['display']:
            self.write("%s%s\n" % ( 
                            self.output_prompt % result['number'],
                            result['display']['pprint']
                            ) )
       

    def render_error(self, failure):
        self.insert_text('\n\n'+str(failure)+'\n\n')
        return failure


    def prefilter_input(self, string):
        string = string.replace('\r\n', '\n')
        string = string.replace('\t', 4*' ')
        # Clean the trailing whitespace
        string = '\n'.join(l.rstrip()  for l in string.split('\n'))
        return string


    def is_complete(self, string):
        if ( len(self.get_current_edit_buffer().split('\n'))>1 
                        and not re.findall(r"\n[\t ]*$", string)):
            return False
        else:
            return FrontEndBase.is_complete(self, string)
    

    def execute(self, python_string, raw_string=None):
        """ Send the python_string to the interpreter, stores the
            raw_string in the history and starts a new prompt.
        """
        if raw_string is None:
            raw_string = string
        # Create a false result, in case there is an exception
        self.last_result = dict(number=self.prompt_number)
        try:
            self.history.input_cache[-1] = raw_string
            result = self.shell.execute(python_string)
            self.last_result = result
            self.render_result(result)
        except:
            self.show_traceback()
        finally:
            self.after_execute()


    def after_execute(self):
        """ All the operations required after an execution to put the
            terminal back in a shape where it is usable.
        """
        self.prompt_number += 1
        self.new_prompt(self.prompt % (self.last_result['number'] + 1))
        # Start a new empty history entry
        self._add_history(None, '')
        # The result contains useful information that can be used
        # elsewhere.


    def _on_enter(self):
        """ Called when the return key is pressed in a line editing
            buffer.
        """
        current_buffer = self.get_current_edit_buffer()
        cleaned_buffer = self.prefilter_input(current_buffer)
        if self.is_complete(cleaned_buffer + '\n'):
            # The '\n' is important in case prefiltering empties the
            # line, to get a new prompt.
            self.execute(cleaned_buffer, raw_string=current_buffer)
        else:
            if len(current_buffer.split('\n'))>1:
                self.write(self._get_indent_string(current_buffer))
            else:
                self.write('\t')


    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 
    def _get_indent_string(self, string):
        string = string.replace('\t', ' '*4)
        string = string.split('\n')[-1]
        indent_chars = len(string) - len(string.lstrip())
        indent_string = '\t'*(indent_chars // 4) + \
                            ' '*(indent_chars % 4)

        return indent_string
 
    

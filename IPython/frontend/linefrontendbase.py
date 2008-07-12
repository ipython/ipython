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
    
    # Are we entering multi line input?
    multi_line_input = False

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
    

    def _on_enter(self):
        """ Called when the return key is pressed in a line editing
            buffer.
        """
        current_buffer = self.get_current_edit_buffer()
        current_buffer = current_buffer.replace('\r\n', '\n')
        current_buffer = current_buffer.replace('\t', 4*' ')
        cleaned_buffer = '\n'.join(l.rstrip() 
                        for l in current_buffer.split('\n'))
        if (    not self.multi_line_input
                or re.findall(r"\n[\t ]*$", cleaned_buffer)):
            if self.is_complete(cleaned_buffer):
                self.history.input_cache[-1] = \
                            current_buffer
                result = self.shell.execute(cleaned_buffer)
                self.render_result(result)
                self.new_prompt(self.prompt % (result['number'] + 1))
                self.multi_line_input = False
                # Start a new empty history entry
                self._add_history(None, '')
            else:
                if self.multi_line_input:
                    self.write('\n' + self._get_indent_string(current_buffer))
                else:
                    self.multi_line_input = True
                    self.write('\n\t')
        else:
            self.write('\n'+self._get_indent_string(current_buffer))


    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 
    def _get_indent_string(self, string):
        string = string.split('\n')[-1]
        indent_chars = len(string) - len(string.lstrip())
        indent_string = '\t'*(indent_chars // 4) + \
                            ' '*(indent_chars % 4)

        return indent_string
 
    

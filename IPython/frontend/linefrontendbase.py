"""
Base front end class for all line-oriented frontends, rather than
block-oriented.

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
import sys

from frontendbase import FrontEndBase
from IPython.kernel.core.interpreter import Interpreter

def common_prefix(strings):
    """ Given a list of strings, return the common prefix between all
        these strings.
    """
    ref = strings[0]
    prefix = ''
    for size in range(len(ref)):
        test_prefix = ref[:size+1]
        for string in strings[1:]:
            if not string.startswith(test_prefix):
                return prefix
        prefix = test_prefix

    return prefix

#-------------------------------------------------------------------------------
# Base class for the line-oriented front ends
#-------------------------------------------------------------------------------
class LineFrontEndBase(FrontEndBase):
    """ Concrete implementation of the FrontEndBase class. This is meant
    to be the base class behind all the frontend that are line-oriented,
    rather than block-oriented.
    """
    
    # We need to keep the prompt number, to be able to increment
    # it when there is an exception.
    prompt_number = 1

    # We keep a reference to the last result: it helps testing and
    # programatic control of the frontend. 
    last_result = dict(number=0)

    #--------------------------------------------------------------------------
    # FrontEndBase interface
    #--------------------------------------------------------------------------

    def __init__(self, shell=None, history=None):
        if shell is None:
            shell = Interpreter()
        FrontEndBase.__init__(self, shell=shell, history=history)
        
        self.new_prompt(self.input_prompt_template.substitute(number=1))


    def complete(self, line):
        """Complete line in engine's user_ns
        
        Parameters
        ----------
        line : string
        
        Result
        ------
        The replacement for the line and the list of possible completions.
        """
        completions = self.shell.complete(line)
        complete_sep =  re.compile('[\s\{\}\[\]\(\)\=]')
        if completions:
            prefix = common_prefix(completions) 
            residual = complete_sep.split(line)[:-1]
            line = line[:-len(residual)] + prefix
        return line, completions 
 

    def render_result(self, result):
        """ Frontend-specific rendering of the result of a calculation
        that has been sent to an engine.
        """
        if 'stdout' in result and result['stdout']:
            self.write('\n' + result['stdout'])
        if 'display' in result and result['display']:
            self.write("%s%s\n" % ( 
                            self.output_prompt_template.substitute(
                                    number=result['number']),
                            result['display']['pprint']
                            ) )
       

    def render_error(self, failure):
        """ Frontend-specific rendering of error. 
        """
        self.write('\n\n'+str(failure)+'\n\n')
        return failure


    def is_complete(self, string):
        """ Check if a string forms a complete, executable set of
        commands.

        For the line-oriented frontend, multi-line code is not executed
        as soon as it is complete: the users has to enter two line
        returns.
        """
        if string in ('', '\n'):
            # Prefiltering, eg through ipython0, may return an empty
            # string although some operations have been accomplished. We
            # thus want to consider an empty string as a complete
            # statement.
            return True
        elif ( len(self.get_current_edit_buffer().split('\n'))>2 
                        and not re.findall(r"\n[\t ]*\n[\t ]*$", string)):
            return False
        else:
            # Add line returns here, to make sure that the statement is
            # complete.
            return FrontEndBase.is_complete(self, string.rstrip() + '\n\n')


    def get_current_edit_buffer(self):
        """ Return the current buffer being entered.
        """
        raise NotImplementedError


    def write(self, string):
        """ Write some characters to the display.

            Subclass should overide this method.
        """
        print >>sys.__stderr__, string

    
    def add_to_edit_buffer(self, string):
        """ Add the given string to the current edit buffer.
        """
        raise NotImplementedError


    def new_prompt(self, prompt):
        """ Prints a prompt and starts a new editing buffer. 

            Subclasses should use this method to make sure that the
            terminal is put in a state favorable for a new line
            input.
        """
        self.write(prompt)


    def execute(self, python_string, raw_string=None):
        """ Stores the raw_string in the history, and sends the
        python string to the interpreter.
        """
        if raw_string is None:
            raw_string = python_string
        # Create a false result, in case there is an exception
        self.last_result = dict(number=self.prompt_number)
        try:
            self.history.input_cache[-1] = raw_string.rstrip()
            result = self.shell.execute(python_string)
            self.last_result = result
            self.render_result(result)
        except:
            self.show_traceback()
        finally:
            self.after_execute()

    #--------------------------------------------------------------------------
    # LineFrontEndBase interface
    #--------------------------------------------------------------------------

    def prefilter_input(self, string):
        """ Priflter the input to turn it in valid python.
        """
        string = string.replace('\r\n', '\n')
        string = string.replace('\t', 4*' ')
        # Clean the trailing whitespace
        string = '\n'.join(l.rstrip()  for l in string.split('\n'))
        return string

    def after_execute(self):
        """ All the operations required after an execution to put the
            terminal back in a shape where it is usable.
        """
        self.prompt_number += 1
        self.new_prompt(self.input_prompt_template.substitute(
                            number=(self.last_result['number'] + 1)))
        # Start a new empty history entry
        self._add_history(None, '')
        self.history_cursor = len(self.history.input_cache) - 1


    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 
    def _on_enter(self):
        """ Called when the return key is pressed in a line editing
            buffer.
        """
        current_buffer = self.get_current_edit_buffer()
        cleaned_buffer = self.prefilter_input(current_buffer)
        if self.is_complete(cleaned_buffer):
            self.execute(cleaned_buffer, raw_string=current_buffer)
        else:
            self.add_to_edit_buffer(self._get_indent_string(
                            current_buffer[:-1]))
            if current_buffer[:-1].split('\n')[-1].rstrip().endswith(':'):
                self.add_to_edit_buffer('\t')


    def _get_indent_string(self, string):
        """ Return the string of whitespace that prefixes a line. Used to
        add the right amount of indendation when creating a new line.
        """
        string = string.replace('\t', ' '*4)
        string = string.split('\n')[-1]
        indent_chars = len(string) - len(string.lstrip())
        indent_string = '\t'*(indent_chars // 4) + \
                            ' '*(indent_chars % 4)

        return indent_string
 
    

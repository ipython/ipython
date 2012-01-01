# encoding: utf-8
# -*- test-case-name: IPython.frontend.tests.test_frontendbase -*-
"""
frontendbase provides an interface and base class for GUI frontends for
IPython.kernel/IPython.kernel.core.

Frontend implementations will likely want to subclass FrontEndBase.

Author: Barry Wark
"""
__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
import string
import codeop
import uuid


from IPython.frontend.zopeinterface import (
    Interface,
    Attribute,
)
from IPython.kernel.core.history import FrontEndHistory
from IPython.kernel.core.util import Bunch

##############################################################################
# TEMPORARY!!! fake configuration, while we decide whether to use tconfig or
# not

rc = Bunch()
rc.prompt_in1 = r'In [$number]:  '
rc.prompt_in2 = r'...'
rc.prompt_out = r'Out [$number]:  '

##############################################################################
# Interface definitions
##############################################################################

class IFrontEndFactory(Interface):
    """Factory interface for frontends."""

    def __call__(engine=None, history=None):
        """
        Parameters:
        interpreter : IPython.kernel.engineservice.IEngineCore
        """

        pass


class IFrontEnd(Interface):
    """Interface for frontends. All methods return t.i.d.Deferred"""

    Attribute("input_prompt_template", "string.Template instance\
                substituteable with execute result.")
    Attribute("output_prompt_template", "string.Template instance\
                substituteable with execute result.")
    Attribute("continuation_prompt_template", "string.Template instance\
                substituteable with execute result.")

    def update_cell_prompt(result, blockID=None):
        """Subclass may override to update the input prompt for a block.

        In asynchronous frontends, this method will be called as a
        twisted.internet.defer.Deferred's callback/errback.
        Implementations should thus return result when finished.

        Result is a result dict in case of success, and a
        twisted.python.util.failure.Failure in case of an error
        """

        pass

    def render_result(result):
        """Render the result of an execute call. Implementors may choose the
         method of rendering.
        For example, a notebook-style frontend might render a Chaco plot
        inline.

        Parameters:
            result : dict (result of IEngineBase.execute )
                blockID = result['blockID']

        Result:
            Output of frontend rendering
        """

        pass

    def render_error(failure):
        """Subclasses must override to render the failure.

        In asynchronous frontend, since this method will be called as a
        twisted.internet.defer.Deferred's callback. Implementations
        should thus return result when finished.

        blockID = failure.blockID
        """

        pass

    def input_prompt(number=''):
        """Returns the input prompt by subsituting into
        self.input_prompt_template
        """
        pass

    def output_prompt(number=''):
        """Returns the output prompt by subsituting into
        self.output_prompt_template
        """

        pass

    def continuation_prompt():
        """Returns the continuation prompt by subsituting into
        self.continuation_prompt_template
        """

        pass

    def is_complete(block):
        """Returns True if block is complete, False otherwise."""

        pass


    def get_history_previous(current_block):
        """Returns the block previous in  the history. Saves currentBlock if
        the history_cursor is currently at the end of the input history"""
        pass

    def get_history_next():
        """Returns the next block in the history."""

        pass

    def complete(self, line):
        """Returns the list of possible completions, and the completed
            line.

        The input argument is the full line to be completed. This method
        returns both the line completed as much as possible, and the list
        of further possible completions (full words).
        """
        pass


##############################################################################
# Base class for all the frontends.
##############################################################################

class FrontEndBase(object):
    """
    FrontEndBase manages the state tasks for a CLI frontend:
        - Input and output history management
        - Input/continuation and output prompt generation

    Some issues (due to possibly unavailable engine):
        - How do we get the current cell number for the engine?
        - How do we handle completions?
    """

    history_cursor = 0

    input_prompt_template = string.Template(rc.prompt_in1)
    output_prompt_template = string.Template(rc.prompt_out)
    continuation_prompt_template = string.Template(rc.prompt_in2)

    def __init__(self, shell=None, history=None):
        self.shell = shell
        if history is None:
                self.history = FrontEndHistory(input_cache=[''])
        else:
            self.history = history


    def input_prompt(self, number=''):
        """Returns the current input prompt

        It would be great to use ipython1.core.prompts.Prompt1 here
        """
        return self.input_prompt_template.safe_substitute({'number':number})


    def continuation_prompt(self):
        """Returns the current continuation prompt"""

        return self.continuation_prompt_template.safe_substitute()

    def output_prompt(self, number=''):
        """Returns the output prompt for result"""

        return self.output_prompt_template.safe_substitute({'number':number})


    def is_complete(self, block):
        """Determine if block is complete.

        Parameters
        block : string

        Result
        True if block can be sent to the engine without compile errors.
        False otherwise.
        """

        try:
            is_complete = codeop.compile_command(block.rstrip() + '\n\n',
                            "<string>", "exec")
        except:
            return False

        lines = block.split('\n')
        return ((is_complete is not None)
                    and (len(lines)==1 or str(lines[-1])==''))


    def execute(self, block, blockID=None):
        """Execute the block and return the result.

        Parameters:
            block : {str, AST}
            blockID : any
                Caller may provide an ID to identify this block.
                result['blockID'] := blockID

        Result:
            Deferred result of self.interpreter.execute
        """

        if(not self.is_complete(block)):
            raise Exception("Block is not compilable")

        if(blockID == None):
            blockID = uuid.uuid4()

        try:
            result = self.shell.execute(block)
        except Exception,e:
            e = self._add_block_id_for_failure(e, blockID=blockID)
            e = self.update_cell_prompt(e, blockID=blockID)
            e = self.render_error(e)
        else:
            result = self._add_block_id_for_result(result, blockID=blockID)
            result = self.update_cell_prompt(result, blockID=blockID)
            result = self.render_result(result)

        return result


    def _add_block_id_for_result(self, result, blockID):
        """Add the blockID to result or failure. Unfortunatley, we have to
        treat failures differently than result dicts.
        """

        result['blockID'] = blockID

        return result

    def _add_block_id_for_failure(self, failure, blockID):
        """_add_block_id_for_failure"""
        failure.blockID = blockID
        return failure


    def _add_history(self, result, block=None):
        """Add block to the history"""

        assert(block != None)
        self.history.add_items([block])
        self.history_cursor += 1

        return result


    def get_history_previous(self, current_block):
        """ Returns previous history string and decrement history cursor.
        """
        command = self.history.get_history_item(self.history_cursor - 1)

        if command is not None:
            if(self.history_cursor+1 == len(self.history.input_cache)):
                self.history.input_cache[self.history_cursor] = current_block
            self.history_cursor -= 1
        return command


    def get_history_next(self):
        """ Returns next history string and increment history cursor.
        """
        command = self.history.get_history_item(self.history_cursor+1)

        if command is not None:
            self.history_cursor += 1
        return command

    ###
    # Subclasses probably want to override these methods...
    ###

    def update_cell_prompt(self, result, blockID=None):
        """Subclass may override to update the input prompt for a block.

        This method only really makes sens in asyncrhonous frontend.
        Since this method will be called as a
        twisted.internet.defer.Deferred's callback, implementations should
        return result when finished.
        """

        raise NotImplementedError


    def render_result(self, result):
        """Subclasses must override to render result.

        In asynchronous frontends, this method will be called as a
        twisted.internet.defer.Deferred's callback. Implementations
        should thus return result when finished.
        """

        raise NotImplementedError


    def render_error(self, failure):
        """Subclasses must override to render the failure.

        In asynchronous frontends, this method will be called as a
        twisted.internet.defer.Deferred's callback. Implementations
        should thus return result when finished.
        """

        raise NotImplementedError


# encoding: utf-8
"""
FrontEndBase: Base classes for frontends. 

Todo: 
- synchronous and asynchronous interfaces
- adapter to add async to FrontEndBase
"""
__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2008 Barry Wark <barrywark at gmail _dot_ com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
import string
import uuid


from IPython.kernel.core.history import FrontEndHistory
from IPython.kernel.core.util import Bunch

from IPython.kernel.engineservice import IEngineCore

import zope.interface as zi

import _ast

##############################################################################
# TEMPORARY!!! fake configuration, while we decide whether to use tconfig or
# not

rc = Bunch()
rc.prompt_in1 = r'In [$number]:  '
rc.prompt_in2 = r'...'
rc.prompt_out = r'Out [$number]:  '

##############################################################################

class IFrontEnd(zi.Interface):
    """Interface for frontends. All methods return t.i.d.Deferred"""
    
    zi.Attribute("input_prompt_template", "string.Template instance substituteable with execute result.")
    zi.Attribute("output_prompt_template", "string.Template instance substituteable with execute result.")
    zi.Attribute("continuation_prompt_template", "string.Template instance substituteable with execute result.")
    
    def __init__(engine=None, history=None):
        """
        Parameters:
        interpreter : IPython.kernel.engineservice.IEngineCore
        """
        pass
    
    def update_cell_prompt(self, result):
        """Subclass may override to update the input prompt for a block. 
        Since this method will be called as a twisted.internet.defer.Deferred's callback,
        implementations should return result when finished."""
        
        return result
    
    def render_result(self, result):
        """Render the result of an execute call. Implementors may choose the method of rendering.
        For example, a notebook-style frontend might render a Chaco plot inline.
        
        Parameters:
            result : dict (result of IEngineBase.execute )
        
        Result:
            Output of frontend rendering
        """
        
        return result
    
    def render_error(self, failure):
        """Subclasses must override to render the failure. Since this method will be called as a 
        twisted.internet.defer.Deferred's callback, implementations should return result 
        when finished."""
        
        return failure
    
    # TODO: finish interface

class FrontEndBase(object):
    """
    FrontEndBase manages the state tasks for a CLI frontend:
        - Input and output history management
        - Input/continuation and output prompt generation
        
    Some issues (due to possibly unavailable engine):
        - How do we get the current cell number for the engine?
        - How do we handle completions?
    """
    
    zi.implements(IFrontEnd)
    
    history_cursor = 0
    
    current_indent_level = 0
    
    
    input_prompt_template = string.Template(rc.prompt_in1)
    output_prompt_template = string.Template(rc.prompt_out)
    continuation_prompt_template = string.Template(rc.prompt_in2)
    
    def __init__(self, engine=None, history=None):
        assert(engine==None or IEngineCore.providedBy(engine))
        self.engine = IEngineCore(engine)
        if history is None:
                self.history = FrontEndHistory(input_cache=[''])
        else:
            self.history = history
        
    
    def inputPrompt(self, result={}):
        """Returns the current input prompt
        
        It would be great to use ipython1.core.prompts.Prompt1 here
        """
        
        result.setdefault('number','')
        
        return self.input_prompt_template.safe_substitute(result)
    
    
    def continuationPrompt(self):
        """Returns the current continuation prompt"""
        
        return self.continuation_prompt_template.safe_substitute()
    
    def outputPrompt(self, result):
        """Returns the output prompt for result"""
        
        return self.output_prompt_template.safe_substitute(result)
    
    
    def is_complete(self, block):
        """Determine if block is complete.
        
        Parameters
        block : string
        
        Result 
        True if block can be sent to the engine without compile errors.
        False otherwise.
        """
        
        try:
            self.compile_ast(block)
            return True
        except:
            return False
    
    
    def compile_ast(self, block):
        """Compile block to an AST
        
        Parameters:
            block : str
        
        Result:
            AST
        
        Throws:
            Exception if block cannot be compiled
        """
        
        return compile(block, "<string>", "exec", _ast.PyCF_ONLY_AST)
    
    
    def execute(self, block, blockID=None):
        """Execute the block and return result.
        
        Parameters:
            block : {str, AST}
            blockID : any
                Caller may provide an ID to identify this block. result['blockID'] := blockID
        
        Result:
            Deferred result of self.interpreter.execute
        """
        # if(not isinstance(block, _ast.AST)):
        #     block = self.compile_ast(block)
        
        if(blockID == None):
            blockID = uuid.uuid4() #random UUID
        
        d = self.engine.execute(block)
        d.addCallback(self._add_block_id, blockID)
        d.addCallback(self.update_cell_prompt)
        d.addCallbacks(self.render_result, errback=self.render_error)
        
        return d
    
    def _add_block_id(self, result, blockID):
        """add_block_id"""
        
        result['blockID'] = blockID
        
        return result
    
    
    def get_history_item_previous(self, current_block):
        """ Returns previous history string and decrement history cursor.
        """
        command = self.history.get_history_item(self.history_cursor - 1)
        if command is not None:
            self.history.input_cache[self.history_cursor] = current_block
            self.history_cursor -= 1
        return command
    
    
    def get_history_item_next(self, current_block):
        """ Returns next history string and increment history cursor.
        """
        command = self.history.get_history_item(self.history_cursor + 1)
        if command is not None:
            self.history.input_cache[self.history_cursor] = current_block
            self.history_cursor += 1
        return command
    
    ###
    # Subclasses probably want to override these methods...
    ###
    
    def update_cell_prompt(self, result):
        """Subclass may override to update the input prompt for a block. 
        Since this method will be called as a twisted.internet.defer.Deferred's callback,
        implementations should return result when finished."""
        
        return result
    
    
    def render_result(self, result):
        """Subclasses must override to render result. Since this method will be called as a 
        twisted.internet.defer.Deferred's callback, implementations should return result 
        when finished."""
        
        return result
    
    
    def render_error(self, failure):
        """Subclasses must override to render the failure. Since this method will be called as a 
        twisted.internet.defer.Deferred's callback, implementations should return result 
        when finished."""
        
        return failure
    



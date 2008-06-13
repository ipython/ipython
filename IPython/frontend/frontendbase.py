# encoding: utf-8
"""
frontendbase provides an interface and base class for GUI frontends for IPython.kernel/IPython.kernel.core.

Frontend implementations will likely want to subclass FrontEndBase. 

Author: Barry Wark
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
import string
import uuid
import _ast

import zope.interface as zi

from IPython.kernel.core.history import FrontEndHistory
from IPython.kernel.core.util import Bunch
from IPython.kernel.engineservice import IEngineCore

from twisted.python.failure import Failure

##############################################################################
# TEMPORARY!!! fake configuration, while we decide whether to use tconfig or
# not

rc = Bunch()
rc.prompt_in1 = r'In [$number]:  '
rc.prompt_in2 = r'...'
rc.prompt_out = r'Out [$number]:  '

##############################################################################

class IFrontEndFactory(zi.Interface):
    """Factory interface for frontends."""
    
    def __call__(engine=None, history=None):
        """
        Parameters:
        interpreter : IPython.kernel.engineservice.IEngineCore
        """
        
        pass



class IFrontEnd(zi.Interface):
    """Interface for frontends. All methods return t.i.d.Deferred"""
    
    zi.Attribute("input_prompt_template", "string.Template instance substituteable with execute result.")
    zi.Attribute("output_prompt_template", "string.Template instance substituteable with execute result.")
    zi.Attribute("continuation_prompt_template", "string.Template instance substituteable with execute result.")
    
    def update_cell_prompt(self, result):
        """Subclass may override to update the input prompt for a block. 
        Since this method will be called as a twisted.internet.defer.Deferred's callback,
        implementations should return result when finished."""
        
        pass
    
    def render_result(self, result):
        """Render the result of an execute call. Implementors may choose the method of rendering.
        For example, a notebook-style frontend might render a Chaco plot inline.
        
        Parameters:
            result : dict (result of IEngineBase.execute )
        
        Result:
            Output of frontend rendering
        """
        
        pass
    
    def render_error(self, failure):
        """Subclasses must override to render the failure. Since this method will be called as a 
        twisted.internet.defer.Deferred's callback, implementations should return result 
        when finished."""
        
        pass
    
    
    def input_prompt(result={}):
        """Returns the input prompt by subsituting into self.input_prompt_template"""
        pass
    
    def output_prompt(result):
        """Returns the output prompt by subsituting into self.output_prompt_template"""
        
        pass
    
    def continuation_prompt():
        """Returns the continuation prompt by subsituting into self.continuation_prompt_template"""
        
        pass
    
    def is_complete(block):
        """Returns True if block is complete, False otherwise."""
        
        pass
    
    def compile_ast(block):
        """Compiles block to an _ast.AST"""
        
        pass
    
    
    def get_history_previous(currentBlock):
        """Returns the block previous in  the history. Saves currentBlock if
        the history_cursor is currently at the end of the input history"""
        pass
    
    def get_history_next():
        """Returns the next block in the history."""
        
        pass
    

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
    zi.classProvides(IFrontEndFactory)
    
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
        
    
    def input_prompt(self, result={}):
        """Returns the current input prompt
        
        It would be great to use ipython1.core.prompts.Prompt1 here
        """
        
        result.setdefault('number','')
        
        return self.input_prompt_template.safe_substitute(result)
    
    
    def continuation_prompt(self):
        """Returns the current continuation prompt"""
        
        return self.continuation_prompt_template.safe_substitute()
    
    def output_prompt(self, result):
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
            ast = self.compile_ast(block)
        except:
            return False
        
        lines = block.split('\n')
        return (len(lines)==1 or str(lines[-1])=='')
    
    
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
        
        if(not self.is_complete(block)):
            return Failure(Exception("Block is not compilable"))
        
        if(blockID == None):
            blockID = uuid.uuid4() #random UUID
        
        d = self.engine.execute(block)
        d.addCallback(self._add_block_id, blockID)
        d.addCallback(self._add_history, block=block)
        d.addCallback(self.update_cell_prompt)
        d.addCallbacks(self.render_result, errback=self.render_error)
        
        return d
    
    
    def _add_block_id(self, result, blockID):
        """Add the blockID to result"""
        
        result['blockID'] = blockID
        
        return result
    
    def _add_history(self, result, block=None):
        """Add block to the history"""
        
        assert(block != None)
        self.history.add_items([block])
        self.history_cursor += 1
        
        return result
    
    
    def get_history_previous(self, currentBlock):
        """ Returns previous history string and decrement history cursor.
        """
        command = self.history.get_history_item(self.history_cursor - 1)
        
        if command is not None:
            if(self.history_cursor == len(self.history.input_cache)):
                self.history.input_cache[self.history_cursor] = currentBlock
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
    



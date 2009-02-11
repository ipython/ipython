"""
Base front end class for all async frontends.
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
from IPython.external import guid


from zope.interface import Interface, Attribute, implements, classProvides
from twisted.python.failure import Failure
from IPython.frontend.frontendbase import FrontEndBase, IFrontEnd, IFrontEndFactory
from IPython.kernel.core.history import FrontEndHistory
from IPython.kernel.engineservice import IEngineCore


class AsyncFrontEndBase(FrontEndBase):
    """
    Overrides FrontEndBase to wrap execute in a deferred result.
    All callbacks are made as callbacks on the deferred result.
    """
    
    implements(IFrontEnd)
    classProvides(IFrontEndFactory)
    
    def __init__(self, engine=None, history=None):
        assert(engine==None or IEngineCore.providedBy(engine))
        self.engine = IEngineCore(engine)
        if history is None:
                self.history = FrontEndHistory(input_cache=[''])
        else:
            self.history = history
    
    
    def execute(self, block, blockID=None):
        """Execute the block and return the deferred result.
        
        Parameters:
            block : {str, AST}
            blockID : any
                Caller may provide an ID to identify this block. 
                result['blockID'] := blockID
        
        Result:
            Deferred result of self.interpreter.execute
        """
        
        if(not self.is_complete(block)):
            return Failure(Exception("Block is not compilable"))
        
        if(blockID == None):
            blockID = guid.generate() 
        
        d = self.engine.execute(block)
        d.addCallback(self._add_history, block=block)
        d.addCallbacks(self._add_block_id_for_result,
                errback=self._add_block_id_for_failure,
                callbackArgs=(blockID,),
                errbackArgs=(blockID,))
        d.addBoth(self.update_cell_prompt, blockID=blockID)
        d.addCallbacks(self.render_result, 
            errback=self.render_error)
        
        return d
    


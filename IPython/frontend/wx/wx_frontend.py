# encoding: utf-8
# -*- test-case-name: ipython1.frontend.cocoa.tests.test_cocoa_frontend -*-

"""Classes to provide a Wx frontend to the 
ipython1.kernel.engineservice.EngineService.

"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------


import wx
from console_widget import ConsoleWidget


import IPython
from IPython.kernel.engineservice import EngineService, ThreadedEngineService
from IPython.frontend.frontendbase import FrontEndBase


from twisted.internet.threads import blockingCallFromThread

#-------------------------------------------------------------------------------
# Classes to implement the Wx frontend
#-------------------------------------------------------------------------------

# TODO: 
#   1. Remove any multithreading. 
    


class IPythonWxController(FrontEndBase, ConsoleWidget):
    userNS = dict() #mirror of engine.user_ns (key=>str(value))
    waiting_for_engine = False
    textView = False 
   
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 *args, **kwds):
        """ Create Shell instance.
        """
        ConsoleWidget.__init__(self, parent, id, pos, size, style)
        FrontEndBase.__init__(self, engine=ThreadedEngineService())

        self.lines = {}
        
        # Start the IPython engine
        self.engine.startService()
        
       
        #FIXME: print banner.
        banner = """IPython1 %s -- An enhanced Interactive Python.""" % IPython.__version__
    
    
    def appWillTerminate_(self, notification):
        """appWillTerminate"""
        
        self.engine.stopService()
    
    
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
        
        return self.engine.complete(token)
    
    
    def execute(self, block, blockID=None):
        self.waiting_for_engine = True
        self.willChangeValueForKey_('commandHistory')
        d = FrontEndBase.execute(block, blockID)
        d.addBoth(self._engine_done)
        
        return d
    
        
    def _engine_done(self, x):
        self.waiting_for_engine = False
        self.didChangeValueForKey_('commandHistory')
        return x
    
    
    def _store_engine_namespace_values(self, values, keys=[]):
        assert(len(values) == len(keys))
        self.willChangeValueForKey_('userNS')
        for (k,v) in zip(keys,values):
            self.userNS[k] = saferepr(v)
        self.didChangeValueForKey_('userNS')
    
    
    def textView_doCommandBySelector_(self, textView, selector):
        assert(textView == self.textView)
        NSLog("textView_doCommandBySelector_: "+selector)
        
        
        if(selector == 'insertNewline:'):
            indent = self.current_indent_string()
            if(indent):
                line = indent + self.current_line()
            else:
                line = self.current_line()
            
            if(self.is_complete(self.current_block())):
                self.execute(self.current_block(),
                                blockID=self.currentBlockID)
                self.start_new_block()
                
                return True
            
            return False
        
        elif(selector == 'moveUp:'):
            prevBlock = self.get_history_previous(self.current_block())
            if(prevBlock != None):
                self.replace_current_block_with_string(textView, prevBlock)
            else:
                NSBeep()
            return True
        
        elif(selector == 'moveDown:'):
            nextBlock = self.get_history_next()
            if(nextBlock != None):
                self.replace_current_block_with_string(textView, nextBlock)
            else:
                NSBeep()
            return True
        
        elif(selector == 'moveToBeginningOfParagraph:'):
            textView.setSelectedRange_(NSMakeRange(
                                        self.current_block_range().location, 
                                        0))
            return True
        elif(selector == 'moveToEndOfParagraph:'):
            textView.setSelectedRange_(NSMakeRange(
                                    self.current_block_range().location + \
                                    self.current_block_range().length, 0))
            return True
        elif(selector == 'deleteToEndOfParagraph:'):
            if(textView.selectedRange().location <= \
                self.current_block_range().location):
                # Intersect the selected range with the current line range
                if(self.current_block_range().length < 0):
                    self.blockRanges[self.currentBlockID].length = 0
            
                r = NSIntersectionRange(textView.rangesForUserTextChange()[0],
                                        self.current_block_range())
                
                if(r.length > 0): #no intersection
                    textView.setSelectedRange_(r)
            
            return False # don't actually handle the delete
        
        elif(selector == 'insertTab:'):
            if(len(self.current_line().strip()) == 0): #only white space
                return False
            else:
                self.textView.complete_(self)
                return True
        
        elif(selector == 'deleteBackward:'):
            #if we're at the beginning of the current block, ignore
            if(textView.selectedRange().location == \
                self.current_block_range().location):
                return True
            else:
                self.current_block_range().length-=1
                return False
        return False
    
    
    def textView_shouldChangeTextInRanges_replacementStrings_(self, 
        textView, ranges, replacementStrings):
        """
        Delegate method for NSTextView.
        
        Refuse change text in ranges not at end, but make those changes at 
        end.
        """
        
        assert(len(ranges) == len(replacementStrings))
        allow = True
        for r,s in zip(ranges, replacementStrings):
            r = r.rangeValue()
            if(textView.textStorage().length() > 0 and
                    r.location < self.current_block_range().location):
                self.insert_text(s)
                allow = False
            
            
            self.blockRanges.setdefault(self.currentBlockID, 
                                        self.current_block_range()).length +=\
                                         len(s)
        
        return allow


    def textView_completions_forPartialWordRange_indexOfSelectedItem_(self, 
        textView, words, charRange, index):
        try:
            ts = textView.textStorage()
            token = ts.string().substringWithRange_(charRange)
            completions = blockingCallFromThread(self.complete, token)
        except:
            completions = objc.nil
            NSBeep()
        
        return (completions,0)
    
    
    def currentLine(self):
        block = self.textForRange(self.currentBlockRange())
        block = block.split('\n')
        return block[-1]
    
    def update_cell_prompt(self, result):
        blockID = result['blockID']
        self.insert_text(self.inputPrompt(result=result),
                        scrollToVisible=False
                        )
        
        return result
    
    
    def render_result(self, result):
        self.insert_text('\n' +
                        self.outputPrompt(result) +
                        result.get('display',{}).get('pprint','') +
                        '\n\n')
        return result
    
        
    def render_error(self, failure):
        self.insert_text('\n\n'+str(failure)+'\n\n')
        return failure
    
    
    def insert_text(self, string, scrollToVisible=True):
        """Insert text into console_widget"""
        self.write(string)
    
    
    def currentIndentString(self):
        """returns string for indent or None if no indent"""
        
        if(len(self.currentBlock()) > 0):
            lines = self.currentBlock().split('\n')
            currentIndent = len(lines[-1]) - len(lines[-1].lstrip())
            if(currentIndent == 0):
                currentIndent = 4 
        
            result = ' ' * currentIndent
        else:
            result = None
        
        return result
    

if __name__ == '__main__':
    class MainWindow(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title, size=(300,250))
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.shell = IPythonWxController(self)
            self._sizer.Add(self.shell, 1, wx.EXPAND)
            self.SetSizer(self._sizer)
            self.SetAutoLayout(1)
            self.Show(True)

    app = wx.PySimpleApp()
    frame = MainWindow(None, wx.ID_ANY, 'Ipython')
    frame.SetSize((780, 460))
    shell = frame.shell

    app.MainLoop()


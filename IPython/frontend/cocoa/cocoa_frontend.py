# encoding: utf-8
# -*- test-case-name: ipython1.frontend.cocoa.tests.test_cocoa_frontend -*-

"""PyObjC classes to provide a Cocoa frontend to the ipython1.kernel.engineservice.EngineService.

The Cocoa frontend is divided into two classes:
    - IPythonCocoaController
    - IPythonCLITextViewDelegate

To add an IPython interpreter to a cocoa app, instantiate both of these classes in an XIB...[FINISH]
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2008  Barry Wark <barrywark@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import objc
import uuid

from Foundation import NSObject, NSMutableArray, NSMutableDictionary,\
                        NSLog, NSNotificationCenter, NSMakeRange,\
                        NSLocalizedString, NSIntersectionRange
                        
from AppKit import NSApplicationWillTerminateNotification, NSBeep,\
                    NSTextView, NSRulerView, NSVerticalRuler

from pprint import saferepr

import IPython
from IPython.kernel.engineservice import EngineService, ThreadedEngineService
from IPython.frontend.frontendbase import FrontEndBase

from twisted.internet.threads import blockingCallFromThread

#-------------------------------------------------------------------------------
# Classes to implement the Cocoa frontend
#-------------------------------------------------------------------------------

# TODO: 
#   1. use MultiEngineClient and out-of-process engine rather than ThreadedEngineService?
#   2. integrate Xgrid launching of engines
        
    


class IPythonCocoaController(NSObject, FrontEndBase):
    userNS = objc.ivar() #mirror of engine.user_ns (key=>str(value))
    waitingForEngine = objc.ivar().bool()
    textView = objc.IBOutlet()
    
    def init(self):
        self = super(IPythonCocoaController, self).init()
        FrontEndBase.__init__(self, engine=ThreadedEngineService())
        if(self != None):
            self._common_init()
        
        return self
    
    def _common_init(self):
        """_common_init"""
        
        self.userNS = NSMutableDictionary.dictionary()
        self.waitingForEngine = False
        
        self.lines = {}
        self.tabSpaces = 4
        self.tabUsesSpaces = True
        self.currentBlockID = self.nextBlockID()
        self.blockRanges = {} # blockID=>NSRange
    
    
    def awakeFromNib(self):
        """awakeFromNib"""
        
        self._common_init()
        
        # Start the IPython engine
        self.engine.startService()
        NSLog('IPython engine started')
        
        # Register for app termination
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self,
                                                'appWillTerminate:',
                                                 NSApplicationWillTerminateNotification,
                                                  None)
        
        self.textView.setDelegate_(self)
        self.textView.enclosingScrollView().setHasVerticalRuler_(True)
        self.verticalRulerView = NSRulerView.alloc().initWithScrollView_orientation_(
            self.textView.enclosingScrollView(),
            NSVerticalRuler)
        self.verticalRulerView.setClientView_(self.textView)
        self.startCLIForTextView()
    
    
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
        Deferred result of ipython1.kernel.engineservice.IEngineInteractive.complete
        """
        
        return self.engine.complete(token)
    
    
    def execute(self, block, blockID=None):
        self.waitingForEngine = True
        self.willChangeValueForKey_('commandHistory')
        d = super(IPythonCocoaController, self).execute(block, blockID)
        d.addBoth(self._engineDone)
        d.addCallback(self._updateUserNS)
        
        return d
    
        
    def _engineDone(self, x):
        self.waitingForEngine = False
        self.didChangeValueForKey_('commandHistory')
        return x
    
    def _updateUserNS(self, result):
        """Update self.userNS from self.engine's namespace"""
        d = self.engine.keys()
        d.addCallback(self._getEngineNamepsaceValuesForKeys)
        
        return result
    
    
    def _getEngineNamepsaceValuesForKeys(self, keys):
        d = self.engine.pull(keys)
        d.addCallback(self._storeEngineNamespaceValues, keys=keys)
    
    
    def _storeEngineNamespaceValues(self, values, keys=[]):
        assert(len(values) == len(keys))
        self.willChangeValueForKey_('userNS')
        for (k,v) in zip(keys,values):
            self.userNS[k] = saferepr(v)
        self.didChangeValueForKey_('userNS')
    
    
    def startCLIForTextView(self):
        """Print banner"""
        
        banner = """IPython1 %s -- An enhanced Interactive Python.""" % IPython.__version__
        
        self.insert_text(banner + '\n\n')
    
    # NSTextView/IPythonTextView delegate methods
    def textView_doCommandBySelector_(self, textView, selector):
        assert(textView == self.textView)
        NSLog("textView_doCommandBySelector_: "+selector)
        
        
        if(selector == 'insertNewline:'):
            indent = self.currentIndentString()
            if(indent):
                line = indent + self.currentLine()
            else:
                line = self.currentLine()
            
            if(self.is_complete(self.currentBlock())):
                self.execute(self.currentBlock(),
                                blockID=self.currentBlockID)
                self.startNewBlock()
                
                return True
            
            return False
        
        elif(selector == 'moveUp:'):
            prevBlock = self.get_history_previous(self.currentBlock())
            if(prevBlock != None):
                self.replaceCurrentBlockWithString(textView, prevBlock)
            else:
                NSBeep()
            return True
        
        elif(selector == 'moveDown:'):
            nextBlock = self.get_history_next()
            if(nextBlock != None):
                self.replaceCurrentBlockWithString(textView, nextBlock)
            else:
                NSBeep()
            return True
        
        elif(selector == 'moveToBeginningOfParagraph:'):
            textView.setSelectedRange_(NSMakeRange(self.currentBlockRange().location, 0))
            return True
        elif(selector == 'moveToEndOfParagraph:'):
            textView.setSelectedRange_(NSMakeRange(self.currentBlockRange().location + \
                                                self.currentBlockRange().length, 0))
            return True
        elif(selector == 'deleteToEndOfParagraph:'):
            if(textView.selectedRange().location <= self.currentBlockRange().location):
                # Intersect the selected range with the current line range
                if(self.currentBlockRange().length < 0):
                    self.blockRanges[self.currentBlockID].length = 0
            
                r = NSIntersectionRange(textView.rangesForUserTextChange()[0],
                                        self.currentBlockRange())
                
                if(r.length > 0): #no intersection
                    textView.setSelectedRange_(r)
            
            return False # don't actually handle the delete
        
        elif(selector == 'insertTab:'):
            if(len(self.currentLine().strip()) == 0): #only white space
                return False
            else:
                self.textView.complete_(self)
                return True
        
        elif(selector == 'deleteBackward:'):
            #if we're at the beginning of the current block, ignore
            if(textView.selectedRange().location == self.currentBlockRange().location):
                return True
            else:
                self.currentBlockRange().length-=1
                return False
        return False
    
    
    def textView_shouldChangeTextInRanges_replacementStrings_(self, textView, ranges, replacementStrings):
        """
        Delegate method for NSTextView.
        
        Refuse change text in ranges not at end, but make those changes at end.
        """
        
        #print 'textView_shouldChangeTextInRanges_replacementStrings_:',ranges,replacementStrings
        assert(len(ranges) == len(replacementStrings))
        allow = True
        for r,s in zip(ranges, replacementStrings):
            r = r.rangeValue()
            if(textView.textStorage().length() > 0 and
                    r.location < self.currentBlockRange().location):
                self.insert_text(s)
                allow = False
            
            
            self.blockRanges.setdefault(self.currentBlockID, self.currentBlockRange()).length += len(s)
        
        return allow
    
    def textView_completions_forPartialWordRange_indexOfSelectedItem_(self, textView, words, charRange, index):
        try:
            token = textView.textStorage().string().substringWithRange_(charRange)
            completions = blockingCallFromThread(self.complete, token)
        except:
            completions = objc.nil
            NSBeep()
        
        return (completions,0)
    
    
    def startNewBlock(self):
        """"""
        
        self.currentBlockID = self.nextBlockID()
    
    
    
    def nextBlockID(self):
        
        return uuid.uuid4()
    
    def currentBlockRange(self):
        return self.blockRanges.get(self.currentBlockID, NSMakeRange(self.textView.textStorage().length(), 0))
    
    def currentBlock(self):
        """The current block's text"""
        
        return self.textForRange(self.currentBlockRange())
    
    def textForRange(self, textRange):
        """textForRange"""
        
        return self.textView.textStorage().string().substringWithRange_(textRange)
    
    def currentLine(self):
        block = self.textForRange(self.currentBlockRange())
        block = block.split('\n')
        return block[-1]
    
    def update_cell_prompt(self, result):
        blockID = result['blockID']
        self.insert_text(self.input_prompt(result=result),
                        textRange=NSMakeRange(self.blockRanges[blockID].location,0),
                        scrollToVisible=False
                        )
        
        return result
    
    
    def render_result(self, result):
        blockID = result['blockID']
        inputRange = self.blockRanges[blockID]
        del self.blockRanges[blockID]
        
        #print inputRange,self.currentBlockRange()
        self.insert_text('\n' +
                        self.output_prompt(result) +
                        result.get('display',{}).get('pprint','') +
                        '\n\n',
                        textRange=NSMakeRange(inputRange.location+inputRange.length, 0))
        return result
    
        
    def render_error(self, failure):
        self.insert_text('\n\n'+str(failure)+'\n\n')
        self.startNewBlock()
        return failure
    
    
    def insert_text(self, string=None, textRange=None, scrollToVisible=True):
        """Insert text into textView at textRange, updating blockRanges as necessary"""
        
        if(textRange == None):
            textRange = NSMakeRange(self.textView.textStorage().length(), 0) #range for end of text
        
        for r in self.blockRanges.itervalues():
            intersection = NSIntersectionRange(r,textRange)
            if(intersection.length == 0): #ranges don't intersect
                if r.location >= textRange.location:
                    r.location += len(string)
            else: #ranges intersect
                if(r.location <= textRange.location):
                    assert(intersection.length == textRange.length)
                    r.length += textRange.length
                else:
                    r.location += intersection.length
        
        self.textView.replaceCharactersInRange_withString_(textRange, string) #textStorage().string()
        self.textView.setSelectedRange_(NSMakeRange(textRange.location+len(string), 0))
        if(scrollToVisible):
            self.textView.scrollRangeToVisible_(textRange)
        
    
    
    def replaceCurrentBlockWithString(self, textView, string):
        textView.replaceCharactersInRange_withString_(self.currentBlockRange(),
                                                        string)
        self.currentBlockRange().length = len(string)
        r = NSMakeRange(textView.textStorage().length(), 0)
        textView.scrollRangeToVisible_(r)
        textView.setSelectedRange_(r)
    
    
    def currentIndentString(self):
        """returns string for indent or None if no indent"""
        
        if(len(self.currentBlock()) > 0):
            lines = self.currentBlock().split('\n')
            currentIndent = len(lines[-1]) - len(lines[-1])
            if(currentIndent == 0):
                currentIndent = self.tabSpaces
        
            if(self.tabUsesSpaces):
                result = ' ' * currentIndent
            else:
                result = '\t' * (currentIndent/self.tabSpaces)
        else:
            result = None
        
        return result
    


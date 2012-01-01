# encoding: utf-8
# -*- test-case-name: IPython.frontend.cocoa.tests.test_cocoa_frontend -*-

"""PyObjC classes to provide a Cocoa frontend to the
IPython.kernel.engineservice.IEngineBase.

To add an IPython interpreter to a cocoa app, instantiate an
IPythonCocoaController in a XIB and connect its textView outlet to an
NSTextView instance in your UI. That's it.

Author: Barry Wark
"""

__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import objc
import uuid

from Foundation import NSObject, NSMutableArray, NSMutableDictionary,\
                        NSLog, NSNotificationCenter, NSMakeRange,\
                        NSLocalizedString, NSIntersectionRange,\
                        NSString, NSAutoreleasePool

from AppKit import NSApplicationWillTerminateNotification, NSBeep,\
                    NSTextView, NSRulerView, NSVerticalRuler

from pprint import saferepr

import IPython
from IPython.kernel.engineservice import ThreadedEngineService
from IPython.frontend.asyncfrontendbase import AsyncFrontEndBase

from twisted.internet.threads import blockingCallFromThread
from twisted.python.failure import Failure

#-----------------------------------------------------------------------------
# Classes to implement the Cocoa frontend
#-----------------------------------------------------------------------------

# TODO:
#   1. use MultiEngineClient and out-of-process engine rather than
#       ThreadedEngineService?
#   2. integrate Xgrid launching of engines

class AutoreleasePoolWrappedThreadedEngineService(ThreadedEngineService):
    """Wrap all blocks in an NSAutoreleasePool"""

    def wrapped_execute(self, msg, lines):
        """wrapped_execute"""
        try:
            p = NSAutoreleasePool.alloc().init()
            result = super(AutoreleasePoolWrappedThreadedEngineService,
                            self).wrapped_execute(msg, lines)
        finally:
            p.drain()

        return result



class Cell(NSObject):
    """
    Representation of the prompts, input and output of a cell in the
    frontend
    """

    blockNumber = objc.ivar().unsigned_long()
    blockID = objc.ivar()
    inputBlock = objc.ivar()
    output = objc.ivar()



class CellBlock(object):
    """
    Storage for information about text ranges relating to a single cell
    """


    def __init__(self, inputPromptRange, inputRange=None, outputPromptRange=None,
                outputRange=None):
        super(CellBlock, self).__init__()
        self.inputPromptRange = inputPromptRange
        self.inputRange = inputRange
        self.outputPromptRange = outputPromptRange
        self.outputRange = outputRange

    def update_ranges_for_insertion(self, text, textRange):
        """Update ranges for text insertion at textRange"""

        for r in [self.inputPromptRange,self.inputRange,
                    self.outputPromptRange, self.outputRange]:
            if(r == None):
                continue
            intersection = NSIntersectionRange(r,textRange)
            if(intersection.length == 0): #ranges don't intersect
                if r.location >= textRange.location:
                    r.location += len(text)
            else: #ranges intersect
                if(r.location > textRange.location):
                    offset = len(text) - intersection.length
                    r.length -= offset
                    r.location += offset
                elif(r.location == textRange.location):
                    r.length += len(text) - intersection.length
                else:
                    r.length -= intersection.length


    def update_ranges_for_deletion(self, textRange):
        """Update ranges for text deletion at textRange"""

        for r in [self.inputPromptRange,self.inputRange,
                    self.outputPromptRange, self.outputRange]:
            if(r==None):
                continue
            intersection = NSIntersectionRange(r, textRange)
            if(intersection.length == 0): #ranges don't intersect
                if r.location >= textRange.location:
                    r.location -= textRange.length
            else: #ranges intersect
                if(r.location > textRange.location):
                    offset = intersection.length
                    r.length -= offset
                    r.location += offset
                elif(r.location == textRange.location):
                    r.length += intersection.length
                else:
                    r.length -= intersection.length

    def __repr__(self):
        return 'CellBlock('+ str((self.inputPromptRange,
                                self.inputRange,
                                self.outputPromptRange,
                                self.outputRange)) + ')'




class IPythonCocoaController(NSObject, AsyncFrontEndBase):
    userNS = objc.ivar() #mirror of engine.user_ns (key=>str(value))
    waitingForEngine = objc.ivar().bool()
    textView = objc.IBOutlet()

    def init(self):
        self = super(IPythonCocoaController, self).init()
        AsyncFrontEndBase.__init__(self,
                    engine=AutoreleasePoolWrappedThreadedEngineService())
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
        self.currentBlockID = self.next_block_ID()
        self.blockRanges = {} # blockID=>CellBlock


    def awakeFromNib(self):
        """awakeFromNib"""

        self._common_init()

        # Start the IPython engine
        self.engine.startService()
        NSLog('IPython engine started')

        # Register for app termination
        nc = NSNotificationCenter.defaultCenter()
        nc.addObserver_selector_name_object_(
                                    self,
                                    'appWillTerminate:',
                                    NSApplicationWillTerminateNotification,
                                    None)

        self.textView.setDelegate_(self)
        self.textView.enclosingScrollView().setHasVerticalRuler_(True)
        r = NSRulerView.alloc().initWithScrollView_orientation_(
                                        self.textView.enclosingScrollView(),
                                        NSVerticalRuler)
        self.verticalRulerView = r
        self.verticalRulerView.setClientView_(self.textView)
        self._start_cli_banner()
        self.start_new_block()


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
        self.waitingForEngine = True
        self.willChangeValueForKey_('commandHistory')
        d = super(IPythonCocoaController, self).execute(block,
                                                        blockID)
        d.addBoth(self._engine_done)
        d.addCallback(self._update_user_ns)

        return d


    def push_(self, namespace):
        """Push dictionary of key=>values to python namespace"""

        self.waitingForEngine = True
        self.willChangeValueForKey_('commandHistory')
        d = self.engine.push(namespace)
        d.addBoth(self._engine_done)
        d.addCallback(self._update_user_ns)


    def pull_(self, keys):
        """Pull keys from python namespace"""

        self.waitingForEngine = True
        result = blockingCallFromThread(self.engine.pull, keys)
        self.waitingForEngine = False

    @objc.signature('v@:@I')
    def executeFileAtPath_encoding_(self, path, encoding):
        """Execute file at path in an empty namespace. Update the engine
        user_ns with the resulting locals."""

        lines,err = NSString.stringWithContentsOfFile_encoding_error_(
            path,
            encoding,
            None)
        self.engine.execute(lines)


    def _engine_done(self, x):
        self.waitingForEngine = False
        self.didChangeValueForKey_('commandHistory')
        return x

    def _update_user_ns(self, result):
        """Update self.userNS from self.engine's namespace"""
        d = self.engine.keys()
        d.addCallback(self._get_engine_namespace_values_for_keys)

        return result


    def _get_engine_namespace_values_for_keys(self, keys):
        d = self.engine.pull(keys)
        d.addCallback(self._store_engine_namespace_values, keys=keys)


    def _store_engine_namespace_values(self, values, keys=[]):
        assert(len(values) == len(keys))
        self.willChangeValueForKey_('userNS')
        for (k,v) in zip(keys,values):
            self.userNS[k] = saferepr(v)
        self.didChangeValueForKey_('userNS')


    def update_cell_prompt(self, result, blockID=None):
        print self.blockRanges
        if(isinstance(result, Failure)):
            prompt = self.input_prompt()

        else:
            prompt = self.input_prompt(number=result['number'])

        r = self.blockRanges[blockID].inputPromptRange
        self.insert_text(prompt,
                textRange=r,
                scrollToVisible=False
                )

        return result


    def render_result(self, result):
        blockID = result['blockID']
        inputRange = self.blockRanges[blockID].inputRange
        del self.blockRanges[blockID]

        #print inputRange,self.current_block_range()
        self.insert_text('\n' +
                self.output_prompt(number=result['number']) +
                result.get('display',{}).get('pprint','') +
                '\n\n',
                textRange=NSMakeRange(inputRange.location+inputRange.length,
                                    0))
        return result


    def render_error(self, failure):
        print failure
        blockID = failure.blockID
        inputRange = self.blockRanges[blockID].inputRange
        self.insert_text('\n' +
                        self.output_prompt() +
                        '\n' +
                        failure.getErrorMessage() +
                        '\n\n',
                        textRange=NSMakeRange(inputRange.location +
                                                inputRange.length,
                                                0))
        self.start_new_block()
        return failure


    def _start_cli_banner(self):
        """Print banner"""

        banner = """IPython1 %s -- An enhanced Interactive Python.""" % \
                    IPython.__version__

        self.insert_text(banner + '\n\n')


    def start_new_block(self):
        """"""

        self.currentBlockID = self.next_block_ID()
        self.blockRanges[self.currentBlockID] = self.new_cell_block()
        self.insert_text(self.input_prompt(),
            textRange=self.current_block_range().inputPromptRange)



    def next_block_ID(self):

        return uuid.uuid4()

    def new_cell_block(self):
        """A new CellBlock at the end of self.textView.textStorage()"""

        return CellBlock(NSMakeRange(self.textView.textStorage().length(),
                                    0), #len(self.input_prompt())),
                        NSMakeRange(self.textView.textStorage().length(),# + len(self.input_prompt()),
                                    0))


    def current_block_range(self):
        return self.blockRanges.get(self.currentBlockID,
                        self.new_cell_block())

    def current_block(self):
        """The current block's text"""

        return self.text_for_range(self.current_block_range().inputRange)

    def text_for_range(self, textRange):
        """text_for_range"""

        ts = self.textView.textStorage()
        return ts.string().substringWithRange_(textRange)

    def current_line(self):
        block = self.text_for_range(self.current_block_range().inputRange)
        block = block.split('\n')
        return block[-1]


    def insert_text(self, string=None, textRange=None, scrollToVisible=True):
        """Insert text into textView at textRange, updating blockRanges
        as necessary
        """
        if(textRange == None):
            #range for end of text
            textRange = NSMakeRange(self.textView.textStorage().length(), 0)


        self.textView.replaceCharactersInRange_withString_(
            textRange, string)

        for r in self.blockRanges.itervalues():
            r.update_ranges_for_insertion(string, textRange)

        self.textView.setSelectedRange_(textRange)
        if(scrollToVisible):
            self.textView.scrollRangeToVisible_(textRange)



    def replace_current_block_with_string(self, textView, string):
        textView.replaceCharactersInRange_withString_(
                                    self.current_block_range().inputRange,
                                    string)
        self.current_block_range().inputRange.length = len(string)
        r = NSMakeRange(textView.textStorage().length(), 0)
        textView.scrollRangeToVisible_(r)
        textView.setSelectedRange_(r)


    def current_indent_string(self):
        """returns string for indent or None if no indent"""

        return self._indent_for_block(self.current_block())


    def _indent_for_block(self, block):
        lines = block.split('\n')
        if(len(lines) > 1):
            currentIndent = len(lines[-1]) - len(lines[-1].lstrip())
            if(currentIndent == 0):
                currentIndent = self.tabSpaces

            if(self.tabUsesSpaces):
                result = ' ' * currentIndent
            else:
                result = '\t' * (currentIndent/self.tabSpaces)
        else:
            result = None

        return result


    # NSTextView delegate methods...
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
                            self.current_block_range().inputRange.location,
                            0))
            return True
        elif(selector == 'moveToEndOfParagraph:'):
            textView.setSelectedRange_(NSMakeRange(
                            self.current_block_range().inputRange.location + \
                            self.current_block_range().inputRange.length, 0))
            return True
        elif(selector == 'deleteToEndOfParagraph:'):
            if(textView.selectedRange().location <= \
                self.current_block_range().location):
                raise NotImplemented()

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
                self.current_block_range().inputRange.location):
                return True
            else:
                for r in self.blockRanges.itervalues():
                    deleteRange = textView.selectedRange
                    if(deleteRange.length == 0):
                        deleteRange.location -= 1
                        deleteRange.length = 1
                    r.update_ranges_for_deletion(deleteRange)
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
                r.location < self.current_block_range().inputRange.location):
                self.insert_text(s)
                allow = False

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



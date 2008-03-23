#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
'''
Provides IPython WX console widgets.

@author: Laurent Dufrechou
laurent.dufrechou _at_ gmail.com
This WX widget is based on the original work of Eitan Isaacson
that provided the console for the GTK toolkit.

Original work from:
@author: Eitan Isaacson
@organization: IBM Corporation
@copyright: Copyright (c) 2007 IBM Corporation
@license: BSD

All rights reserved. This program and the accompanying materials are made
available under the terms of the BSD which accompanies this distribution, and
is available at U{http://www.opensource.org/licenses/bsd-license.php}
'''

__version__ = 0.8
__author__  = "Laurent Dufrechou"
__email__   = "laurent.dufrechou _at_ gmail.com"
__license__ = "BSD"

import wx
import wx.stc  as  stc
import wx.lib.newevent

import re
import sys
import os
import locale
import time
from StringIO import StringIO
try:
        import IPython
except Exception,e:
        raise "Error importing IPython (%s)" % str(e)


from NonBlockingIPShell import *

class WxNonBlockingIPShell(NonBlockingIPShell):
    '''
    An NonBlockingIPShell Thread that is WX dependent.
    Thus it permits direct interaction with a WX GUI without OnIdle event state machine trick...
    '''
    def __init__(self,wx_instance,
                 argv=[],user_ns={},user_global_ns=None,
                 cin=None, cout=None, cerr=None,
                 ask_exit_handler=None):
        
        #user_ns['addGUIShortcut'] = self.addGUIShortcut
        NonBlockingIPShell.__init__(self,argv,user_ns,user_global_ns,
                                    cin, cout, cerr,
                                    ask_exit_handler)

        # This creates a new Event class and a EVT binder function
        (self.IPythonAskExitEvent, EVT_IP_ASK_EXIT) = wx.lib.newevent.NewEvent()
        #(self.IPythonAddButtonEvent, EVT_IP_ADD_BUTTON_EXIT) = \
        #                                     wx.lib.newevent.NewEvent()
        (self.IPythonExecuteDoneEvent, EVT_IP_EXECUTE_DONE) = \
                                            wx.lib.newevent.NewEvent()

        wx_instance.Bind(EVT_IP_ASK_EXIT, wx_instance.ask_exit_handler)
        #wx_instance.Bind(EVT_IP_ADD_BUTTON_EXIT, wx_instance.add_button_handler)
        wx_instance.Bind(EVT_IP_EXECUTE_DONE, wx_instance.evtStateExecuteDone)

        self.wx_instance = wx_instance
        self._IP.ask_exit = self._askExit
        
    #def addGUIShortcut(self,text,func):
    #    evt = self.IPythonAddButtonEvent(
    #        button_info={   'text':text, 
    #                        'func':self.wx_instance.doExecuteLine(func)})
    #    wx.PostEvent(self.wx_instance, evt)
                    
    def _askExit(self):
        evt = self.IPythonAskExitEvent()
        wx.PostEvent(self.wx_instance, evt)

    def _afterExecute(self):
        evt = self.IPythonExecuteDoneEvent()
        wx.PostEvent(self.wx_instance, evt)

                
class WxConsoleView(stc.StyledTextCtrl):
    '''
    Specialized styled text control view for console-like workflow.
    We use here a scintilla frontend thus it can be reused in any GUI taht supports
    scintilla with less work.

    @cvar ANSI_COLORS_BLACK: Mapping of terminal colors to X11 names.(with Black background)
    @type ANSI_COLORS_BLACK: dictionary

    @cvar ANSI_COLORS_WHITE: Mapping of terminal colors to X11 names.(with White background)
    @type ANSI_COLORS_WHITE: dictionary

    @ivar color_pat: Regex of terminal color pattern
    @type color_pat: _sre.SRE_Pattern
    '''
    ANSI_STYLES_BLACK ={'0;30': [0,'WHITE'],             '0;31': [1,'RED'],
                        '0;32': [2,'GREEN'],             '0;33': [3,'BROWN'],
                        '0;34': [4,'BLUE'],              '0;35': [5,'PURPLE'],
                        '0;36': [6,'CYAN'],              '0;37': [7,'LIGHT GREY'],
                        '1;30': [8,'DARK GREY'],         '1;31': [9,'RED'],
                        '1;32': [10,'SEA GREEN'],        '1;33': [11,'YELLOW'],
                        '1;34': [12,'LIGHT BLUE'],       '1;35': [13,'MEDIUM VIOLET RED'],
                        '1;36': [14,'LIGHT STEEL BLUE'], '1;37': [15,'YELLOW']}

    ANSI_STYLES_WHITE ={'0;30': [0,'BLACK'],             '0;31': [1,'RED'],
                        '0;32': [2,'GREEN'],             '0;33': [3,'BROWN'],
                        '0;34': [4,'BLUE'],              '0;35': [5,'PURPLE'],
                        '0;36': [6,'CYAN'],              '0;37': [7,'LIGHT GREY'],
                        '1;30': [8,'DARK GREY'],         '1;31': [9,'RED'],
                        '1;32': [10,'SEA GREEN'],        '1;33': [11,'YELLOW'],
                        '1;34': [12,'LIGHT BLUE'],       '1;35': [13,'MEDIUM VIOLET RED'],
                        '1;36': [14,'LIGHT STEEL BLUE'], '1;37': [15,'YELLOW']}

    def __init__(self,parent,prompt,intro="",background_color="BLACK",pos=wx.DefaultPosition, ID = -1, size=wx.DefaultSize,
                 style=0):
        '''
        Initialize console view.

        @param parent: Parent widget
        @param prompt: User specified prompt
        @type intro: string
        @param intro: User specified startup introduction string
        @type intro: string
        @param background_color: Can be BLACK or WHITE
        @type background_color: string
        @param other: init param of styledTextControl (can be used as-is)
        '''
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        ####### Scintilla configuration ##################################################
        
        # Ctrl + B or Ctrl + N can be used to zoomin/zoomout the text inside the widget
        self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        #we define platform specific fonts
        if wx.Platform == '__WXMSW__':
                faces = { 'times': 'Times New Roman',
                          'mono' : 'Courier New',
                          'helv' : 'Arial',
                          'other': 'Comic Sans MS',
                          'size' : 10,
                          'size2': 8,
                         }
        elif wx.Platform == '__WXMAC__':
            faces = { 'times': 'Times New Roman',
                      'mono' : 'Monaco',
                      'helv' : 'Arial',
                      'other': 'Comic Sans MS',
                      'size' : 10,
                      'size2': 8,
                     }
        else:
            faces = { 'times': 'Times',
                      'mono' : 'Courier',
                      'helv' : 'Helvetica',
                      'other': 'new century schoolbook',
                      'size' : 10,
                      'size2': 8,
                     }

        #We draw a line at position 80
        self.SetEdgeMode(stc.STC_EDGE_LINE)
        self.SetEdgeColumn(80)
        self.SetEdgeColour(wx.LIGHT_GREY)

        #self.SetViewWhiteSpace(True)
        #self.SetViewEOL(True)
        self.SetEOLMode(stc.STC_EOL_CRLF)
        #self.SetWrapMode(stc.STC_WRAP_CHAR)
        #self.SetWrapMode(stc.STC_WRAP_WORD)
        self.SetBufferedDraw(True)
        #self.SetUseAntiAliasing(True)
        self.SetLayoutCache(stc.STC_CACHE_PAGE)

        self.EnsureCaretVisible()
        
        self.SetMargins(3,3) #text is moved away from border with 3px
        # Suppressing Scintilla margins
        self.SetMarginWidth(0,0)
        self.SetMarginWidth(1,0)
        self.SetMarginWidth(2,0)

        # make some styles
        if background_color != "BLACK":
            self.background_color = "WHITE"
            self.SetCaretForeground("BLACK")
            self.ANSI_STYLES = self.ANSI_STYLES_WHITE
        else:
            self.background_color = background_color
            self.SetCaretForeground("WHITE")
            self.ANSI_STYLES = self.ANSI_STYLES_BLACK

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "fore:%s,back:%s,size:%d,face:%s" % (self.ANSI_STYLES['0;30'][1],
                                                                                      self.background_color,
                                                                                      faces['size'], faces['mono']))
        self.StyleClearAll()
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FF0000,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")
    
        for style in self.ANSI_STYLES.values():
            self.StyleSetSpec(style[0], "bold,fore:%s" % style[1])
        
        #######################################################################
        
        self.indent = 0
        self.prompt_count = 0
        self.color_pat = re.compile('\x01?\x1b\[(.*?)m\x02?')
        
        self.write(intro)
        self.setPrompt(prompt)
        self.showPrompt()
        
        self.Bind(wx.EVT_KEY_DOWN, self._onKeypress, self)
        #self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)

    def write(self, text):
        '''
        Write given text to buffer.

        @param text: Text to append.
        @type text: string
        '''
        segments = self.color_pat.split(text)
        segment = segments.pop(0)
        self.StartStyling(self.getCurrentLineEnd(),0xFF)
        self.AppendText(segment)
        
        if segments:
            ansi_tags = self.color_pat.findall(text)

            for tag in ansi_tags:
                i = segments.index(tag)
                self.StartStyling(self.getCurrentLineEnd(),0xFF)
                self.AppendText(segments[i+1])

                if tag != '0':
                    self.SetStyling(len(segments[i+1]),self.ANSI_STYLES[tag][0])

                segments.pop(i)
                
        self.moveCursor(self.getCurrentLineEnd())
         
    def getPromptLen(self):
        '''
        Return the length of current prompt
        '''
        return len(str(self.prompt_count)) + 7

    def setPrompt(self,prompt):
        self.prompt = prompt

    def setIndentation(self,indentation):
        self.indent = indentation
        
    def setPromptCount(self,count):
        self.prompt_count = count
        
    def showPrompt(self):
        '''
        Prints prompt at start of line.

        @param prompt: Prompt to print.
        @type prompt: string
        '''
        self.write(self.prompt)
        #now we update the position of end of prompt
        self.current_start = self.getCurrentLineEnd()
        
        autoindent = self.indent*' '
        autoindent = autoindent.replace('    ','\t')
        self.write(autoindent)
        
    def changeLine(self, text):
        '''
        Replace currently entered command line with given text.

        @param text: Text to use as replacement.
        @type text: string
        '''
        self.SetSelection(self.getCurrentPromptStart(),self.getCurrentLineEnd())
        self.ReplaceSelection(text)
        self.moveCursor(self.getCurrentLineEnd())

    def getCurrentPromptStart(self):
        return self.current_start

    def getCurrentLineStart(self):
        return self.GotoLine(self.LineFromPosition(self.GetCurrentPos()))

    def getCurrentLineEnd(self):
        return self.GetLength()

    def getCurrentLine(self):
        '''
        Get text in current command line.

        @return: Text of current command line.
        @rtype: string
        '''
        return self.GetTextRange(self.getCurrentPromptStart(),
                                 self.getCurrentLineEnd())

    def showReturned(self, text):
        '''
        Show returned text from last command and print new prompt.

        @param text: Text to show.
        @type text: string
        '''
        self.write('\n'+text)
        if text:
            self.write('\n')
        self.showPrompt()

    def moveCursorOnNewValidKey(self):
        #If cursor is at wrong position put it at last line...
        if self.GetCurrentPos() < self.getCurrentPromptStart():
            self.GotoPos(self.getCurrentPromptStart())
        
    def removeFromTo(self,from_pos,to_pos):
        if from_pos < to_pos:
            self.SetSelection(from_pos,to_pos)
            self.DeleteBack()
                                                          
    def removeCurrentLine(self):
        self.LineDelete()
        
    def moveCursor(self,position):
        self.GotoPos(position)

    def getCursorPos(self):
        return self.GetCurrentPos()

    def selectFromTo(self,from_pos,to_pos):
        self.SetSelectionStart(from_pos)
        self.SetSelectionEnd(to_pos)
        
    def writeHistory(self,history):
        self.removeFromTo(self.getCurrentPromptStart(),self.getCurrentLineEnd())
        self.changeLine(history)
        
    def writeCompletion(self, possibilities):
        max_len = len(max(possibilities,key=len))
        max_symbol =' '*max_len
        
        #now we check how much symbol we can put on a line...
        cursor_pos = self.getCursorPos()
        test_buffer = max_symbol + ' '*4
        current_lines = self.GetLineCount()
        
        allowed_symbols = 80/len(test_buffer)
        if allowed_symbols == 0:
                allowed_symbols = 1
        
        pos = 1
        buf = ''
        for symbol in possibilities:
            #buf += symbol+'\n'#*spaces)
            if pos<allowed_symbols:
                spaces = max_len - len(symbol) + 4
                buf += symbol+' '*spaces
                pos += 1
            else:
                buf+=symbol+'\n'
                pos = 1
        self.write(buf)
                             
    def _onKeypress(self, event, skip=True):
        '''
        Key press callback used for correcting behavior for console-like
        interfaces. For example 'home' should go to prompt, not to begining of
        line.

        @param widget: Widget that key press accored in.
        @type widget: gtk.Widget
        @param event: Event object
        @type event: gtk.gdk.Event

        @return: Return True if event as been catched.
        @rtype: boolean
        '''
	
        if event.GetKeyCode() == wx.WXK_HOME:
            if event.Modifiers == wx.MOD_NONE:
                self.moveCursorOnNewValidKey()
                self.moveCursor(self.getCurrentPromptStart())
                return True
            elif event.Modifiers == wx.MOD_SHIFT:
                self.moveCursorOnNewValidKey()
                self.selectFromTo(self.getCurrentPromptStart(),self.getCursorPos())
                return True
            else:
                return False

        elif event.GetKeyCode() == wx.WXK_LEFT:
            if event.Modifiers == wx.MOD_NONE:
                self.moveCursorOnNewValidKey()
                
                self.moveCursor(self.getCursorPos()-1)
                if self.getCursorPos() < self.getCurrentPromptStart():
                    self.moveCursor(self.getCurrentPromptStart())
                return True

        elif event.GetKeyCode() == wx.WXK_BACK:
            self.moveCursorOnNewValidKey()
	    if self.getCursorPos() > self.getCurrentPromptStart():
                self.removeFromTo(self.getCursorPos()-1,self.getCursorPos())
	    return True
        
        if skip:
            if event.GetKeyCode() not in [wx.WXK_PAGEUP,wx.WXK_PAGEDOWN] and event.Modifiers == wx.MOD_NONE:
                self.moveCursorOnNewValidKey()
                
            event.Skip()
            return True
        return False

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)
            #pt = self.PointFromPosition(braceOpposite)
            #self.Refresh(True, wxRect(pt.x, pt.y, 5,5))
            #print pt
            #self.Refresh(False)
        
class WxIPythonViewPanel(wx.Panel):
    '''
    This is wx.Panel that embbed the IPython Thread and the wx.StyledTextControl
    If you want to port this to any other GUI toolkit, just replace the WxConsoleView
    by YOURGUIConsoleView and make YOURGUIIPythonView derivate from whatever container you want.
    I've choosed to derivate from a wx.Panel because it seems to be ore usefull
    Any idea to make it more 'genric' welcomed.
    '''

    def __init__(self, parent, ask_exit_handler=None, intro=None,
                 background_color="BLACK", add_button_handler=None, 
                 wx_ip_shell=None,
                 ):
        '''
        Initialize.
        Instanciate an IPython thread.
        Instanciate a WxConsoleView.
        Redirect I/O to console.
        '''
        wx.Panel.__init__(self,parent,-1)

        ### IPython non blocking shell instanciation ###
        self.cout = StringIO()

        self.add_button_handler = add_button_handler
        self.ask_exit_handler = ask_exit_handler

        if wx_ip_shell is not None:
            self.IP = wx_ip_shell
        else:
            self.IP = WxNonBlockingIPShell(self,
                                    cout=self.cout,cerr=self.cout,
                                    ask_exit_handler = ask_exit_handler)

        ### IPython wx console view instanciation ###
        #If user didn't defined an intro text, we create one for him
        #If you really wnat an empty intrp just call wxIPythonViewPanel with intro=''
        if intro == None:
            welcome_text = "Welcome to WxIPython Shell.\n\n"
            welcome_text+= self.IP.getBanner()
            welcome_text+= "!command  -> Execute command in shell\n"
            welcome_text+= "TAB       -> Autocompletion\n"

        self.text_ctrl = WxConsoleView(self,
                                       self.IP.getPrompt(),
                                       intro=welcome_text,
                                       background_color=background_color)
        
        self.text_ctrl.Bind(wx.EVT_KEY_DOWN, self.keyPress, self.text_ctrl)

        ### making the layout of the panel ###
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        #and we focus on the widget :)
        self.SetFocus()

        #widget state management (for key handling different cases)
        self.setCurrentState('IDLE')
        self.pager_state = 'DONE'
        
    def __del__(self):
        WxConsoleView.__del__()
        
    #---------------------------- IPython Thread Management ---------------------------------------
    def stateDoExecuteLine(self):
        #print >>sys.__stdout__,"command:",self.getCurrentLine()
        self.doExecuteLine(self.text_ctrl.getCurrentLine())
        
    def doExecuteLine(self,line):
        #print >>sys.__stdout__,"command:",line
        self.IP.doExecute(line.replace('\t',' '*4))
        self.updateHistoryTracker(self.text_ctrl.getCurrentLine())
        self.setCurrentState('WAIT_END_OF_EXECUTION')

        
    def evtStateExecuteDone(self,evt):
        self.doc = self.IP.getDocText()
        self.help = self.IP.getHelpText()
        if self.doc:
            self.pager_lines = self.doc[7:].split('\n')
	    self.pager_state = 'INIT'
            self.setCurrentState('SHOW_DOC')
            self.pager(self.doc)
            
        if self.help:
            self.pager_lines = self.help.split('\n')
	    self.pager_state = 'INIT'
            self.setCurrentState('SHOW_DOC')
            self.pager(self.help)
                
        else:
            self.stateShowPrompt()

    def stateShowPrompt(self):
        self.setCurrentState('SHOW_PROMPT')
        self.text_ctrl.setPrompt(self.IP.getPrompt())
        self.text_ctrl.setIndentation(self.IP.getIndentation())
        self.text_ctrl.setPromptCount(self.IP.getPromptCount())
        rv = self.cout.getvalue()
        if rv: rv = rv.strip('\n')
        self.text_ctrl.showReturned(rv)
        self.cout.truncate(0)
        self.IP.initHistoryIndex()
        self.setCurrentState('IDLE')

    def setCurrentState(self, state):
        self.cur_state = state
        self.updateStatusTracker(self.cur_state)
        
    #---------------------------- IPython pager ---------------------------------------
    def pager(self,text):#,start=0,screen_lines=0,pager_cmd = None):
        if self.pager_state == 'WAITING':
		#print >>sys.__stdout__,"PAGER waiting"
        	return
	
	if self.pager_state == 'INIT':
		#print >>sys.__stdout__,"PAGER state:",self.pager_state
                self.pager_nb_lines = len(self.pager_lines)
		self.pager_index = 0
		self.pager_do_remove = False
		self.text_ctrl.write('\n')
		self.pager_state = 'PROCESS_LINES'

	if self.pager_state == 'PROCESS_LINES':
        	#print >>sys.__stdout__,"PAGER state:",self.pager_state
        	if self.pager_do_remove == True:
			self.text_ctrl.removeCurrentLine()
			self.pager_do_remove = False
	
		if self.pager_nb_lines > 10:
	                #print >>sys.__stdout__,"PAGER processing 10 lines"
			if self.pager_index > 0:
				self.text_ctrl.write(">\x01\x1b[1;36m\x02"+self.pager_lines[self.pager_index]+'\n')
			else:
				self.text_ctrl.write("\x01\x1b[1;36m\x02 "+self.pager_lines[self.pager_index]+'\n')
			
			for line in self.pager_lines[self.pager_index+1:self.pager_index+9]:
				self.text_ctrl.write("\x01\x1b[1;36m\x02 "+line+'\n')
			self.pager_index += 10
			self.pager_nb_lines -= 10
			self.text_ctrl.write("--- Push Enter to continue or 'Q' to quit---")
			self.pager_do_remove = True
			self.pager_state = 'WAITING'
			return
        	else:
	                #print >>sys.__stdout__,"PAGER processing last lines"
			if self.pager_nb_lines > 0:
				if self.pager_index > 0:
					self.text_ctrl.write(">\x01\x1b[1;36m\x02"+self.pager_lines[self.pager_index]+'\n')
				else:
					self.text_ctrl.write("\x01\x1b[1;36m\x02 "+self.pager_lines[self.pager_index]+'\n')
				
				self.pager_index += 1
                                self.pager_nb_lines -= 1
	              	if self.pager_nb_lines > 0:
        	        	for line in self.pager_lines[self.pager_index:]:
					self.text_ctrl.write("\x01\x1b[1;36m\x02 "+line+'\n')
                			self.pager_nb_lines = 0
			self.pager_state = 'DONE'
			self.stateShowPrompt()
                
    #---------------------------- Key Handler --------------------------------------------
    def keyPress(self, event):
        '''
        Key press callback with plenty of shell goodness, like history,
        autocompletions, etc.
        '''
	
        if event.GetKeyCode() == ord('C'):
            if event.Modifiers == wx.MOD_CONTROL:
                if self.cur_state == 'WAIT_END_OF_EXECUTION':
                    #we raise an exception inside the IPython thread container
                    self.IP.ce.raise_exc(KeyboardInterrupt)
                    return
                
        if event.KeyCode == wx.WXK_RETURN:
            if self.cur_state == 'IDLE':
                #we change the state ot the state machine
                self.setCurrentState('DO_EXECUTE_LINE')
                self.stateDoExecuteLine()
                return
            if self.pager_state == 'WAITING':
                self.pager_state = 'PROCESS_LINES'
                self.pager(self.doc)
                return
            
        if event.GetKeyCode() in [ord('q'),ord('Q')]:
            if self.pager_state == 'WAITING':
                self.pager_state = 'DONE'
                self.stateShowPrompt()
                return
            
        #scroll_position = self.text_ctrl.GetScrollPos(wx.VERTICAL)
	if self.cur_state == 'IDLE':
            if event.KeyCode == wx.WXK_UP:
                history = self.IP.historyBack()
                self.text_ctrl.writeHistory(history)
                return
            if event.KeyCode == wx.WXK_DOWN:
                history = self.IP.historyForward()
                self.text_ctrl.writeHistory(history)
                return
            if event.KeyCode == wx.WXK_TAB:
                #if line empty we disable tab completion
                if not self.text_ctrl.getCurrentLine().strip():
                    self.text_ctrl.write('\t')
                    return
                completed, possibilities = self.IP.complete(self.text_ctrl.getCurrentLine())
                if len(possibilities) > 1:
                    cur_slice = self.text_ctrl.getCurrentLine()
                    self.text_ctrl.write('\n')
                    self.text_ctrl.writeCompletion(possibilities)
                    self.text_ctrl.write('\n')

                    self.text_ctrl.showPrompt()
                    self.text_ctrl.write(cur_slice)
                self.text_ctrl.changeLine(completed or cur_slice)
                
                return
            event.Skip()
	
    #---------------------------- Hook Section --------------------------------------------
    def updateHistoryTracker(self,command_line):
        '''
        Default history tracker (does nothing)
        '''
        pass
    
    def setHistoryTrackerHook(self,func):
        '''
        Define a new history tracker
        '''
        self.updateHistoryTracker = func
    def updateStatusTracker(self,status):
        '''
        Default status tracker (does nothing)
        '''
        pass
    
    def setStatusTrackerHook(self,func):
        '''
        Define a new status tracker
        '''
        self.updateStatusTracker = func
    

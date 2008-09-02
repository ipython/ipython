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

import re
from StringIO import StringIO

import sys
import codecs
import locale
for enc in (locale.getpreferredencoding(),
            sys.getfilesystemencoding(),
            sys.getdefaultencoding()):
    try:
        codecs.lookup(enc)
        ENCODING = enc
        break
    except LookupError:
        pass
else:
    ENCODING = 'utf-8'

from ipshell_nonblocking import NonBlockingIPShell

class WxNonBlockingIPShell(NonBlockingIPShell):
    '''
    An NonBlockingIPShell Thread that is WX dependent.
    '''
    def __init__(self, parent, 
                 argv=[],user_ns={},user_global_ns=None,
                 cin=None, cout=None, cerr=None,
                 ask_exit_handler=None):
        
        NonBlockingIPShell.__init__(self, argv, user_ns, user_global_ns,
                                    cin, cout, cerr,
                                    ask_exit_handler)

        self.parent = parent

        self.ask_exit_callback = ask_exit_handler
        self._IP.exit = self._askExit

    def addGUIShortcut(self, text, func):
        wx.CallAfter(self.parent.add_button_handler, 
                button_info={   'text':text, 
                                'func':self.parent.doExecuteLine(func)})

    def _askExit(self):
        wx.CallAfter(self.ask_exit_callback, ())

    def _afterExecute(self):
        wx.CallAfter(self.parent.evtStateExecuteDone, ())

                
class WxConsoleView(stc.StyledTextCtrl):
    '''
    Specialized styled text control view for console-like workflow.
    We use here a scintilla frontend thus it can be reused in any GUI that 
    supports scintilla with less work.

    @cvar ANSI_COLORS_BLACK: Mapping of terminal colors to X11 names.
                    (with Black background)
    @type ANSI_COLORS_BLACK: dictionary

    @cvar ANSI_COLORS_WHITE: Mapping of terminal colors to X11 names.
                    (with White background)
    @type ANSI_COLORS_WHITE: dictionary

    @ivar color_pat: Regex of terminal color pattern
    @type color_pat: _sre.SRE_Pattern
    '''
    ANSI_STYLES_BLACK = {'0;30': [0, 'WHITE'],            '0;31': [1, 'RED'],
                         '0;32': [2, 'GREEN'],            '0;33': [3, 'BROWN'],
                         '0;34': [4, 'BLUE'],             '0;35': [5, 'PURPLE'],
                         '0;36': [6, 'CYAN'],             '0;37': [7, 'LIGHT GREY'],
                         '1;30': [8, 'DARK GREY'],        '1;31': [9, 'RED'],
                         '1;32': [10, 'SEA GREEN'],       '1;33': [11, 'YELLOW'],
                         '1;34': [12, 'LIGHT BLUE'],      '1;35': 
                                                          [13, 'MEDIUM VIOLET RED'],
                         '1;36': [14, 'LIGHT STEEL BLUE'], '1;37': [15, 'YELLOW']}

    ANSI_STYLES_WHITE = {'0;30': [0, 'BLACK'],            '0;31': [1, 'RED'],
                         '0;32': [2, 'GREEN'],            '0;33': [3, 'BROWN'],
                         '0;34': [4, 'BLUE'],             '0;35': [5, 'PURPLE'],
                         '0;36': [6, 'CYAN'],             '0;37': [7, 'LIGHT GREY'],
                         '1;30': [8, 'DARK GREY'],        '1;31': [9, 'RED'],
                         '1;32': [10, 'SEA GREEN'],       '1;33': [11, 'YELLOW'],
                         '1;34': [12, 'LIGHT BLUE'],      '1;35':
                                                           [13, 'MEDIUM VIOLET RED'],
                         '1;36': [14, 'LIGHT STEEL BLUE'], '1;37': [15, 'YELLOW']}

    def __init__(self, parent, prompt, intro="", background_color="BLACK",
                 pos=wx.DefaultPosition, ID = -1, size=wx.DefaultSize,
                 style=0, autocomplete_mode = 'IPYTHON'):
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
        @param autocomplete_mode: Can be 'IPYTHON' or 'STC'
            'IPYTHON' show autocompletion the ipython way
            'STC" show it scintilla text control way
        '''
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        ####### Scintilla configuration ###################################
        
        # Ctrl + B or Ctrl + N can be used to zoomin/zoomout the text inside 
        # the widget
        self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

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
        self.SetUndoCollection(False)
        self.SetUseTabs(True)
        self.SetIndent(4)
        self.SetTabWidth(4)

        self.EnsureCaretVisible()
        
        self.SetMargins(3, 3) #text is moved away from border with 3px
        # Suppressing Scintilla margins
        self.SetMarginWidth(0, 0)
        self.SetMarginWidth(1, 0)
        self.SetMarginWidth(2, 0)

        self.background_color = background_color
        self.buildStyles()
        
        self.indent = 0
        self.prompt_count = 0
        self.color_pat = re.compile('\x01?\x1b\[(.*?)m\x02?')
        
        self.write(intro)
        self.setPrompt(prompt)
        self.showPrompt()

        self.autocomplete_mode = autocomplete_mode
        
        self.Bind(wx.EVT_KEY_DOWN, self._onKeypress)
        
    def buildStyles(self):
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

        # make some styles
        if self.background_color != "BLACK":
            self.background_color = "WHITE"
            self.SetCaretForeground("BLACK")
            self.ANSI_STYLES = self.ANSI_STYLES_WHITE
        else:
            self.SetCaretForeground("WHITE")
            self.ANSI_STYLES = self.ANSI_STYLES_BLACK

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 
                          "fore:%s,back:%s,size:%d,face:%s" 
                                    % (self.ANSI_STYLES['0;30'][1],
                          self.background_color,
                          faces['size'], faces['mono']))
        self.StyleClearAll()
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  
                          "fore:#FF0000,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
                          "fore:#000000,back:#FF0000,bold")

        for style in self.ANSI_STYLES.values():
            self.StyleSetSpec(style[0], "bold,fore:%s" % style[1])
        
        #######################################################################
        
    def setBackgroundColor(self, color):
        self.background_color = color
        self.buildStyles()

    def getBackgroundColor(self, color):
        return self.background_color
        
    def asyncWrite(self, text):
        '''
        Write given text to buffer in an asynchroneous way.
        It is used from another thread to be able to acces the GUI.
        @param text: Text to append
        @type text: string
        '''
        try:
            #print >>sys.__stdout__,'entering'
            wx.MutexGuiEnter()
            #print >>sys.__stdout__,'locking the GUI'
                
            #be sure not to be interrutpted before the MutexGuiLeave!
            self.write(text)
                
            #print >>sys.__stdout__,'done'
                
        except KeyboardInterrupt:
            #print >>sys.__stdout__,'got keyboard interrupt'
            wx.MutexGuiLeave()
            #print >>sys.__stdout__,'interrupt unlock the GUI'
            raise KeyboardInterrupt
        wx.MutexGuiLeave()
        #print >>sys.__stdout__,'normal unlock the GUI'
        
                
    def write(self, text):
        '''
        Write given text to buffer.

        @param text: Text to append.
        @type text: string
        '''
        segments = self.color_pat.split(text)
        segment = segments.pop(0)
        self.StartStyling(self.getCurrentLineEnd(), 0xFF)
        self.AppendText(segment)
        
        if segments:
            ansi_tags = self.color_pat.findall(text)

            for tag in ansi_tags:
                i = segments.index(tag)
                self.StartStyling(self.getCurrentLineEnd(), 0xFF)
                self.AppendText(segments[i+1])

                if tag != '0':
                    self.SetStyling(len(segments[i+1]), self.ANSI_STYLES[tag][0])

                segments.pop(i)
                
        self.moveCursor(self.getCurrentLineEnd())
         
    def getPromptLen(self):
        '''
        Return the length of current prompt
        '''
        return len(str(self.prompt_count)) + 7

    def setPrompt(self, prompt):
        self.prompt = prompt

    def setIndentation(self, indentation):
        self.indent = indentation
        
    def setPromptCount(self, count):
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
        self.SetSelection(self.getCurrentPromptStart(), self.getCurrentLineEnd())
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

    def moveCursorOnNewValidKey(self):
        #If cursor is at wrong position put it at last line...
        if self.GetCurrentPos() < self.getCurrentPromptStart():
            self.GotoPos(self.getCurrentPromptStart())
        
    def removeFromTo(self, from_pos, to_pos):
        if from_pos < to_pos:
            self.SetSelection(from_pos, to_pos)
            self.DeleteBack()
                                                          
    def removeCurrentLine(self):
        self.LineDelete()
        
    def moveCursor(self, position):
        self.GotoPos(position)

    def getCursorPos(self):
        return self.GetCurrentPos()

    def selectFromTo(self, from_pos, to_pos):
        self.SetSelectionStart(from_pos)
        self.SetSelectionEnd(to_pos)
        
    def writeHistory(self, history):
        self.removeFromTo(self.getCurrentPromptStart(), self.getCurrentLineEnd())
        self.changeLine(history)

    def setCompletionMethod(self, completion):
        if completion in ['IPYTHON', 'STC']:
            self.autocomplete_mode = completion
        else:
            raise AttributeError

    def getCompletionMethod(self, completion):
        return self.autocomplete_mode
        
    def writeCompletion(self, possibilities):
        if self.autocomplete_mode == 'IPYTHON':
            max_len = len(max(possibilities, key=len))
            max_symbol = ' '*max_len
            
            #now we check how much symbol we can put on a line...
            test_buffer = max_symbol + ' '*4
            
            allowed_symbols = 80/len(test_buffer)
            if allowed_symbols == 0:
                allowed_symbols = 1
            
            pos = 1
            buf = ''
            for symbol in possibilities:
                #buf += symbol+'\n'#*spaces)
                if pos < allowed_symbols:
                    spaces = max_len - len(symbol) + 4
                    buf += symbol+' '*spaces
                    pos += 1
                else:
                    buf += symbol+'\n'
                    pos = 1
            self.write(buf)
        else:
            possibilities.sort()  # Python sorts are case sensitive
            self.AutoCompSetIgnoreCase(False)
            self.AutoCompSetAutoHide(False)
            #let compute the length ot last word
            splitter = [' ', '(', '[', '{']
            last_word = self.getCurrentLine()
            for breaker in splitter:
                last_word = last_word.split(breaker)[-1]
            self.AutoCompShow(len(last_word), " ".join(possibilities))
        
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

        if not self.AutoCompActive():
            if event.GetKeyCode() == wx.WXK_HOME:
                if event.Modifiers == wx.MOD_NONE:
                    self.moveCursorOnNewValidKey()
                    self.moveCursor(self.getCurrentPromptStart())
                    return True
                elif event.Modifiers == wx.MOD_SHIFT:
                    self.moveCursorOnNewValidKey()
                    self.selectFromTo(self.getCurrentPromptStart(), self.getCursorPos())
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
                    event.Skip()
                return True
            
            if skip:
                if event.GetKeyCode() not in [wx.WXK_PAGEUP, wx.WXK_PAGEDOWN]\
                and event.Modifiers == wx.MOD_NONE:
                    self.moveCursorOnNewValidKey()
                    
                event.Skip()
                return True
            return False
        else:
            event.Skip()
            
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
        
class IPShellWidget(wx.Panel):
    '''
    This is wx.Panel that embbed the IPython Thread and the wx.StyledTextControl
    If you want to port this to any other GUI toolkit, just replace the 
    WxConsoleView by YOURGUIConsoleView and make YOURGUIIPythonView derivate 
    from whatever container you want. I've choosed to derivate from a wx.Panel 
    because it seems to be more useful
    Any idea to make it more 'generic' welcomed.
    '''

    def __init__(self, parent, intro=None,
                 background_color="BLACK", add_button_handler=None, 
                 wx_ip_shell=None, user_ns={},user_global_ns=None,
                 ):
        '''
        Initialize.
        Instanciate an IPython thread.
        Instanciate a WxConsoleView.
        Redirect I/O to console.
        '''
        wx.Panel.__init__(self,parent,wx.ID_ANY)

        self.parent = parent
        ### IPython non blocking shell instanciation ###
        self.cout = StringIO()
        self.add_button_handler = add_button_handler

        if wx_ip_shell is not None:
            self.IP = wx_ip_shell
        else:
            self.IP = WxNonBlockingIPShell(self,
                                    cout = self.cout, cerr = self.cout,
                                    ask_exit_handler = self.askExitCallback)

        ### IPython wx console view instanciation ###
        #If user didn't defined an intro text, we create one for him
        #If you really wnat an empty intro just call wxIPythonViewPanel 
        #with intro=''
        if intro is None:
            welcome_text = "Welcome to WxIPython Shell.\n\n"
            welcome_text+= self.IP.getBanner()
            welcome_text+= "!command  -> Execute command in shell\n"
            welcome_text+= "TAB       -> Autocompletion\n"
        else:
            welcome_text = intro

        self.text_ctrl = WxConsoleView(self,
                                       self.IP.getPrompt(),
                                       intro=welcome_text,
                                       background_color=background_color)

        self.cout.write = self.text_ctrl.asyncWrite

        option_text = wx.StaticText(self, -1, "Options:")
        self.completion_option = wx.CheckBox(self, -1, "Scintilla Completion")
        #self.completion_option.SetValue(False)
        self.background_option = wx.CheckBox(self, -1, "White Background")
        #self.background_option.SetValue(False)
        
        self.options={'completion':{'value':'IPYTHON',
                                    'checkbox':self.completion_option,'STC':True,'IPYTHON':False,
                                    'setfunc':self.text_ctrl.setCompletionMethod},
                      'background_color':{'value':'BLACK',
                                          'checkbox':self.background_option,'WHITE':True,'BLACK':False,
                                          'setfunc':self.text_ctrl.setBackgroundColor},
                     }
        self.reloadOptions(self.options)
        
        self.text_ctrl.Bind(wx.EVT_KEY_DOWN, self.keyPress)
        self.completion_option.Bind(wx.EVT_CHECKBOX, self.evtCheckOptionCompletion)
        self.background_option.Bind(wx.EVT_CHECKBOX, self.evtCheckOptionBackgroundColor)
            
        ### making the layout of the panel ###
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        option_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(option_sizer, 0)
        option_sizer.AddMany([(10, 20),
                              (option_text, 0, wx.ALIGN_CENTER_VERTICAL),
                              (5, 5),
                              (self.completion_option, 0, wx.ALIGN_CENTER_VERTICAL),
                              (8, 8),
                              (self.background_option, 0, wx.ALIGN_CENTER_VERTICAL)
                              ])
        self.SetAutoLayout(True)
        sizer.Fit(self)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        #and we focus on the widget :)
        self.SetFocus()

        #widget state management (for key handling different cases)
        self.setCurrentState('IDLE')
        self.pager_state = 'DONE'
        self.raw_input_current_line = 0

    def askExitCallback(self, event):
        self.askExitHandler(event)
        
    #---------------------- IPython Thread Management ------------------------
    def stateDoExecuteLine(self):
        lines=self.text_ctrl.getCurrentLine()
        self.text_ctrl.write('\n')
        lines_to_execute = lines.replace('\t',' '*4)
        lines_to_execute = lines_to_execute.replace('\r','')
        self.IP.doExecute(lines_to_execute.encode(ENCODING))
        self.updateHistoryTracker(lines)
        self.setCurrentState('WAIT_END_OF_EXECUTION')
        
    def evtStateExecuteDone(self,evt):
        self.doc = self.IP.getDocText()
        self.help = self.IP.getHelpText()
        if self.doc:
            self.pager_lines = self.doc[7:].split('\n')
            self.pager_state = 'INIT'
            self.setCurrentState('SHOW_DOC')
            self.pager(self.doc)
        elif self.help:
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
        self.text_ctrl.showPrompt()
        self.IP.initHistoryIndex()
        self.setCurrentState('IDLE')

    def setCurrentState(self, state):
        self.cur_state = state
        self.updateStatusTracker(self.cur_state)

    def pager(self,text):

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
            
    #------------------------ Key Handler ------------------------------------
    def keyPress(self, event):
        '''
        Key press callback with plenty of shell goodness, like history,
        autocompletions, etc.
        '''
        if event.GetKeyCode() == ord('C'):
            if event.Modifiers == wx.MOD_CONTROL or event.Modifiers == wx.MOD_ALT:
                if self.cur_state == 'WAIT_END_OF_EXECUTION':
                    #we raise an exception inside the IPython thread container
                    self.IP.ce.raise_exc(KeyboardInterrupt)
                    return
                
        #let this before 'wx.WXK_RETURN' because we have to put 'IDLE'
        #mode if AutoComp has been set as inactive
        if self.cur_state == 'COMPLETING':
            if not self.text_ctrl.AutoCompActive():
                self.cur_state = 'IDLE'
            else:
                event.Skip()

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
            
            if self.cur_state == 'WAITING_USER_INPUT':
                line=self.text_ctrl.getCurrentLine()
                self.text_ctrl.write('\n')
                self.setCurrentState('WAIT_END_OF_EXECUTION')
                return
          
        if event.GetKeyCode() in [ord('q'),ord('Q')]:
            if self.pager_state == 'WAITING':
                self.pager_state = 'DONE'
                self.text_ctrl.write('\n')
                self.stateShowPrompt()
                return

        if self.cur_state == 'WAITING_USER_INPUT':
            event.Skip()   
            
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
                    if self.text_ctrl.autocomplete_mode == 'IPYTHON':    
                        cur_slice = self.text_ctrl.getCurrentLine()
                        self.text_ctrl.write('\n')
                        self.text_ctrl.writeCompletion(possibilities)
                        self.text_ctrl.write('\n')

                        self.text_ctrl.showPrompt()
                        self.text_ctrl.write(cur_slice)
                        self.text_ctrl.changeLine(completed or cur_slice)
                    else:
                        self.cur_state = 'COMPLETING'
                        self.text_ctrl.writeCompletion(possibilities)
                else:
                    self.text_ctrl.changeLine(completed or cur_slice)
                return
            event.Skip()

    #------------------------ Option Section ---------------------------------
    def evtCheckOptionCompletion(self, event):
        if event.IsChecked():
            self.options['completion']['value']='STC'
        else:
            self.options['completion']['value']='IPYTHON'
        self.text_ctrl.setCompletionMethod(self.options['completion']['value'])
        self.updateOptionTracker('completion',
                                 self.options['completion']['value'])
        self.text_ctrl.SetFocus()

    def evtCheckOptionBackgroundColor(self, event):
        if event.IsChecked():
            self.options['background_color']['value']='WHITE'
        else:
            self.options['background_color']['value']='BLACK'
        self.text_ctrl.setBackgroundColor(self.options['background_color']['value'])
        self.updateOptionTracker('background_color',
                                 self.options['background_color']['value'])
        self.text_ctrl.SetFocus()
    
    def getOptions(self):
        return self.options
        
    def reloadOptions(self,options):
        self.options = options
        for key in self.options.keys():
            value = self.options[key]['value']
            self.options[key]['checkbox'].SetValue(self.options[key][value])
            self.options[key]['setfunc'](value)
        
        
    #------------------------ Hook Section -----------------------------------
    def updateOptionTracker(self,name,value):
        '''
        Default history tracker (does nothing)
        '''
        pass
    
    def setOptionTrackerHook(self,func):
        '''
        Define a new history tracker
        '''
        self.updateOptionTracker = func

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

    def askExitHandler(self, event):
        '''
        Default exit handler
        '''
        self.text_ctrl.write('\nExit callback has not been set.')

    def setAskExitHandler(self, func):
        '''
        Define an exit handler
        '''
        self.askExitHandler = func

if __name__ == '__main__':
    # Some simple code to test the shell widget.
    class MainWindow(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title, size=(300,250))
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.shell = IPShellWidget(self)
            self._sizer.Add(self.shell, 1, wx.EXPAND)
            self.SetSizer(self._sizer)
            self.SetAutoLayout(1)
            self.Show(True)

    app = wx.PySimpleApp()
    frame = MainWindow(None, wx.ID_ANY, 'Ipython')
    frame.SetSize((780, 460))
    shell = frame.shell

    app.MainLoop()



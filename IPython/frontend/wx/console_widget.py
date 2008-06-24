# encoding: utf-8
"""
A Wx widget that deals with prompts and provides an edit buffer
restricted to after the last prompt.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is
#  in the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import wx
import wx.stc  as  stc

import re

# FIXME: Need to provide an API for non user-generated display on the
# screen: this should not be editable by the user.

#-------------------------------------------------------------------------------
# The console widget class
#-------------------------------------------------------------------------------
class ConsoleWidget(stc.StyledTextCtrl):
    """ Specialized styled text control view for console-like workflow.
        This widget is mainly interested in dealing with the prompt and
        keeping the cursor inside the editing line.
    """

    # Translation table from ANSI escape sequences to color. Override
    # this to specify your colors.
    ANSI_STYLES = {'0;30': [0, 'BLACK'],            '0;31': [1, 'RED'],
                   '0;32': [2, 'GREEN'],            '0;33': [3, 'BROWN'],
                   '0;34': [4, 'BLUE'],             '0;35': [5, 'PURPLE'],
                   '0;36': [6, 'CYAN'],             '0;37': [7, 'LIGHT GREY'],
                   '1;30': [8, 'DARK GREY'],        '1;31': [9, 'RED'],
                   '1;32': [10, 'SEA GREEN'],       '1;33': [11, 'YELLOW'],
                   '1;34': [12, 'LIGHT BLUE'],      '1;35':
                                                     [13, 'MEDIUM VIOLET RED'],
                   '1;36': [14, 'LIGHT STEEL BLUE'], '1;37': [15, 'YELLOW']}

    # The color of the carret (call _apply_style() after setting)
    carret_color = 'BLACK'
    
    
    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
    
    def write(self, text):
        """ Write given text to buffer, while translating the ansi escape
            sequences.
        """
        segments = self.color_pat.split(text)
        segment = segments.pop(0)
        self.StartStyling(self.GetLength(), 0xFF)
        self.AppendText(segment)
                
        if segments:
            ansi_tags = self.color_pat.findall(text)

            for tag in ansi_tags:
                i = segments.index(tag)
                self.StartStyling(self.GetLength(), 0xFF)
                self.AppendText(segments[i+1])

                if tag != '0':
                    self.SetStyling(len(segments[i+1]), 
                                            self.ANSI_STYLES[tag][0])

                segments.pop(i)
                
        self.GotoPos(self.GetLength())
    
    
    def new_prompt(self, prompt):
        """ Prints a prompt at start of line, and move the start of the
            current block there.

            The prompt can be give with ascii escape sequences.
        """
        self.write(prompt)
        # now we update our cursor giving end of prompt
        self.current_prompt_pos = self.GetLength()
        self.current_prompt_line = self.GetCurrentLine()
        
        autoindent = self.indent * ' '
        autoindent = autoindent.replace('    ','\t')
        self.write(autoindent)

        
    def replace_current_edit_buffer(self, text):
        """ Replace currently entered command line with given text.
        """
        self.SetSelection(self.current_prompt_pos, self.GetLength())
        self.ReplaceSelection(text)
        self.GotoPos(self.GetLength())
    
    
    def get_current_edit_buffer(self):
        """ Returns the text in current edit buffer.
        """
        return self.GetTextRange(self.current_prompt_pos,
                                 self.GetLength())


    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
    
    def __init__(self, parent, pos=wx.DefaultPosition, ID=-1, 
                        size=wx.DefaultSize, style=0, 
                        autocomplete_mode='IPYTHON'):
        """ Autocomplete_mode: Can be 'IPYTHON' or 'STC'
            'IPYTHON' show autocompletion the ipython way
            'STC" show it scintilla text control way
        """
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        #------ Scintilla configuration -----------------------------------
        
        # Ctrl"+" or Ctrl "-" can be used to zoomin/zoomout the text inside 
        # the widget
        self.CmdKeyAssign(ord('+'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('-'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)
        # Also allow Ctrl Shift "=" for poor non US keyboard users. 
        self.CmdKeyAssign(ord('='), stc.STC_SCMOD_CTRL|stc.STC_SCMOD_SHIFT, 
                                            stc.STC_CMD_ZOOMIN)

        self.SetEOLMode(stc.STC_EOL_CRLF)
        self.SetWrapMode(stc.STC_WRAP_CHAR)
        self.SetWrapMode(stc.STC_WRAP_WORD)
        self.SetBufferedDraw(True)
        self.SetUseAntiAliasing(True)
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

        self._apply_style()
        
        self.indent = 0
        self.color_pat = re.compile('\x01?\x1b\[(.*?)m\x02?')
        
        # FIXME: we need to retrieve this from the interpreter.
        self.prompt = \
            '\n\x01\x1b[0;34m\x02In [\x01\x1b[1;34m\x026\x01\x1b[0;34m\x02]: \x01\x1b[0m\x02'
        self.new_prompt(self.prompt)

        self.autocomplete_mode = autocomplete_mode
        
        self.Bind(wx.EVT_KEY_DOWN, self._onKeypress)
    
    
    def _apply_style(self):
        """ Applies the colors for the different text elements and the
            carret.
        """
        # FIXME: We need to do something for the fonts, but this is
        # clearly not the right option.
        #we define platform specific fonts
#        if wx.Platform == '__WXMSW__':
#            faces = { 'times': 'Times New Roman',
#                      'mono' : 'Courier New',
#                      'helv' : 'Arial',
#                      'other': 'Comic Sans MS',
#                      'size' : 10,
#                      'size2': 8,
#                     }
#        elif wx.Platform == '__WXMAC__':
#            faces = { 'times': 'Times New Roman',
#                      'mono' : 'Monaco',
#                      'helv' : 'Arial',
#                      'other': 'Comic Sans MS',
#                      'size' : 10,
#                      'size2': 8,
#                     }
#        else:
#            faces = { 'times': 'Times',
#                      'mono' : 'Courier',
#                      'helv' : 'Helvetica',
#                      'other': 'new century schoolbook',
#                      'size' : 10,
#                      'size2': 8,
#                     }
#        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 
#                          "fore:%s,back:%s,size:%d,face:%s" 
#                                    % (self.ANSI_STYLES['0;30'][1],
#                          self.background_color,
#                          faces['size'], faces['mono']))

        self.SetCaretForeground(self.carret_color)

        self.StyleClearAll()
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  
                          "fore:#FF0000,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
                          "fore:#000000,back:#FF0000,bold")

        for style in self.ANSI_STYLES.values():
            self.StyleSetSpec(style[0], "bold,fore:%s" % style[1])


     def removeFromTo(self, from_pos, to_pos):
        if from_pos < to_pos:
            self.SetSelection(from_pos, to_pos)
            self.DeleteBack()


    def selectFromTo(self, from_pos, to_pos):
        self.SetSelectionStart(from_pos)
        self.SetSelectionEnd(to_pos)
    
    
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
            last_word = self.get_current_edit_buffer()
            for breaker in splitter:
                last_word = last_word.split(breaker)[-1]
            self.AutoCompShow(len(last_word), " ".join(possibilities))


    def _onKeypress(self, event, skip=True):
        """ Key press callback used for correcting behavior for 
            console-like interfaces: the cursor is constraint to be after
            the last prompt.

            Return True if event as been catched.
        """
        catched = False
        if self.AutoCompActive():
            event.Skip()
        else:
            if event.GetKeyCode() == wx.WXK_HOME:
                if event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN):
                    self.GotoPos(self.current_prompt_pos)
                    catched = True

                elif event.Modifiers == wx.MOD_SHIFT:
                    self.selectFromTo(self.current_prompt_pos, 
                                                        self.GetCurrentPos())
                    catched = True

            elif event.GetKeyCode() == wx.WXK_UP:
                if self.GetCurrentLine() > self.current_prompt_line:
                    if self.GetCurrentLine() == self.current_prompt_line + 1 \
                            and self.GetColumn(self.GetCurrentPos()) < \
                                self.GetColumn(self.current_prompt_pos):
                        self.GotoPos(self.current_prompt_pos)
                    else:
                        event.Skip()
                catched = True

            elif event.GetKeyCode() in (wx.WXK_LEFT, wx.WXK_BACK):
                if self.GetCurrentPos() > self.current_prompt_pos:
                    event.Skip()
                catched = True

            if skip and not catched:
                event.Skip()

            if event.GetKeyCode() not in (wx.WXK_PAGEUP, wx.WXK_PAGEDOWN)\
                    and event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN,
                                                            wx.MOD_SHIFT):
                # If cursor is outside the editing region, put it back.
                if self.GetCurrentPos() < self.current_prompt_pos:
                    self.GotoPos(self.current_prompt_pos)

        return catched


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


if __name__ == '__main__':
    # Some simple code to test the console widget.
    class MainWindow(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title, size=(300,250))
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.console_widget = ConsoleWidget(self)
            self._sizer.Add(self.console_widget, 1, wx.EXPAND)
            self.SetSizer(self._sizer)
            self.SetAutoLayout(1)
            self.Show(True)

    app = wx.PySimpleApp()
    w = MainWindow(None, wx.ID_ANY, 'ConsoleWidget')
    w.SetSize((780, 460))
    w.Show()

    app.MainLoop()



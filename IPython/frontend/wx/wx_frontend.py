# encoding: utf-8 -*- test-case-name:
# FIXME: Need to add tests.
# ipython1.frontend.cocoa.tests.test_cocoa_frontend -*-

"""Classes to provide a Wx frontend to the
IPython.kernel.core.interpreter.

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
import re
from wx import stc
from console_widget import ConsoleWidget

from IPython.frontend.prefilterfrontend import PrefilterFrontEnd

#_COMMAND_BG = '#FAFAF1' # Nice green
_RUNNING_BUFFER_BG = '#FDFFBE' # Nice yellow

_RUNNING_BUFFER_MARKER = 31


#-------------------------------------------------------------------------------
# Classes to implement the Wx frontend
#-------------------------------------------------------------------------------
class IPythonWxController(PrefilterFrontEnd, ConsoleWidget):

    output_prompt = \
    '\x01\x1b[0;31m\x02Out[\x01\x1b[1;31m\x02%i\x01\x1b[0;31m\x02]: \x01\x1b[0m\x02'
  
    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
 
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 *args, **kwds):
        """ Create Shell instance.
        """
        ConsoleWidget.__init__(self, parent, id, pos, size, style)
        PrefilterFrontEnd.__init__(self)

        # Capture Character keys
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

        # Marker for running buffer.
        self.MarkerDefine(_RUNNING_BUFFER_MARKER, stc.STC_MARK_BACKGROUND,
                                background=_RUNNING_BUFFER_BG)



    def do_completion(self, mode=None):
        """ Do code completion. 
            mode can be 'text', 'popup' or 'none' to use default.
        """
        line = self.get_current_edit_buffer()
        completions = self.complete(line)
        if len(completions)>0:
            self.write_completion(completions, mode=mode)


    def update_completion(self):
        line = self.get_current_edit_buffer()
        if self.AutoCompActive() and not line[-1] == '.':
            line = line[:-1]
            completions = self.complete(line)
            choose_single = self.AutoCompGetChooseSingle()
            self.AutoCompSetChooseSingle(False)
            self.write_completion(completions, mode='popup')
            self.AutoCompSetChooseSingle(choose_single)


    def execute(self, python_string, raw_string=None):
        self._cursor = wx.BusyCursor()
        if raw_string is None:
            raw_string = python_string
        end_line = self.current_prompt_line \
                        + max(1,  len(raw_string.split('\n'))-1)
        for i in range(self.current_prompt_line, end_line):
            self.MarkerAdd(i, 31)
        PrefilterFrontEnd.execute(self, python_string, raw_string=raw_string)


    def after_execute(self):
        PrefilterFrontEnd.after_execute(self)
        if hasattr(self, '_cursor'):
            del self._cursor

    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 

    def _on_key_down(self, event, skip=True):
        """ Capture the character events, let the parent
            widget handle them, and put our logic afterward.
        """
        current_line_number = self.GetCurrentLine()
        if self.AutoCompActive():
            event.Skip()
            if event.KeyCode in (wx.WXK_BACK, wx.WXK_DELETE): 
                wx.CallAfter(self.do_completion)
            elif not event.KeyCode in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT,
                            wx.WXK_RIGHT):
                wx.CallAfter(self.update_completion)
        else:
            # Up history
            if event.KeyCode == wx.WXK_UP and (
                    ( current_line_number == self.current_prompt_line and
                        event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                    or event.ControlDown() ):
                new_buffer = self.get_history_previous(
                                            self.get_current_edit_buffer())
                if new_buffer is not None:
                    self.replace_current_edit_buffer(new_buffer)
                    if self.GetCurrentLine() > self.current_prompt_line:
                        # Go to first line, for seemless history up.
                        self.GotoPos(self.current_prompt_pos)
            # Down history
            elif event.KeyCode == wx.WXK_DOWN and (
                    ( current_line_number == self.LineCount -1 and
                        event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                    or event.ControlDown() ):
                new_buffer = self.get_history_next()
                if new_buffer is not None:
                    self.replace_current_edit_buffer(new_buffer)
            elif event.KeyCode == ord('\t'):
                last_line = self.get_current_edit_buffer().split('\n')[-1]
                if not re.match(r'^\s*$', last_line):
                    self.do_completion(mode='text')
                else:
                    event.Skip()
            else:
                ConsoleWidget._on_key_down(self, event, skip=skip)


    def _on_key_up(self, event, skip=True):
        if event.KeyCode == 59:
            # Intercepting '.'
            event.Skip()
            #self.do_completion(mode='popup')
        else:
            ConsoleWidget._on_key_up(self, event, skip=skip)


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
    frame.shell.SetFocus()
    frame.SetSize((660, 460))
    self = frame.shell

    app.MainLoop()


# encoding: utf-8 -*- test-case-name:
# FIXME: Need to add tests.
# ipython1.frontend.cocoa.tests.test_cocoa_frontend -*-

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

from IPython.frontend.linefrontendbase import LineFrontEndBase

#-------------------------------------------------------------------------------
# Classes to implement the Wx frontend
#-------------------------------------------------------------------------------

   


class IPythonWxController(LineFrontEndBase, ConsoleWidget):

    output_prompt = \
    '\n\x01\x1b[0;31m\x02Out[\x01\x1b[1;31m\x02%i\x01\x1b[0;31m\x02]: \x01\x1b[0m\x02'
  
    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
 
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 *args, **kwds):
        """ Create Shell instance.
        """
        ConsoleWidget.__init__(self, parent, id, pos, size, style)
        LineFrontEndBase.__init__(self)

        # Capture Character keys
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
       
    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 

    def _on_key_down(self, event, skip=True):
        """ Capture the character events, let the parent
            widget handle them, and put our logic afterward.
        """
        current_line_number = self.GetCurrentLine()
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
        else:
            ConsoleWidget._on_key_down(self, event, skip=skip)


       

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


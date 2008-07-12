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
import re

import IPython
from IPython.kernel.engineservice import EngineService
from IPython.frontend.frontendbase import FrontEndBase

#-------------------------------------------------------------------------------
# Classes to implement the Wx frontend
#-------------------------------------------------------------------------------

   


class IPythonWxController(FrontEndBase, ConsoleWidget):

    output_prompt = \
    '\n\x01\x1b[0;31m\x02Out[\x01\x1b[1;31m\x02%i\x01\x1b[0;31m\x02]: \x01\x1b[0m\x02'
  
    # Are we entering multi line input?
    multi_line_input = False

    # The added tab stop to the string. It may, for instance, come from 
    # copy and pasting something with tabs.
    tab_stop = 0
    # FIXME: We still have to deal with this.

    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
 
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 *args, **kwds):
        """ Create Shell instance.
        """
        ConsoleWidget.__init__(self, parent, id, pos, size, style)
        FrontEndBase.__init__(self, engine=EngineService(),
                                    )

        # FIXME: Something is wrong with the history, I instanciate it
        # with an empty cache, but this is not the way to do.
        self.lines = {}

        # Start the IPython engine
        self.engine.startService()
        
        # Capture Character keys
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
       
        #FIXME: print banner.
        banner = """IPython1 %s -- An enhanced Interactive Python.""" \
                            % IPython.__version__
    
    
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
    
    
    def render_result(self, result):
        if 'stdout' in result and result['stdout']:
            self.write('\n' + result['stdout'])
        if 'display' in result and result['display']:
            self.write("%s%s\n" % ( 
                            self.output_prompt % result['number'],
                            result['display']['pprint']
                            ) )
    
        
    def render_error(self, failure):
        self.insert_text('\n\n'+str(failure)+'\n\n')
        return failure
    
    
    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 

    def _on_key_down(self, event, skip=True):
        """ Capture the character events, let the parent
            widget handle them, and put our logic afterward.
        """
        current_line_number = self.GetCurrentLine()
        # Capture enter
        if event.KeyCode in (13, wx.WXK_NUMPAD_ENTER) and \
                event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN):
            self._on_enter()
        # Up history
        elif event.KeyCode == wx.WXK_UP and (
                ( current_line_number == self.current_prompt_line and
                    event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                or event.ControlDown() ):
            new_buffer = self.get_history_previous(
                                        self.get_current_edit_buffer())
            if new_buffer is not None:
                self.replace_current_edit_buffer(new_buffer)
        # Down history
        elif event.KeyCode == wx.WXK_DOWN and (
                ( current_line_number == self.LineCount -1 and
                    event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                or event.ControlDown() ):
            new_buffer = self.get_history_next()
            if new_buffer is not None:
                self.replace_current_edit_buffer(new_buffer)
        else:
            ConsoleWidget._on_key_down(self, event, skip=True)


    def _on_enter(self):
        """ Called when the return key is pressed in a line editing
            buffer.
        """
        current_buffer = self.get_current_edit_buffer()
        current_buffer = current_buffer.replace('\r\n', '\n')
        current_buffer = current_buffer.replace('\t', 4*' ')
        cleaned_buffer = '\n'.join(l.rstrip() 
                        for l in current_buffer.split('\n'))
        if (    not self.multi_line_input
                or re.findall(r"\n[\t ]*$", cleaned_buffer)):
            if self.is_complete(cleaned_buffer):
                self._add_history(None, cleaned_buffer.rstrip())
                result = self.engine.shell.execute(cleaned_buffer)
                self.render_result(result)
                self.new_prompt(self.prompt % (result['number'] + 1))
                self.multi_line_input = False
            else:
                if self.multi_line_input:
                    self.write('\n' + self._get_indent_string(current_buffer))
                else:
                    self.multi_line_input = True
                    self.write('\n\t')
        else:
            self.write('\n'+self._get_indent_string(current_buffer))


    def _get_indent_string(self, string):
        string = string.split('\n')[-1]
        indent_chars = len(string) - len(string.lstrip())
        indent_string = '\t'*(indent_chars // 4) + \
                            ' '*(indent_chars % 4)

        return indent_string
 
        

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


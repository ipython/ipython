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
        FrontEndBase.__init__(self, engine=EngineService())

        self.lines = {}
        
        # Start the IPython engine
        self.engine.startService()
        
        # Capture Character keys
        self.Bind(wx.EVT_KEY_UP, self._on_key_up)
       
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
        if 'stdout' in result:
            self.write(result['stdout'])
        if 'display' in result:
            self.write(self.output_prompt % result['number']
                + result['display']['pprint'])
    
        
    def render_error(self, failure):
        self.insert_text('\n\n'+str(failure)+'\n\n')
        return failure
    
    
    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 

    def _on_key_up(self, event, skip=True):
        """ Capture the character events, let the parent
            widget handle them, and put our logic afterward.
        """
        event.Skip()
        # Capture enter
        if event.KeyCode == 13 and \
                event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN):
            self._on_enter()

    
    def _on_enter(self):
        """ Called when the return key is pressed in a line editing
            buffer.
        """
        current_buffer = self.get_current_edit_buffer()
        current_buffer = current_buffer.replace('\r\n', '\n')
        current_buffer = current_buffer.replace('\t', 4*' ')
        if (    not self.multi_line_input
                or re.findall(r"\n[\t ]*\n[\t ]*$", current_buffer)):
            if self.is_complete(current_buffer):
                result = self.engine.shell.execute(current_buffer)
                self.render_result(result)
                self.new_prompt(self.prompt % result['number'])
                self.multi_line_input = False
            else:
                if self.multi_line_input:
                    self.write(self._get_indent_string(current_buffer[:-1]))
                else:
                    self.multi_line_input = True
                    self.write('\t')
        else:
            self.write(self._get_indent_string(current_buffer[:-1]))


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
    frame.SetSize((780, 460))
    shell = frame.shell

#    app.MainLoop()


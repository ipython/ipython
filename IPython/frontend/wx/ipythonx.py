#!/usr/bin/env python
"""
Entry point for a simple application giving a graphical frontend to
ipython.
"""

import wx
from wx_frontend import WxController
import __builtin__

class IPythonXController(WxController):
    """ Sub class of WxController that adds some application-specific
        bindings.
    """

    debug = False

    def __init__(self, *args, **kwargs):
        WxController.__init__(self, *args, **kwargs)
        self.ipython0.ask_exit = self.do_exit


    def _on_key_down(self, event, skip=True):
        # Intercept Ctrl-D to quit
        if event.KeyCode == ord('D') and event.ControlDown() and \
                self.input_buffer == '' and \
                self._input_state == 'readline':
            wx.CallAfter(self.ask_exit)
        else:
            WxController._on_key_down(self, event, skip=skip) 


    def ask_exit(self):
        """ Ask the user whether to exit.
        """
        self.write('\n')
        self.capture_output()
        self.ipython0.shell.exit()
        self.release_output()
        wx.Yield()
        if not self.ipython0.exit_now:
            self.new_prompt(self.input_prompt_template.substitute(
                                number=self.last_result['number'] + 1))
 

    def do_exit(self):
        """ Exits the interpreter, kills the windows.
        """
        WxController.do_exit(self)
        self.release_output()
        wx.CallAfter(wx.Exit)



class IPythonX(wx.Frame):
    """ Main frame of the IPythonX app.
    """

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(300,250))
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.shell = IPythonXController(self)
        self._sizer.Add(self.shell, 1, wx.EXPAND)
        self.SetSizer(self._sizer)
        self.SetAutoLayout(1)
        self.Show(True)


def main():
    from optparse import OptionParser
    usage = """usage: %prog [options]

Simple graphical frontend to IPython, using WxWidgets."""
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug",
                    action="store_true", dest="debug", default=False,
                    help="Enable debug message for the wx frontend.")

    options, args = parser.parse_args()

    app = wx.PySimpleApp()
    frame = IPythonX(None, wx.ID_ANY, 'IPythonX')
    frame.shell.debug = options.debug
    frame.shell.SetFocus()
    frame.shell.app = app
    frame.SetSize((680, 460))

    app.MainLoop()

if __name__ == '__main__':
    main()

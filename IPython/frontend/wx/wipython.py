"""
Entry point for a simple application giving a graphical frontend to
ipython.
"""

import wx
from wx_frontend import WxController

class WIPythonController(WxController):
    """ Sub class of WxController that adds some application-specific
        bindings.
    """

    def __init__(self, *args, **kwargs):
        WxController.__init__(self, *args, **kwargs)
        self.ipython0.ask_exit = self.do_exit


    def _on_key_down(self, event, skip=True):
        # Intercept Ctrl-D to quit
        if event.KeyCode == ord('D') and event.ControlDown() and \
                self.get_current_edit_buffer()=='':
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
            self.new_prompt(self.prompt % (self.last_result['number'] + 1))
 

    def do_exit(self):
        """ Exits the interpreter, kills the windows.
        """
        WxController.do_exit(self)
        # Remove the callbacks, to avoid PyDeadObjectErrors
        do_nothing = lambda *args, **kwargs: True
        self.release_output()
        self._on_key_down = do_nothing
        self._on_key_up = do_nothing
        self._on_enter = do_nothing
        self.after_execute = do_nothing
        wx.Yield()
        wx.CallAfter(self.Parent.Destroy)



class WIPython(wx.Frame):
    """ Main frame of the WIPython app.
    """

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(300,250))
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.shell = WIPythonController(self)
        self._sizer.Add(self.shell, 1, wx.EXPAND)
        self.SetSizer(self._sizer)
        self.SetAutoLayout(1)
        self.Show(True)


def main():
    app = wx.PySimpleApp()
    frame = WIPython(None, wx.ID_ANY, 'WIpython')
    frame.shell.SetFocus()
    frame.shell.app = app
    frame.SetSize((680, 460))

    app.MainLoop()

if __name__ == '__main__':
    main()

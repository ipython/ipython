#!/usr/bin/env python
"""
WARNING: This example is currently broken, see
https://github.com/ipython/ipython/issues/645 for details on our progress on
this issue.

A Simple wx example to test IPython's event loop integration.

To run this do:

In [5]: %gui wx

In [6]: %run gui-wx.py

Ref: Modified from wxPython source code wxPython/samples/simple/simple.py

This example can only be run once in a given IPython session because when
the frame is closed, wx goes through its shutdown sequence, killing further
attempts.  I am sure someone who knows wx can fix this issue.

Furthermore, once this example is run, the Wx event loop is mostly dead, so
even other new uses of Wx may not work correctly.  If you know how to better
handle this, please contact the ipython developers and let us know.

Note however that we will work with the Matplotlib and Enthought developers so
that the main interactive uses of Wx we are aware of, namely these tools, will
continue to work well with IPython interactively.
"""

import wx


class MyFrame(wx.Frame):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(350, 200))

        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu
        menu = wx.Menu()

        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit this simple sample")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)

        # and put the menu on the menubar
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)

        self.CreateStatusBar()

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self)

        # and a few controls
        text = wx.StaticText(panel, -1, "Hello World!")
        text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        text.SetSize(text.GetBestSize())
        btn = wx.Button(panel, -1, "Close")
        funbtn = wx.Button(panel, -1, "Just for fun...")

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.OnTimeToClose, btn)
        self.Bind(wx.EVT_BUTTON, self.OnFunButton, funbtn)

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, 0, wx.ALL, 10)
        sizer.Add(btn, 0, wx.ALL, 10)
        sizer.Add(funbtn, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        panel.Layout()


    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
        print "See ya later!"
        self.Close()

    def OnFunButton(self, evt):
        """Event handler for the button click."""
        print "Having fun yet?"


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Simple wxPython App")
        self.SetTopWindow(frame)

        print "Print statements go to this stdout window by default."

        frame.Show(True)
        return True


if __name__ == '__main__':
    raise NotImplementedError(
        'Standalone WX GUI support is currently broken. '
        'See https://github.com/ipython/ipython/issues/645 for details')

    app = wx.GetApp()
    if app is None:
        app = MyApp(redirect=False, clearSigInt=False)

    try:
        from IPython.lib.inputhook import enable_wx
        enable_wx(app)
    except ImportError:
        app.MainLoop()


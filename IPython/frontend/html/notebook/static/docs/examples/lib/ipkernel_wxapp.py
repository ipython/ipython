#!/usr/bin/env python
"""Example integrating an IPython kernel into a GUI App.

This trivial GUI application internally starts an IPython kernel, to which Qt
consoles can be connected either by the user at the command line or started
from the GUI itself, via a button.  The GUI can also manipulate one variable in
the kernel's namespace, and print the namespace to the console.

Play with it by running the script and then opening one or more consoles, and
pushing the 'Counter++' and 'Namespace' buttons.

Upon exit, it should automatically close all consoles opened from the GUI.

Consoles attached separately from a terminal will not be terminated, though
they will notice that their kernel died.

Ref: Modified from wxPython source code wxPython/samples/simple/simple.py
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import sys

import wx

from internal_ipkernel import InternalIPKernel

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

class MyFrame(wx.Frame, InternalIPKernel):
    """
    This is MyFrame.  It just shows a few controls on a wxPanel,
    and has a simple menu.
    """

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(350, 285))

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
        qtconsole_btn = wx.Button(panel, -1, "Qt Console")
        ns_btn = wx.Button(panel, -1, "Namespace")
        count_btn = wx.Button(panel, -1, "Count++")
        close_btn = wx.Button(panel, -1, "Quit")

        # bind the button events to handlers
        self.Bind(wx.EVT_BUTTON, self.new_qt_console, qtconsole_btn)
        self.Bind(wx.EVT_BUTTON, self.print_namespace, ns_btn)
        self.Bind(wx.EVT_BUTTON, self.count, count_btn)
        self.Bind(wx.EVT_BUTTON, self.OnTimeToClose, close_btn)

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        sizer = wx.BoxSizer(wx.VERTICAL)
        for ctrl in [text, qtconsole_btn, ns_btn, count_btn, close_btn]:
            sizer.Add(ctrl, 0, wx.ALL, 10)
        panel.SetSizer(sizer)
        panel.Layout()

        # Start the IPython kernel with gui support
        self.init_ipkernel('wx')

    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
        print("See ya later!")
        sys.stdout.flush()
        self.cleanup_consoles(evt)
        self.Close()
        # Not sure why, but our IPython kernel seems to prevent normal WX
        # shutdown, so an explicit exit() call is needed.
        sys.exit()


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Simple wxPython App")
        self.SetTopWindow(frame)
        frame.Show(True)
        self.ipkernel = frame.ipkernel
        return True

#-----------------------------------------------------------------------------
# Main script
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    app = MyApp(redirect=False, clearSigInt=False)

    # Very important, IPython-specific step: this gets GUI event loop
    # integration going, and it replaces calling app.MainLoop()
    app.ipkernel.start()

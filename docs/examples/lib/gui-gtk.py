#!/usr/bin/env python
"""Simple GTK example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [5]: %gui gtk

In [6]: %run gui-gtk.py
"""


import pygtk
pygtk.require('2.0')
import gtk


def hello_world(wigdet, data=None):
    print "Hello World"

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
button = gtk.Button("Hello World")
button.connect("clicked", hello_world, None)

window.add(button)
button.show()
window.show()

try:
    from IPython.lib.inputhook import appstart_gtk
    appstart_gtk()
except ImportError:
    gtk.main()




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
    print("Hello World")

def delete_event(widget, event, data=None):
    return False

def destroy(widget, data=None):
    gtk.main_quit()

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.connect("delete_event", delete_event)
window.connect("destroy", destroy)
button = gtk.Button("Hello World")
button.connect("clicked", hello_world, None)

window.add(button)
button.show()
window.show()

try:
    from IPython.lib.inputhook import enable_gui
    enable_gui('gtk')
except ImportError:
    gtk.main()

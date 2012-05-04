#!/usr/bin/env python
"""Simple Gtk example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [1]: %gui gtk3

In [2]: %run gui-gtk3.py
"""

from gi.repository import Gtk


def hello_world(wigdet, data=None):
    print("Hello World")

def delete_event(widget, event, data=None):
    return False

def destroy(widget, data=None):
    Gtk.main_quit()

window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
window.connect("delete_event", delete_event)
window.connect("destroy", destroy)
button = Gtk.Button("Hello World")
button.connect("clicked", hello_world, None)

window.add(button)
button.show()
window.show()

try:
    from IPython.lib.inputhook import enable_gtk3
    enable_gtk3()
except ImportError:
    Gtk.main()

#!/usr/bin/env python
"""Simple Gtk example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [1]: %gui gtk4

In [2]: %run gui-gtk4.py
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa


def hello_world(wigdet, data=None):
    print("Hello World")


def close_request_cb(widget, data=None):
    global running
    running = False


running = True
window = Gtk.Window()
window.connect("close-request", close_request_cb)
button = Gtk.Button(label="Hello World")
button.connect("clicked", hello_world, None)

window.set_child(button)
window.show()

context = GLib.MainContext.default()
while running:
    context.iteration(True)

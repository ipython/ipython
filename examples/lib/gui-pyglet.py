#!/usr/bin/env python
"""Simple pyglet example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [5]: %gui pyglet

In [6]: %run gui-pyglet.py
"""

import pyglet


window = pyglet.window.Window()
label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')
@window.event
def on_close():
    window.close()

@window.event
def on_draw():
    window.clear()
    label.draw()

try:
    from IPython.lib.inputhook import enable_pyglet
    enable_pyglet()
except ImportError:
    pyglet.app.run()

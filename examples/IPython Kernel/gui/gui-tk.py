#!/usr/bin/env python
"""Simple Tk example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [5]: %gui tk

In [6]: %run gui-tk.py
"""

try:
    from tkinter import *  # Python 3
except ImportError:
    from Tkinter import *  # Python 2

class MyApp:

    def __init__(self, root):
        frame = Frame(root)
        frame.pack()

        self.button = Button(frame, text="Hello", command=self.hello_world)
        self.button.pack(side=LEFT)

    def hello_world(self):
        print("Hello World!")

root = Tk()

app = MyApp(root)

try:
    from IPython.lib.inputhook import enable_gui
    enable_gui('tk', root)
except ImportError:
    root.mainloop()

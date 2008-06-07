import IPython.ipapi
ip = IPython.ipapi.get()

import win32api
import win32ui
import win32console
import os

path = r"C:\Program Files\PSPad editor"

def synchronize_with_editor(ip, filename, lineno, columnno):
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)
    if not os.path.isfile(filename):
        print "couldn't find file:", file
        return

    h = win32console.GetConsoleWindow()
    w = win32ui.CreateWindowFromHandle(h)
    w.SetWindowText("%s %d" % (filename, lineno))

    command = r'start %s "%s" -%d ' % (win32api.GetShortPathName(os.path.join(path, "pspad.exe")), filename, lineno)
    os.system(command)

    win32api.Sleep(100)
    w.SetForegroundWindow()

ip.set_hook("synchronize_with_editor", synchronize_with_editor)

import IPython.ipapi
ip = IPython.ipapi.get()

import win32api
import win32ui
import win32console
import os

path = r"C:\Program Files\emacs\bin"

def synchronize_with_editor(ip, filename, lineno, columnno):
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)
    if not os.path.isfile(filename):
        print "couldn't find file:", file
        return

    h = win32console.GetConsoleWindow()
    w = win32ui.CreateWindowFromHandle(h)
    w.SetWindowText("%s %d" % (filename, lineno))

    command = r'%s -n +%d:%d "%s" 2>nul' % (win32api.GetShortPathName(os.path.join(path, "emacsclient.exe")), lineno, columnno, filename)
    r = os.system(command)
    if r != 0:
        command = r'start %s --quick -f server-start +%d:%d "%s"' % (win32api.GetShortPathName(os.path.join(path, "runemacs.exe")), lineno, columnno, filename)
        os.system(command)
        win32api.Sleep(500)
    else:
        win32api.Sleep(100)

    w.SetForegroundWindow()

ip.set_hook("synchronize_with_editor", synchronize_with_editor)

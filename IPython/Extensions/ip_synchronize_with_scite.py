import IPython.ipapi
ip = IPython.ipapi.get()

import win32api
import win32ui
import win32console
import os

import scitedirector

path = r"C:\Program Files\SciTE Source Code Editor"

def synchronize_with_editor(ip, filename, lineno, columnno):
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)
    if not os.path.isfile(filename):
        print "couldn't find file:", file
        return

    scites = scitedirector.findWindows()
    if not scites:
        h = win32console.GetConsoleWindow()
        w = win32ui.CreateWindowFromHandle(h)
        w.SetWindowText("%s %d" % (filename, lineno))

        command = r'start %s "-open:%s" -goto:%d' % (win32api.GetShortPathName(os.path.join(path, "scite.exe")), filename.replace("\\", "/"), lineno)
        os.system(command)

        win32api.Sleep(100)
        w.SetForegroundWindow()
    else:
        scite = scites[0]
        scitedirector.sendCommand(scite, 'open:%s' % filename.replace("\\", "/"))
        scitedirector.sendCommand(scite, "goto:%d" % lineno)

ip.set_hook("synchronize_with_editor", synchronize_with_editor)

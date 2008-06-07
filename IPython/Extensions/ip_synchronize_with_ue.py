import IPython.ipapi
ip = IPython.ipapi.get()

import win32api
import win32ui
import win32console
import dde
import os

path = r"C:\Program Files\IDM Computer Solutions\UltraEdit-32"

def synchronize_with_editor(ip, filename, lineno, columnno):
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)
    if not os.path.isfile(filename):
        print "couldn't find file:", file
        return

    h = win32console.GetConsoleWindow()
    w = win32ui.CreateWindowFromHandle(h)
    w.SetWindowText("%s %d" % (filename, lineno))

    server = dde.CreateServer()
    server.Create("myddeserver")
    conversation = dde.CreateConversation(server)
    try:
        conversation.ConnectTo("uedit32", "System")
        conversation.Exec(r'[open("%s/%d"])' % (filename, lineno))
        win32api.Sleep(10)
    except:
    	command = r'start %s "%s/%d"' % (win32api.GetShortPathName(os.path.join(path, "uedit32.exe")), filename, lineno)
        os.system(command)
        win32api.Sleep(2000)

    w.SetForegroundWindow()
    server.Shutdown()

ip.set_hook("synchronize_with_editor", synchronize_with_editor)

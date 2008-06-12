import IPython.ipapi
ip = IPython.ipapi.get()

import win32api
import win32ui
import win32console
import dde
import os
import scitedirector


def setHook(synchronize_with_editor):
    ip.set_hook("synchronize_with_editor", synchronize_with_editor)


def findFilename(filename):
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)

    if os.path.isfile(filename):
        return filename

    return ""


def restoreConsoleFocus():
    h = win32console.GetConsoleWindow()
    console_window = win32ui.CreateWindowFromHandle(h)
    console_window.SetForegroundWindow()


# This is the most simple example of hook:
class GVimHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        command = r'start %s --remote-silent +%d "%s"' % (win32api.GetShortPathName(os.path.join(self.path, "gvim.exe")), lineno, filename)
        os.system(command)

        win32api.Sleep(self.wakeup_duration)

        restoreConsoleFocus()


def gvim(path = r"C:\Program Files\vim\vim71", wakeup_duration = 100):
    synchronize_with_editor = GVimHook(path, wakeup_duration)
    setHook(synchronize_with_editor)


class EmacsHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        command = r'%s -n +%d:%d "%s" 2>nul' % (win32api.GetShortPathName(os.path.join(self.path, "emacsclient.exe")), lineno, columnno, filename)
        r = os.system(command)
        if r != 0:
            command = r'start %s --quick -f server-start +%d:%d "%s"' % (win32api.GetShortPathName(os.path.join(self.path, "runemacs.exe")), lineno, columnno, filename)
            os.system(command)
            win32api.Sleep(self.start_duration)
        else:
            win32api.Sleep(self.wakeup_duration)

        restoreConsoleFocus()


def emacs(path = r"C:\Program Files\emacs\bin", wakeup_duration = 100, start_duration = 2000):
    synchronize_with_editor = EmacsHook(path, wakeup_duration, start_duration)
    setHook(synchronize_with_editor)


class SciteHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        scites = scitedirector.findWindows()
        if not scites:
            command = r'start %s "-open:%s" -goto:%d' % (win32api.GetShortPathName(os.path.join(self.path, "scite.exe")), filename.replace("\\", "/"), lineno)
            os.system(command)

            win32api.Sleep(self.start_duration)
            restoreConsoleFocus()
        else:
            scite = scites[0]
            scitedirector.sendCommand(scite, 'open:%s' % filename.replace("\\", "/"))
            scitedirector.sendCommand(scite, "goto:%d" % lineno)


def scite(path = r"C:\Program Files\SciTE Source Code Editor", wakeup_duration = 100, start_duration = 500):
    synchronize_with_editor = SciteHook(path, wakeup_duration, start_duration)
    setHook(synchronize_with_editor)


class NodePadPlusPlusHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        command = r'start %s "%s" -n%d' % (win32api.GetShortPathName(os.path.join(self.path, "notepad++.exe")), filename, lineno)
        os.system(command)

        win32api.Sleep(self.wakeup_duration)

        restoreConsoleFocus()


def notepadplusplus(path = r"C:\Program Files\Notepad++", wakeup_duration = 100):
    synchronize_with_editor = NodePadPlusPlusHook(path, wakeup_duration)
    setHook(synchronize_with_editor)


class PsPadHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        command = r'start %s "%s" -%d ' % (win32api.GetShortPathName(os.path.join(self.path, "pspad.exe")), filename, lineno)
        os.system(command)

        win32api.Sleep(self.wakeup_duration)

        restoreConsoleFocus()


def pspad(path = r"C:\Program Files\PSPad editor", wakeup_duration = 100):
    synchronize_with_editor = PsPadHook(path, wakeup_duration)
    setHook(synchronize_with_editor)


# This is an example of DDE hook:
class UltraEditHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = findFilename(filename)

        if not filename:
            return

        server = dde.CreateServer()
        server.Create("myddeserver")
        conversation = dde.CreateConversation(server)
        try:
            conversation.ConnectTo("uedit32", "System")
            conversation.Exec(r'[open("%s/%d"])' % (filename, lineno))
            win32api.Sleep(self.wakeup_duration)
        except:
            command = r'start %s "%s/%d"' % (win32api.GetShortPathName(os.path.join(self.path, "uedit32.exe")), filename, lineno)
            os.system(command)
            win32api.Sleep(self.start_duration)

        server.Shutdown()

        restoreConsoleFocus()


def ultraedit(path = r"C:\Program Files\IDM Computer Solutions\UltraEdit-32", wakeup_duration = 10, start_duration = 2000):
    synchronize_with_editor = UltraEditHook(path, wakeup_duration, start_duration)
    setHook(synchronize_with_editor)
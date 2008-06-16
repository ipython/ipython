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


def runCommand(path, command, arguments, asynchronous = True):
    line = ''
    if asynchronous:
        line += 'start '
        
    try:
        line += win32api.GetShortPathName(os.path.join(path, command) + ".exe") + " "
    except:
        print 'could not find: "%s"' % (os.path.join(path, command) + ".exe")
        return -1
        
    line += arguments
    r = os.system(line)
    return r


def sleep(milliseconds):
    win32api.Sleep(milliseconds)


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

        runCommand(self.path, 'gvim', '--remote-silent +%d "%s"' % (lineno, filename))

        sleep(self.wakeup_duration)

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

        r = runCommand(self.path, "emacsclient", '-n +%d:%d "%s" 2>nul' % (lineno, columnno, filename), False)
        if r != 0:
            runCommand(self.path, 'runemacs', '--quick -f server-start +%d:%d "%s"' % (lineno, columnno, filename))
            sleep(self.start_duration)
        else:
            sleep(self.wakeup_duration)

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
            runCommand(self.path, "scite", '"-open:%s" -goto:%d' % (filename.replace("\\", "/"), lineno))

            sleep(self.start_duration)
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

        runCommand(self.path, "notepad++", '"%s" -n%d' % (filename, lineno))

        sleep(self.wakeup_duration)

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

        runCommand(self.path, "pspad", '"%s" -%d' % (filename, lineno))

        sleep(self.wakeup_duration)

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
            
            sleep(self.wakeup_duration)
        except:
            runCommand(self.path, 'uedit32', '"%s/%d"' % (filename, lineno))
            
            sleep(self.start_duration)

        server.Shutdown()

        restoreConsoleFocus()


def ultraedit(path = r"C:\Program Files\IDM Computer Solutions\UltraEdit-32", wakeup_duration = 10, start_duration = 2000):
    synchronize_with_editor = UltraEditHook(path, wakeup_duration, start_duration)
    setHook(synchronize_with_editor)
    
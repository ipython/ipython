from IPython.core import ipapi
ip = ipapi.get()

import win32api
import win32ui
import win32console
import dde
import os
import scitedirector

# test to write.

def set_hook(synchronize_with_editor):
    """Set the synchronize with editor hook with a callable object.
    
    The callable object will be called with the following arguments when
    IPython wants to synchronize with you favorite editor:
    
     - ip: a running IPython instance.
     
     - filename: the path of the file the editor is supposed to display.
     
     - lineno : the line number of the line the editor is supposed to
     highlight.
     
     - columnno : the column number of the character the editor is supposed
     to highlight.
    """
    ip.set_hook("synchronize_with_editor", synchronize_with_editor)


def find_filename(filename):
    """Return the filename to synchronize with based on """
    filename = os.path.splitext(filename)
    if filename[1] == ".pyc":
        filename = (filename[0], ".py")
    filename = "".join(filename)

    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwdu(), filename)

    if os.path.isfile(filename):
        return filename

    return ""


def run_command(path, command, arguments, asynchronous = True):
    """Run a shell command and return the exit code of the command"""
    # This is a thin wrapper around os.system that:
    #  - Let you run command asynchronously.
    #  - Accept spaces in command path.
    #  - Dont throw exception if the command don't exist.
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
    """Wait some milliseconds."""
    # This is used to make sure the editor did its job before we reset the focus on the console.
    win32api.Sleep(milliseconds)


def restore_console_focus():
    """Restore the focus to the IPython console."""
    h = win32console.GetConsoleWindow()
    console_window = win32ui.CreateWindowFromHandle(h)
    console_window.SetForegroundWindow()
    

# This is the most simple example of hook:
class GVimHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

        if not filename:
            return

        run_command(self.path, 'gvim', '--remote-silent +%d "%s"' % (lineno, filename))

        sleep(self.wakeup_duration)

        restore_console_focus()


def gvim(path = r"C:\Program Files\vim\vim71", wakeup_duration = 100):
    synchronize_with_editor = GVimHook(path, wakeup_duration)
    set_hook(synchronize_with_editor)


class EmacsHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

        if not filename:
            return

        r = run_command(self.path, "emacsclient", '-n +%d:%d "%s" 2>nul' % (lineno, columnno, filename), False)
        if r != 0:
            run_command(self.path, 'runemacs', '--quick -f server-start +%d:%d "%s"' % (lineno, columnno, filename))
            sleep(self.start_duration)
        else:
            sleep(self.wakeup_duration)

        restore_console_focus()


def emacs(path = r"C:\Program Files\emacs\bin", wakeup_duration = 100, start_duration = 2000):
    synchronize_with_editor = EmacsHook(path, wakeup_duration, start_duration)
    set_hook(synchronize_with_editor)


class SciteHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

        if not filename:
            return

        scites = scitedirector.findWindows()
        if not scites:
            run_command(self.path, "scite", '"-open:%s" -goto:%d' % (filename.replace("\\", "/"), lineno))

            sleep(self.start_duration)
            restore_console_focus()
        else:
            scite = scites[0]
            scitedirector.sendCommand(scite, 'open:%s' % filename.replace("\\", "/"))
            scitedirector.sendCommand(scite, "goto:%d" % lineno)


def scite(path = r"C:\Program Files\SciTE Source Code Editor", wakeup_duration = 100, start_duration = 500):
    synchronize_with_editor = SciteHook(path, wakeup_duration, start_duration)
    set_hook(synchronize_with_editor)


class NodePadPlusPlusHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

        if not filename:
            return

        run_command(self.path, "notepad++", '"%s" -n%d' % (filename, lineno))

        sleep(self.wakeup_duration)

        restore_console_focus()


def notepadplusplus(path = r"C:\Program Files\Notepad++", wakeup_duration = 100):
    synchronize_with_editor = NodePadPlusPlusHook(path, wakeup_duration)
    set_hook(synchronize_with_editor)


class PsPadHook:
    def __init__(self, path, wakeup_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

        if not filename:
            return

        run_command(self.path, "pspad", '"%s" -%d' % (filename, lineno))

        sleep(self.wakeup_duration)

        restore_console_focus()


def pspad(path = r"C:\Program Files\PSPad editor", wakeup_duration = 100):
    synchronize_with_editor = PsPadHook(path, wakeup_duration)
    set_hook(synchronize_with_editor)


# This is an example of DDE hook:
class UltraEditHook:
    def __init__(self, path, wakeup_duration, start_duration):
        self.path = path
        self.wakeup_duration = wakeup_duration
        self.start_duration = start_duration

    def __call__(self, ip, filename, lineno, columnno):
        filename = find_filename(filename)

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
            run_command(self.path, 'uedit32', '"%s/%d"' % (filename, lineno))
            
            sleep(self.start_duration)

        server.Shutdown()

        restore_console_focus()


def ultraedit(path = r"C:\Program Files\IDM Computer Solutions\UltraEdit-32", wakeup_duration = 10, start_duration = 2000):
    synchronize_with_editor = UltraEditHook(path, wakeup_duration, start_duration)
    set_hook(synchronize_with_editor)
    
"""Windows-specific implementation of process utilities with direct WinAPI.

This file is meant to be used by process.py
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

# stdlib
import os, sys, time, threading
import ctypes, msvcrt

# Win32 API types needed for the API calls
from ctypes import POINTER
from ctypes.wintypes import HANDLE, HLOCAL, LPVOID, WORD, DWORD, BOOL, \
        ULONG, LPCWSTR
LPDWORD = POINTER(DWORD)
LPHANDLE = POINTER(HANDLE)
ULONG_PTR = POINTER(ULONG)
class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", DWORD),
                ("lpSecurityDescriptor", LPVOID),
                ("bInheritHandle", BOOL)]
LPSECURITY_ATTRIBUTES = POINTER(SECURITY_ATTRIBUTES)
class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", DWORD),
                ("lpReserved", LPCWSTR),
                ("lpDesktop", LPCWSTR),
                ("lpTitle", LPCWSTR),
                ("dwX", DWORD),
                ("dwY", DWORD),
                ("dwXSize", DWORD),
                ("dwYSize", DWORD),
                ("dwXCountChars", DWORD),
                ("dwYCountChars", DWORD),
                ("dwFillAttribute", DWORD),
                ("dwFlags", DWORD),
                ("wShowWindow", WORD),
                ("cbReserved2", WORD),
                ("lpReserved2", LPVOID),
                ("hStdInput", HANDLE),
                ("hStdOutput", HANDLE),
                ("hStdError", HANDLE)]
LPSTARTUPINFO = POINTER(STARTUPINFO)
class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", HANDLE),
                ("hThread", HANDLE),
                ("dwProcessId", DWORD),
                ("dwThreadId", DWORD)]
LPPROCESS_INFORMATION = POINTER(PROCESS_INFORMATION)

# Win32 API constants needed
ERROR_HANDLE_EOF = 38
ERROR_BROKEN_PIPE = 109
HANDLE_FLAG_INHERIT = 0x0001
STARTF_USESTDHANDLES = 0x0100
CREATE_SUSPENDED = 0x0004
CREATE_NEW_CONSOLE = 0x0010
STILL_ACTIVE = 259
WAIT_TIMEOUT = 0x0102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF
DUPLICATE_SAME_ACCESS = 0x00000002

# Win32 API functions needed
GetLastError = ctypes.windll.kernel32.GetLastError
GetLastError.argtypes = []
GetLastError.restype = DWORD

CreateFile = ctypes.windll.kernel32.CreateFileW
CreateFile.argtypes = [LPCWSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE]
CreateFile.restype = HANDLE

CreatePipe = ctypes.windll.kernel32.CreatePipe
CreatePipe.argtypes = [POINTER(HANDLE), POINTER(HANDLE),
        LPSECURITY_ATTRIBUTES, DWORD]
CreatePipe.restype = BOOL

CreateProcess = ctypes.windll.kernel32.CreateProcessW
CreateProcess.argtypes = [LPCWSTR, LPCWSTR, LPSECURITY_ATTRIBUTES,
        LPSECURITY_ATTRIBUTES, BOOL, DWORD, LPVOID, LPCWSTR, LPSTARTUPINFO,
        LPPROCESS_INFORMATION]
CreateProcess.restype = BOOL

GetExitCodeProcess = ctypes.windll.kernel32.GetExitCodeProcess
GetExitCodeProcess.argtypes = [HANDLE, LPDWORD]
GetExitCodeProcess.restype = BOOL

GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = HANDLE

ResumeThread = ctypes.windll.kernel32.ResumeThread
ResumeThread.argtypes = [HANDLE]
ResumeThread.restype = DWORD

ReadFile = ctypes.windll.kernel32.ReadFile
ReadFile.argtypes = [HANDLE, LPVOID, DWORD, LPDWORD, LPVOID]
ReadFile.restype = BOOL

WriteFile = ctypes.windll.kernel32.WriteFile
WriteFile.argtypes = [HANDLE, LPVOID, DWORD, LPDWORD, LPVOID]
WriteFile.restype = BOOL

WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [HANDLE, DWORD]
WaitForSingleObject.restype = DWORD

DuplicateHandle = ctypes.windll.kernel32.DuplicateHandle
DuplicateHandle.argtypes = [HANDLE, HANDLE, HANDLE, LPHANDLE,
        DWORD, BOOL, DWORD]
DuplicateHandle.restype = BOOL

SetHandleInformation = ctypes.windll.kernel32.SetHandleInformation
SetHandleInformation.argtypes = [HANDLE, DWORD, DWORD]
SetHandleInformation.restype = BOOL

CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

CommandLineToArgvW = ctypes.windll.shell32.CommandLineToArgvW
CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(ctypes.c_int)]
CommandLineToArgvW.restype = POINTER(LPCWSTR)

LocalFree = ctypes.windll.kernel32.LocalFree
LocalFree.argtypes = [HLOCAL]
LocalFree.restype = HLOCAL

class AvoidUNCPath(object):
    """A context manager to protect command execution from UNC paths.

    In the Win32 API, commands can't be invoked with the cwd being a UNC path.
    This context manager temporarily changes directory to the 'C:' drive on
    entering, and restores the original working directory on exit.

    The context manager returns the starting working directory *if* it made a
    change and None otherwise, so that users can apply the necessary adjustment
    to their system calls in the event of a change.

    Example
    -------
    ::
        cmd = 'dir'
        with AvoidUNCPath() as path:
            if path is not None:
                cmd = '"pushd %s &&"%s' % (path, cmd)
            os.system(cmd)
    """
    def __enter__(self):
        self.path = os.getcwdu()
        self.is_unc_path = self.path.startswith(r"\\")
        if self.is_unc_path:
            # change to c drive (as cmd.exe cannot handle UNC addresses)
            os.chdir("C:")
            return self.path
        else:
            # We return None to signal that there was no change in the working
            # directory
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_unc_path:
            os.chdir(self.path)


class Win32ShellCommandController(object):
    """Runs a shell command in a 'with' context.

    This implementation is Win32-specific.

    Example:
        # Runs the command interactively with default console stdin/stdout
        with ShellCommandController('python -i') as scc:
            scc.run()

        # Runs the command using the provided functions for stdin/stdout
        def my_stdout_func(s):
            # print or save the string 's'
            write_to_stdout(s)
        def my_stdin_func():
            # If input is available, return it as a string.
            if input_available():
                return get_input()
            # If no input available, return None after a short delay to
            # keep from blocking.
            else:
                time.sleep(0.01)
                return None
      
        with ShellCommandController('python -i') as scc:
            scc.run(my_stdout_func, my_stdin_func)
    """

    def __init__(self, cmd, mergeout = True):
        """Initializes the shell command controller.

        The cmd is the program to execute, and mergeout is
        whether to blend stdout and stderr into one output
        in stdout. Merging them together in this fashion more
        reliably keeps stdout and stderr in the correct order
        especially for interactive shell usage.
        """
        self.cmd = cmd
        self.mergeout = mergeout

    def __enter__(self):
        cmd = self.cmd
        mergeout = self.mergeout

        self.hstdout, self.hstdin, self.hstderr = None, None, None
        self.piProcInfo = None
        try:
            p_hstdout, c_hstdout, p_hstderr, \
                    c_hstderr, p_hstdin, c_hstdin = [None]*6

            # SECURITY_ATTRIBUTES with inherit handle set to True
            saAttr = SECURITY_ATTRIBUTES()
            saAttr.nLength = ctypes.sizeof(saAttr)
            saAttr.bInheritHandle = True
            saAttr.lpSecurityDescriptor = None

            def create_pipe(uninherit):
                """Creates a Windows pipe, which consists of two handles.

                The 'uninherit' parameter controls which handle is not
                inherited by the child process.
                """
                handles = HANDLE(), HANDLE()
                if not CreatePipe(ctypes.byref(handles[0]),
                            ctypes.byref(handles[1]), ctypes.byref(saAttr), 0):
                    raise ctypes.WinError()
                if not SetHandleInformation(handles[uninherit],
                            HANDLE_FLAG_INHERIT, 0):
                    raise ctypes.WinError()
                return handles[0].value, handles[1].value

            p_hstdout, c_hstdout = create_pipe(uninherit=0)
            # 'mergeout' signals that stdout and stderr should be merged.
            # We do that by using one pipe for both of them.
            if mergeout:
                c_hstderr = HANDLE()
                if not DuplicateHandle(GetCurrentProcess(), c_hstdout,
                                GetCurrentProcess(), ctypes.byref(c_hstderr),
                                0, True, DUPLICATE_SAME_ACCESS):
                    raise ctypes.WinError()
            else:
                p_hstderr, c_hstderr = create_pipe(uninherit=0)
            c_hstdin,  p_hstdin  = create_pipe(uninherit=1)

            # Create the process object
            piProcInfo = PROCESS_INFORMATION()
            siStartInfo = STARTUPINFO()
            siStartInfo.cb = ctypes.sizeof(siStartInfo)
            siStartInfo.hStdInput = c_hstdin
            siStartInfo.hStdOutput = c_hstdout
            siStartInfo.hStdError = c_hstderr
            siStartInfo.dwFlags = STARTF_USESTDHANDLES
            dwCreationFlags = CREATE_SUSPENDED # | CREATE_NEW_CONSOLE

            if not CreateProcess(None,
                    u"cmd.exe /c " + cmd,
                    None, None, True, dwCreationFlags,
                    None, None, ctypes.byref(siStartInfo),
                    ctypes.byref(piProcInfo)):
                raise ctypes.WinError()

            # Close this process's versions of the child handles
            CloseHandle(c_hstdin)
            c_hstdin = None
            CloseHandle(c_hstdout)
            c_hstdout = None
            if c_hstderr != None:
                CloseHandle(c_hstderr)
                c_hstderr = None

            # Transfer ownership of the parent handles to the object
            self.hstdin = p_hstdin
            p_hstdin = None
            self.hstdout = p_hstdout
            p_hstdout = None
            if not mergeout:
                self.hstderr = p_hstderr
                p_hstderr = None
            self.piProcInfo = piProcInfo

        finally:
            if p_hstdin:
                CloseHandle(p_hstdin)
            if c_hstdin:
                CloseHandle(c_hstdin)
            if p_hstdout:
                CloseHandle(p_hstdout)
            if c_hstdout:
                CloseHandle(c_hstdout)
            if p_hstderr:
                CloseHandle(p_hstderr)
            if c_hstderr:
                CloseHandle(c_hstderr)

        return self

    def _stdin_thread(self, handle, hprocess, func, stdout_func):
        # TODO: Use WaitForInputIdle to avoid calling func() until
        #       an input is actually requested.
        exitCode = DWORD()
        bytesWritten = DWORD(0)
        while True:
            #print("stdin thread loop start")
            # Get the input string (may be bytes or unicode)
            data = func()

            # None signals to poll whether the process has exited
            if data is None:
                #print("checking for process completion")
                if not GetExitCodeProcess(hprocess, ctypes.byref(exitCode)):
                    raise ctypes.WinError()
                if exitCode.value != STILL_ACTIVE:
                    return
                # TESTING: Does zero-sized writefile help?
                if not WriteFile(handle, "", 0,
                        ctypes.byref(bytesWritten), None):
                    raise ctypes.WinError()
                continue
            #print("\nGot str %s\n" % repr(data), file=sys.stderr)

            # Encode the string to the console encoding
            if isinstance(data, unicode): #FIXME: Python3
                data = data.encode('utf_8')

            # What we have now must be a string of bytes
            if not isinstance(data, str): #FIXME: Python3
                raise RuntimeError("internal stdin function string error")

            # An empty string signals EOF
            if len(data) == 0:
                return

            # In a windows console, sometimes the input is echoed,
            # but sometimes not. How do we determine when to do this?
            stdout_func(data)
            # WriteFile may not accept all the data at once.
            # Loop until everything is processed
            while len(data) != 0:
                #print("Calling writefile")
                if not WriteFile(handle, data, len(data),
                        ctypes.byref(bytesWritten), None):
                    raise ctypes.WinError()
                #print("Called writefile")
                data = data[bytesWritten.value:]

    def _stdout_thread(self, handle, func):
        # Allocate the output buffer
        data = ctypes.create_string_buffer(4096)
        while True:
            bytesRead = DWORD(0)
            if not ReadFile(handle, data, 4096,
                        ctypes.byref(bytesRead), None):
                le = GetLastError()
                if le == ERROR_BROKEN_PIPE:
                    return
                else:
                    raise ctypes.WinError()
            # FIXME: Python3
            s = data.value[0:bytesRead.value]
            #print("\nv: %s" % repr(s), file=sys.stderr)
            func(s.decode('utf_8', 'replace'))

    def run(self, stdout_func = None, stdin_func = None, stderr_func = None):
        """Runs the process, using the provided functions for I/O.

        The function stdin_func should return strings whenever a
        character or characters become available.
        The functions stdout_func and stderr_func are called whenever
        something is printed to stdout or stderr, respectively.
        These functions are called from different threads (but not
        concurrently, because of the GIL).
        """
        if stdout_func == None and stdin_func == None and stderr_func == None:
            return self._run_stdio()

        if stderr_func != None and self.hstderr == None:
            raise RuntimeError("Shell command was initiated with "
                    "merged stdin/stdout, but a separate stderr_func "
                    "was provided to the run() method")

        # Create a thread for each input/output handle
        threads = []
        if stdin_func:
            threads.append(threading.Thread(target=self._stdin_thread,
                                args=(self.hstdin, self.piProcInfo.hProcess,
                                stdin_func, stdout_func)))
        threads.append(threading.Thread(target=self._stdout_thread,
                                    args=(self.hstdout, stdout_func)))
        if self.hstderr != None:
            if stderr_func == None:
                stderr_func = stdout_func
            threads.append(threading.Thread(target=self._stdout_thread,
                                        args=(self.hstderr, stderr_func)))
        # Start the I/O threads and the process
        if ResumeThread(self.piProcInfo.hThread) == 0xFFFFFFFF:
            raise ctypes.WinError()
        for thread in threads:
            thread.start()
        # Wait for the process to complete
        if WaitForSingleObject(self.piProcInfo.hProcess, INFINITE) == \
                    WAIT_FAILED:
            raise ctypes.WinError()
        # Wait for the I/O threads to complete
        for thread in threads:
            thread.join()

    def _stdin_raw(self):
        """Uses msvcrt.kbhit/getwch to do read stdin without blocking"""
        if msvcrt.kbhit():
            #s = msvcrt.getwch()
            s = msvcrt.getwch()
            # Key code for Enter is '\r', but need to give back '\n'
            if s == u'\r':
                s = u'\n'
            return s
        else:
            # This should make it poll at about 100 Hz, which
            # is hopefully good enough to be responsive but
            # doesn't waste CPU.
            time.sleep(0.01)
            return None

    def _stdout_raw(self, s):
        """Writes the string to stdout"""
        print(s, end='', file=sys.stdout)

    def _stderr_raw(self, s):
        """Writes the string to stdout"""
        print(s, end='', file=sys.stderr)

    def _run_stdio(self):
        """Runs the process using the system standard I/O.

        IMPORTANT: stdin needs to be asynchronous, so the Python
                   sys.stdin object is not used. Instead,
                   msvcrt.kbhit/getwch are used asynchronously.
        """
        if self.hstderr != None:
            return self.run(stdout_func = self._stdout_raw,
                    stdin_func = self._stdin_raw,
                    stderr_func = self._stderr_raw)
        else:
            return self.run(stdout_func = self._stdout_raw,
                    stdin_func = self._stdin_raw)
                    

    def __exit__(self, exc_type, exc_value, traceback):
        if self.hstdin:
            CloseHandle(self.hstdin)
            self.hstdin = None
        if self.hstdout:
            CloseHandle(self.hstdout)
            self.hstdout = None
        if self.hstderr:
            CloseHandle(self.hstderr)
            self.hstderr = None
        if self.piProcInfo != None:
            CloseHandle(self.piProcInfo.hProcess)
            CloseHandle(self.piProcInfo.hThread)
            self.piProcInfo = None


def system(cmd):
    """Win32 version of os.system() that works with network shares.

    Note that this implementation returns None, as meant for use in IPython.

    Parameters
    ----------
    cmd : str
      A command to be executed in the system shell.

    Returns
    -------
    None : we explicitly do NOT return the subprocess status code, as this
    utility is meant to be used extensively in IPython, where any return value
    would trigger :func:`sys.displayhook` calls.
    """
    with AvoidUNCPath() as path:
        if path is not None:
            cmd = '"pushd %s &&"%s' % (path, cmd)
        with Win32ShellCommandController(cmd) as scc:
            scc.run()


if __name__ == "__main__":
    print("Test starting!")
    #system("cmd")
    system("python -i")
    print("Test finished!")

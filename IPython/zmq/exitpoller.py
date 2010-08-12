import os
import time
from threading import Thread


class ExitPollerUnix(Thread):
    """ A Unix-specific daemon thread that terminates the program immediately 
    when the parent process no longer exists.
    """

    def __init__(self):
        super(ExitPollerUnix, self).__init__()
        self.daemon = True
    
    def run(self):
        # We cannot use os.waitpid because it works only for child processes.
        from errno import EINTR
        while True:
            try:
                if os.getppid() == 1:
                    os._exit(1)
                time.sleep(1.0)
            except OSError, e:
                if e.errno == EINTR:
                    continue
                raise

class ExitPollerWindows(Thread):
    """ A Windows-specific daemon thread that terminates the program immediately
    when a Win32 handle is signaled.
    """ 
    
    def __init__(self, handle):
        super(ExitPollerWindows, self).__init__()
        self.daemon = True
        self.handle = handle

    def run(self):
        from _subprocess import WaitForSingleObject, WAIT_OBJECT_0, INFINITE
        result = WaitForSingleObject(self.handle, INFINITE)
        if result == WAIT_OBJECT_0:
            os._exit(1)
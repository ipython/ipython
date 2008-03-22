from IPython.genutils import Term,warn,error,flag_calls, ask_yes_no

import thread,inspect

try:
    import ctypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False


# Globals
# global flag to pass around information about Ctrl-C without exceptions
KBINT = False

# global flag to turn on/off Tk support.
USE_TK = False

# ID for the main thread, used for cross-thread exceptions
MAIN_THREAD_ID = thread.get_ident()

# Tag when runcode() is active, for exception handling
CODE_RUN = None


#-----------------------------------------------------------------------------
# This class is trivial now, but I want to have it in to publish a clean
# interface. Later when the internals are reorganized, code that uses this
# shouldn't have to change.


if HAS_CTYPES:
    #  Add async exception support.  Trick taken from:
    # http://sebulba.wikispaces.com/recipe+thread2
    def _async_raise(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid,
                                                         ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble, 
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def sigint_handler (signum,stack_frame):
        """Sigint handler for threaded apps.

        This is a horrible hack to pass information about SIGINT _without_
        using exceptions, since I haven't been able to properly manage
        cross-thread exceptions in GTK/WX.  In fact, I don't think it can be
        done (or at least that's my understanding from a c.l.py thread where
        this was discussed)."""

        global KBINT

        if CODE_RUN:
            _async_raise(MAIN_THREAD_ID,KeyboardInterrupt)
        else:
            KBINT = True
            print '\nKeyboardInterrupt - Press <Enter> to continue.',
            Term.cout.flush()

else:
    def sigint_handler (signum,stack_frame):
        """Sigint handler for threaded apps.

        This is a horrible hack to pass information about SIGINT _without_
        using exceptions, since I haven't been able to properly manage
        cross-thread exceptions in GTK/WX.  In fact, I don't think it can be
        done (or at least that's my understanding from a c.l.py thread where
        this was discussed)."""

        global KBINT

        print '\nKeyboardInterrupt - Press <Enter> to continue.',
        Term.cout.flush()
        # Set global flag so that runsource can know that Ctrl-C was hit
        KBINT = True

def run_in_frontend(src):
    """ Check if source snippet can be run in the REPL thread, as opposed to GUI mainloop
    
    (to prevent unnecessary hanging of mainloop).  
    
    """
    
    if src.startswith('_ip.system(') and not '\n' in src:
        return True
    return False
    
    
    

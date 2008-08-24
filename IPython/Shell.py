# -*- coding: utf-8 -*-
"""IPython Shell classes.

All the matplotlib support code was co-developed with John Hunter,
matplotlib's author.

$Id: Shell.py 3024 2008-02-07 15:34:42Z darren.dale $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# Code begins
# Stdlib imports
import __builtin__
import __main__
import Queue
import inspect
import os
import sys
import thread
import threading
import time

from signal import signal, SIGINT

try:
    import ctypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False

# IPython imports
import IPython
from IPython import ultraTB, ipapi
from IPython.Magic import Magic
from IPython.genutils import Term,warn,error,flag_calls, ask_yes_no
from IPython.iplib import InteractiveShell
from IPython.ipmaker import make_IPython
from IPython.ipstruct import Struct
from IPython.testing import decorators as testdec

# Globals
# global flag to pass around information about Ctrl-C without exceptions
KBINT = False

# global flag to turn on/off Tk support.
USE_TK = False

# ID for the main thread, used for cross-thread exceptions
MAIN_THREAD_ID = thread.get_ident()

# Tag when runcode() is active, for exception handling
CODE_RUN = None

# Default timeout for waiting for multithreaded shells (in seconds)
GUI_TIMEOUT = 10

#-----------------------------------------------------------------------------
# This class is trivial now, but I want to have it in to publish a clean
# interface. Later when the internals are reorganized, code that uses this
# shouldn't have to change.

class IPShell:
    """Create an IPython instance."""
    
    def __init__(self,argv=None,user_ns=None,user_global_ns=None,
                 debug=1,shell_class=InteractiveShell):
        self.IP = make_IPython(argv,user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug,shell_class=shell_class)

    def mainloop(self,sys_exit=0,banner=None):
        self.IP.mainloop(banner)
        if sys_exit:
            sys.exit()

#-----------------------------------------------------------------------------
def kill_embedded(self,parameter_s=''):
    """%kill_embedded : deactivate for good the current embedded IPython.

    This function (after asking for confirmation) sets an internal flag so that
    an embedded IPython will never activate again.  This is useful to
    permanently disable a shell that is being called inside a loop: once you've
    figured out what you needed from it, you may then kill it and the program
    will then continue to run without the interactive shell interfering again.
    """
    
    kill = ask_yes_no("Are you sure you want to kill this embedded instance "
                     "(y/n)? [y/N] ",'n')
    if kill:
        self.shell.embedded_active = False
        print "This embedded IPython will not reactivate anymore once you exit."
    
class IPShellEmbed:
    """Allow embedding an IPython shell into a running program.

    Instances of this class are callable, with the __call__ method being an
    alias to the embed() method of an InteractiveShell instance.

    Usage (see also the example-embed.py file for a running example):

    ipshell = IPShellEmbed([argv,banner,exit_msg,rc_override])

    - argv: list containing valid command-line options for IPython, as they
    would appear in sys.argv[1:].

    For example, the following command-line options:

      $ ipython -prompt_in1 'Input <\\#>' -colors LightBG

    would be passed in the argv list as:

      ['-prompt_in1','Input <\\#>','-colors','LightBG']

    - banner: string which gets printed every time the interpreter starts.

    - exit_msg: string which gets printed every time the interpreter exits.

    - rc_override: a dict or Struct of configuration options such as those
    used by IPython. These options are read from your ~/.ipython/ipythonrc
    file when the Shell object is created. Passing an explicit rc_override
    dict with any options you want allows you to override those values at
    creation time without having to modify the file. This way you can create
    embeddable instances configured in any way you want without editing any
    global files (thus keeping your interactive IPython configuration
    unchanged).

    Then the ipshell instance can be called anywhere inside your code:
    
    ipshell(header='') -> Opens up an IPython shell.

    - header: string printed by the IPython shell upon startup. This can let
    you know where in your code you are when dropping into the shell. Note
    that 'banner' gets prepended to all calls, so header is used for
    location-specific information.

    For more details, see the __call__ method below.

    When the IPython shell is exited with Ctrl-D, normal program execution
    resumes.

    This functionality was inspired by a posting on comp.lang.python by cmkl
    <cmkleffner@gmx.de> on Dec. 06/01 concerning similar uses of pyrepl, and
    by the IDL stop/continue commands."""

    def __init__(self,argv=None,banner='',exit_msg=None,rc_override=None,
                 user_ns=None):
        """Note that argv here is a string, NOT a list."""
        self.set_banner(banner)
        self.set_exit_msg(exit_msg)
        self.set_dummy_mode(0)

        # sys.displayhook is a global, we need to save the user's original
        # Don't rely on __displayhook__, as the user may have changed that.
        self.sys_displayhook_ori = sys.displayhook

        # save readline completer status
        try:
            #print 'Save completer',sys.ipcompleter  # dbg
            self.sys_ipcompleter_ori = sys.ipcompleter
        except:
            pass # not nested with IPython
        
        self.IP = make_IPython(argv,rc_override=rc_override,
                               embedded=True,
                               user_ns=user_ns)

        ip = ipapi.IPApi(self.IP)
        ip.expose_magic("kill_embedded",kill_embedded)

        # copy our own displayhook also
        self.sys_displayhook_embed = sys.displayhook
        # and leave the system's display hook clean
        sys.displayhook = self.sys_displayhook_ori
        # don't use the ipython crash handler so that user exceptions aren't
        # trapped
        sys.excepthook = ultraTB.FormattedTB(color_scheme = self.IP.rc.colors,
                                             mode = self.IP.rc.xmode,
                                             call_pdb = self.IP.rc.pdb)
        self.restore_system_completer()

    def restore_system_completer(self):
        """Restores the readline completer which was in place.

        This allows embedded IPython within IPython not to disrupt the
        parent's completion.
        """
        
        try:
            self.IP.readline.set_completer(self.sys_ipcompleter_ori)
            sys.ipcompleter = self.sys_ipcompleter_ori
        except:
            pass

    def __call__(self,header='',local_ns=None,global_ns=None,dummy=None):
        """Activate the interactive interpreter.

        __call__(self,header='',local_ns=None,global_ns,dummy=None) -> Start
        the interpreter shell with the given local and global namespaces, and
        optionally print a header string at startup.

        The shell can be globally activated/deactivated using the
        set/get_dummy_mode methods. This allows you to turn off a shell used
        for debugging globally.

        However, *each* time you call the shell you can override the current
        state of dummy_mode with the optional keyword parameter 'dummy'. For
        example, if you set dummy mode on with IPShell.set_dummy_mode(1), you
        can still have a specific call work by making it as IPShell(dummy=0).

        The optional keyword parameter dummy controls whether the call
        actually does anything.  """

        # If the user has turned it off, go away
        if not self.IP.embedded_active:
            return

        # Normal exits from interactive mode set this flag, so the shell can't
        # re-enter (it checks this variable at the start of interactive mode).
        self.IP.exit_now = False

        # Allow the dummy parameter to override the global __dummy_mode
        if dummy or (dummy != 0 and self.__dummy_mode):
            return

        # Set global subsystems (display,completions) to our values
        sys.displayhook = self.sys_displayhook_embed
        if self.IP.has_readline:
            self.IP.set_completer()

        if self.banner and header:
            format = '%s\n%s\n'
        else:
            format = '%s%s\n'
        banner =  format % (self.banner,header)

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.IP.embed_mainloop(banner,local_ns,global_ns,stack_depth=1)

        if self.exit_msg:
            print self.exit_msg
            
        # Restore global systems (display, completion)
        sys.displayhook = self.sys_displayhook_ori
        self.restore_system_completer()
    
    def set_dummy_mode(self,dummy):
        """Sets the embeddable shell's dummy mode parameter.

        set_dummy_mode(dummy): dummy = 0 or 1.

        This parameter is persistent and makes calls to the embeddable shell
        silently return without performing any action. This allows you to
        globally activate or deactivate a shell you're using with a single call.

        If you need to manually"""

        if dummy not in [0,1,False,True]:
            raise ValueError,'dummy parameter must be boolean'
        self.__dummy_mode = dummy

    def get_dummy_mode(self):
        """Return the current value of the dummy mode parameter.
        """
        return self.__dummy_mode
    
    def set_banner(self,banner):
        """Sets the global banner.

        This banner gets prepended to every header printed when the shell
        instance is called."""

        self.banner = banner

    def set_exit_msg(self,exit_msg):
        """Sets the global exit_msg.

        This exit message gets printed upon exiting every time the embedded
        shell is called. It is None by default. """

        self.exit_msg = exit_msg

#-----------------------------------------------------------------------------
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


class MTInteractiveShell(InteractiveShell):
    """Simple multi-threaded shell."""

    # Threading strategy taken from:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65109, by Brian
    # McErlean and John Finlay.  Modified with corrections by Antoon Pardon,
    # from the pygtk mailing list, to avoid lockups with system calls.

    # class attribute to indicate whether the class supports threads or not.
    # Subclasses with thread support should override this as needed.
    isthreaded = True

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns=None,user_global_ns=None,banner2='',
                 gui_timeout=GUI_TIMEOUT,**kw):
        """Similar to the normal InteractiveShell, but with threading control"""
        
        InteractiveShell.__init__(self,name,usage,rc,user_ns,
                                  user_global_ns,banner2)

        # Timeout we wait for GUI thread
        self.gui_timeout = gui_timeout

        # A queue to hold the code to be executed. 
        self.code_queue = Queue.Queue()

        # Stuff to do at closing time
        self._kill = None
        on_kill = kw.get('on_kill', [])
        # Check that all things to kill are callable:
        for t in on_kill:
            if not callable(t):
                raise TypeError,'on_kill must be a list of callables'
        self.on_kill = on_kill
        # thread identity of the "worker thread" (that may execute code directly)
        self.worker_ident = None
        
    def runsource(self, source, filename="<input>", symbol="single"):
        """Compile and run some source in the interpreter.

        Modified version of code.py's runsource(), to handle threading issues.
        See the original for full docstring details."""
        
        global KBINT
        
        # If Ctrl-C was typed, we reset the flag and return right away
        if KBINT:
            KBINT = False
            return False

        if self._kill:
            # can't queue new code if we are being killed
            return True
        
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # shortcut - if we are in worker thread, or the worker thread is not
        # running, execute directly (to allow recursion and prevent deadlock if
        # code is run early in IPython construction)
        
        if (self.worker_ident is None
            or self.worker_ident == thread.get_ident() ):
            InteractiveShell.runcode(self,code)
            return

        # Case 3
        # Store code in queue, so the execution thread can handle it.

        completed_ev, received_ev = threading.Event(), threading.Event() 
        
        self.code_queue.put((code,completed_ev, received_ev))
        # first make sure the message was received, with timeout
        received_ev.wait(self.gui_timeout)
        if not received_ev.isSet():
            # the mainloop is dead, start executing code directly
            print "Warning: Timeout for mainloop thread exceeded"
            print "switching to nonthreaded mode (until mainloop wakes up again)"
            self.worker_ident = None
        else:
            completed_ev.wait()
        return False

    def runcode(self):
        """Execute a code object.

        Multithreaded wrapper around IPython's runcode()."""
        
        global CODE_RUN
        
        # we are in worker thread, stash out the id for runsource() 
        self.worker_ident = thread.get_ident()

        if self._kill:
            print >>Term.cout, 'Closing threads...',
            Term.cout.flush()
            for tokill in self.on_kill:
                tokill()
            print >>Term.cout, 'Done.'
            # allow kill() to return
            self._kill.set()
            return True

        # Install sigint handler.  We do it every time to ensure that if user
        # code modifies it, we restore our own handling.
        try:
            signal(SIGINT,sigint_handler)
        except SystemError:
            # This happens under Windows, which seems to have all sorts
            # of problems with signal handling.  Oh well...
            pass

        # Flush queue of pending code by calling the run methood of the parent
        # class with all items which may be in the queue.
        code_to_run = None
        while 1:
            try:
                code_to_run, completed_ev, received_ev = self.code_queue.get_nowait()                
            except Queue.Empty:
                break
            received_ev.set()
            
            # Exceptions need to be raised differently depending on which
            # thread is active.  This convoluted try/except is only there to
            # protect against asynchronous exceptions, to ensure that a KBINT
            # at the wrong time doesn't deadlock everything.  The global
            # CODE_TO_RUN is set to true/false as close as possible to the
            # runcode() call, so that the KBINT handler is correctly informed.
            try:
                try:
                   CODE_RUN = True
                   InteractiveShell.runcode(self,code_to_run)
                except KeyboardInterrupt:
                   print "Keyboard interrupted in mainloop"
                   while not self.code_queue.empty():
                      code, ev1,ev2 = self.code_queue.get_nowait()
                      ev1.set()
                      ev2.set()                      
                   break
            finally:
                CODE_RUN = False
                # allow runsource() return from wait
                completed_ev.set()
                
        
        # This MUST return true for gtk threading to work
        return True

    def kill(self):
        """Kill the thread, returning when it has been shut down."""
        self._kill = threading.Event()
        self._kill.wait()

class MatplotlibShellBase:
    """Mixin class to provide the necessary modifications to regular IPython
    shell classes for matplotlib support.

    Given Python's MRO, this should be used as the FIRST class in the
    inheritance hierarchy, so that it overrides the relevant methods."""
    
    def _matplotlib_config(self,name,user_ns,user_global_ns=None):
        """Return items needed to setup the user's shell with matplotlib"""

        # Initialize matplotlib to interactive mode always
        import matplotlib
        from matplotlib import backends
        matplotlib.interactive(True)

        def use(arg):
            """IPython wrapper for matplotlib's backend switcher.

            In interactive use, we can not allow switching to a different
            interactive backend, since thread conflicts will most likely crash
            the python interpreter.  This routine does a safety check first,
            and refuses to perform a dangerous switch.  It still allows
            switching to non-interactive backends."""

            if arg in backends.interactive_bk and arg != self.mpl_backend:
                m=('invalid matplotlib backend switch.\n'
                   'This script attempted to switch to the interactive '
                   'backend: `%s`\n'
                   'Your current choice of interactive backend is: `%s`\n\n'
                   'Switching interactive matplotlib backends at runtime\n'
                   'would crash the python interpreter, '
                   'and IPython has blocked it.\n\n'
                   'You need to either change your choice of matplotlib backend\n'
                   'by editing your .matplotlibrc file, or run this script as a \n'
                   'standalone file from the command line, not using IPython.\n' %
                   (arg,self.mpl_backend) )
                raise RuntimeError, m
            else:
                self.mpl_use(arg)
                self.mpl_use._called = True
        
        self.matplotlib = matplotlib
        self.mpl_backend = matplotlib.rcParams['backend']

        # we also need to block switching of interactive backends by use()
        self.mpl_use = matplotlib.use
        self.mpl_use._called = False
        # overwrite the original matplotlib.use with our wrapper
        matplotlib.use = use

        # This must be imported last in the matplotlib series, after
        # backend/interactivity choices have been made
        import matplotlib.pylab as pylab
        self.pylab = pylab

        self.pylab.show._needmain = False
        # We need to detect at runtime whether show() is called by the user.
        # For this, we wrap it into a decorator which adds a 'called' flag.
        self.pylab.draw_if_interactive = flag_calls(self.pylab.draw_if_interactive)

        # Build a user namespace initialized with matplotlib/matlab features.
        user_ns, user_global_ns = IPython.ipapi.make_user_namespaces(user_ns,
            user_global_ns)

        # Import numpy as np/pyplot as plt are conventions we're trying to
        # somewhat standardize on.  Making them available to users by default
        # will greatly help this. 
        exec ("import numpy\n"
              "import numpy as np\n"
              "import matplotlib\n"
              "import matplotlib.pylab as pylab\n"
              "try:\n"
              "    import matplotlib.pyplot as plt\n"
              "except ImportError:\n"
              "    pass\n"
              ) in user_ns
        
        # Build matplotlib info banner
        b="""
  Welcome to pylab, a matplotlib-based Python environment.
  For more information, type 'help(pylab)'.
"""
        return user_ns,user_global_ns,b

    def mplot_exec(self,fname,*where,**kw):
        """Execute a matplotlib script.

        This is a call to execfile(), but wrapped in safeties to properly
        handle interactive rendering and backend switching."""

        #print '*** Matplotlib runner ***' # dbg
        # turn off rendering until end of script
        isInteractive = self.matplotlib.rcParams['interactive']
        self.matplotlib.interactive(False)
        self.safe_execfile(fname,*where,**kw)
        self.matplotlib.interactive(isInteractive)
        # make rendering call now, if the user tried to do it
        if self.pylab.draw_if_interactive.called:
            self.pylab.draw()
            self.pylab.draw_if_interactive.called = False
                
        # if a backend switch was performed, reverse it now
        if self.mpl_use._called:
            self.matplotlib.rcParams['backend'] = self.mpl_backend

    @testdec.skip_doctest
    def magic_run(self,parameter_s=''):
        Magic.magic_run(self,parameter_s,runner=self.mplot_exec)

    # Fix the docstring so users see the original as well
    magic_run.__doc__ = "%s\n%s" % (Magic.magic_run.__doc__,
                                    "\n        *** Modified %run for Matplotlib,"
                                    " with proper interactive handling ***")

# Now we provide 2 versions of a matplotlib-aware IPython base shells, single
# and multithreaded.  Note that these are meant for internal use, the IPShell*
# classes below are the ones meant for public consumption.

class MatplotlibShell(MatplotlibShellBase,InteractiveShell):
    """Single-threaded shell with matplotlib support."""

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns=None,user_global_ns=None,**kw):
        user_ns,user_global_ns,b2 = self._matplotlib_config(name,user_ns,user_global_ns)
        InteractiveShell.__init__(self,name,usage,rc,user_ns,user_global_ns,
                                  banner2=b2,**kw)

class MatplotlibMTShell(MatplotlibShellBase,MTInteractiveShell):
    """Multi-threaded shell with matplotlib support."""

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns=None,user_global_ns=None, **kw):
        user_ns,user_global_ns,b2 = self._matplotlib_config(name,user_ns,user_global_ns)
        MTInteractiveShell.__init__(self,name,usage,rc,user_ns,user_global_ns,
                                    banner2=b2,**kw)

#-----------------------------------------------------------------------------
# Utility functions for the different GUI enabled IPShell* classes.

def get_tk():
    """Tries to import Tkinter and returns a withdrawn Tkinter root
    window.  If Tkinter is already imported or not available, this
    returns None.  This function calls `hijack_tk` underneath.
    """
    if not USE_TK or sys.modules.has_key('Tkinter'):
        return None
    else:
        try:
            import Tkinter
        except ImportError:
            return None
        else:
            hijack_tk()
            r = Tkinter.Tk()
            r.withdraw()
            return r

def hijack_tk():
    """Modifies Tkinter's mainloop with a dummy so when a module calls
    mainloop, it does not block.

    """
    def misc_mainloop(self, n=0):
        pass
    def tkinter_mainloop(n=0):
        pass
    
    import Tkinter
    Tkinter.Misc.mainloop = misc_mainloop
    Tkinter.mainloop = tkinter_mainloop

def update_tk(tk):
    """Updates the Tkinter event loop.  This is typically called from
    the respective WX or GTK mainloops.
    """    
    if tk:
        tk.update()

def hijack_wx():
    """Modifies wxPython's MainLoop with a dummy so user code does not
    block IPython.  The hijacked mainloop function is returned.
    """    
    def dummy_mainloop(*args, **kw):
        pass

    try:
        import wx
    except ImportError:
        # For very old versions of WX
        import wxPython as wx
        
    ver = wx.__version__
    orig_mainloop = None
    if ver[:3] >= '2.5':
        import wx
        if hasattr(wx, '_core_'): core = getattr(wx, '_core_')
        elif hasattr(wx, '_core'): core = getattr(wx, '_core')
        else: raise AttributeError('Could not find wx core module')
        orig_mainloop = core.PyApp_MainLoop
        core.PyApp_MainLoop = dummy_mainloop
    elif ver[:3] == '2.4':
        orig_mainloop = wx.wxc.wxPyApp_MainLoop
        wx.wxc.wxPyApp_MainLoop = dummy_mainloop
    else:
        warn("Unable to find either wxPython version 2.4 or >= 2.5.")
    return orig_mainloop

def hijack_gtk():
    """Modifies pyGTK's mainloop with a dummy so user code does not
    block IPython.  This function returns the original `gtk.mainloop`
    function that has been hijacked.
    """    
    def dummy_mainloop(*args, **kw):
        pass
    import gtk
    if gtk.pygtk_version >= (2,4,0): orig_mainloop = gtk.main
    else:                            orig_mainloop = gtk.mainloop
    gtk.mainloop = dummy_mainloop
    gtk.main = dummy_mainloop
    return orig_mainloop

def hijack_qt():
    """Modifies PyQt's mainloop with a dummy so user code does not 
    block IPython.  This function returns the original 
    `qt.qApp.exec_loop` function that has been hijacked.
    """    
    def dummy_mainloop(*args, **kw):
        pass
    import qt
    orig_mainloop = qt.qApp.exec_loop
    qt.qApp.exec_loop = dummy_mainloop
    qt.QApplication.exec_loop = dummy_mainloop
    return orig_mainloop

def hijack_qt4():
    """Modifies PyQt4's mainloop with a dummy so user code does not
    block IPython.  This function returns the original 
    `QtGui.qApp.exec_` function that has been hijacked.
    """    
    def dummy_mainloop(*args, **kw):
        pass
    from PyQt4 import QtGui, QtCore
    orig_mainloop = QtGui.qApp.exec_
    QtGui.qApp.exec_ = dummy_mainloop
    QtGui.QApplication.exec_ = dummy_mainloop
    QtCore.QCoreApplication.exec_ = dummy_mainloop
    return orig_mainloop

#-----------------------------------------------------------------------------
# The IPShell* classes below are the ones meant to be run by external code as
# IPython instances.  Note that unless a specific threading strategy is
# desired, the factory function start() below should be used instead (it
# selects the proper threaded class).

class IPThread(threading.Thread):
    def run(self):
        self.IP.mainloop(self._banner)
        self.IP.kill()

class IPShellGTK(IPThread):
    """Run a gtk mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,user_global_ns=None,
                 debug=1,shell_class=MTInteractiveShell):

        import gtk
        
        self.gtk = gtk
        self.gtk_mainloop = hijack_gtk()

        # Allows us to use both Tk and GTK.
        self.tk = get_tk()
        
        if gtk.pygtk_version >= (2,4,0): mainquit = self.gtk.main_quit
        else:                            mainquit = self.gtk.mainquit

        self.IP = make_IPython(argv,user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug,
                               shell_class=shell_class,
                               on_kill=[mainquit])

        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 

        threading.Thread.__init__(self)

    def mainloop(self,sys_exit=0,banner=None):

        self._banner = banner
        
        if self.gtk.pygtk_version >= (2,4,0):
            import gobject
            gobject.idle_add(self.on_timer)
        else:
            self.gtk.idle_add(self.on_timer)

        if sys.platform != 'win32':
            try:
                if self.gtk.gtk_version[0] >= 2:
                    self.gtk.gdk.threads_init()
            except AttributeError:
                pass
            except RuntimeError:
                error('Your pyGTK likely has not been compiled with '
                      'threading support.\n'
                      'The exception printout is below.\n'
                      'You can either rebuild pyGTK with threads, or '
                      'try using \n'
                      'matplotlib with a different backend (like Tk or WX).\n'
                      'Note that matplotlib will most likely not work in its '
                      'current state!')
                self.IP.InteractiveTB()

        self.start()
        self.gtk.gdk.threads_enter()
        self.gtk_mainloop()
        self.gtk.gdk.threads_leave()
        self.join()

    def on_timer(self):
        """Called when GTK is idle.

        Must return True always, otherwise GTK stops calling it"""
        
        update_tk(self.tk)
        self.IP.runcode()
        time.sleep(0.01)
        return True


class IPShellWX(IPThread):
    """Run a wx mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,user_global_ns=None,
                 debug=1,shell_class=MTInteractiveShell):

        self.IP = make_IPython(argv,user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug,
                               shell_class=shell_class,
                               on_kill=[self.wxexit])

        wantedwxversion=self.IP.rc.wxversion
        if wantedwxversion!="0":
            try:
                import wxversion
            except ImportError:
                error('The wxversion module is needed for WX version selection')
            else:
                try:
                    wxversion.select(wantedwxversion)
                except:
                    self.IP.InteractiveTB()
                    error('Requested wxPython version %s could not be loaded' %
                                                               wantedwxversion)

        import wx

        threading.Thread.__init__(self)
        self.wx = wx
        self.wx_mainloop = hijack_wx()

        # Allows us to use both Tk and GTK.
        self.tk = get_tk()
        
        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 

        self.app = None

    def wxexit(self, *args):
        if self.app is not None:
            self.app.agent.timer.Stop()
            self.app.ExitMainLoop()

    def mainloop(self,sys_exit=0,banner=None):

        self._banner = banner
        
        self.start()

        class TimerAgent(self.wx.MiniFrame):
            wx = self.wx
            IP = self.IP
            tk = self.tk
            def __init__(self, parent, interval):
                style = self.wx.DEFAULT_FRAME_STYLE | self.wx.TINY_CAPTION_HORIZ
                self.wx.MiniFrame.__init__(self, parent, -1, ' ', pos=(200, 200),
                                             size=(100, 100),style=style)
                self.Show(False)
                self.interval = interval
                self.timerId = self.wx.NewId()                                

            def StartWork(self):
                self.timer = self.wx.Timer(self, self.timerId)
                self.wx.EVT_TIMER(self,  self.timerId, self.OnTimer)
                self.timer.Start(self.interval)

            def OnTimer(self, event):
                update_tk(self.tk)
                self.IP.runcode()

        class App(self.wx.App):
            wx = self.wx
            TIMEOUT = self.TIMEOUT
            def OnInit(self):
                'Create the main window and insert the custom frame'
                self.agent = TimerAgent(None, self.TIMEOUT)
                self.agent.Show(False)
                self.agent.StartWork()
                return True

        self.app = App(redirect=False)
        self.wx_mainloop(self.app)
        self.join()


class IPShellQt(IPThread):
    """Run a Qt event loop in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    Qt timer / slot."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self, argv=None, user_ns=None, user_global_ns=None,
                 debug=0, shell_class=MTInteractiveShell):

        import qt

        self.exec_loop = hijack_qt()

        # Allows us to use both Tk and QT.
        self.tk = get_tk()

        self.IP = make_IPython(argv,
                               user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug,
                               shell_class=shell_class,
                               on_kill=[qt.qApp.exit])

        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 
        
        threading.Thread.__init__(self)

    def mainloop(self, sys_exit=0, banner=None):

        import qt

        self._banner = banner

        if qt.QApplication.startingUp():
            a = qt.QApplication(sys.argv)

        self.timer = qt.QTimer()
        qt.QObject.connect(self.timer,
                           qt.SIGNAL('timeout()'),
                           self.on_timer)

        self.start()
        self.timer.start(self.TIMEOUT, True)
        while True:
            if self.IP._kill: break
            self.exec_loop()
        self.join()

    def on_timer(self):
        update_tk(self.tk)
        result = self.IP.runcode()
        self.timer.start(self.TIMEOUT, True)
        return result


class IPShellQt4(IPThread):
    """Run a Qt event loop in a separate thread.

    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    Qt timer / slot."""

    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self, argv=None, user_ns=None, user_global_ns=None,
                 debug=0, shell_class=MTInteractiveShell):

        from PyQt4 import QtCore, QtGui

        try:
            # present in PyQt4-4.2.1 or later
            QtCore.pyqtRemoveInputHook()
        except AttributeError:
            pass

        if QtCore.PYQT_VERSION_STR == '4.3':
            warn('''PyQt4 version 4.3 detected.
If you experience repeated threading warnings, please update PyQt4.
''')

        self.exec_ = hijack_qt4()

        # Allows us to use both Tk and QT.
        self.tk = get_tk()

        self.IP = make_IPython(argv,
                               user_ns=user_ns,
                               user_global_ns=user_global_ns,
                               debug=debug,
                               shell_class=shell_class,
                               on_kill=[QtGui.qApp.exit])

        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None

        threading.Thread.__init__(self)

    def mainloop(self, sys_exit=0, banner=None):

        from PyQt4 import QtCore, QtGui

        self._banner = banner

        if QtGui.QApplication.startingUp():
            a = QtGui.QApplication(sys.argv)

        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer,
                               QtCore.SIGNAL('timeout()'),
                               self.on_timer)

        self.start()
        self.timer.start(self.TIMEOUT)
        while True:
            if self.IP._kill: break
            self.exec_()
        self.join()

    def on_timer(self):
        update_tk(self.tk)
        result = self.IP.runcode()
        self.timer.start(self.TIMEOUT)
        return result


# A set of matplotlib public IPython shell classes, for single-threaded (Tk*
# and FLTK*) and multithreaded (GTK*, WX* and Qt*) backends to use.
def _load_pylab(user_ns):
    """Allow users to disable pulling all of pylab into the top-level
    namespace.

    This little utility must be called AFTER the actual ipython instance is
    running, since only then will the options file have been fully parsed."""
    
    ip = IPython.ipapi.get()
    if ip.options.pylab_import_all:
        ip.ex("from matplotlib.pylab import *")
        ip.IP.user_config_ns.update(ip.user_ns)
        

class IPShellMatplotlib(IPShell):
    """Subclass IPShell with MatplotlibShell as the internal shell.

    Single-threaded class, meant for the Tk* and FLTK* backends.

    Having this on a separate class simplifies the external driver code."""
    
    def __init__(self,argv=None,user_ns=None,user_global_ns=None,debug=1):
        IPShell.__init__(self,argv,user_ns,user_global_ns,debug,
                         shell_class=MatplotlibShell)
        _load_pylab(self.IP.user_ns)

class IPShellMatplotlibGTK(IPShellGTK):
    """Subclass IPShellGTK with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the GTK* backends."""
    
    def __init__(self,argv=None,user_ns=None,user_global_ns=None,debug=1):
        IPShellGTK.__init__(self,argv,user_ns,user_global_ns,debug,
                            shell_class=MatplotlibMTShell)
        _load_pylab(self.IP.user_ns)

class IPShellMatplotlibWX(IPShellWX):
    """Subclass IPShellWX with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the WX* backends."""
    
    def __init__(self,argv=None,user_ns=None,user_global_ns=None,debug=1):
        IPShellWX.__init__(self,argv,user_ns,user_global_ns,debug,
                           shell_class=MatplotlibMTShell)
        _load_pylab(self.IP.user_ns)

class IPShellMatplotlibQt(IPShellQt):
    """Subclass IPShellQt with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the Qt* backends."""
    
    def __init__(self,argv=None,user_ns=None,user_global_ns=None,debug=1):
        IPShellQt.__init__(self,argv,user_ns,user_global_ns,debug,
                           shell_class=MatplotlibMTShell)
        _load_pylab(self.IP.user_ns)

class IPShellMatplotlibQt4(IPShellQt4):
    """Subclass IPShellQt4 with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the Qt4* backends."""

    def __init__(self,argv=None,user_ns=None,user_global_ns=None,debug=1):
        IPShellQt4.__init__(self,argv,user_ns,user_global_ns,debug,
                           shell_class=MatplotlibMTShell)
        _load_pylab(self.IP.user_ns)

#-----------------------------------------------------------------------------
# Factory functions to actually start the proper thread-aware shell

def _select_shell(argv):
    """Select a shell from the given argv vector.

    This function implements the threading selection policy, allowing runtime
    control of the threading mode, both for general users and for matplotlib.

    Return:
      Shell class to be instantiated for runtime operation.
    """
    
    global USE_TK

    mpl_shell = {'gthread' : IPShellMatplotlibGTK,
                 'wthread' : IPShellMatplotlibWX,
                 'qthread' : IPShellMatplotlibQt,
                 'q4thread' : IPShellMatplotlibQt4,
                 'tkthread' : IPShellMatplotlib,  # Tk is built-in
                 }

    th_shell = {'gthread' : IPShellGTK,
                'wthread' : IPShellWX,
                'qthread' : IPShellQt,
                'q4thread' : IPShellQt4,
                'tkthread' : IPShell, # Tk is built-in
                }

    backends = {'gthread' : 'GTKAgg',
                'wthread' : 'WXAgg',
                'qthread' : 'QtAgg',
                'q4thread' :'Qt4Agg',
                'tkthread' :'TkAgg',
                }

    all_opts = set(['tk','pylab','gthread','qthread','q4thread','wthread',
                    'tkthread'])
    user_opts = set([s.replace('-','') for s in argv[:3]])
    special_opts = user_opts & all_opts            

    if 'tk' in special_opts:
        USE_TK = True
        special_opts.remove('tk')

    if 'pylab' in special_opts:

        try:
            import matplotlib
        except ImportError:
            error('matplotlib could NOT be imported!  Starting normal IPython.')
            return IPShell
        
        special_opts.remove('pylab')
        # If there's any option left, it means the user wants to force the
        # threading backend, else it's auto-selected from the rc file
        if special_opts:
            th_mode = special_opts.pop()
            matplotlib.rcParams['backend'] = backends[th_mode]
        else:
            backend = matplotlib.rcParams['backend']
            if backend.startswith('GTK'):
                th_mode = 'gthread'
            elif backend.startswith('WX'):
                th_mode = 'wthread'
            elif backend.startswith('Qt4'):
                th_mode = 'q4thread'
            elif backend.startswith('Qt'):
                th_mode = 'qthread'
            else:
                # Any other backend, use plain Tk
                th_mode = 'tkthread'
                
        return mpl_shell[th_mode]
    else:
        # No pylab requested, just plain threads
        try:
            th_mode = special_opts.pop()
        except KeyError:
            th_mode = 'tkthread'
        return th_shell[th_mode]


# This is the one which should be called by external code.
def start(user_ns = None):
    """Return a running shell instance, dealing with threading options.

    This is a factory function which will instantiate the proper IPython shell
    based on the user's threading choice.  Such a selector is needed because
    different GUI toolkits require different thread handling details."""

    shell = _select_shell(sys.argv)
    return shell(user_ns = user_ns)

# Some aliases for backwards compatibility
IPythonShell = IPShell
IPythonShellEmbed = IPShellEmbed
#************************ End of file <Shell.py> ***************************

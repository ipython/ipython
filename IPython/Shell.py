# -*- coding: utf-8 -*-
"""IPython Shell classes.

All the matplotlib support code was co-developed with John Hunter,
matplotlib's author.

$Id: Shell.py 927 2005-12-08 23:19:59Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# Code begins
import __main__
import __builtin__
import sys
import os
import code
import threading
import signal

import IPython
from IPython.iplib import InteractiveShell
from IPython.ipmaker import make_IPython
from IPython.genutils import Term,warn,error,flag_calls
from IPython.Struct import Struct
from IPython.Magic import Magic
from IPython import ultraTB

# global flag to pass around information about Ctrl-C without exceptions
KBINT = False

# global flag to turn on/off Tk support.
USE_TK = False

#-----------------------------------------------------------------------------
# This class is trivial now, but I want to have it in to publish a clean
# interface. Later when the internals are reorganized, code that uses this
# shouldn't have to change.

class IPShell:
    """Create an IPython instance."""
    
    def __init__(self,argv=None,user_ns=None,debug=1,
                 shell_class=InteractiveShell):
        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class)

    def mainloop(self,sys_exit=0,banner=None):
        self.IP.mainloop(banner)
        if sys_exit:
            sys.exit()

#-----------------------------------------------------------------------------
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

    def __init__(self,argv=None,banner='',exit_msg=None,rc_override=None):
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
        
        # FIXME. Passing user_ns breaks namespace handling.
        #self.IP = make_IPython(argv,user_ns=__main__.__dict__)
        self.IP = make_IPython(argv,rc_override=rc_override,embedded=True)

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

        # Allow the dummy parameter to override the global __dummy_mode
        if dummy or (dummy != 0 and self.__dummy_mode):
            return

        # Set global subsystems (display,completions) to our values
        sys.displayhook = self.sys_displayhook_embed
        if self.IP.has_readline:
            self.IP.readline.set_completer(self.IP.Completer.complete)

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

        if dummy not in [0,1]:
            raise ValueError,'dummy parameter must be 0 or 1'
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
def sigint_handler (signum,stack_frame):
    """Sigint handler for threaded apps.

    This is a horrible hack to pass information about SIGINT _without_ using
    exceptions, since I haven't been able to properly manage cross-thread
    exceptions in GTK/WX.  In fact, I don't think it can be done (or at least
    that's my understanding from a c.l.py thread where this was discussed)."""

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

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None, banner2='',**kw):
        """Similar to the normal InteractiveShell, but with threading control"""
        
        IPython.iplib.InteractiveShell.__init__(self,name,usage,rc,user_ns,banner2)

        # Locking control variable
        self.thread_ready = threading.Condition()

        # Stuff to do at closing time
        self._kill = False
        on_kill = kw.get('on_kill')
        if on_kill is None:
            on_kill = []
        # Check that all things to kill are callable:
        for t in on_kill:
            if not callable(t):
                raise TypeError,'on_kill must be a list of callables'
        self.on_kill = on_kill

    def runsource(self, source, filename="<input>", symbol="single"):
        """Compile and run some source in the interpreter.

        Modified version of code.py's runsource(), to handle threading issues.
        See the original for full docstring details."""

        global KBINT
        
        # If Ctrl-C was typed, we reset the flag and return right away
        if KBINT:
            KBINT = False
            return False
        
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        # Store code in self, so the execution thread can handle it
        self.thread_ready.acquire()
        self.code_to_run = code
        self.thread_ready.wait()  # Wait until processed in timeout interval
        self.thread_ready.release()

        return False

    def runcode(self):
        """Execute a code object.

        Multithreaded wrapper around IPython's runcode()."""

        # lock thread-protected stuff
        self.thread_ready.acquire()

        # Install sigint handler
        try:
            signal.signal(signal.SIGINT, sigint_handler)
        except SystemError:
            # This happens under Windows, which seems to have all sorts
            # of problems with signal handling.  Oh well...
            pass

        if self._kill:
            print >>Term.cout, 'Closing threads...',
            Term.cout.flush()
            for tokill in self.on_kill:
                tokill()
            print >>Term.cout, 'Done.'

        # Run pending code by calling parent class
        if self.code_to_run is not None:
            self.thread_ready.notify()
            InteractiveShell.runcode(self,self.code_to_run)
            
        # We're done with thread-protected variables
        self.thread_ready.release()
        # This MUST return true for gtk threading to work
        return True

    def kill (self):
        """Kill the thread, returning when it has been shut down."""
        self.thread_ready.acquire()
        self._kill = True
        self.thread_ready.release()

class MatplotlibShellBase:
    """Mixin class to provide the necessary modifications to regular IPython
    shell classes for matplotlib support.

    Given Python's MRO, this should be used as the FIRST class in the
    inheritance hierarchy, so that it overrides the relevant methods."""
    
    def _matplotlib_config(self,name):
        """Return various items needed to setup the user's shell with matplotlib"""

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
        try:
            import matplotlib.pylab as pylab
            self.pylab = pylab
            self.pylab_name = 'pylab'
        except ImportError:
            import matplotlib.matlab as matlab            
            self.pylab = matlab
            self.pylab_name = 'matlab'

        self.pylab.show._needmain = False
        # We need to detect at runtime whether show() is called by the user.
        # For this, we wrap it into a decorator which adds a 'called' flag.
        self.pylab.draw_if_interactive = flag_calls(self.pylab.draw_if_interactive)

        # Build a user namespace initialized with matplotlib/matlab features.
        user_ns = {'__name__':'__main__',
                   '__builtins__' : __builtin__ }

        # Be careful not to remove the final \n in the code string below, or
        # things will break badly with py22 (I think it's a python bug, 2.3 is
        # OK).
        pname = self.pylab_name # Python can't interpolate dotted var names
        exec ("import matplotlib\n"
              "import matplotlib.%(pname)s as %(pname)s\n"
              "from matplotlib.%(pname)s import *\n" % locals()) in user_ns
        
        # Build matplotlib info banner
        b="""
  Welcome to pylab, a matplotlib-based Python environment.
  For more information, type 'help(pylab)'.
"""
        return user_ns,b

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
                 user_ns = None, **kw):
        user_ns,b2 = self._matplotlib_config(name)
        InteractiveShell.__init__(self,name,usage,rc,user_ns,banner2=b2,**kw)

class MatplotlibMTShell(MatplotlibShellBase,MTInteractiveShell):
    """Multi-threaded shell with matplotlib support."""

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None, **kw):
        user_ns,b2 = self._matplotlib_config(name)
        MTInteractiveShell.__init__(self,name,usage,rc,user_ns,banner2=b2,**kw)

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
    import wxPython
    ver = wxPython.__version__
    orig_mainloop = None
    if ver[:3] >= '2.5':
        import wx
        if hasattr(wx, '_core_'): core = getattr(wx, '_core_')
        elif hasattr(wx, '_core'): core = getattr(wx, '_core')
        else: raise AttributeError('Could not find wx core module')
        orig_mainloop = core.PyApp_MainLoop
        core.PyApp_MainLoop = dummy_mainloop
    elif ver[:3] == '2.4':
        orig_mainloop = wxPython.wxc.wxPyApp_MainLoop
        wxPython.wxc.wxPyApp_MainLoop = dummy_mainloop
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

#-----------------------------------------------------------------------------
# The IPShell* classes below are the ones meant to be run by external code as
# IPython instances.  Note that unless a specific threading strategy is
# desired, the factory function start() below should be used instead (it
# selects the proper threaded class).

class IPShellGTK(threading.Thread):
    """Run a gtk mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,debug=1,
                 shell_class=MTInteractiveShell):

        import gtk
        
        self.gtk = gtk
        self.gtk_mainloop = hijack_gtk()

        # Allows us to use both Tk and GTK.
        self.tk = get_tk()
        
        if gtk.pygtk_version >= (2,4,0): mainquit = self.gtk.main_quit
        else:                            mainquit = self.gtk.mainquit

        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class,
                               on_kill=[mainquit])

        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 

        threading.Thread.__init__(self)

    def run(self):
        self.IP.mainloop(self._banner)
        self.IP.kill()

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
                    self.gtk.threads_init()
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
        self.gtk.threads_enter()
        self.gtk_mainloop()
        self.gtk.threads_leave()
        self.join()

    def on_timer(self):
        update_tk(self.tk)
        return self.IP.runcode()
        

class IPShellWX(threading.Thread):
    """Run a wx mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,debug=1,
                 shell_class=MTInteractiveShell):

        import wxPython.wx as wx

        threading.Thread.__init__(self)
        self.wx = wx
        self.wx_mainloop = hijack_wx()

        # Allows us to use both Tk and GTK.
        self.tk = get_tk()
        
        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class,
                               on_kill=[self.wxexit])
        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 

        self.app = None

    def wxexit(self, *args):
        if self.app is not None:
            self.app.agent.timer.Stop()
            self.app.ExitMainLoop()

    def run(self):
        self.IP.mainloop(self._banner)
        self.IP.kill()

    def mainloop(self,sys_exit=0,banner=None):

        self._banner = banner
        
        self.start()

        class TimerAgent(self.wx.wxMiniFrame):
            wx = self.wx
            IP = self.IP
            tk = self.tk
            def __init__(self, parent, interval):
                style = self.wx.wxDEFAULT_FRAME_STYLE | self.wx.wxTINY_CAPTION_HORIZ
                self.wx.wxMiniFrame.__init__(self, parent, -1, ' ', pos=(200, 200),
                                             size=(100, 100),style=style)
                self.Show(False)
                self.interval = interval
                self.timerId = self.wx.wxNewId()                                

            def StartWork(self):
                self.timer = self.wx.wxTimer(self, self.timerId)
                self.wx.EVT_TIMER(self,  self.timerId, self.OnTimer)
                self.timer.Start(self.interval)

            def OnTimer(self, event):
                update_tk(self.tk)
                self.IP.runcode()

        class App(self.wx.wxApp):
            wx = self.wx
            TIMEOUT = self.TIMEOUT
            def OnInit(self):
                'Create the main window and insert the custom frame'
                self.agent = TimerAgent(None, self.TIMEOUT)
                self.agent.Show(self.wx.false)
                self.agent.StartWork()
                return self.wx.true
        
        self.app = App(redirect=False)
        self.wx_mainloop(self.app)
        self.join()


class IPShellQt(threading.Thread):
    """Run a Qt event loop in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    Qt timer / slot."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,debug=0,
                 shell_class=MTInteractiveShell):
        
        import qt

        class newQApplication:
            def __init__( self ):
                self.QApplication = qt.QApplication
                
            def __call__( *args, **kwargs ):
                return qt.qApp

            def exec_loop( *args, **kwargs ):
                pass

            def __getattr__( self, name ):
                return getattr( self.QApplication, name )
          
        qt.QApplication = newQApplication()

        # Allows us to use both Tk and QT.
        self.tk = get_tk()

        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class,
                               on_kill=[qt.qApp.exit])

        # HACK: slot for banner in self; it will be passed to the mainloop
        # method only and .run() needs it.  The actual value will be set by
        # .mainloop().
        self._banner = None 
        
        threading.Thread.__init__(self)

    def run(self):
        self.IP.mainloop(self._banner)
        self.IP.kill()

    def mainloop(self,sys_exit=0,banner=None):

        import qt

        self._banner = banner

        if qt.QApplication.startingUp():
          a = qt.QApplication.QApplication(sys.argv)
        self.timer = qt.QTimer()
        qt.QObject.connect( self.timer, qt.SIGNAL( 'timeout()' ), self.on_timer )

        self.start()
        self.timer.start( self.TIMEOUT, True )
        while True:
            if self.IP._kill: break
            qt.qApp.exec_loop()
        self.join()

    def on_timer(self):
        update_tk(self.tk)
        result = self.IP.runcode()
        self.timer.start( self.TIMEOUT, True )
        return result

# A set of matplotlib public IPython shell classes, for single-threaded
# (Tk* and FLTK* backends) and multithreaded (GTK* and WX* backends) use.
class IPShellMatplotlib(IPShell):
    """Subclass IPShell with MatplotlibShell as the internal shell.

    Single-threaded class, meant for the Tk* and FLTK* backends.

    Having this on a separate class simplifies the external driver code."""
    
    def __init__(self,argv=None,user_ns=None,debug=1):
        IPShell.__init__(self,argv,user_ns,debug,shell_class=MatplotlibShell)

class IPShellMatplotlibGTK(IPShellGTK):
    """Subclass IPShellGTK with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the GTK* backends."""
    
    def __init__(self,argv=None,user_ns=None,debug=1):
        IPShellGTK.__init__(self,argv,user_ns,debug,shell_class=MatplotlibMTShell)

class IPShellMatplotlibWX(IPShellWX):
    """Subclass IPShellWX with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the WX* backends."""
    
    def __init__(self,argv=None,user_ns=None,debug=1):
        IPShellWX.__init__(self,argv,user_ns,debug,shell_class=MatplotlibMTShell)

class IPShellMatplotlibQt(IPShellQt):
    """Subclass IPShellQt with MatplotlibMTShell as the internal shell.

    Multi-threaded class, meant for the Qt* backends."""
    
    def __init__(self,argv=None,user_ns=None,debug=1):
        IPShellQt.__init__(self,argv,user_ns,debug,shell_class=MatplotlibMTShell)

#-----------------------------------------------------------------------------
# Factory functions to actually start the proper thread-aware shell

def _matplotlib_shell_class():
    """Factory function to handle shell class selection for matplotlib.

    The proper shell class to use depends on the matplotlib backend, since
    each backend requires a different threading strategy."""

    try:
        import matplotlib
    except ImportError:
        error('matplotlib could NOT be imported!  Starting normal IPython.')
        sh_class = IPShell
    else:
        backend = matplotlib.rcParams['backend']
        if backend.startswith('GTK'):
            sh_class = IPShellMatplotlibGTK
        elif backend.startswith('WX'):
            sh_class = IPShellMatplotlibWX
        elif backend.startswith('Qt'):
            sh_class = IPShellMatplotlibQt
        else:
            sh_class = IPShellMatplotlib
    #print 'Using %s with the %s backend.' % (sh_class,backend) # dbg
    return sh_class

# This is the one which should be called by external code.
def start():
    """Return a running shell instance, dealing with threading options.

    This is a factory function which will instantiate the proper IPython shell
    based on the user's threading choice.  Such a selector is needed because
    different GUI toolkits require different thread handling details."""

    global USE_TK
    # Crude sys.argv hack to extract the threading options.
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            arg2 = sys.argv[2]
            if arg2.endswith('-tk'):
                USE_TK = True
        arg1 = sys.argv[1]
        if arg1.endswith('-gthread'):
            shell = IPShellGTK
        elif arg1.endswith( '-qthread' ):
            shell = IPShellQt
        elif arg1.endswith('-wthread'):
            shell = IPShellWX
        elif arg1.endswith('-pylab'):
            shell = _matplotlib_shell_class()
        else:
            shell = IPShell
    else:
        shell = IPShell
    return shell()

# Some aliases for backwards compatibility
IPythonShell = IPShell
IPythonShellEmbed = IPShellEmbed
#************************ End of file <Shell.py> ***************************

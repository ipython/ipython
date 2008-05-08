import sys

from twisted.internet import reactor, threads

from IPython.ipmaker import make_IPython
from IPython.iplib import InteractiveShell 
from IPython.ipstruct import Struct
import Queue,thread,threading,signal
from signal import signal, SIGINT
from IPython.genutils import Term,warn,error,flag_calls, ask_yes_no
import shellglobals

def install_gtk2():
    """ Install gtk2 reactor, needs to be called bef """
    from twisted.internet import gtk2reactor
    gtk2reactor.install()


def hijack_reactor():
    """Modifies Twisted's reactor with a dummy so user code does
    not block IPython.  This function returns the original
    'twisted.internet.reactor' that has been hijacked.

    NOTE: Make sure you call this *AFTER* you've installed
    the reactor of your choice.
    """
    from twisted import internet
    orig_reactor = internet.reactor

    class DummyReactor(object):
        def run(self):
            pass
        def __getattr__(self, name):
            return getattr(orig_reactor, name)
        def __setattr__(self, name, value):
            return setattr(orig_reactor, name, value)
    
    internet.reactor = DummyReactor()
    return orig_reactor

class TwistedInteractiveShell(InteractiveShell):
    """Simple multi-threaded shell."""

    # Threading strategy taken from:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65109, by Brian
    # McErlean and John Finlay.  Modified with corrections by Antoon Pardon,
    # from the pygtk mailing list, to avoid lockups with system calls.

    # class attribute to indicate whether the class supports threads or not.
    # Subclasses with thread support should override this as needed.
    isthreaded = True

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns=None,user_global_ns=None,banner2='',**kw):
        """Similar to the normal InteractiveShell, but with threading control"""
        
        InteractiveShell.__init__(self,name,usage,rc,user_ns,
                                  user_global_ns,banner2)


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
        self.reactor_started = False
        self.first_run = True
        
    def runsource(self, source, filename="<input>", symbol="single"):
        """Compile and run some source in the interpreter.

        Modified version of code.py's runsource(), to handle threading issues.
        See the original for full docstring details."""
        
        # If Ctrl-C was typed, we reset the flag and return right away
        if shellglobals.KBINT:
            shellglobals.KBINT = False
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

        # shortcut - if we are in worker thread, or the worker thread is not running, 
        # execute directly (to allow recursion and prevent deadlock if code is run early 
        # in IPython construction)
        
        if (not self.reactor_started or (self.worker_ident is None and not self.first_run) 
            or self.worker_ident == thread.get_ident() or shellglobals.run_in_frontend(source)):
            InteractiveShell.runcode(self,code)
            return

        # Case 3
        # Store code in queue, so the execution thread can handle it.
 
        self.first_run = False
        completed_ev, received_ev = threading.Event(), threading.Event() 
        
        self.code_queue.put((code,completed_ev, received_ev))

        reactor.callLater(0.0,self.runcode)
        received_ev.wait(5)
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

        # Install SIGINT handler.  We do it every time to ensure that if user
        # code modifies it, we restore our own handling.
        try:
            pass
            signal(SIGINT,shellglobals.sigint_handler)
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
            # protect against asynchronous exceptions, to ensure that a shellglobals.KBINT
            # at the wrong time doesn't deadlock everything.  The global
            # CODE_TO_RUN is set to true/false as close as possible to the
            # runcode() call, so that the KBINT handler is correctly informed.
            try:
                try:
                   shellglobals.CODE_RUN = True
                   InteractiveShell.runcode(self,code_to_run)
                except KeyboardInterrupt:
                   print "Keyboard interrupted in mainloop"
                   while not self.code_queue.empty():
                      code = self.code_queue.get_nowait()
                   break
            finally:
                shellglobals.CODE_RUN = False
                # allow runsource() return from wait
                completed_ev.set()                
        
        # This MUST return true for gtk threading to work
        return True

    def kill(self):
        """Kill the thread, returning when it has been shut down."""
        self._kill = threading.Event()
        reactor.callLater(0.0,self.runcode)
        self._kill.wait()



class IPShellTwisted:
    """Run a Twisted reactor while in an IPython session.

    Python commands can be passed to the thread where they will be
    executed.  This is implemented by periodically checking for
    passed code using a Twisted reactor callback.
    """

    TIMEOUT = 0.01 # Millisecond interval between reactor runs.

    def __init__(self, argv=None, user_ns=None, debug=1,
                 shell_class=TwistedInteractiveShell):

        from twisted.internet import reactor
        self.reactor = hijack_reactor()

        mainquit = self.reactor.stop

        # Make sure IPython keeps going after reactor stop.
        def reactorstop():
            pass
        self.reactor.stop = reactorstop
        reactorrun_orig = self.reactor.run
        self.quitting = False
        def reactorrun():
            while True and not self.quitting:
                reactorrun_orig()
        self.reactor.run = reactorrun
        
        self.IP = make_IPython(argv, user_ns=user_ns, debug=debug,
                               shell_class=shell_class,
                               on_kill=[mainquit])

        # threading.Thread.__init__(self)

    def run(self):
        self.IP.mainloop()
        self.quitting = True
        self.IP.kill()

    def mainloop(self):
        def mainLoopThreadDeath(r):
            print "mainLoopThreadDeath: ", str(r)
        def spawnMainloopThread():
            d=threads.deferToThread(self.run)
            d.addBoth(mainLoopThreadDeath)
        reactor.callWhenRunning(spawnMainloopThread)
        self.IP.reactor_started = True
        self.reactor.run()
        print "mainloop ending...."   
        
exists = True


if __name__ == '__main__':
    # Sample usage.

    # Create the shell object. This steals twisted.internet.reactor
    # for its own purposes, to make sure you've already installed a
    # reactor of your choice.
    shell = IPShellTwisted(
        argv=[],
        user_ns={'__name__': '__example__',
                 'hello': 'world',
                 },
        )

    # Run the mainloop.  This runs the actual reactor.run() method.
    # The twisted.internet.reactor object at this point is a dummy
    # object that passes through to the actual reactor, but prevents
    # run() from being called on it again.
    shell.mainloop()

    # You must exit IPython to terminate your program.
    print 'Goodbye!'


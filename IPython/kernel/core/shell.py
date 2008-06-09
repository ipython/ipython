# encoding: utf-8
# -*- test-case-name: IPython.test.test_shell -*-

"""The core IPython Shell"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import pprint
import signal
import sys
import threading
import time

from code import InteractiveConsole, softspace
from StringIO import StringIO

from IPython.OutputTrap import OutputTrap
from IPython import ultraTB

from IPython.kernel.error import NotDefined


class InteractiveShell(InteractiveConsole):
    """The Basic IPython Shell class.  
    
    This class provides the basic capabilities of IPython.  Currently
    this class does not do anything IPython specific.  That is, it is
    just a python shell.
    
    It is modelled on code.InteractiveConsole, but adds additional
    capabilities.  These additional capabilities are what give IPython
    its power.  
    
    The current version of this class is meant to be a prototype that guides
    the future design of the IPython core.  This class must not use Twisted
    in any way, but it must be designed in a way that makes it easy to 
    incorporate into Twisted and hook network protocols up to.  
    
    Some of the methods of this class comprise the official IPython core
    interface.  These methods must be tread safe and they must return types
    that can be easily serialized by protocols such as PB, XML-RPC and SOAP.
    Locks have been provided for making the methods thread safe, but additional
    locks can be added as needed.
      
    Any method that is meant to be a part of the official interface must also
    be declared in the kernel.coreservice.ICoreService interface.  Eventually
    all other methods should have single leading underscores to note that they
    are not designed to be 'public.'  Currently, because this class inherits
    from code.InteractiveConsole there are many private methods w/o leading
    underscores.  The interface should be as simple as possible and methods 
    should not be added to the interface unless they really need to be there.   
    
    Note:
    
    - For now I am using methods named put/get to move objects in/out of the
      users namespace.  Originally, I was calling these methods push/pull, but
      because code.InteractiveConsole already has a push method, I had to use
      something different.  Eventually, we probably won't subclass this class
      so we can call these methods whatever we want.  So, what do we want to
      call them?
    - We need a way of running the trapping of stdout/stderr in different ways.
      We should be able to i) trap, ii) not trap at all or iii) trap and echo
      things to stdout and stderr.
    - How should errors be handled?  Should exceptions be raised?
    - What should methods that don't compute anything return?  The default of 
      None?
    """
     
    def __init__(self, locals=None, filename="<console>"):
        """Creates a new TrappingInteractiveConsole object."""
        InteractiveConsole.__init__(self,locals,filename)
        self._trap = OutputTrap(debug=0)
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self._last_type = self._last_traceback = self._last_value = None
        #self._namespace_lock = threading.Lock()
        #self._command_lock = threading.Lock()
        self.lastCommandIndex = -1
        # I am using this user defined signal to interrupt the currently 
        # running command.  I am not sure if this is the best way, but
        # it is working!
        # This doesn't work on Windows as it doesn't have this signal.
        #signal.signal(signal.SIGUSR1, self._handleSIGUSR1)

        # An exception handler.  Experimental: later we need to make the
        # modes/colors available to user configuration, etc.
        self.tbHandler = ultraTB.FormattedTB(color_scheme='NoColor',
                                             mode='Context',
                                             tb_offset=2)

    def _handleSIGUSR1(self, signum, frame):
        """Handle the SIGUSR1 signal by printing to stderr."""
        print>>sys.stderr, "Command stopped."
        
    def _prefilter(self, line, more):
        return line

    def _trapRunlines(self, lines):
        """
        This executes the python source code, source, in the
        self.locals namespace and traps stdout and stderr.  Upon
        exiting, self.out and self.err contain the values of 
        stdout and stderr for the last executed command only.
        """
        
        # Execute the code
        #self._namespace_lock.acquire()
        self._trap.flush()
        self._trap.trap()
        self._runlines(lines)
        self.lastCommandIndex += 1
        self._trap.release()
        #self._namespace_lock.release()
                
        # Save stdin, stdout and stderr to lists
        #self._command_lock.acquire()
        self._stdin.append(lines)
        self._stdout.append(self.prune_output(self._trap.out.getvalue()))
        self._stderr.append(self.prune_output(self._trap.err.getvalue()))
        #self._command_lock.release()

    def prune_output(self, s):
        """Only return the first and last 1600 chars of stdout and stderr.
        
        Something like this is required to make sure that the engine and
        controller don't become overwhelmed by the size of stdout/stderr.
        """
        if len(s) > 3200:
            return s[:1600] + '\n............\n' + s[-1600:]
        else: 
            return s

    # Lifted from iplib.InteractiveShell
    def _runlines(self,lines):
        """Run a string of one or more lines of source.

        This method is capable of running a string containing multiple source
        lines, as if they had been entered at the IPython prompt.  Since it
        exposes IPython's processing machinery, the given strings can contain
        magic calls (%magic), special shell access (!cmd), etc."""

        # We must start with a clean buffer, in case this is run from an
        # interactive IPython session (via a magic, for example).
        self.resetbuffer()
        lines = lines.split('\n')
        more = 0
        for line in lines:
            # skip blank lines so we don't mess up the prompt counter, but do
            # NOT skip even a blank line if we are in a code block (more is
            # true)
            if line or more:
                more = self.push((self._prefilter(line,more)))
                # IPython's runsource returns None if there was an error
                # compiling the code.  This allows us to stop processing right
                # away, so the user gets the error message at the right place.
                if more is None:
                    break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            self.push('\n')

    def runcode(self, code):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to
        display a traceback.  All exceptions are caught except
        SystemExit, which is reraised.

        A note about KeyboardInterrupt: this exception may occur
        elsewhere in this code, and may not always be caught.  The
        caller should be prepared to deal with it.

        """

        self._last_type = self._last_traceback = self._last_value = None
        try:
            exec code in self.locals
        except:
            # Since the exception info may need to travel across the wire, we
            # pack it in right away.  Note that we are abusing the exception
            # value to store a fully formatted traceback, since the stack can
            # not be serialized for network transmission.
            et,ev,tb = sys.exc_info()
            self._last_type = et
            self._last_traceback = tb
            tbinfo = self.tbHandler.text(et,ev,tb)
            # Construct a meaningful traceback message for shipping over the
            # wire.
            buf = pprint.pformat(self.buffer)
            try:
                ename = et.__name__
            except:
                ename = et
            msg = """\
%(ev)s            
***************************************************************************
An exception occurred in an IPython engine while executing user code.

Current execution buffer (lines being run):
%(buf)s

A full traceback from the actual engine:
%(tbinfo)s
***************************************************************************
            """ % locals()
            self._last_value = msg
        else:
            if softspace(sys.stdout, 0):
                print

    ##################################################################
    # Methods that are a part of the official interface
    #
    # These methods should also be put in the 
    # kernel.coreservice.ICoreService interface.
    #
    # These methods must conform to certain restrictions that allow
    # them to be exposed to various network protocols:
    #
    # - As much as possible, these methods must return types that can be 
    #   serialized by PB, XML-RPC and SOAP.  None is OK.
    # - Every method must be thread safe.  There are some locks provided
    #   for this purpose, but new, specialized locks can be added to the
    #   class.
    ##################################################################
    
    # Methods for running code

    def exc_info(self):
        """Return exception information much like sys.exc_info().

        This method returns the same (etype,evalue,tb) tuple as sys.exc_info,
        but from the last time that the engine had an exception fire."""

        return self._last_type,self._last_value,self._last_traceback
    
    def execute(self, lines):
        self._trapRunlines(lines)
        if self._last_type is None:
            return self.getCommand()
        else:
            raise self._last_type(self._last_value)
        
    # Methods for working with the namespace

    def put(self, key, value):
        """Put value into locals namespace with name key.
        
        I have often called this push(), but in this case the
        InteractiveConsole class already defines a push() method that
        is different.
        """          
                  
        if not isinstance(key, str):
            raise TypeError, "Objects must be keyed by strings."
        self.update({key:value})

    def get(self, key):
        """Gets an item out of the self.locals dict by key.
        
        Raise NameError if the object doesn't exist.
        
        I have often called this pull().  I still like that better.
        """
        
        class NotDefined(object):
            """A class to signify an objects that is not in the users ns."""
            pass
        
        if not isinstance(key, str):
            raise TypeError, "Objects must be keyed by strings."
        result = self.locals.get(key, NotDefined())
        if isinstance(result, NotDefined):
            raise NameError('name %s is not defined' % key)
        else:
            return result


    def update(self, dictOfData):
        """Loads a dict of key value pairs into the self.locals namespace."""
        if not isinstance(dictOfData, dict):
            raise TypeError, "update() takes a dict object."
        #self._namespace_lock.acquire()
        self.locals.update(dictOfData)
        #self._namespace_lock.release()
        
    # Methods for getting stdout/stderr/stdin
           
    def reset(self):
        """Reset the InteractiveShell."""
        
        #self._command_lock.acquire()        
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self.lastCommandIndex = -1
        #self._command_lock.release()

        #self._namespace_lock.acquire()
        # preserve id, mpi objects
        mpi = self.locals.get('mpi', None)
        id = self.locals.get('id', None)
        del self.locals
        self.locals = {'mpi': mpi, 'id': id}
        #self._namespace_lock.release()
                
    def getCommand(self,i=None):
        """Get the stdin/stdout/stderr of command i."""
        
        #self._command_lock.acquire()
        
        
        if i is not None and not isinstance(i, int):
            raise TypeError("Command index not an int: " + str(i))
            
        if i in range(self.lastCommandIndex + 1):
            inResult = self._stdin[i]
            outResult = self._stdout[i]
            errResult = self._stderr[i]
            cmdNum = i
        elif i is None and self.lastCommandIndex >= 0:
            inResult = self._stdin[self.lastCommandIndex]
            outResult = self._stdout[self.lastCommandIndex]
            errResult = self._stderr[self.lastCommandIndex]
            cmdNum = self.lastCommandIndex
        else:
            inResult = None
            outResult = None
            errResult = None
        
        #self._command_lock.release()
        
        if inResult is not None:
            return dict(commandIndex=cmdNum, stdin=inResult, stdout=outResult, stderr=errResult)
        else:
            raise IndexError("Command with index %s does not exist" % str(i))
            
    def getLastCommandIndex(self):
        """Get the index of the last command."""
        #self._command_lock.acquire()
        ind = self.lastCommandIndex
        #self._command_lock.release()
        return ind


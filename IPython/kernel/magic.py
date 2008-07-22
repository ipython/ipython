# encoding: utf-8

"""Magic command interface for interactive parallel work."""

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

import new

from IPython.iplib import InteractiveShell
from IPython.Shell import MTInteractiveShell

from twisted.internet.defer import Deferred


#-------------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-------------------------------------------------------------------------------

NO_ACTIVE_CONTROLLER = """
Error:  No Controller is activated
Use activate() on a RemoteController object to activate it for magics.
"""

def magic_result(self,parameter_s=''):
    """Print the result of command i on all engines of the active controller.
    
    To activate a controller in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
    
    >>> result                                # Print the latest result
    Printing result... 
    [127.0.0.1:0] In [1]: b = 10
    [127.0.0.1:1] In [1]: b = 10
    
    >>> result 0                              # Print result 0
    In [14]: result 0
    Printing result... 
    [127.0.0.1:0] In [0]: a = 5
    [127.0.0.1:1] In [0]: a = 5
    """
    try:
        activeController = __IPYTHON__.activeController
    except AttributeError:
        print NO_ACTIVE_CONTROLLER
    else:
        try:
            index = int(parameter_s)
        except:
            index = None
        result = activeController.get_result(index)
        return result

def magic_px(self,parameter_s=''):
    """Executes the given python command on the active IPython Controller.
    
    To activate a Controller in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    >>> %px a = 5       # Runs a = 5 on all nodes
    """

    try:
        activeController = __IPYTHON__.activeController
    except AttributeError:
        print NO_ACTIVE_CONTROLLER
    else:
        print "Parallel execution on engines: %s" % activeController.targets
        result = activeController.execute(parameter_s)
        return result

def pxrunsource(self, source, filename="<input>", symbol="single"):

    try:
        code = self.compile(source, filename, symbol)
    except (OverflowError, SyntaxError, ValueError):
        # Case 1
        self.showsyntaxerror(filename)
        return None

    if code is None:
        # Case 2
        return True

    # Case 3
    # Because autopx is enabled, we now call executeAll or disable autopx if
    # %autopx or autopx has been called
    if '_ip.magic("%autopx' in source or '_ip.magic("autopx' in source:
        _disable_autopx(self)
        return False
    else:
        try:
            result = self.activeController.execute(source)
        except:
            self.showtraceback()
        else:
            print result.__repr__()
        return False
        
def magic_autopx(self, parameter_s=''):
    """Toggles auto parallel mode for the active IPython Controller.
    
    To activate a Controller in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    >>> %autopx                    # Now all commands are executed in parallel
    Auto Parallel Enabled
    Type %autopx to disable
    ...
    >>> %autopx                    # Now all commands are locally executed
    Auto Parallel Disabled
    """
  
    if hasattr(self, 'autopx'):
        if self.autopx == True:
            _disable_autopx(self)
        else:
            _enable_autopx(self)
    else:
        _enable_autopx(self)

def _enable_autopx(self):
    """Enable %autopx mode by saving the original runsource and installing 
    pxrunsource.
    """
    try:
        activeController = __IPYTHON__.activeController
    except AttributeError:
        print "No active RemoteController found, use RemoteController.activate()."
    else:
        self._original_runsource = self.runsource
        self.runsource = new.instancemethod(pxrunsource, self, self.__class__)
        self.autopx = True
        print "Auto Parallel Enabled\nType %autopx to disable"

def _disable_autopx(self):
    """Disable %autopx by restoring the original runsource."""
    if hasattr(self, 'autopx'):
        if self.autopx == True:
            self.runsource = self._original_runsource
            self.autopx = False
            print "Auto Parallel Disabled"
            
# Add the new magic function to the class dict:

InteractiveShell.magic_result = magic_result
InteractiveShell.magic_px = magic_px
InteractiveShell.magic_autopx = magic_autopx

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_result
del magic_px
del magic_autopx


"""Infrastructure for registering and firing callbacks.

Unlike :mod:`IPython.core.hooks`, which lets end users set single functions to
be called at specific times, or a collection of alternative methods to try,
callbacks are designed to be used by extension authors. A number of callbacks
can be registered for the same event without needing to be aware of one another.

The functions defined in this module are no-ops indicating the names of available
events and the arguments which will be passed to them.
"""
from __future__ import print_function

class CallbackManager(object):
    """Manage a collection of events and a sequence of callbacks for each.
    
    This is attached to :class:`~IPython.core.interactiveshell.InteractiveShell`
    instances as a ``callbacks`` attribute.
    """
    def __init__(self, shell, available_callbacks):
        """Initialise the :class:`CallbackManager`.
        
        Parameters
        ----------
        shell
          The :class:`~IPython.core.interactiveshell.InteractiveShell` instance
        available_callbacks
          An iterable of names for callback events.
        """
        self.shell = shell
        self.callbacks = {n:[] for n in available_callbacks}
    
    def register(self, name, function):
        """Register a new callback
        
        Parameters
        ----------
        name : str
          The event for which to register this callback.
        function : callable
          A function to be called on the given event. It should take the same
          parameters as the appropriate callback prototype.
        
        Raises
        ------
        TypeError
          If ``function`` is not callable.
        KeyError
          If ``name`` is not one of the known callback events.
        """
        if not callable(function):
            raise TypeError('Need a callable, got %r' % function)
        self.callbacks[name].append(function)
    
    def unregister(self, name, function):
        """Remove a callback from the given event."""
        self.callbacks[name].remove(function)
    
    def reset(self, name):
        """Clear all callbacks for the given event."""
        self.callbacks[name] = []
    
    def reset_all(self):
        """Clear all callbacks for all events."""
        self.callbacks = {n:[] for n in self.callbacks}
    
    def fire(self, name, *args, **kwargs):
        """Call callbacks for the event ``name``.
        
        Any additional arguments are passed to all callbacks registered for this
        event. Exceptions raised by callbacks are caught, and a message printed.
        """
        for func in self.callbacks[name]:
            try:
                func(*args, **kwargs)
            except Exception:
                print("Error in callback {} (for {}):".format(func, name))
                self.shell.showtraceback()

# event_name -> prototype mapping
available_callbacks = {}

def _collect(callback_proto):
    available_callbacks[callback_proto.__name__] = callback_proto
    return callback_proto

# ------------------------------------------------------------------------------
# Callback prototypes
#
# No-op functions which describe the names of available events and the
# signatures of callbacks for those events.
# ------------------------------------------------------------------------------

@_collect
def pre_execute():
    """Fires before code is executed in response to user/frontend action.
    
    This includes comm and widget messages as well as user code cells."""
    pass

@_collect
def pre_execute_explicit():
    """Fires before user-entered code runs."""
    pass

@_collect
def post_execute():
    """Fires after code is executed in response to user/frontend action.
    
    This includes comm and widget messages as well as user code cells."""
    pass

@_collect
def post_execute_explicit():
    """Fires after user-entered code runs."""
    pass

@_collect
def shell_initialised(ip):
    """Fires after initialisation of :class:`~IPython.core.interactiveshell.InteractiveShell`.
    
    This is before extensions and startup scripts are loaded, so it can only be
    set by subclassing.
    
    Parameters
    ----------
    ip : :class:`~IPython.core.interactiveshell.InteractiveShell`
      The newly initialised shell.
    """
    pass

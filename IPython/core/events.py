"""Infrastructure for registering and firing callbacks on application events.

Unlike :mod:`IPython.core.hooks`, which lets end users set single functions to
be called at specific times, or a collection of alternative methods to try,
callbacks are designed to be used by extension authors. A number of callbacks
can be registered for the same event without needing to be aware of one another.

The functions defined in this module are no-ops indicating the names of available
events and the arguments which will be passed to them.

.. note::

   This API is experimental in IPython 2.0, and may be revised in future versions.
"""
from __future__ import print_function

class EventManager(object):
    """Manage a collection of events and a sequence of callbacks for each.
    
    This is attached to :class:`~IPython.core.interactiveshell.InteractiveShell`
    instances as an ``events`` attribute.
    
    .. note::

       This API is experimental in IPython 2.0, and may be revised in future versions.
    """
    def __init__(self, shell, available_events):
        """Initialise the :class:`CallbackManager`.
        
        Parameters
        ----------
        shell
          The :class:`~IPython.core.interactiveshell.InteractiveShell` instance
        available_callbacks
          An iterable of names for callback events.
        """
        self.shell = shell
        self.callbacks = {n:[] for n in available_events}
    
    def register(self, event, function):
        """Register a new event callback
        
        Parameters
        ----------
        event : str
          The event for which to register this callback.
        function : callable
          A function to be called on the given event. It should take the same
          parameters as the appropriate callback prototype.
        
        Raises
        ------
        TypeError
          If ``function`` is not callable.
        KeyError
          If ``event`` is not one of the known events.
        """
        if not callable(function):
            raise TypeError('Need a callable, got %r' % function)
        self.callbacks[event].append(function)
    
    def unregister(self, event, function):
        """Remove a callback from the given event."""
        self.callbacks[event].remove(function)
    
    def trigger(self, event, *args, **kwargs):
        """Call callbacks for ``event``.
        
        Any additional arguments are passed to all callbacks registered for this
        event. Exceptions raised by callbacks are caught, and a message printed.
        """
        for func in self.callbacks[event][:]:
            try:
                func(*args, **kwargs)
            except Exception:
                print("Error in callback {} (for {}):".format(func, event))
                self.shell.showtraceback()

# event_name -> prototype mapping
available_events = {}

def _define_event(callback_proto):
    available_events[callback_proto.__name__] = callback_proto
    return callback_proto

# ------------------------------------------------------------------------------
# Callback prototypes
#
# No-op functions which describe the names of available events and the
# signatures of callbacks for those events.
# ------------------------------------------------------------------------------

@_define_event
def pre_execute():
    """Fires before code is executed in response to user/frontend action.
    
    This includes comm and widget messages and silent execution, as well as user
    code cells."""
    pass

@_define_event
def pre_run_cell():
    """Fires before user-entered code runs."""
    pass

@_define_event
def post_execute():
    """Fires after code is executed in response to user/frontend action.
    
    This includes comm and widget messages and silent execution, as well as user
    code cells."""
    pass

@_define_event
def post_run_cell():
    """Fires after user-entered code runs."""
    pass

@_define_event
def shell_initialized(ip):
    """Fires after initialisation of :class:`~IPython.core.interactiveshell.InteractiveShell`.
    
    This is before extensions and startup scripts are loaded, so it can only be
    set by subclassing.
    
    Parameters
    ----------
    ip : :class:`~IPython.core.interactiveshell.InteractiveShell`
      The newly initialised shell.
    """
    pass

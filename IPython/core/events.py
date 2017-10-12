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

from backcall import callback_prototype


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
        self.callbacks[event].append(_adapt_function(event, function))
    
    def unregister(self, event, function):
        """Remove a callback from the given event."""
        self.callbacks[event].remove(_adapt_function(event, function))
    
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

# (event, function) -> adapted function mapping
adapted_functions = {}


def _define_event(callback_proto):
    available_events[callback_proto.__name__] = callback_proto
    return callback_proto


def _adapt_function(event, function):
    """Adapts and caches a function using `backcall` to provide compatibility.
    
    Function adaptations depend not only on the function but also on the event,
    as events may expect different arguments (e.g. `request` vs. `result`).
    Hence, `(event, function)` is used as the cache key.
    """
    if (event, function) in adapted_functions:
        return adapted_functions[(event, function)]
    callback_proto = available_events.get(event)
    adapted_function = callback_proto.adapt(function)
    adapted_functions[(event, function)] = adapted_function
    return adapted_function


# ------------------------------------------------------------------------------
# Callback prototypes
#
# No-op functions which describe the names of available events and the
# signatures of callbacks for those events.
# ------------------------------------------------------------------------------

@_define_event
@callback_prototype
def pre_execute(request):
    """Fires before code is executed in response to user/frontend action.
    
    This includes comm and widget messages and silent execution, as well as user
    code cells.

    Parameters
    ----------
    request : :class:`~IPython.core.interactiveshell.ExecutionRequest`
      The object representing the code execution request.
    """
    pass

@_define_event
@callback_prototype
def pre_run_cell(request):
    """Fires before user-entered code runs.

    Parameters
    ----------
    request : :class:`~IPython.core.interactiveshell.ExecutionRequest`
      The object representing the code execution request.
    """
    pass

@_define_event
@callback_prototype
def post_execute(result):
    """Fires after code is executed in response to user/frontend action.
    
    This includes comm and widget messages and silent execution, as well as user
    code cells.

    Parameters
    ----------
    result : :class:`~IPython.core.interactiveshell.ExecutionResult`
      The object which will be returned as the execution result.
    """
    pass

@_define_event
@callback_prototype
def post_run_cell(result):
    """Fires after user-entered code runs.

    Parameters
    ----------
    result : :class:`~IPython.core.interactiveshell.ExecutionResult`
      The object which will be returned as the execution result.
    """
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

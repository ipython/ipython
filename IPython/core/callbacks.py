from __future__ import print_function

class CallbackManager(object):
    def __init__(self, shell, available_callbacks):
        self.shell = shell
        self.callbacks = {n:[] for n in available_callbacks}
    
    def register(self, name, function):
        if not callable(function):
            raise TypeError('Need a callable, got %r' % function)
        self.callbacks[name].append(function)
    
    def unregister(self, name, function):
        self.callbacks[name].remove(function)
    
    def reset(self, name):
        self.callbacks[name] = []
    
    def reset_all(self):
        self.callbacks = {n:[] for n in self.callbacks}
    
    def fire(self, name, *args, **kwargs):
        for func in self.callbacks[name]:
            try:
                func(*args, **kwargs)
            except Exception:
                print("Error in callback {} (for {}):".format(func, name))
                self.shell.showtraceback()

available_callbacks = {}
def _collect(callback_proto):
    available_callbacks[callback_proto.__name__] = callback_proto
    return callback_proto

@_collect
def pre_execute():
    """Fires before code is executed in response to user/frontend action.
    
    This includes comm and widget messages."""
    pass

@_collect
def pre_execute_explicit():
    """Fires before user-entered code runs."""
    pass

@_collect
def post_execute():
    """Fires after code is executed in response to user/frontend action.
    
    This includes comm and widget messages."""
    pass

@_collect
def post_execute_explicit():
    """Fires after user-entered code runs."""
    pass
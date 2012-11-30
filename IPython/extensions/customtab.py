# -*- coding: utf-8 -*-
"""
Decorators for function specific tab competion
"""
import inspect

__all__ == ['tab_completion']


def tab_completion(**kwargs):
    """ Decorator to add special ipython tab completion to a function.
    
    Currently only static strings are supported as the values, but more will
    be added soon.
    
    Example
    -------
    >>> @tabcompletion(mode=['read', 'write'])
    >>> def loadfile(fname, mode='read'):
    ...     pass
    
    With this function, tab completion will recommend 'read' and 'write'
    when you're trying to ender the mode argument, like this:

    >>> loadfile('filename', mode=<TAB_CHARACTER>
    'read'   'write'

    Or like this:

    >>> loadfile('filename', <TAB_CHARACTER>
    'read'   'write'
    """
    
    def wrapper(wrapped):
        # check that each of the keys in kwargs are actually arguments taken
        # by wrapped()
        for key in kwargs:
            if not key in inspect.getargspec(wrapped).args:
                raise ValueError('%s is not an argument taken by %s' \
                    % (key, wrapped.__name__))
        
        wrapped.tab_completion = kwargs
        return wrapped

    return wrapper
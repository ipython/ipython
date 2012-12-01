# -*- coding: utf-8 -*-
"""
Decorators for function specific tab competion
"""
import inspect
import functools
import warnings

__all__ = ['tab_completion', 'annotate']

class AnnotationWarning(RuntimeWarning):
    pass

def annotate(**kwargs):
    """Decorator to annotate function arguments in Python 2.x. 
    Note, in Python3, this decorator is not required as the ability
    is built into the language. See PEP 3107 for details.
    
    Examples
    --------
    >>> @annotate(foo='bar', qux=str)
    >>> def f(foo, qux='hello'):
    ...    pass
    
    Is evalent to the following python3 code:
    >>> def f(foo : 'bar', qux : str = 'hello'):
    ...    pass
    """

    def wrapper(f):
        argspec = inspect.getargspec(f)
        for key in kwargs.iterkeys():
            if (key not in argspec.args) and (key != argspec.varargs) \
                    and (key != argspec.kwargs):
                raise ValueError('%s is not an argument taken by %s' \
                    % (key, wrapped.__name__))
                
            if hasattr(f, '__annotations__'):
                # check that the annotations being provided don't already exist
                # if they do, we warn and overwrite. this decorator does not
                # implement any scheme for composing annotations.
                if key in f.__annotations__:
                    warnings.warn('Overwriting annotation on %s' % key, 
                        AnnotationWarning)

        f.__annotations__ = kwargs
        return f

    return wrapper


class TabBase(object):
    def match(self, last_token):
        return []
    
class tab_glob(TabBase):
    def __init__(self, pattern):
        self.pattern = pattern 
        
class tab_instance(TabBase):
    def __init__(self, klass):
        self.klass = klass

class tab_literal(TabBase):
    def __init__(self, *completions):
        self.completions = completions
    
    def match(self, event):
        """Implements the IPython function specfic tab completion API
        
        Parameters
        ----------
        event : nametupled with keys 'text', 'line', 'tokens'
            event.text contains the current text being entered, which is
        """
        
        matches = []
        for cb in iter(self.completions):
            if event.tokens[-1] in [',', ' ', '=']:
                # this indicates that the token we're trying to tab
                # complete on hasn't started. i.e. the last token
                # that the user entered was, for instance, the comma
                # that ended the last arguments. So we need to show the
                # full list of recommended tab completions
                matches.append("'" + cb + "'")
        
            elif ("'" + cb).startswith(event.tokens[-1]):
                # adding "'" + cb + "'" to the matches when one quote
                # mark is already on the command line seems to cause
                # a two quote-marks to be inserted before cb.
                # this has to do with readline thinking that the quote
                # mark is a delimiter, but we're using it as part of the
                # token since we're trying to match string literals
                matches.append(cb)
        return matches

@annotate(filename=tab_glob('*.txt'), mode=tab_literal('read', 'write'))
def load(filename, mode):
    pass
    


# 
# def tab_completion(**kwargs):
#     """ Decorator to add special ipython tab completion to a function.
# 
#     Currently only static strings are supported as the values, but more will
#     be added soon.
# 
#     Example
#     -------
#     >>> @tabcompletion(mode=['read', 'write'])
#     >>> def loadfile(fname, mode='read'):
#     ...     pass
# 
#     With this function, tab completion will recommend 'read' and 'write'
#     when you're trying to ender the mode argument, like this:
# 
#     >>> loadfile('filename', mode=<TAB_CHARACTER>
#     'read'   'write'
# 
#     Or like this:
# 
#     >>> loadfile('filename', <TAB_CHARACTER>
#     'read'   'write'
#     """
# 
#     def wrapper(wrapped):
#         # check that each of the keys in kwargs are actually arguments taken
#         # by wrapped()
#         for key in kwargs:
#             if not key in inspect.getargspec(wrapped).args:
#                 raise ValueError('%s is not an argument taken by %s' \
#                     % (key, wrapped.__name__))
#     
#         wrapped.tab_completion = kwargs
#         return wrapped
# 
#     return wrapper
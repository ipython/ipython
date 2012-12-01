# -*- coding: utf-8 -*-
"""
Decorators for function specific tab competion
"""
import inspect
import functools
import warnings
import types
import glob
import abc


__all__ = ['annotate', 'tab_glob', 'tab_instance', 'tab_literal']


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
                        RuntimeWarning)

        f.__annotations__ = kwargs

        return f

    return wrapper


class TabBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def tab_matches(self, event):
        """Callback for the function-annotation tab completion system.
        
        If the user attempts to do a tab completion on an argument
        (to a function/method) that is annotated for tab completion,
        this callback will be executed.
        
        Parameters
        ----------
        event : nametuple
            event is a namedtuple containing four keys: 'text', 'tokens',
            'line', and 'ipcompleter'
            
        `Event` Attributes
        ------------------
        event.line : str
            event.line contains the full line entered by the IPython user.
        event.text : str
            event.text is the last portion of the line, formed by splitting
            the line on a set of python-language delimiters, and returning you
            the last portion.
        event.tokens : list of strings
            event.tokens is the result of running the python standard library
            tokenizer on event.line, and 
        
        """
        pass


class tab_literal(TabBase):

    def __init__(self, *completions):
        self.completions = completions

    def tab_matches(self, event):
        """Implements the IPython function specfic tab completion API

        Parameters
        ----------
        event : nametupled with keys 'text', 'line', 'tokens'
            event.text contains the current text being entered, which is
        """
        matches = []
        for cb in self.completions:
            if isinstance(cb, basestring):
                if event.tokens[-1] in [' ', '=', '(']:
                    matches.append("'%s'" % cb)
                elif event.tokens[-1] == ',':
                    matches.append(" '%s'" % cb)
                elif event.tokens[-2] == "'" and cb.startswith(event.text):
                    # adding "'" + cb + "'" to the matches when one quote
                    # mark is already on the command line seems to cause
                    # a two quote-marks to be inserted before cb.
                    # this has to do with readline thinking that the quote
                    # mark is a delimiter, but we're using it as part of the
                    # token since we're trying to match string literals

                    # note we're not returning strings that start with "'"...
                    matches.append(cb)
            else:
                str_cb = str(cb)
                if str_cb.startswith(event.text):
                    matches.append(str_cb)

        return matches


class tab_glob(TabBase):

    def __init__(self, glob_pattern):
        self.glob_pattern = glob_pattern

    def tab_matches(self, event):
        matches = []

        if event.tokens[-1] in [' ', '=', '(']:
            fmt = "'%s'"
        elif event.tokens[-1] == ',':
            fmt = " '%s'"
        else:
            fmt = '%s'

        file_matches = [fmt % m for m in glob.glob(event.text + self.glob_pattern)]
        dir_matches = [fmt % m for m in glob.glob(event.text + '*/')]

        return file_matches + dir_matches


class tab_instance(TabBase):

    def __init__(self, *klasses):
        self.klasses = set(klasses)

        # add some more default classes
        self.klasses.update([types.FunctionType, types.BuiltinFunctionType,
            types.TypeType, types.ModuleType])

    def tab_matches(self, event):
        matches = []
        for key in event.ipcompleter.python_matches(event.text):
            try:
                if any(isinstance(eval(key, event.ipcompleter.namespace), klass)
                        for klass in self.klasses):
                    matches.append(key)
            except:
                continue
        return matches


if __name__ == '__main__':
    # some testing code.

    @annotate(filename=['ignoreme!', tab_glob('*.txt')], mode=tab_literal('read', 'write', 1))
    def load0(mode, filename):
        pass

    @annotate(filename=['ignoreme!', tab_glob('*.txt')], mode=tab_literal('read', 'write', 1))
    def load(filename, mode):
        pass

    @annotate(filename=tab_literal(2234,233333,233322233333))
    def load2(filename, mode):
        pass


    @annotate(filename=tab_glob('*.txt'), mode=tab_instance(str))
    def load23(filename, mode):
        pass

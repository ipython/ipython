# -*- coding: utf-8 -*-
"""
Interact with the IPython tab completion system via function annotations.

For example (python3):

>>> def load(filename : tab_glob('*.txt'), mode):
...     pass

Will trigger the IPython tab completion system to recomment files ending in .txt
to you, when you're calling the load function interactively.
"""

import inspect
import functools
import warnings
import types
import glob
import abc
from IPython.core.completer import has_open_quotes


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


class AnnotationCompleterBase(object):
    """Abstract base class for IPython annotation based tab completion
    annotators
    """
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
            tokenizer on event.line. This is similar to splitting on
            delimiters as above, but slightly different for string literals in
            particular, where, for instance, '''a''' would be a single token.
        event.ipcompleter : IPython.core.completer.IPCompleter
            This is a reference back to the caller's class. You can use this
            to get access to more functions to aid in parsing the line,
            namespaces, to get configuration options from the IPython
            configuration system, etc.
        """
        pass


class tab_literal(AnnotationCompleterBase):
    """Annotation for function arguments that recommends completions from a
    set of enumerated literals. This is useful if you have an argumnet for a
    function that is designed to be called only with a small handful of possible
    values"""

    def __init__(self, *completions):
        """Set up a tab completion callback.

        Examples
        --------
        >>> def f(x : tab_literal(100, 200, 300)):
        ...    pass

        >>> f(1<TAB>
        will fill in the 100
        """
        self.completions = completions

    def tab_matches(self, event):
        """Callback for the IPython annoation tab-completion system
        """
        # the complicated stuff here is handling string literals, because we want
        # to make readline see the quotation marks, which it usually thinks are
        # just delimiters and doesn't deal with.
        matches = []
        for cb in self.completions:
            if isinstance(cb, basestring):
                if event.tokens[-1] in [' ', '=', '(']:
                    matches.append("'%s'" % cb)
                elif event.tokens[-1] == ',':
                    matches.append(" '%s'" % cb)
                elif has_open_quotes(event.line) and cb.startswith(event.text):
                    matches.append(cb)
            else:
                str_cb = str(cb)
                if str_cb.startswith(event.text):
                    matches.append(str_cb)

        return matches


class tab_glob(AnnotationCompleterBase):
    """Annotation for function arguments that recommends completions which are
    filenames matching a glob pattern.
    """

    def __init__(self, glob_pattern):
        """Set up a tab completion callback with glob matching

        Examples
        --------
        >>> def f(x : tab_glob("*.txt")):
        ...    pass

        >>> f(<TAB>
        will show you files ending in .txt
        """
        self.glob_pattern = glob_pattern

    def tab_matches(self, event):
        """Callback for the IPython annoation tab-completion system
        """

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


class tab_instance(AnnotationCompleterBase):
    """Annotation for function arguments that recommends python variables in
    your namespace that an instance of supplied types"""

    def __init__(self, *klasses):
        """Set up a tab completion callback with isinstance matching

        Parameters
        ----------
        klasses : the classes you'd like to match on

        Examples
        --------
        >>> x, y = 1, 2
        >>> def f(x : tab_instance(int)):
        ...    pass

        >>> f(<TAB>
        will show you files ending in .txt

        Limitations
        -----------
        Because of python's dynamic typing, this can't check the type of the
        return value of functions, so this won't be able to recommend something
        like max(1,2) in the previous example.
        """
        self.klasses = set(klasses)

        # add some extras
        self.klasses.update([types.FunctionType, types.BuiltinFunctionType,
                types.TypeType, types.ModuleType])

    def tab_matches(self, event):
        """Callback for the IPython annoation tab-completion system
        """

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

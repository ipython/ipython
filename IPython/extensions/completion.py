import inspect
import functools
import warnings
import types
import glob
import abc
import re

from IPython.core.completer import has_open_quotes
__all__ = ['tab_complete', 'globs_to', 'literal', 'instance_of']

def _init_completers(annotations):
    tab_completers = {}
    for key, value in annotations.iteritems():
        error = ValueError("I could not understand the "
            "annotation %s on argument %s" % (value, key))
        
        # the return value annotation must be just a straight class
        if key == 'return':
            if inspect.isclass(value):
                tab_completers[key] = value
            else:
                raise error
        elif isinstance(value, AnnotationCompleterBase):
            tab_completers[key] = value
        elif inspect.isclass(value):
            # instance_of is the default
            tab_completers[key] = instance_of(value)
        else:
            raise error
    return tab_completers


def tab_complete(*args, **kwargs):
    if (len(args) == 1 and len(kwargs.keys()) == 0 and
        hasattr(args[0], '__call__')):
        # this decorator was called with no arguments and is
        # wrapping a function where the annotations are defined
        # with py3k syntax
        f = args[0] # rename
        if not hasattr(f, '__annotations__'):
            raise ValueError('f is not annotated')
            
        f._tab_completions = _init_completers(f.__annotations__)
        return f

    # otherwise, this decorator is being called with arguments, indicating
    # python2 syntax
    def wrapper(f):
        argspec = inspect.getargspec(f)
        for key in kwargs.keys():
            if (key not in argspec.args) and (key != argspec.varargs) \
                    and (key != argspec.keywords) and key != 'return':
                raise ValueError('%s is not an argument taken by %s' \
                    % (key, wrapper.__name__))

            if hasattr(f, '_tab_completions'):
                # check that the annotations being provided don't already exist
                # if they do, we warn and overwrite. this decorator does not
                # implement any scheme for composing annotations.
                if key in f.__annotations__:
                    warnings.warn('Overwriting tab completion on %s' % key,
                        RuntimeWarning)
        
        try:
            f._tab_completions.update(_init_completers(kwargs))
        except AttributeError:
            f._tab_completions = _init_completers(kwargs)

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

class literal(AnnotationCompleterBase):
    """Annotation for function arguments that recommends completions from a
    set of enumerated literals. This is useful if you have an argumnet for a
    function that is designed to be called only with a small handful of possible
    values"""

    def __init__(self, *completions):
        """Set up a tab completion callback.

        Example (python 3)
        ------------------
        In[3]: def f(x : tab_literal(100, 200, 300)):
        ...        pass
        In[4]: f(1<HIT_THE_TAB_KEY>
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

class globs_to(AnnotationCompleterBase):
    """Annotation for function arguments that recommends completions which are
    filenames matching a glob pattern.
    """

    def __init__(self, glob_pattern):
        """Set up a tab completion callback with glob matching

        Example (python 3)
        ------------------
        In[5]: def f(x : tab_glob("*.txt")):
        ...        pass

        In[6]: f(<HIT_THE_TAB_KEY>
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


class instance_of(AnnotationCompleterBase):
    """Annotation for function arguments that recommends python variables in
    your namespace that an instance of supplied types"""

    def __init__(self, *klasses):
        """Set up a tab completion callback with isinstance matching

        Parameters
        ----------
        klasses : the classes you'd like to match on

        Example (python 3)
        ------------------
        In[7]: x, y = 1, 2
        In[8]: def f(x : tab_instance(int)):
        ...        pass

        In[9]: f(<TAB>
        will show you files ending in .txt

        Limitations
        -----------
        Because of python's dynamic typing, this can't check the type of the
        return value of functions, so this won't be able to recommend something
        like max(1,2) in the previous example.
        """
        self.klasses = set(klasses)
        self._omit__names_1 = re.compile(r'__.*?__')
        self._omit__names_2 = re.compile(r'_.*?')
        
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

        if event.ipcompleter.omit__names:
            if event.ipcompleter.omit__names == 1:
                no__name = (lambda txt: self._omit__names_1.match(txt) is None)
            else:
                # true if txt is _not_ a _ name, false otherwise:
                no__name = (lambda txt: self._omit__names_2.match(txt) is None)

            matches = filter(no__name, matches)
        return matches
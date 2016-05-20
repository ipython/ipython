# IPython: modified copy of numpy.testing.utils, so
# IPython.external._decorators works without numpy being installed.
"""
Utility function to facilitate testing.
"""

import sys
import warnings

# The following two classes are copied from python 2.6 warnings module (context
# manager)
class WarningMessage(object):

    """
    Holds the result of a single showwarning() call.

    Notes
    -----
    `WarningMessage` is copied from the Python 2.6 warnings module,
    so it can be used in NumPy with older Python versions.

    """

    _WARNING_DETAILS = ("message", "category", "filename", "lineno", "file",
                        "line")

    def __init__(self, message, category, filename, lineno, file=None,
                    line=None):
        local_values = locals()
        for attr in self._WARNING_DETAILS:
            setattr(self, attr, local_values[attr])
        if category:
            self._category_name = category.__name__
        else:
            self._category_name = None

    def __str__(self):
        return ("{message : %r, category : %r, filename : %r, lineno : %s, "
                    "line : %r}" % (self.message, self._category_name,
                                    self.filename, self.lineno, self.line))

class WarningManager:
    """
    A context manager that copies and restores the warnings filter upon
    exiting the context.

    The 'record' argument specifies whether warnings should be captured by a
    custom implementation of ``warnings.showwarning()`` and be appended to a
    list returned by the context manager. Otherwise None is returned by the
    context manager. The objects appended to the list are arguments whose
    attributes mirror the arguments to ``showwarning()``.

    The 'module' argument is to specify an alternative module to the module
    named 'warnings' and imported under that name. This argument is only useful
    when testing the warnings module itself.

    Notes
    -----
    `WarningManager` is a copy of the ``catch_warnings`` context manager
    from the Python 2.6 warnings module, with slight modifications.
    It is copied so it can be used in NumPy with older Python versions.

    """
    def __init__(self, record=False, module=None):
        self._record = record
        if module is None:
            self._module = sys.modules['warnings']
        else:
            self._module = module
        self._entered = False

    def __enter__(self):
        if self._entered:
            raise RuntimeError("Cannot enter %r twice" % self)
        self._entered = True
        self._filters = self._module.filters
        self._module.filters = self._filters[:]
        self._showwarning = self._module.showwarning
        if self._record:
            log = []
            def showwarning(*args, **kwargs):
                log.append(WarningMessage(*args, **kwargs))
            self._module.showwarning = showwarning
            return log
        else:
            return None

    def __exit__(self, type_, value, traceback):
        if not self._entered:
            raise RuntimeError("Cannot exit %r without entering first" % self)
        self._module.filters = self._filters
        self._module.showwarning = self._showwarning

def assert_warns(warning_class, func, *args, **kw):
    """Fail unless a warning of class warning_class is thrown by callable when
    invoked with arguments args and keyword arguments kwargs.
    
    If a different type of warning is thrown, it will not be caught, and the
    test case will be deemed to have suffered an error.
    """

    # XXX: once we may depend on python >= 2.6, this can be replaced by the
    # warnings module context manager.
    with WarningManager(record=True) as l:
        warnings.simplefilter('always')
        func(*args, **kw)
        if not len(l) > 0:
            raise AssertionError("No warning raised when calling %s"
                    % func.__name__)
        if not l[0].category is warning_class:
            raise AssertionError("First warning for %s is not a " \
                    "%s( is %s)" % (func.__name__, warning_class, l[0]))

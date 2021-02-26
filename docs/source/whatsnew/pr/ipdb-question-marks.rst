Show pinfo information in ipdb using "?" and "??"
-------------------------------------------------

In IPDB, it is now possible to show the information about an object using "?"
and "??", in much the same way it can be done when using the IPython prompt::

    ipdb> partial?
    Init signature: partial(self, /, *args, **kwargs)
    Docstring:     
    partial(func, *args, **keywords) - new function with partial application
    of the given arguments and keywords.
    File:           ~/.pyenv/versions/3.8.6/lib/python3.8/functools.py
    Type:           type
    Subclasses:     

Previously, "pinfo" or "pinfo2" command had to be used for this purpose.

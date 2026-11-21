Fix traceback formatting crash on non-mapping frame locals
===========================================================

Formatting a traceback no longer crashes with
``AttributeError: 'list' object has no attribute 'get'`` when a frame's
``f_locals`` is not a dict — for example the class-body frame of a class
whose metaclass ``__prepare__`` returns a list. The original exception
is now shown instead.

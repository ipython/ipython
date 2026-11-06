Fixed a ``RuntimeError: dictionary changed size during iteration`` that could
be raised when pretty-printing a mapping that mutates while it is being
formatted, such as a module's ``__dict__`` that populates lazily on first
attribute access (for example ``vars(posix)`` on its first call). The dict
pretty-printer now snapshots the mapping's items before iterating. See
:ghissue:`14541`.

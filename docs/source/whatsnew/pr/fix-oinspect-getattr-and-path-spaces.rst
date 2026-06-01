Fix oinspect TypeError with objects using generic ``__getattr__``
=================================================================

Objects whose ``__getattr__`` returns something other than ``dict`` for
``__custom_documentations__`` (e.g. polars ``Expr``, which returns a new
``Expr`` for any attribute name) no longer cause a ``TypeError`` when
inspected with ``?`` or :func:`%pinfo`.  The lookup is now guarded with
``isinstance(..., dict)``.  :ghissue:`15072`

Also fixed an incorrect comparison in the MIME-hook inspection path
(``inspect.Parameter.default`` → ``inspect.Parameter.empty``) that
accidentally relied on a property-object inequality to filter required
parameters.

Fix test failures when IPython source path contains spaces
==========================================================

``test_exit_code_signal`` in :file:`tests/test_interactiveshell.py` now
uses :func:`shlex.quote` when interpolating ``sys.executable`` and the
temporary filename into a shell command string, preventing test failures
on systems where either path contains spaces.  :ghissue:`15100`

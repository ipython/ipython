Removal of long-deprecated APIs
-------------------------------

A number of APIs that had been emitting deprecation warnings for several years
have been removed:

- ``IPCompleter.limit_to__all__`` configuration option (deprecated since
  IPython 5.0). Completion on ``object.<tab>`` now always uses ``dir()``-based
  discovery, regardless of ``__all__``.
- ``IPCompleter.python_matches`` method (deprecated since IPython 8.27). Use
  ``IPCompleter.python_matcher`` instead.
- ``OInfo.get()`` (deprecated since IPython 8.13, added only as a transitional
  helper when ``OInfo`` stopped being a dict in 8.12). Access the dataclass
  fields directly, e.g. ``oinfo.found`` instead of ``oinfo.get('found')``.
- The module-level ``backends`` and ``backend2gui`` attributes of
  ``IPython.core.pylabtools`` (deprecated since IPython 8.24). Matplotlib
  backends are resolved by Matplotlib itself since 3.9.
- ``InteractiveShell.run_cell_async`` and ``InteractiveShell.should_run_async``
  no longer call ``transform_cell`` automatically when ``transformed_cell`` is
  not passed (this fallback had emitted a ``DeprecationWarning`` since IPython
  7.17); they now raise a ``TypeError``. Run ``transform_cell`` yourself and
  pass the result via the ``transformed_cell`` keyword argument (as ipykernel
  6.0 and newer already do). ``InteractiveShell.run_cell`` is unaffected.

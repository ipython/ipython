Cell_Meta now a part of ExecutionInfo
-------------------------------------
The ``cell_meta`` field is now part of the ``ExecutionInfo`` object, which is passed to IPython extensions in the ``pre_run_cell`` and ``post_run_cell`` callbacks.

See :ghpull:`15071`
The *post* event callbacks are now always called, even when the execution failed
(for example because of a ``SyntaxError``).
Additionally, the execution info and result objects are now made available in
the corresponding *pre* or *post* ``*_run_cell`` event callbacks in a backward
compatible manner.

* `Related GitHub issue <https://github.com/ipython/ipython/issues/10774>`__

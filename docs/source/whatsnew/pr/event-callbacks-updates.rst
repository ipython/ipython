The *post* event callbacks are now always called, even when the execution failed
(for example because of a ``SyntaxError``).
Additionally, the execution result object is now made available in both *pre*
and *post* event callbacks in a backward compatible manner.

* `Related GitHub issue <https://github.com/ipython/ipython/issues/10774>`__

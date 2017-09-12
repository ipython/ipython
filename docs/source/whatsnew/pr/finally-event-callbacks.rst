Two new event callbacks have been added: ``finally_execute`` and ``finally_run_cell``.
They work similar to the corresponding *post* callbacks, but are guaranteed to be triggered (even when, for example, a ``SyntaxError`` was raised).
Also, the execution result is provided as an argument for further inspection.

* `GitHub issue <https://github.com/ipython/ipython/issues/10774>`__
* `Updated docs <http://ipython.readthedocs.io/en/stable/config/callbacks.html?highlight=finally>`__

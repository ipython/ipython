changes to hidden namespace on startup
--------------------------------------

Previously, all names declared in code run at startup
(startup files, ``ipython -i script.py``, etc.)
were added to the hidden namespace, which hides the names from tools like ``%whos``.
There are two changes to this behavior:

1. Scripts run on the command-line ``ipython -i script.py``now behave the same as if they were
   passed to ``%run``, so their variables are never hidden.
2. A boolean config flag ``InteractiveShellApp.hide_initial_ns`` has been added to optionally
   disable the hidden behavior altogether. The default behavior is unchanged.

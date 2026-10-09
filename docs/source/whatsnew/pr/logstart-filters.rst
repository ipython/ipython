Filter what ``%logstart`` logs
==============================

``%logstart`` accepts three new flags for keeping a session log that replays
cleanly: ``-m`` leaves out cells containing IPython special commands (magics, shell
escapes and help lookups), ``-e`` leaves out input that raised an error, and ``-d`` leaves
out input that has already been logged in the session. They can be combined,
for example ``%logstart -med session.py``.

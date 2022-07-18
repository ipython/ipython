New setting to silence warning if working inside a virtual environment
======================================================================

Previously, when starting IPython in a virtual environment without IPython installed (so IPython from the global environment is used), the following warning was printed:

    Attempting to work in a virtualenv. If you encounter problems, please install IPython inside the virtualenv.

This warning can be permanently silenced by setting ``c.InteractiveShell.warn_venv`` to ``False`` (the default is ``True``).

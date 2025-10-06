Respect PYTHONSAFEPATH
======================

IPython now respects the value of Python's flag ``sys.flags.safe_path``, a flag which is most often set by the ``PYTHONSAFEPATH`` environment variable. Setting this causes Python not to automatically include the current working directory in the sys.path.

IPython can already be configured to do this via the ``--ignore_cwd`` command-line flag or by setting ``c.InteractiveShellApp.ignore_cwd=True``. Now, IPython can also be configured by setting ``PYTHONSAFEPATH=1`` or by calling python with ``-P``.

The behavior of ``safe_path`` was described in `what's new in 3.11`_ and in `PyConfig docs`_.


.. _what's new in 3.11: https://docs.python.org/3/whatsnew/3.11.html#whatsnew311-pythonsafepath
.. _PyConfig docs: https://docs.python.org/3/c-api/init_config.html#c.PyConfig.safe_path



============
 4.x Series
============

IPython 4.0
===========

Released August, 2015

IPython 4.0 is the first major release after the Big Split.
IPython no longer contains the notebook, qtconsole, etc. which have moved to
`jupyter <https://jupyter.readthedocs.org>`_.
IPython subprojects, such as `IPython.parallel <https://ipyparallel.readthedocs.org>`_ and `widgets <https://ipywidgets.readthedocs.org>`_ have moved to their own repos as well.

The following subpackages are deprecated:

- IPython.kernel (now jupyter_client and ipykernel)
- IPython.consoleapp (now jupyter_client.consoleapp)
- IPython.nbformat (now nbformat)
- IPython.nbconvert (now nbconvert)
- IPython.html (now notebook)
- IPython.parallel (now ipyparallel)
- IPython.utils.traitlets (now traitlets)
- IPython.config (now traitlets.config)
- IPython.qt (now qtconsole)
- IPython.terminal.console (now jupyter_console)

and a few other utilities.

Shims for the deprecated subpackages have been added,
so existing code should continue to work with a warning about the new home.

There are few changes to the code beyond the reorganization and some bugfixes.

IPython highlights:

- Public APIs for discovering IPython paths is moved from :mod:`IPython.utils.path` to :mod:`IPython.paths`.
  The old function locations continue to work with deprecation warnings.
- Code raising ``DeprecationWarning``
  entered by the user in an interactive session will now display the warning by
  default. See :ghpull:`8480` an :ghissue:`8478`.
- The `--deep-reload` flag and the corresponding options to inject `dreload` or
  `reload` into the interactive namespace have been deprecated, and will be
  removed in future versions. You should now explicitly import `reload` from
  `IPython.lib.deepreload` to use it.


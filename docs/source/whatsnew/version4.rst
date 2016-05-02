============
 4.x Series
============

IPython 4.2
===========

IPython 4.2 (April, 2016) includes various bugfixes and improvements over 4.1.

- Fix ``ipython -i`` on errors, which was broken in 4.1.
- The delay meant to highlight deprecated commands that have moved to jupyter has been removed.
- Improve compatibility with future versions of traitlets and matplotlib.
- Use stdlib :func:`python:shutil.get_terminal_size` to measure terminal width when displaying tracebacks
  (provided by ``backports.shutil_get_terminal_size`` on Python 2).

You can see the rest `on GitHub <https://github.com/ipython/ipython/issues?q=milestone%3A4.2>`__.


IPython 4.1
===========

IPython 4.1.2 (March, 2016) fixes installation issues with some versions of setuptools.

Released February, 2016. IPython 4.1 contains mostly bug fixes,
though there are a few improvements.


- IPython debugger (IPdb) now supports the number of context lines for the
  ``where`` (and ``w``) commands. The `context` keyword is also available in
  various APIs. See PR :ghpull:`9097`
- YouTube video will now show thumbnail when exported to a media that do not
  support video. (:ghpull:`9086`)
- Add warning when running `ipython <subcommand>` when subcommand is
  deprecated. `jupyter` should now be used.
- Code in `%pinfo` (also known as `??`) are now highlighter (:ghpull:`8947`)
- `%aimport` now support module completion. (:ghpull:`8884`)
- `ipdb` output is now colored ! (:ghpull:`8842`)
- Add ability to transpose columns for completion: (:ghpull:`8748`)

Many many docs improvements and bug fixes, you can see the
`list of changes <https://github.com/ipython/ipython/compare/4.0.0...4.1.0>`_

IPython 4.0
===========

Released August, 2015

IPython 4.0 is the first major release after the Big Split.
IPython no longer contains the notebook, qtconsole, etc. which have moved to
`jupyter <https://jupyter.readthedocs.io>`_.
IPython subprojects, such as `IPython.parallel <https://ipyparallel.readthedocs.io>`_ and `widgets <https://ipywidgets.readthedocs.io>`_ have moved to their own repos as well.

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


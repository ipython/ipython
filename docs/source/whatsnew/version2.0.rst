============
 2.x Series
============

Release 2.3.1
=============

November, 2014

- Fix CRCRLF line-ending bug in notebooks on Windows

For more information on what fixes have been backported to 2.3.1,
see our :ref:`detailed release info <issues_list_200>`.

Release 2.3.0
=============

October, 2014

- improve qt5 support
- prevent notebook data loss with atomic writes

For more information on what fixes have been backported to 2.3,
see our :ref:`detailed release info <issues_list_200>`.

Release 2.2.0
=============

August, 2014

- Add CORS configuration

For more information on what fixes have been backported to 2.2,
see our :ref:`detailed release info <issues_list_200>`.

Release 2.1.0
=============

May, 2014

IPython 2.1 is the first bugfix release for 2.0.
For more information on what fixes have been backported to 2.1,
see our :ref:`detailed release info
<issues_list_200>`.


Release 2.0.0
=============

April, 2014

IPython 2.0 requires Python ≥ 2.7.2 or ≥ 3.3.0.
It does not support Python 3.0, 3.1, 3.2, 2.5, or 2.6.

The principal milestones of 2.0 are:

- interactive widgets for the notebook
- directory navigation in the notebook dashboard
- persistent URLs for notebooks
- a new modal user interface in the notebook
- a security model for notebooks

Contribution summary since IPython 1.0 in August, 2013:

- ~8 months of work
- ~650 pull requests merged
- ~400 issues closed (non-pull requests)
- contributions from ~100 authors
- ~4000 commits

The amount of work included in this release is so large that we can only cover
here the main highlights; please see our :ref:`detailed release statistics
<issues_list_200>` for links to every issue and pull request closed on GitHub
as well as a full list of individual contributors.

New stuff in the IPython notebook
---------------------------------

Directory navigation
********************

.. image:: /_images/2.0/treeview.png
    :width: 392px
    :alt: Directory navigation
    :align: center

The IPython notebook dashboard allows navigation into subdirectories.
URLs are persistent based on the notebook's path and name,
so no more random UUID URLs.

Serving local files no longer needs the ``files/`` prefix.
Relative links across notebooks and other files should work just as if notebooks were regular HTML files.

Interactive widgets
*******************

.. image:: /_images/2.0/widgets.png
    :width: 392px
    :alt: Interactive widgets
    :align: center

IPython 2.0 adds :mod:`IPython.html.widgets`, for manipulating
Python objects in the kernel with GUI controls in the notebook.
IPython comes with a few built-in widgets for simple data types,
and an API designed for developers to build more complex widgets.
See the `widget docs`_ for more information.

.. _widget docs: http://nbviewer.ipython.org/github/ipython/ipython/blob/2.x/examples/Interactive%20Widgets/Index.ipynb


Modal user interface
********************

The notebook has added separate Edit and Command modes,
allowing easier keyboard commands and making keyboard shortcut customization possible.
See the new `User Interface notebook`_ for more information.

.. _User Interface Notebook: http://nbviewer.ipython.org/github/ipython/ipython/blob/2.x/examples/Notebook/User%20Interface.ipynb


You can familiarize yourself with the updated notebook user interface, including an
explanation of Edit and Command modes, by going through the short guided tour
which can be started from the Help menu.

.. image:: /_images/2.0/user-interface.png
    :width: 392px
    :alt: Interface tour
    :align: center


Security
********

2.0 introduces a :ref:`security model <notebook_security>` for notebooks,
to prevent untrusted code from executing on users' behalf when notebooks open.
A quick summary of the model:

- Trust is determined by :ref:`signing notebooks<signing_notebooks>`.
- Untrusted HTML output is sanitized.
- Untrusted Javascript is never executed.
- HTML and Javascript in Markdown are never trusted.

Dashboard "Running" tab
***********************

.. image:: /_images/2.0/running-crop.png
    :width: 392px
    :alt: Running tab
    :align: center

The dashboard now has a "Running" tab which shows all of the running notebooks.

Single codebase Python 3 support
--------------------------------

IPython previously supported Python 3 by running 2to3 during setup. We
have now switched to a single codebase which runs natively on Python 2.7
and 3.3.

For notes on how to maintain this, see :doc:`/development/pycompat`.

Selecting matplotlib figure formats
-----------------------------------

Deprecate single-format ``InlineBackend.figure_format``
configurable in favor of ``InlineBackend.figure_formats``,
which is a set, supporting multiple simultaneous figure formats (e.g. png, pdf).

This is available at runtime with the new API function :func:`IPython.display.set_matplotlib_formats`.

clear_output changes
--------------------

* There is no longer a 500ms delay when calling ``clear_output``.
* The ability to clear stderr and stdout individually was removed.
* A new ``wait`` flag that prevents ``clear_output`` from being executed until new
  output is available.  This eliminates animation flickering by allowing the
  user to double buffer the output.
* The output div height is remembered when the ``wait=True`` flag is used.

Extending configurable containers
---------------------------------

Some configurable traits are containers (list, dict, set)
Config objects now support calling ``extend``, ``update``, ``insert``, etc.
on traits in config files, which will ultimately result in calling
those methods on the original object.

The effect being that you can now add to containers without having to copy/paste
the initial value::

    c = get_config()
    c.InlineBackend.rc.update({ 'figure.figsize' : (6, 4) })

Changes to hidden namespace on startup
--------------------------------------

Previously, all names declared in code run at startup
(startup files, ``ipython -i script.py``, etc.)
were added to the hidden namespace, which hides the names from tools like ``%whos``.
There are two changes to this behavior:

1. Scripts run on the command-line ``ipython -i script.py``now behave the same as if they were
   passed to ``%run``, so their variables are never hidden.
2. A boolean config flag ``InteractiveShellApp.hide_initial_ns`` has been added to optionally
   disable the hidden behavior altogether. The default behavior is unchanged.

Using dill to expand serialization support
------------------------------------------

The new function :func:`~IPython.utils.pickleutil.use_dill` allows
dill to extend serialization support in :mod:`IPython.parallel` (closures, etc.).
A :meth:`DirectView.use_dill` convenience method was also added, to enable dill
locally and on all engines with one call.

New IPython console lexer
-------------------------

The IPython console lexer has been rewritten and now supports tracebacks
and customized input/output prompts. See the :ref:`new lexer docs <console_lexer>`
for details.

DisplayFormatter changes
------------------------

There was no official way to query or remove callbacks in the Formatter API.
To remedy this, the following methods are added to :class:`BaseFormatter`:

- ``lookup(instance)`` - return appropriate callback or a given object
- ``lookup_by_type(type_or_str)`` - return appropriate callback for a given type or ``'mod.name'`` type string
- ``pop(type_or_str)`` - remove a type (by type or string).
  Pass a second argument to avoid KeyError (like dict).

All of the above methods raise a KeyError if no match is found.

And the following methods are changed:

- ``for_type(type_or_str)`` - behaves the same as before, only adding support for ``'mod.name'``
  type strings in addition to plain types. This removes the need for ``for_type_by_name()``,
  but it remains for backward compatibility.

Formatters can now raise NotImplementedError in addition to returning None
to indicate that they cannot format a given object.

Exceptions and Warnings
***********************

Exceptions are no longer silenced when formatters fail.
Instead, these are turned into a :class:`~IPython.core.formatters.FormatterWarning`.
A FormatterWarning will also be issued if a formatter returns data of an invalid type
(e.g. an integer for 'image/png').


Other changes
-------------

* `%%capture` cell magic now captures the rich display output, not just
  stdout/stderr

* In notebook, Showing tooltip on tab has been disables to avoid conflict with
  completion, Shift-Tab could still be used to invoke tooltip when inside
  function signature and/or on selection.

* ``object_info_request`` has been replaced by ``object_info`` for consistency in the javascript API.
  ``object_info`` is a simpler interface to register callback that is incompatible with ``object_info_request``.

* Previous versions of IPython on Linux would use the XDG config directory,
  creating :file:`~/.config/ipython` by default. We have decided to go
  back to :file:`~/.ipython` for consistency among systems. IPython will
  issue a warning if it finds the XDG location, and will move it to the new
  location if there isn't already a directory there.

* Equations, images and tables are now centered in Markdown cells.
* Multiline equations are now centered in output areas; single line equations
  remain left justified.

* IPython config objects can be loaded from and serialized to JSON.
  JSON config file have the same base name as their ``.py`` counterpart,
  and will be loaded with higher priority if found.

* bash completion updated with support for all ipython subcommands and flags, including nbconvert

* ``ipython history trim``: added ``--keep=<N>`` as an alias for the more verbose
  ``--HistoryTrim.keep=<N>``
* New ``ipython history clear`` subcommand, which is the same as the newly supported
  ``ipython history trim --keep=0``

* You can now run notebooks in an interactive session via ``%run notebook.ipynb``.

* Print preview is back in the notebook menus, along with options to
  download the open notebook in various formats. This is powered by
  nbconvert.

* :exc:`~IPython.nbconvert.utils.pandoc.PandocMissing` exceptions will be
  raised if Pandoc is unavailable, and warnings will be printed if the version
  found is too old. The recommended Pandoc version for use with nbconvert is
  1.12.1.

* The InlineBackend.figure_format now supports JPEG output if PIL/Pillow is available.

* Input transformers (see :doc:`/config/inputtransforms`) may now raise
  :exc:`SyntaxError` if they determine that input is invalid. The input
  transformation machinery in IPython will handle displaying the exception to
  the user and resetting state.

* Calling ``container.show()`` on javascript display is deprecated and will
  trigger errors on future IPython notebook versions. ``container`` now show
  itself as soon as non-empty

* Added ``InlineBackend.print_figure_kwargs`` to allow passing keyword arguments
  to matplotlib's ``Canvas.print_figure``. This can be used to change the value of
  ``bbox_inches``, which is 'tight' by default, or set the quality of JPEG figures.

* A new callback system has been introduced. For details, see :doc:`/config/callbacks`.

* jQuery and require.js are loaded from CDNs in the default HTML template,
  so javascript is available in static HTML export (e.g. nbviewer).

Backwards incompatible changes
------------------------------

* Python 2.6 and 3.2 are no longer supported: the minimum required
  Python versions are now 2.7 and 3.3.
* The Transformer classes have been renamed to Preprocessor in nbconvert and
  their ``call`` methods have been renamed to ``preprocess``.
* The ``call`` methods of nbconvert post-processsors have been renamed to
  ``postprocess``.

* The module ``IPython.core.fakemodule`` has been removed.

* The alias system has been reimplemented to use magic functions. There should be little
  visible difference while automagics are enabled, as they are by default, but parts of the
  :class:`~IPython.core.alias.AliasManager` API have been removed.

* We fixed an issue with switching between matplotlib inline and GUI backends,
  but the fix requires matplotlib 1.1 or newer.  So from now on, we consider
  matplotlib 1.1 to be the minimally supported version for IPython. Older
  versions for the most part will work, but we make no guarantees about it.

* The :command:`pycolor` command has been removed. We recommend the much more capable
  :command:`pygmentize` command from the `Pygments <http://pygments.org/>`_ project.
  If you need to keep the exact output of :command:`pycolor`, you can still use
  ``python -m IPython.utils.PyColorize foo.py``.

* :mod:`IPython.lib.irunner` and its command-line entry point have been removed.
  It had fallen out of use long ago.

* The ``input_prefilter`` hook has been removed, as it was never
  actually used by the code. The input transformer system offers much
  more powerful APIs to work with input code. See
  :doc:`/config/inputtransforms` for details.

* :class:`IPython.core.inputsplitter.IPythonInputSplitter` no longer has a method
  ``source_raw_reset()``, but gains :meth:`~IPython.core.inputsplitter.IPythonInputSplitter.raw_reset`
  instead. Use of ``source_raw_reset`` can be replaced with::

      raw = isp.source_raw
      transformed = isp.source_reset()

* The Azure notebook manager was removed as it was no longer compatible with the notebook storage scheme.

* Simplifying configurable URLs

  - base_project_url is renamed to base_url (base_project_url is kept as a deprecated alias, for now)
  - base_kernel_url configurable is removed (use base_url)
  - websocket_url configurable is removed (use base_url)

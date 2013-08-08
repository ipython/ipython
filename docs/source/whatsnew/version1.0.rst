============
 1.0 Series
============

Release 1.0.0: An Afternoon Hack
================================


IPython 1.0 requires Python ≥ 2.6.5 or ≥ 3.2.1.
It does not support Python 3.0, 3.1, or 2.5.

This is a big release.  The principal milestone is the addition of :mod:`IPython.nbconvert`,
but there has been a great deal of work improving all parts of IPython as well.

The previous version (0.13) was released on June 30, 2012,
and in this development cycle we had:

- ~12 months of work.
- ~700 pull requests merged.
- ~600 issues closed (non-pull requests).
- contributions from ~150 authors.
- ~4000 commits.

The amount of work included in this release is so large that we can only cover
here the main highlights; please see our :ref:`detailed release statistics
<issues_list_100>` for links to every issue and pull request closed on GitHub
as well as a full list of individual contributors.
It includes

Reorganization
--------------

There have been two major reorganizations in IPython 1.0:

- Added :mod:`IPython.kernel` for all kernel-related code.
  This means that :mod:`IPython.zmq` has been removed,
  and much of it is now in :mod:`IPython.kernel.zmq`,
  some of it being in the top-level :mod:`IPython.kernel`.
- We have removed the `frontend` subpackage,
  as it caused unnecessary depth.  So what was :mod:`IPython.frontend.qt`
  is now :mod:`IPython.qt`, and so on.  The one difference is that
  the notebook has been further flattened, so that
  :mod:`IPython.frontend.html.notebook` is now just `IPython.html`.
  There is a shim module, so :mod:`IPython.frontend` is still
  importable in 1.0, but there will be a warning.
- The IPython sphinx directives are now installed in :mod:`IPython.sphinx`,
  so they can be imported by other projects.


Public APIs
-----------

For the first time since 0.10 (sorry, everyone),
there is an official public API for starting IPython:

.. sourcecode:: python

    from IPython import start_ipython
    start_ipython()

This is what packages should use that start their own IPython session,
but don't actually want embedded IPython (most cases).
:func:`IPython.embed()` is used for embedding IPython into the calling namespace,
similar to calling :func:`Pdb.set_trace`, whereas :func:`start_ipython`
will start a plain IPython session, loading config and startup files as normal.

We also have added:

.. sourcecode:: python

    from IPython import get_ipython


Which is a *library* function for getting the current IPython instance,
and will return ``None`` if no IPython instance is running.
This is the official way to check whether your code is called from inside an IPython session.
If you want to check for IPython without unnecessarily importing IPython,
use this function:

.. sourcecode:: python

    def get_ipython():
        """return IPython instance if there is one, None otherwise"""
        import sys
        if "IPython" in sys.modules:
            import IPython
            return IPython.get_ipython()

Core
----

- The input transformation framework has been reworked. This fixes some corner
  cases, and adds more flexibility for projects which use IPython, like SymPy &
  SAGE. For more details, see :doc:`/config/inputtransforms`.
- Exception types can now be displayed with a custom traceback, by defining a
  ``_render_traceback_()`` method which returns a list of strings, each
  containing one line of the traceback.
- A new command, ``ipython history trim`` can be used to delete everything but
  the last 1000 entries in the history database.
- ``__file__`` is defined in both config files at load time,
  and ``.ipy`` files executed with ``%run``.
- ``%logstart`` and ``%logappend`` are no longer broken.
- Add glob expansion for ``%run``, e.g. ``%run -g script.py *.txt``.
- Expand variables (``$foo``) in Cell Magic argument line.
- By default, :command:`iptest` will exclude various slow tests.
  All tests can be run with :command:`iptest --all`.
- SQLite history can be disabled in the various cases that it does not behave well.
- ``%edit`` works on interactively defined variables.
- editor hooks have been restored from quarantine, enabling TextMate as editor,
  etc.
- The env variable PYTHONSTARTUP is respected by IPython.
- The ``%matplotlib`` magic was added, which is like the old ``%pylab`` magic,
  but it does not import anything to the interactive namespace.
  It is recommended that users switch to ``%matplotlib`` and explicit imports.
- The ``--matplotlib`` command line flag was also added. It invokes the new
  ``%matplotlib`` magic and can be used in the same way as the old ``--pylab``
  flag. You can either use it by itself as a flag (``--matplotlib``), or you
  can also pass a backend explicitly (``--matplotlib qt`` or
  ``--matplotlib=wx``, etc).


Backwards incompatible changes
******************************

- Calling :meth:`InteractiveShell.prefilter` will no longer perform static
  transformations - the processing of escaped commands such as ``%magic`` and
  ``!system``, and stripping input prompts from code blocks. This functionality
  was duplicated in :mod:`IPython.core.inputsplitter`, and the latter version
  was already what IPython relied on. A new API to transform input will be ready
  before release.
- Functions from :mod:`IPython.lib.inputhook` to control integration with GUI
  event loops are no longer exposed in the top level of :mod:`IPython.lib`.
  Code calling these should make sure to import them from
  :mod:`IPython.lib.inputhook`.
- For all kernel managers, the ``sub_channel`` attribute has been renamed to
  ``iopub_channel``.
- Users on Python versions before 2.6.6, 2.7.1 or 3.2 will now need to call
  :func:`IPython.utils.doctestreload.doctest_reload` to make doctests run 
  correctly inside IPython. Python releases since those versions are unaffected.
  For details, see :ghpull:`3068` and `Python issue 8048 <http://bugs.python.org/issue8048>`_.
- The ``InteractiveShell.cache_main_mod()`` method has been removed, and
  :meth:`~IPython.core.interactiveshell.InteractiveShell.new_main_mod` has a
  different signature, expecting a filename where earlier versions expected
  a namespace. See :ghpull:`3555` for details.
- The short-lived plugin system has been removed. Extensions are the way to go.


.. _nbconvert1:

NbConvert
---------

The major milestone for IPython 1.0 is the addition of :mod:`IPython.nbconvert` - tools for converting
IPython notebooks to various other formats.

.. warning::

    nbconvert is α-level preview code in 1.0

To use nbconvert to convert various file formats::

    ipython nbconvert --to html *.ipynb

See ``ipython nbconvert --help`` for more information.
nbconvert depends on `pandoc`_ for many of the translations to and from various formats.

.. seealso::

    :ref:`nbconvert`

.. _pandoc: http://johnmacfarlane.net/pandoc/

Notebook
--------

Major changes to the IPython Notebook in 1.0:

- The notebook is now autosaved, by default at an interval of two minutes.
  When you press 'save' or Ctrl-S, a *checkpoint* is made, in a hidden folder.
  This checkpoint can be restored, so that the autosave model is strictly safer
  than traditional save. If you change nothing about your save habits,
  you will always have a checkpoint that you have written,
  and an autosaved file that is kept up to date.
- The notebook supports :func:`raw_input` / :func:`input`, and thus also ``%debug``,
  and many other Python calls that expect user input.
- You can load custom javascript and CSS in the notebook by editing the files
  :file:`$(ipython locate profile)/static/custom/custom.{js,css}`.
- Add ``%%html``, ``%%svg``, ``%%javascript``, and ``%%latex`` cell magics
  for writing raw output in notebook cells.
- add a redirect handler and anchors on heading cells, so you can link
  across notebooks, directly to heading cells in other notebooks.
- Images support width and height metadata,
  and thereby 2x scaling (retina support).
- ``_repr_foo_`` methods can return a tuple of (data, metadata),
  where metadata is a dict containing metadata about the displayed object.
  This is used to set size, etc. for retina graphics. To enable retina matplotlib figures,
  simply set ``InlineBackend.figure_format = 'retina'`` for 2x PNG figures,
  in your :ref:`IPython config file <config_overview>` or via the ``%config`` magic.
- Add display.FileLink and FileLinks for quickly displaying HTML links to local files.
- Cells have metadata, which can be edited via cell toolbars.
  This metadata can be used by external code (e.g. reveal.js or exporters),
  when examining the notebook.
- Fix an issue parsing LaTeX in markdown cells, which required users to type ``\\\``,
  instead of ``\\``.
- Notebook templates are rendered with Jinja instead of Tornado.
- ``%%file`` has been renamed ``%%writefile`` (``%%file`` is deprecated).
- ANSI (and VT100) color parsing has been improved in both performance and
  supported values.
- The static files path can be found as ``IPython.html.DEFAULT_STATIC_FILES_PATH``,
  which may be changed by package managers.
- IPython's CSS is installed in :file:`static/css/style.min.css`
  (all style, including bootstrap), and :file:`static/css/ipython.min.css`,
  which only has IPython's own CSS. The latter file should be useful for embedding
  IPython notebooks in other pages, blogs, etc.
- The Print View has been removed. Users are encouraged to test :ref:`ipython
  nbconvert <nbconvert1>` to generate a static view.

Javascript Components
*********************

The javascript components used in the notebook have been updated significantly.

- updates to jQuery (2.0) and jQueryUI (1.10)
- Update CodeMirror to 3.14
- Twitter Bootstrap (2.3) for layout
- Font-Awesome (3.1) for icons
- highlight.js (7.3) for syntax highlighting
- marked (0.2.8) for markdown rendering
- require.js (2.1) for loading javascript

Some relevant changes that are results of this:

- Markdown cells now support GitHub-flavored Markdown (GFM),
  which includes `````python`` code blocks and tables.
- Notebook UI behaves better on more screen sizes.
- Various code cell input issues have been fixed.


Kernel
------

The kernel code has been substantially reorganized.

New features in the kernel:

- Kernels support ZeroMQ IPC transport, not just TCP
- The message protocol has added a top-level metadata field,
  used for information about messages.
- Add a `data_pub` message that functions much like `display_pub`,
  but publishes raw (usually pickled) data, rather than representations.
- Ensure that ``sys.stdout.encoding`` is defined in Kernels.
- Stdout from forked subprocesses should be forwarded to frontends (instead of crashing).

IPEP 13
*******

The KernelManager has been split into a :class:`~.KernelManager` and a :class:`~.KernelClient`.
The Manager owns a kernel and starts / signals / restarts it. There is always zero or one
KernelManager per Kernel.  Clients communicate with Kernels via zmq channels,
and there can be zero-to-many Clients connected to a Kernel at any given time.

The KernelManager now automatically restarts the kernel when it dies,
rather than requiring user input at the notebook or QtConsole UI
(which may or may not exist at restart time).

In-process kernels
******************

The Python-language frontends, particularly the Qt console, may now communicate
with in-process kernels, in addition to the traditional out-of-process
kernels. An in-process kernel permits direct access to the kernel namespace,
which is necessary in some applications. It should be understood, however, that
the in-process kernel is not robust to bad user input and will block the main
(GUI) thread while executing. Developers must decide on a case-by-case basis
whether this tradeoff is appropriate for their application.



Parallel
--------

IPython.parallel has had some refactoring as well.  
There are many improvements and fixes, but these are the major changes:

- Connections have been simplified. All ports and the serialization in use
  are written to the connection file, rather than the initial two-stage system.
- Serialization has been rewritten, fixing many bugs and dramatically improving
  performance serializing large containers.
- Load-balancing scheduler performance with large numbers of tasks has been dramatically improved.
- There should be fewer (hopefully zero) false-positives for engine failures.
- Increased compatibility with various use cases that produced serialization / argument errors
  with map, etc.
- The controller can attempt to resume operation if it has crashed,
  by passing ``ipcontroller --restore``.
- Engines can monitor the Hub heartbeat, and shutdown if the Hub disappears for too long.
- add HTCondor support in launchers


QtConsole
---------

Various fixes, including improved performance with lots of text output,
and better drag and drop support.
The initial window size of the qtconsole is now configurable via ``IPythonWidget.width``
and ``IPythonWidget.height``.


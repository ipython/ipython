============
 9.x Series
============

.. _version 9.17:

IPython 9.17
------------

Summary
~~~~~~~

This release is mostly about how long IPython takes to start. Two further
passes over the startup path -- deferring imports to their use sites, keeping
pygments' plugin machinery out of it, and declaring IPython's own magics
lazily -- together cut a large fraction off ``import IPython`` and off getting
to a prompt, without any change in behaviour. Alongside that: a new
``IPYTHON_KITTY_GRAPHICS`` environment variable to override terminal graphics
detection, ``as`` aliasing in :magic:`aimport`, and two input- and
output-handling fixes.

There are no backwards-incompatible changes in this release.

``%aimport`` understands ``as`` aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``%aimport`` now accepts the ``module as alias`` form, matching a plain
``import`` statement::

    %aimport numpy as np

The module is marked for autoreloading as before, and is pushed into the user
namespace under the alias rather than under its own name.

Malformed number literals are reported as syntax errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since Python 3.12 the tokenizer raises ``TokenError`` for malformed numeric
literals such as ``0b12``, ``0o1239`` or ``1__2``. IPython did not recognise
those errors, and the resulting token stream had no ``ENDMARKER``, so
``check_complete`` reported the input as *incomplete*: typing one of them in the
terminal left you at a continuation prompt instead of raising ``SyntaxError``.
They are now treated like the other hard tokenizer errors and the input is
reported as invalid. Genuinely unfinished input -- an unterminated multiline
string or expression -- is still reported as incomplete.

Control characters are stripped from the terminal title
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~IPython.utils.terminal.set_term_title` writes the title inside a
terminal escape sequence, so a title containing control characters -- an
escape, a bell, or a newline -- could end the sequence early and have the rest
interpreted by the terminal. This mattered for titles built from data IPython
does not control, such as a directory name. Control characters are now removed
before the title is written.

Forcing kitty graphics support on or off
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython decides whether the terminal understands the `kitty graphics protocol
<https://sw.kovidgoyal.net/kitty/graphics-protocol/>`__ by walking up the
process tree looking for a known terminal emulator. That guess can be wrong --
for instance inside ``tmux``, a container, or an emulator not on the list -- and
it is not free: it imports ``psutil`` and inspects the process tree on every
startup that has a tty.

The ``IPYTHON_KITTY_GRAPHICS`` environment variable now states the answer
outright and skips the detection entirely::

    IPYTHON_KITTY_GRAPHICS=1 ipython     # my terminal does support it
    IPYTHON_KITTY_GRAPHICS=0 ipython     # it does not; do not even look

Accepted values are ``1``/``true`` and ``0``/``false``, case-insensitive.
Leaving it unset, or setting it to the empty string, keeps the existing
autodetection. Any other value is ignored with a warning, so a typo cannot
silently turn graphics off.

Built-in magics are declared lazily
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython's own magics are now declared lazily. Starting a shell used to import
all fifteen modules under :mod:`IPython.core.magics` and instantiate every
:class:`~IPython.core.magic.Magics` class in them, even though a session
typically uses a handful of magics at most. Only the magic *names* are now known
up front, from a hand-maintained table in ``IPython.core.magics._table``, and the
module implementing a magic is imported the first time it is looked up. This
takes roughly 25 ms off ``import IPython`` and shell startup.

This reuses :attr:`~IPython.core.magic.MagicsManager.lazy_magics`, which already
existed for extensions, so third-party code can declare its magics the same way::

    shell.magics_manager.register_lazy("my_magic", "my_package.magics:MyMagics")

Its values may now be either ``"package.module"``, loaded as an IPython extension
as before, or ``"package.module:MagicsClass"``, imported and registered directly.
Unlike before, a magic declared through
:meth:`~IPython.core.magic.MagicsManager.register_lazy` shows up in ``%lsmagic``
and in completion right away rather than only after its first use.

Until a magic is loaded, ``shell.magics_manager.magics[kind][name]`` holds a
:class:`~IPython.core.magic.LazyMagic` placeholder. Calling it, or reading any
attribute of it, loads and delegates to the real magic, so existing code that
reaches into that table keeps working. A magics class only appears in
``shell.configurables`` once loaded; ``%config`` loads everything first, so the
list of configurable classes it shows is unchanged.

More startup work moved off the critical path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A second pass over what IPython does before it can show a prompt, on top of the
lazy imports and lazy magic registration. Nothing here is visible in normal
use; it is all work that used to happen on every start and is now either
avoided or postponed until something actually needs it.

* Resolving a theme's base pygments style no longer imports
  :mod:`pygments.styles`, and with it the pygments plugin machinery,
  :mod:`importlib.metadata` and :mod:`email`. Only the base style's ``styles``
  mapping was ever used, so for the builtin styles IPython's own themes are
  based on the defining module is read directly. Styles that are not builtin --
  including any provided by a pygments plugin -- still resolve exactly as
  before.

* Detecting whether the terminal speaks the kitty graphics protocol no longer
  imports psutil on Linux. The walk up the process tree needs each ancestor's
  name and parent pid, and ``/proc/<pid>/stat`` has both. macOS still uses
  psutil. This one only ever showed up in an actual terminal: a headless
  ``ipython -c ...`` stops at the ``isatty`` check before reaching it. Setting
  ``IPYTHON_KITTY_GRAPHICS`` still skips detection entirely.

* The prompt style is built the first time it is drawn rather than each of the
  several times it is invalidated while a shell is being set up, and not at all
  for a run that never draws a prompt.

* More single-use imports moved to their use sites: :mod:`platform`,
  :mod:`pprint`, :mod:`textwrap`, :mod:`html`, :mod:`mimetypes`,
  :mod:`locale`, :mod:`glob` and :mod:`runpy`. The AST operator tables the
  terminal shortcut filters need moved out of
  :mod:`IPython.core.guarded_eval` into a module of their own, so evaluating
  a shortcut's filter expression no longer imports the whole guarded
  evaluation machinery (and ``typing_extensions``). They are still importable
  from :mod:`IPython.core.guarded_eval`.

Together this takes another ~13% off starting an interactive ``ipython`` in a
real terminal, ~9% off ``ipython -c pass``, and another ~43 modules off an
interactive start, on top of the previous rounds.

Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.17
<https://github.com/ipython/ipython/milestone/169?closed=1>`__ milestone.

.. _version 9.16:

IPython 9.16
------------

Summary
~~~~~~~

This release contains two security-hardening fixes — HTML-attribute escaping in
the display objects and closing an arbitrary-code-execution path in completion —
a new ``cell_meta`` field on
:class:`~IPython.core.interactiveshell.ExecutionInfo`, several completion, autoreload,
and path-handling fixes, and two backwards-incompatible changes (:magic:`lsmagic`
default output and the removal of long-deprecated APIs). It also includes a
large amount of internal typing, test, and CI modernization.

- :ghpull:`15337` Resolve attribute annotations under the policy in :func:`~IPython.core.guarded_eval.eval_node`
- :ghpull:`15335` Make :magic:`lsmagic` return plain text by default
- :ghpull:`15334` Escape URLs and file names interpolated into display HTML attributes
- :ghpull:`15332` Add yakuake to the list of Kitty-compatible terminals
- :ghpull:`15330` Add version information to deprecation warnings
- :ghpull:`15317` Only substitute ``~`` in :func:`~IPython.utils.path.compress_user` on a path-component boundary
- :ghpull:`15314` Refactor banner property logic
- :ghpull:`15310` Deprecation cleanup and decorator-dependency removal
- :ghpull:`15289` Make caller locals visible to nested scopes in embedded shells
- :ghpull:`15288` Limit file completions to path contexts
- :ghpull:`15287` Centralize image format handling
- :ghpull:`15285` Disable path elision in tab-completion with ``min_elide=0``
- :ghpull:`15276` Make :class:`~IPython.display.Image` with ``retina=True`` work with WebP
- :ghpull:`15275` Fix memory leak and error handling in the LLM autosuggester
- :ghpull:`15274` Reload ``__kwdefaults__``, ``__annotations__``, and ``__type_params__`` in autoreload
- :ghpull:`15273` Close the history database during shell shutdown
- :ghpull:`15266` Add test covering ``%%timeit`` cell magic output format with multiline code
- :ghpull:`15260` Fix doctest prompt stripping regression
- :ghpull:`15071` Add ``cell_meta`` to :class:`~IPython.core.interactiveshell.ExecutionInfo` and pass it through :meth:`~IPython.core.interactiveshell.InteractiveShell.run_cell`

In addition, this release lands a broad sweep of internal maintenance: strict
``mypy`` type checking and many new annotations, ``pyupgrade``/modernized type
annotations, additional ``ruff`` rules, narrowed bare ``except:`` clauses,
removal of the deprecated ``IPython.utils.py3compat`` module, new test coverage,
and a number of test-suite resource-leak and CI fixes.


Security Hardening
~~~~~~~~~~~~~~~~~~~

Two fixes close paths that could execute unintended code or inject markup:

- Values passed to the display objects were interpolated unescaped into quoted
  HTML attributes, so a quote character could close the attribute and have the
  remainder parsed as markup. :class:`~IPython.display.Image` and
  :class:`~IPython.display.Video` (``src``), :class:`~IPython.display.IFrame`
  and its :class:`~IPython.display.YouTubeVideo`/:class:`~IPython.display.VimeoVideo`/:class:`~IPython.display.ScribdDocument`
  subclasses (``src``, ``width``, ``height``, reachable through the id argument),
  :class:`~IPython.display.Audio` (url and ``element_id``), and the
  :class:`~IPython.display.FileLinks` formatter (names read off disk) now escape
  these values. For example ``YouTubeVideo('abc"><script>')`` no longer closes
  the iframe and injects markup (:ghpull:`15334`).

- The attribute-completion branch in :func:`~IPython.core.guarded_eval.eval_node`
  fell back to :func:`typing.get_type_hints` after the completion policy had
  already refused an attribute. That call resolves stringized annotations with
  :func:`eval`, so completing ``obj.attr`` could run whatever an annotation
  contained under the default ``limited`` policy. Annotations are now collected
  with :func:`inspect.get_annotations` (``eval_str=False``) and resolved through
  :func:`~IPython.core.guarded_eval.eval_node`, routing them through the same
  policy checks as the rest of the input (:ghpull:`15337`).


``cell_meta`` in ``ExecutionInfo``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``cell_meta`` field is now part of the
:class:`~IPython.core.interactiveshell.ExecutionInfo` object passed to IPython
extensions in the ``pre_run_cell`` and ``post_run_cell`` callbacks, letting
extensions read per-cell metadata forwarded through
:meth:`~IPython.core.interactiveshell.InteractiveShell.run_cell`
(:ghpull:`15071`).


Completion Improvements
~~~~~~~~~~~~~~~~~~~~~~~~

File-name completions are now limited to contexts where a path is expected:
string literals, shell and magic contexts, and explicit path-looking tokens.
Direct path completion is preserved for prefixes such as ``./``, ``../``, ``~``,
absolute paths, and Windows drive paths, and ``name = !command`` shell
assignment is still recognized (:ghpull:`15288`, fixes :ghissue:`14501`).

Setting ``c.TerminalInteractiveShell.min_elide = 0`` now completely disables
filename abbreviation (path elision) in tab-completion output, for users who
prefer to always see full completion paths (:ghpull:`15285`).


Autoreload and Embedded Shells
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- :magic:`autoreload` now also refreshes ``__kwdefaults__``, ``__annotations__``,
  and ``__type_params__`` when reloading functions, keeping reloaded objects
  consistent with the edited source (:ghpull:`15274`).
- Local variables of the calling frame are now visible to nested scopes (such
  as comprehensions and nested functions) in embedded shells (:ghpull:`15289`).


Doctest Prompt Stripping Regression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A regression introduced in IPython 9.10 caused doctest prompts (``>>>`` and
``...``) to stop being stripped inside multiline strings, after the input
transformer's regex was tightened from ``\s`` to ``[ \t]`` to avoid eating
newlines on bare continuation lines. The prompt stripper now strips leading
PS1/PS2 prompts inside multiline strings only when they agree with the
indentation of the outer stripped prompts, so genuine ``>>>``/``...`` text
inside a multiline string is preserved (:ghpull:`15260`, fixes
:ghissue:`15259`).


Other Fixes
~~~~~~~~~~~

- :func:`~IPython.utils.path.compress_user` — the reverse of
  :func:`os.path.expanduser` used when
  displaying paths — tested ``path.startswith(home)`` with no path-component
  boundary, so a path merely sharing a string prefix with ``$HOME`` (for example
  ``/home/alice-backup/...`` when ``$HOME`` is ``/home/alice``) was rewritten
  into a different, nonexistent ``~``-path. The substitution now only happens on
  a path separator boundary (:ghpull:`15317`).
- :class:`~IPython.display.Image` with ``retina=True`` now works with WebP
  images (:ghpull:`15276`).
- A memory leak in the LLM autosuggester was fixed and its errors are now
  handled gracefully (:ghpull:`15275`).
- The history database is now closed during shell shutdown, avoiding a leaked
  connection (:ghpull:`15273`).
- ``yakuake`` is now recognized as a Kitty-graphics-compatible terminal
  (:ghpull:`15332`).


Backwards incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:magic:`lsmagic` now returns plain text by default so that frontends render its
human-readable output consistently. Use ``%lsmagic --json`` to retrieve the
machine-readable mapping of registered magics (:ghpull:`15335`).

A number of APIs that had been emitting deprecation warnings for several years
have been removed (:ghpull:`15310`):

- ``IPCompleter.limit_to__all__`` configuration option (deprecated since
  IPython 5.0). Completion on ``object.<tab>`` now always uses :func:`dir`-based
  discovery, regardless of ``__all__``.
- ``IPCompleter.python_matches`` method (deprecated since IPython 8.27). Use
  :meth:`~IPython.core.completer.IPCompleter.python_matcher` instead.
- ``OInfo.get()`` (deprecated since IPython 8.13). Access the dataclass fields
  directly, e.g. ``oinfo.found`` instead of ``oinfo.get('found')``.
- The module-level ``backends`` and ``backend2gui`` attributes of
  :mod:`IPython.core.pylabtools` (deprecated since IPython 8.24). Matplotlib
  backends are resolved by Matplotlib itself since 3.9.
- :meth:`~IPython.core.interactiveshell.InteractiveShell.run_cell_async` and
  :meth:`~IPython.core.interactiveshell.InteractiveShell.should_run_async` no
  longer call :meth:`~IPython.core.interactiveshell.InteractiveShell.transform_cell`
  automatically when ``transformed_cell`` is not passed (this fallback had
  emitted a :exc:`DeprecationWarning` since IPython 7.17); they now raise a
  :exc:`TypeError`. Run
  :meth:`~IPython.core.interactiveshell.InteractiveShell.transform_cell`
  yourself and pass the result via the ``transformed_cell`` keyword argument (as
  ipykernel 6.0 and newer already do).
  :meth:`~IPython.core.interactiveshell.InteractiveShell.run_cell` is unaffected.

The deprecated ``IPython.utils.py3compat`` module has also been removed, and its
utilities inlined at their call sites (:ghpull:`15292`).


Deprecations
~~~~~~~~~~~~

Deprecation warnings emitted by IPython now include the version in which the
feature was deprecated, making it easier to tell how long a warning has been
outstanding (:ghpull:`15330`).


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.16
<https://github.com/ipython/ipython/milestone/168?closed=1>`__ milestone.


.. _version 9.15:

IPython 9.15
------------

Summary
~~~~~~~

This release adds a new ``%xmode Doctest`` (:ghpull:`15185`) traceback mode and a number of
robustness fixes around startup, history storage, the debugger, and the Sphinx
directive. It also contains one backwards-incompatible change to :magic:`run` glob
expansion and one deprecation.

- :ghpull:`15220` Fix :magic:`debug` and ipdb with Python 3.15
- :ghpull:`15219` Add ``exception`` as an alias for the ``exceptions`` pdb command
- :ghpull:`15236` Hide ``execfile`` internals in debugger backtraces
- :ghissue:`15072`/:ghpull:`15246` Fix oinspect ``TypeError`` with objects using a generic ``__getattr__``
- :ghpull:`15249` Skip ipython directive execution inside excluded ``only`` blocks
- :ghissue:`15241`/:ghpull:`15255` Close SQLite connections before replacing the history database
- :ghissue:`15068`/:ghpull:`15255` Deprecate ``IPython.utils.generics.inspect_object``


- :ghpull:`15242` Use :meth:`~IPython.core.debugger.Pdb.print_stack_entry` to print frames on Python 3.14
- :ghpull:`15247` Avoid ``psutil`` requirement on Cygwin
- :ghpull:`15252` Narrow bare ``except:`` clauses in oinspect and interactiveshell
- :ghpull:`15253` Remove Python 2 references and fix links in the documentation
- :ghpull:`15254` Remove stale TODO comment in ``DisplayObject.reload``
- :ghissue:`15100` Fix test failures when the IPython source path contains spaces
- :ghissue:`15193` Honor PEP 263 coding cookies when reading sources in autoreload
- :ghissue:`12726` Quoted arguments to :magic:`run` no longer undergo glob expansion
- :ghissue:`11424` Strip ANSI escape sequences from Sphinx directive output
- :ghissue:`14538` Hide ``execfile`` frames in debugger backtraces


Doctest Traceback Mode
~~~~~~~~~~~~~~~~~~~~~~~~

A new ``%xmode Doctest`` mode formats tracebacks for easy copy-paste into
Python doctests. The output shows only the traceback header, a literal
ellipsis, and the exception line::

    Traceback (most recent call last):
        ...
    ZeroDivisionError: division by zero


Robust Startup and Terminal Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Kitty graphics protocol detection walks the process tree with ``psutil``
at import time. On shared multi-user systems where ``/proc`` is mounted with
``hidepid`` (common on HPC clusters), reaching an ancestor process owned by
another user raised ``psutil.AccessDenied``, which was unhandled and aborted
the entire ``import IPython``. Such errors are now caught and treated as
"graphics unsupported"; detection capability for the user's own terminals is
unchanged.

``psutil`` is also no longer required on Cygwin, where it is not available
(:ghpull:`15247`).


History Storage Robustness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``sqlite3.Connection`` used as a context manager only commits or rolls back;
it does not close the connection. ``ipython history trim`` and
``ipython history clear`` therefore still held open handles on
``history.sqlite`` when unlinking and renaming it, which failed with
``PermissionError`` on Windows and left ``history.sqlite.new*`` files behind.
The connections are now closed before any file shuffling (:ghissue:`15241`).


Debugger Fixes
~~~~~~~~~~~~~~

- :magic:`debug` and ipdb work again under Python 3.15, and frames are printed with
  :meth:`~IPython.core.debugger.Pdb.print_stack_entry` on Python 3.14 (:ghpull:`15220`, :ghpull:`15242`).
- ``execfile`` internals are now marked as the ``__ipython_bottom__`` traceback
  boundary, so the file runner and the frames above it are hidden as IPython
  internals while user script frames stay visible (:ghpull:`15236`,
  :ghissue:`14538`).
- ``exception`` is now accepted as an alias for the ``exceptions`` pdb command
  (:ghpull:`15219`).


Inspection (``?``) Fix
~~~~~~~~~~~~~~~~~~~~~~~~

Objects whose ``__getattr__`` returns something other than a ``dict`` for
``__custom_documentations__`` (e.g. a polars ``Expr``, which returns a new
``Expr`` for any attribute name) no longer raise a ``TypeError`` when inspected
with ``?`` or :func:`%pinfo`. The lookup is now guarded with ``isinstance(...,
dict)`` (:ghissue:`15072`).


Autoreload Encoding Fix
~~~~~~~~~~~~~~~~~~~~~~~~

The autoreload diffing logic now reads module sources with ``tokenize.open``,
honoring PEP 263 coding cookies the way the import system does, instead of
assuming UTF-8. Sources declaring another encoding were previously read as
empty, silently disabling hot-patching for those modules (:ghissue:`15193`).


Sphinx Directive Fixes
~~~~~~~~~~~~~~~~~~~~~~~~

The IPython Sphinx directive now strips ANSI escape sequences from executed
code-block output, so tracebacks and other colored output no longer appear as
garbled text in rendered HTML/PDF documentation (:ghissue:`11424`). Execution
is also now skipped inside excluded ``only`` blocks (:ghpull:`15249`).


Backwards incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wrapping a :magic:`run` argument in single or double quotes now suppresses glob
expansion of that argument, matching real shells. Previously quoting was
documented as *not* suppressing expansion, which was surprising. For example
with ``foo.txt`` and ``bar.txt`` in the working directory::

    %run script.py "*.txt"    # before: ['foo.txt', 'bar.txt']
                              # after:  ['*.txt']

The unquoted form (``%run script.py *.txt``) and the backslash-escape form
(``%run script.py \*.txt``) are unchanged. Pass ``-G`` to disable expansion
entirely (:ghissue:`12726`).


Deprecations
~~~~~~~~~~~~

``IPython.utils.generics.inspect_object`` is deprecated since IPython 9.15 and
will be removed in a future version. It is no longer used within IPython, so
registering handlers on it has no effect. :func:`~IPython.utils.generics.complete_object` is unaffected
(:ghissue:`15068`).


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.15
<https://github.com/ipython/ipython/milestone/165?closed=1>`__ milestone.


.. _version 9.14:

IPython 9.14
------------

Summary
~~~~~~~

This release is mostly a maintenance release, with fixes for SQLite history
handling, terminal image rendering, reproducible banner output, Pyodide
support, and a number of documentation improvements.

- :ghpull:`15204` Fix history memory fallback after SQLite lock
- :ghpull:`15208` Fix banner customization when ``SOURCE_DATE_EPOCH`` is set
- :ghpull:`15196` Handle stdout without ``isatty`` in kitty support check
- :ghpull:`15190` Avoid ``psutil`` requirement on emscripten
- :ghpull:`15206` Accept singular pdb exception command
- :ghpull:`15203` Fix incorrect ``Configuration`` type import
- :ghpull:`15179` Copyedit :std:configtrait:`prompt_line_number_format <TerminalInteractiveShell.prompt_line_number_format>` description
- :ghpull:`15209` Fix typos in user-facing documentation
- :ghpull:`15211` Fix duplicated words in ``usage.py`` and ``oinspect.py`` docstrings
- :ghpull:`15215` Fix terminal title config description
- :ghpull:`15218` Fix broken 'Edit on GitHub' link for auto-generated API docs
- :ghpull:`15224` Fix docstring formatting for :std:configtrait:`prompt_line_number_format <TerminalInteractiveShell.prompt_line_number_format>` help text


SQLite History Fallback Fix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When file-backed SQLite history could not create a new session (for example
because the ``history.sqlite`` file was locked by another running session), the
fallback only changed ``hist_file`` to ``:memory:`` while the existing
connection still pointed at the locked on-disk database. Later history writes
could therefore keep raising ``sqlite3.OperationalError: database is locked``.
The fallback now closes the current connection, switches to an in-memory
database, and creates a fresh history session there (:ghpull:`15204`).


Reproducible Banner Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Banner customization now honors the ``SOURCE_DATE_EPOCH`` environment variable,
fixing reproducible-build setups that pin the date (:ghpull:`15208`).


Terminal Image Rendering Robustness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Kitty graphics protocol support check now handles the case where ``stdout``
has no ``isatty`` method, avoiding an ``AttributeError`` in some embedded or
redirected-output environments (:ghpull:`15196`).


Pyodide / Emscripten Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython no longer requires ``psutil`` on the emscripten platform, where it is
not available (:ghpull:`15190`).


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.14
<https://github.com/ipython/ipython/milestone/164?closed=1>`__ milestone.


.. _version 9.13:

IPython 9.13
------------

Summary
~~~~~~~

This release includes native terminal image rendering via the Kitty graphics
protocol, a fix for illegible text in light-background themes, Python 3.11
support restoration, and type annotation corrections.

- :ghpull:`15184` Implement support for ``image/png`` format in terminal
- :ghpull:`15175` Restore Python 3.11 support with conditional imports
- :ghpull:`15156` Fix illegible yellow text on yellow background in light themes
- :ghpull:`15172` Fix ``CapturedIO.__init__`` type annotations to accept ``Optional[StringIO]``
- :ghpull:`15180` Clarify custom prompts example in documentation
- :ghpull:`15182` Update Contributing.md


Terminal Image Rendering via Kitty Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython now renders ``image/png`` MIME output natively in supported terminals
using the `Kitty graphics protocol
<https://sw.kovidgoyal.net/kitty/graphics-protocol/>`_. Objects such as
``PIL.Image`` instances and SymPy expressions rendered with
``sympy.init_printing(use_latex="png")`` will display as actual inline images
in Kitty, Ghostty, and other compatible terminals. No configuration is required
(:ghpull:`15184`, closes :ghissue:`13287`).


Python 3.11 Support Restored
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.11 support has been restored. While IPython follows `SPEC-0
<https://scientific-python.org/specs/spec-0000/>`__ for determining the minimum
supported Python version, continued Python 3.11 support is funded by the
`D. E. Shaw group <https://deshaw.com/>`_ (:ghpull:`15175`).


Theme-Aware Output Color Fix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Text that was previously rendered in a fixed yellow color—causing it to be
illegible on terminals with a light or yellow background—is now rendered using
a theme-aware color (:ghpull:`15156`, fixes :ghissue:`14901`).


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython including extended Python 3.11 support.

As usual, you can find the full list of PRs on GitHub under `the 9.13
<https://github.com/ipython/ipython/milestone/162?closed=1>`__ milestone.


.. _version 9.12:

IPython 9.12
------------

Security Update
~~~~~~~~~~~~~~~

This include a fix for `CVE-2025-30167
<https://github.com/jupyter/jupyter_core/security/advisories/GHSA-33p9-3p43-82vq>`__
that also affects IPython and should have been fixed as the same time than
Jupyter-Core. This will be backported to 9.10.1 and 8.39

Summary
~~~~~~~

This release includes traceback rendering improvements, a SQLite resource leak fix,
Python 3.15 compatibility, and type annotation additions.

- :ghpull:`15167` Fix missing space in pdb chained exceptions warning message
- :ghpull:`15166` Interleave fast path when rendering large tracebacks
- :ghpull:`15165` Include function names when using the fast-traceback path
- :ghpull:`15163` Fix expected length in ``test_unicode_range`` for Python 3.15 alpha 7
- :ghpull:`15157` Clarify :magic:`xmode` docstring with mode descriptions
- :ghpull:`15152` Use ``weakref.finalize`` to close SQLite connections
- :ghpull:`15146` Add runtime type annotations to ``IPython.utils`` via MonkeyType
- :ghpull:`15164` Add return type hint in ``alias.py``
- :ghpull:`15160` Add return type hints in ``compilerop.py``


Traceback Rendering Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fast traceback path (used when ``stack_data`` is unavailable or too slow) now
includes function names in all frames (:ghpull:`15165`), and large tracebacks now
interleave the fast and slow rendering paths (:ghpull:`15166`) to preserve syntax
highlighting on functions that live in small modules.


SQLite Resource Leak Fix
~~~~~~~~~~~~~~~~~~~~~~~~

SQLite connections are now closed via ``weakref.finalize`` instead of ``__del__``.
This eliminates ``ResourceWarning`` leaks that could surface when running tests
with ``-W error``.


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.12
<https://github.com/ipython/ipython/milestone/161?closed=1>`__ milestone.


.. _version 9.11:

IPython 9.11
------------

This release includes a new shell error-handling config option, a reproducible
banner for builds, history thread management improvements, autoreload encoding
fixes, Python 3.11 deprecation notices, and various type annotation improvements.

- :ghpull:`15073` Add :std:configtrait:`system_raise_on_error <InteractiveShell.system_raise_on_error>` config option for ``!`` shell operator
- :ghpull:`15121` Start dropping Python 3.11
- :ghpull:`15122` Fix encoding to utf8 for autoreload
- :ghpull:`15130` Stricter config + add typing to ``IPython/core/magic.py``
- :ghpull:`15133` Inline and remove only usage of ``on_off``
- :ghpull:`15144` Have a static banner when setting ``SOURCE_DATE_EPOCH``

In addition there are many type annotations that have been added by using Generative AI (Clause Sonnet and Opus from
Anthropicl; GitHub Copilot)



New ``system_raise_on_error`` Config Option
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A new :std:configtrait:`system_raise_on_error <InteractiveShell.system_raise_on_error>` Bool traitlet configuration option (default:
``False``) has been added. When set to ``True``, shell commands executed via
the ``!`` operator will raise :exc:`subprocess.CalledProcessError` if they
return a non-zero exit status. This makes it easier to write robust IPython
scripts that need to detect shell command failures::

    %config InteractiveShell.system_raise_on_error = True
    ! false  # will now raise CalledProcessError


Reproducible Banner
~~~~~~~~~~~~~~~~~~~~

When the ``SOURCE_DATE_EPOCH`` environment variable is set, IPython now
produces a static, reproducible banner. This
helps with reproducible builds and packaging workflows that may capture this state
(related to
`jupyterlab/jupyterlab#18552 <https://github.com/jupyterlab/jupyterlab/issues/18552>`_).


Python 3.11 Deprecation (Reverted in 9.13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The deprecation of Python 3.11 announced in 9.11 has been reverted in 9.13.
Python 3.11 support is maintained thanks to funding from the
`D. E. Shaw group <https://deshaw.com/>`_.


Autoreload Encoding Fix
~~~~~~~~~~~~~~~~~~~~~~~~

The autoreload extension now explicitly sets UTF-8 as the default encoding
when reading source files. Previously, the platform default encoding was
used, which could cause failures on systems where the default encoding is
not UTF-8.

Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.11
<https://github.com/ipython/ipython/milestone/160?closed=1>`__ milestone.


.. _version 9.10:

IPython 9.10
------------

This release includes improvements to history management during forking and formatting fixes.

- :ghpull:`15110` Fix Removing leading indentation when stripping prompt
- :ghpull:`15115` Stop HistorySavingThread before fork
- :ghpull:`15118` Add debug info for autoreload


History Thread Management Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~IPython.core.history.HistorySavingThread` is now properly stopped before process forking,
preventing threading issues in child processes. This ensures that history
operations work correctly when IPython is used in applications that perform
process forking.


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.10
<https://github.com/ipython/ipython/milestone/159?closed=1>`__ milestone.


.. _version 9.9:

IPython 9.9
-----------

This release includes several bug fixes and improvements across completions,
type annotations, and developer experience.

- :ghpull:`15092` Fix formatting for completion suggestions section
- :ghpull:`15057` Reduce types in splitinput.py
- :ghpull:`15096` Use Any type in traceback tuple
- :ghpull:`15099` Fix filename of CVE test
- :ghpull:`15091` Skip downstream CI if only docs changes
- :ghpull:`15093` Replace sphinxext/github with extlink configuration
- :ghpull:`15103` Tips and docs about argcomplete
- :ghpull:`15105` Add prompt_toolkit's unix_word_rubout to assignable commands for shortcuts
- :ghpull:`15095` Enable pretty-printing for PEP-649 annotated functions
- :ghpull:`15106` Fix completions for methods starting with ``_``
- :ghpull:`15111` Stop assuming that memory addresses are signed
- :ghpull:`15102` Bump macOS runner version in GitHub Actions
- :ghpull:`15101` Fix crash on literal with surrogate

Improvements to PEP-649 Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython now properly pretty-prints functions with PEP-649 style annotations.
This improves the display of functions in interactive sessions when using Python
3.14+ annotation semantics.


Shell Shortcuts Enhancement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``unix_word_rubout`` command from prompt_toolkit is now available as an
assignable command for terminal shortcuts, giving users more flexibility in
customizing their keybindings.


Type Annotation Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Various type annotation improvements have been made throughout the codebase for
better static analysis support, including fixes for tracebacks and improved type
inference in the completion engine.


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.9
<https://github.com/ipython/ipython/milestone/157?closed=1>`__ milestone.


.. _version 9.8:

IPython 9.8
-----------

This release brings improvements to concurrent execution, history commands, tab
completion, and debugger performance.


- :ghpull:`15037` Fix some ruff issues with import
- :ghpull:`15060` Stricter typing for many utils files
- :ghpull:`15066` Strict typing of a few more files
- :ghpull:`15067` Fix self import of deprecated items
- :ghpull:`15069` Document :magic:`history` usage with all lines of a session
- :ghpull:`15070` Allow session number without trailing slash in :magic:`history` magic
- :ghpull:`15074` Use values for tab completion of variables created using annotated assignment
- :ghpull:`15076` Fix error on tab completions
- :ghpull:`15078` Show completions for annotated union types
- :ghpull:`15079` Fallback to type annotations for attribute completions
- :ghpull:`15081` Strictly suppress file completions in attribute completion context
- :ghpull:`15083` Minor performance improvements in debugger
- :ghpull:`15084` Documentation updates
- :ghpull:`15088` Make :any:`run_cell_async` reenterable for concurrent cell execution


Concurrent Cell Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :any:`run_cell_async` method is now reenterable, making the execution count
more atomic and preventing session resets when cells are executed concurrently.
This allows frontends to run multiple cells in parallel without interfering with
each other's execution context or history tracking. The execution count is now
incremented before running the user code, ensuring consistent behavior across
concurrent executions.


History Magic Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :magic:`history` magic now supports open-ended line ranges using ``-`` as the end
marker. For example, you can use ``%history 1/10-`` to retrieve all commands from
line 10 onwards in session 1, or ``%history ~5-`` to get the last 5 commands and
onwards from the current session. This makes it easier to retrieve ranges of
commands without needing to know the exact ending line number.


Tab Completion Enhancements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several improvements were made to the tab completer, particularly when jedi is
disabled:

- Variables created with annotated assignment (e.g., ``x: int = 5``) now use
  their runtime values for completion suggestions, providing more accurate
  attribute completions.

- File path completions are now strictly suppressed when completing attributes,
  preventing confusion when typing patterns like ``obj.file``.

- Union types in annotations (e.g., ``x: int | str``) are now properly handled
  for completion suggestions.

- The completer now falls back to type annotations when runtime evaluation is
  not available, improving completion accuracy for typed code.


Thanks
~~~~~~

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.8
<https://github.com/ipython/ipython/milestone/156?closed=1>`__ milestone.


.. _version 9.7:

IPython 9.7
-----------

As ususal this new version of IPython brings a number of bugfixes:


- :ghpull:`15012` Fix ``Exception.text`` may be None
- :ghpull:`15007` Start Testign on free-threaded Python
- :ghpull:`15036` Suppress file completions in context of attributes/methods
- :ghpull:`15056` Completion in loops and conditionals
- :ghpull:`15048` Support completions for lambdas and ``async`` functions
- :ghpull:`15042` Support subscript assignment in completions
- :ghpull:`15027` Infer type from return value and improve attribute completions
- :ghpull:`15020` Fix tab completion for subclasses of trusted classes
- :ghpull:`15022` Prevent trusting modules with matching prefix


Gruvbox Dark Theme
~~~~~~~~~~~~~~~~~~

Gruvbox Dark is now available as a terminal syntax theme for IPython.

Respect PYTHONSAFEPATH
~~~~~~~~~~~~~~~~~~~~~~

IPython now respects the value of Python's flag ``sys.flags.safe_path``, a flag which is most often set by the ``PYTHONSAFEPATH`` environment variable. Setting this causes Python not to automatically include the current working directory in the sys.path.

IPython can already be configured to do this via the ``--ignore_cwd`` command-line flag or by setting ``c.InteractiveShellApp.ignore_cwd=True``. Now, IPython can also be configured by setting ``PYTHONSAFEPATH=1`` or by calling python with ``-P``.

The behavior of ``safe_path`` was described in `what's new in 3.11`_ and in `PyConfig.safe_path <https://docs.python.org/3/c-api/init_config.html#c.PyConfig.safe_path>`_.


.. _what's new in 3.11: https://docs.python.org/3/whatsnew/3.11.html#whatsnew311-pythonsafepath


Tab Completion
~~~~~~~~~~~~~~

Multiple improvements were made to the tab completer.
The tab completions now work for more complex code, even when jedi is disabled, using a hybrid evaluation procedure
which infers available completions from both the typing information, runtime values, and static code analysis.
The paths to hidden files are no longer suggested when attempting attribute completion.


As usual, you can find the full list of PRs on GitHub under `the 9.7
<https://github.com/ipython/ipython/milestone/155?closed=1>`__ milestone.


.. _version 9.6:

IPython 9.6
-----------

This version brings improvements to tab completion, :magic:`notebook` magic, module ignoring functionality to debugger.

- :ghpull:`14973` Add module ignoring functionality to debugger
- :ghpull:`14982` Extract code from line magics for attribute completion
- :ghpull:`14998` Fix matplotlib plots displaying in wrong cells during :magic:`notebook` export
- :ghpull:`14996` Respect ``DisplayFormatter.active_types`` trait configuration
- :ghpull:`15001` Fix :magic:`notebook` magic creating multiple display_data outputs for single widgets
- :ghpull:`14997` Make :magic:`notebook` magic notarise exported notebooks (mark as trusted)
- :ghpull:`14993` Type-guided partial evaluation for completion of uninitialized variables
- :ghpull:`14978` deduperreload: patch NULL for empty closure rather than None
- :ghpull:`14994` Bump minimum version (spec-0) and whitespace update

The :magic:`notebook` magic can now reliably export plots generated by ``matplotlib``, whether with the default ``inline`` or the interactive ``ipympl`` backend.
For the plots to display when using the ``inline`` backend the ``c.DisplayFormatter.active_types`` needs to include ``image/png`` (or another image media type, depending on the backend configuration).

Tab completion now works on multi-line buffers with unevaluated code even when jedi is disabled.
Additionally, completion works when writing code as an argument to :magic:`timeit` and :magic:`debug`.

As usual, you can find the full list of PRs on GitHub under `the 9.6
<https://github.com/ipython/ipython/milestone/154?closed=1>`__ milestone.


.. _version 9.5:

IPython 9.5
-----------

Featuring improvements for numerous magics (:magic:`autoreload`, :magic:`whos`, :cellmagic:`script`, ``%%notebook``), a streaming performance regression fix, completer policy overrides improvements, and initial support for Python 3.14.

- :ghpull:`14938` Fix printing long strings in :magic:`whos` magic command
- :ghpull:`14941` Fix performance of streaming long text
- :ghpull:`14943` Simplify overriding selective evaluation policy settings for modules
- :ghpull:`14955` Populate notebook metadata when exporting with :magic:`notebook` magic
- :ghpull:`14960` Better handling in deduperreload for patching functions with freevars
- :ghpull:`14964` Fix traceback logic for non-SyntaxError exceptions in plain mode
- :ghpull:`14966` Do not warn repeatedly if policy overrides are not applicable
- :ghpull:`14967` Support Python 3.14.0rc2, test on CI
- :ghpull:`14969` Fix truncated output in ``%script`` magic
- :ghpull:`14970` Fix exceptions in :magic:`whos` magic command

The :magic:`notebook` magic now stores the language and kernel information in notebook metadata, allowing users to quickly open the exported notebook with syntax highlighting and an appropriate kernel.

The completer :std:configtrait:`Completer.policy_overrides` traitlet handling was improved.
It no longer repeatedly warns on each completion after switching away to a policy that does not support previously specified overrides.
Allow-listing attribute access on all objects in a given library is now possible.
The specification now also accepts dotted strings (rather than requiring tuples to specify the path) which should make configuration easier and less error-prone.

.. code::

    c.Completer.policy_overrides = {
        "allowed_getattr_external": {
            "my_trusted_library"
        }
    }

A number of recent regressions were fixed:

- :magic:`autoreload` now again shows the correct module name in traceback
- standard output/error streaming of long text/logs is now as fast as in IPython 9.0
- in the :magic:`whos` magic handling of long strings and class objects that implement ``__len__`` was fixed.

As usual, you can find the full list of PRs on GitHub under `the 9.5
<https://github.com/ipython/ipython/milestone/153?closed=1>`__ milestone.


.. _version 9.4:

IPython 9.4
-----------

Featuring :magic:`autoreload`, :magic:`whos`, :cellmagic:`script`, ``%%time`` magic improvements, along with a fix for use of list comprehensions and generators in the interactive debugger (and ipdb).

- :ghpull:`14922` Improved reloading of decorated functions when using :magic:`autoreload`
- :ghpull:`14872` Do not always import all variables with ``%autoreload 3``
- :ghpull:`14906` Changed behaviour of :magic:`time` magic to always interrupt execution on exception and always show execution time
- :ghpull:`14926` Support data frames, series, and objects with ``__len__`` in the :magic:`whos` magic
- :ghpull:`14933` List comprehensions and generators now work reliably in debugger on all supported Python versions
- :ghpull:`14931` Fix streaming multi-byte Unicode characters in the ``%script`` magic and its derivatives

The :magic:`time` magic no longer swallows exceptions raised by the measured
code, and always prints the time of execution. If you wish the execution to
continue after measuring time to execute code that is meant to raise an
exception, pass the new ``--no-raise-error`` flag. The ``--no-raise-error`` flag
does not affect ``KeyboardInterrupt`` as this exception is used to signal
intended interruption of execution flow.

Previously the debugger (ipdb) evaluation of list comprehensions and generators
could fail with ``NameError`` due to generator implementation detail in CPython.
This was recently fixed in Python 3.13. Because IPython is often used for
interactive debugging, this release includes a backport of that fix, providing
users who cannot yet update from Python 3.11 or 3.12 with a smoother debugging
experience.

The :magic:`autoreload` magic is now more reliable. The behaviour around
decorators has been improved and ``%autoreload 3`` no longer imports all symbols
when reloading the module, however, the heuristic used to determine which
symbols to reload can sometimes lead to addition of imports from non-evaluated
code branches, see `issue #14934
<https://github.com/ipython/ipython/issues/14934>`__.


As usual, you can find the full list of PRs on GitHub under `the 9.4
<https://github.com/ipython/ipython/milestone/151?closed=1>`__ milestone.



.. _version 9.3:

IPython 9.3
-----------

This release includes improvements to the tab and LLM completer, along with typing improvements:

- :ghpull:`14911` Implement auto-import and evaluation policy overrides
- :ghpull:`14910` Eliminate startup delay when LLM completion provider is configured
- :ghpull:`14898` Fix attribute completion for expressions with comparison operators
- :ghpull:`14908` Fix typing of `error_before_exec`, enhance ``mypy`` coverage

Notably, the native completer can now suggest attribute completion on not-yet-imported modules.
This is particularly useful when writing code which includes an import and the use of the imported
module in the same line or in the same cell; the default implementation does not insert
the imported module into the user namespace, for which an actual execution is required.

The auto-import of modules by completer is turned off and requires opting-in using
a new :std:configtrait:`Completer.policy_overrides` traitlet.
To enable auto-import on completion specify:

.. code-block::

    ipython --Completer.policy_overrides='{"allow_auto_import": True}' --Completer.use_jedi=False

This change aligns the capability of both jedi-powered and the native completer.
The function used for auto-import can be configured using :std:configtrait:`Completer.auto_import_method` traitlet.

As usual, you can find the full list of PRs on GitHub under `the 9.3
<https://github.com/ipython/ipython/milestone/149?closed=1>`__ milestone.


.. _version 9.2:

IPython 9.2
-----------

This is a small release with minor changes in the context passed to the LLM completion
provider along few other bug fixes and documentation improvements:

- :ghpull:`14890` Fixed interruption of ``%%time`` and ``%%debug`` magics
- :ghpull:`14877` Removed spurious empty lines from ``prefix`` passed to LLM, and separated part after cursor into the ``suffix``
- :ghpull:`14876` Fixed syntax warning in Python 3.14 (remove return from finally block)
- :ghpull:`14887` Documented the recommendation to use ``ipykernel.embed.embed_kernel()`` over ``ipython.embed``.

As usual, you can find the full list of PRs on GitHub under `the 9.2
<https://github.com/ipython/ipython/milestone/146?closed=1>`__ milestone.

.. _version 9.1:

IPython 9.1
-----------

This is a small release that introduces enhancements to :magic:`notebook` and ``%%timeit`` magics,
and a number of bug fixes related to colors/formatting, performance, and completion.

``%notebook`` saves outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :magic:`notebook` magic can be used to create a Jupyter notebook from the
commands executed in the current IPython session (since the interpreter startup).

Prior to IPython 9.1, the resulting notebook did not include the outputs,
streams, or exceptions. IPython 9.1 completes the implementation of this
magic allowing for an easier transition from an interactive IPython session
to a Jupyter notebook.

To capture streams (stdio/stderr), IPython temporarily swaps the `write`
method of the active stream class during code execution. This ensures
compatibility with ipykernel which swaps the entire stream implementation
and requires it to remain an instance of ``IOStream`` subclass.
If this leads to undesired behaviour in any downstream applications,
your feedback and suggestions would be greatly appreciated.


``%%timeit -v`` argument
~~~~~~~~~~~~~~~~~~~~~~~~

New ``-v`` argument allows users to save the timing result
directly to a specified variable, e.g.

.. code::

   %%timeit -v timing_result
   2**32


Completer improvements
~~~~~~~~~~~~~~~~~~~~~~

The LLM-based completer will now receive the request number for each subsequent
execution.

The tab completer used when jedi is turned off now correctly completes
variables in lines where it previously was incorrectly attempting to complete
attributes due to simplistic context detection based on the presence of a dot.

Thanks
~~~~~~

A big thank you to everyone who contributed towards the 9.1 release,
including new contributors: @Darshan808, @kwinkunks, @carschandler,
returning contributors (shout out to @wjandrea!), and of course
@Carreau whom I would like to thank for the guidance in the preparation
of this release and stewardship of IPython over the years - Mike.

As usual, you can find the full list of PRs on GitHub under `the 9.1
<https://github.com/ipython/ipython/milestone/142?closed=1>`__ milestone.


.. _version90:

IPython 9.0
-----------

Welcome to IPython 9.0. As with any version of IPython before this release, it
should not be majorly different from the previous version, at least on the surface.
We still hope you can upgrade as soon as possible and look forward to your feedback.

I take the opportunity of this new release to remind you that IPython is
governed by the `Jupyter code of conduct
<https://jupyter.org/governance/conduct/code_of_conduct.html>`_. And that even
beyond so we strive to be an inclusive, accepting and progressive community,
Here is a relevant extract from the COC.

    We strive to be a community that welcomes and supports people of all backgrounds
    and identities. This includes, but is not limited to, members of any race,
    ethnicity, culture, national origin, color, immigration status, social and
    economic class, educational level, sex, sexual orientation, gender identity and
    expression, age, physical appearance, family status, technological or
    professional choices, academic discipline, religion, mental ability, and
    physical ability.


As a short overview of the changes in 9.0, we have over 100 PRs merged since 8.x,
many of which are refactors, cleanups and simplifications.

 - (optional) LLM integration in the CLI.
 - Complete rewrite of color and theme handling, which now supports more colors and symbols.
 - Move tests out of tree in the wheel with a massive reduction in file size.
 - Tips at startup
 - Removal of (almost) all deprecated functionalities and options.
 - Stricter and more stable codebase.


Removal and deprecation
~~~~~~~~~~~~~~~~~~~~~~~

I am not going to list the removals and deprecations, but anything deprecated since before IPython 8.16 is gone,
including many shim modules and indirect imports that would just re-expose IPykernel, qtconsole, etc.

A number of new deprecations have been added (run your test suites with `-Werror`), as those will be removed in the future.


Color and theme rewrite
~~~~~~~~~~~~~~~~~~~~~~~

IPython's color handling had grown many options through the years, and it was
quite entrenched in the codebase, directly emitting ansi escape sequences deep
in traceback printing and other places.

This made developing new color schemes difficult, and limited us to the 16 colors
of the original ansi standard defined by your terminal.

Syntax highlighting was also inconsistent, and not all syntax elements were
always using the same theme.

Using (style, token) pairs
^^^^^^^^^^^^^^^^^^^^^^^^^^

Starting with 9.0, the color and theme handling has been rewritten, and
internally all the printing is done by yielding pairs of Style and token objects
(compatible with pygments and prompt_toolkit), then as much as possible, IPython
formats these objects at the last moment, using the current theme.

256-bit colors and unicode symbols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This means that new themes can now use all of pygments's color names and
functionalities, and you can define for each token style, the foreground,
background, underline, bold, italic and likely a few other options.

In addition, themes now provide a number of `symbols`, that can be used when
rendering traceback or debugger prompts. This let you customize the appearance a
bit more. For example, instead of using dash and greater-than sign, The arrow
pointing the current frame can actually use horizontal line and right arrow
unicode symbol, for a more refined experience.


New themes using colors and symbols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All the existing themes (Linux, LightBG, Neutral and NoColor) should not see any
changes, but I added two new *pride themes*, that show the use of 256bits colors
and unicode symbols. I'm not a designer, so feel free to suggest updates and new
themes to add.

Themes  currently still require writing a bit of Python, but I hope to get
contributions for IPython to be able to load them from text files, for easier
redistribution.

Tips at startup
~~~~~~~~~~~~~~~

IPython now displays a few tips at startup (1 line), to help you discover new features.
All those are in the codebase, and can be displayed randomly or based on date.
You can disable it via a configuration option or the ``--no-tips`` flag.

Please contribute more tips by sending pull requests!

Out-of-tree tests
~~~~~~~~~~~~~~~~~

And more generally I have changed the folder structure and what is packaged in
the wheel to reduce the file size. The wheel is down from 825kb to 590kb
(-235kb) which is about a 28% reduction. This should help when you run IPython
via Pyodide – when your browser needs to download it.

According to https://pypistats.org/packages/ipython, IPython is downloaded about
13 million times per week, so this should reduce PyPI bandwidth by about 2Tb each
week, which is small compared to the total download, but still, trying to reduce
resource usage is a worthy goal.

Integration with Jupyter-AI LLM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This feature allow IPython CLI to make use of Jupyter-AI provider to use LLM for
suggestion, and completing the current text. Unlike many features
of IPython this is disabled by default, and need several configuration options to
be set to work:

 - Choose a provider in ``jupyter-ai`` and set it as default one:
   ``c.TerminalInteractiveShell.llm_provider_class = <fully qualified path>``
   You likely need to setup your provider with API key or other things.
 - Choose and available shortcut (I'll take ``Ctrl-Q`` as an example) and bind
   to trigger ``llm_autosuggestion`` only while typing.

.. code::

   c.TerminalInteractiveShell.shortcuts = [
        {
            "new_keys": ["c-q"],
            "command": "IPython:auto_suggest.llm_autosuggestion",
            "new_filter": "navigable_suggestions & default_buffer_focused",
            "create": True,
        },
    ]

See :ref:`llm_suggestions` for more.

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
this work.


For something completely different
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ruth Bader Ginsburg 1933-2020 was an American lawyer and jurist who served on
the Supreme Court of the United States. Ginsburg spent much of her legal career
as an advocate for gender equality, women's rights, abortion rights, and religious
freedom.

Thanks
~~~~~~

Thanks to everyone who helped with the 9.0 release and working toward 9.0.

As usual you can find the full list of PRs on GitHub under `the 9.0
<https://github.com/ipython/ipython/milestone/138?closed=1>`__ milestone.

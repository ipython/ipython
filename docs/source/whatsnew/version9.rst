============
 9.x Series
============


.. _version 9.9:

IPython 9.9
===========

This release includes several bug fixes and improvements across completions, type annotations, and developer experience.

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
-------------------------------

IPython now properly pretty-prints functions with PEP-649 style annotations. This improves the display of functions in interactive sessions when using Python 3.14+ annotation semantics.


Shell Shortcuts Enhancement
-----------------------------

The ``unix_word_rubout`` command from prompt_toolkit is now available as an assignable command for terminal shortcuts, giving users more flexibility in customizing their keybindings.


Type Annotation Improvements
----------------------------

Various type annotation improvements have been made throughout the codebase for better static analysis support, including fixes for tracebacks and improved type inference in the completion engine.


Thanks
------

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.9
<https://github.com/ipython/ipython/milestone/157?closed=1>`__ milestone.


.. _version 9.8:

IPython 9.8
===========

This release brings improvements to concurrent execution, history commands, tab completion, and debugger performance.


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
--------------------------

The :any:`run_cell_async` method is now reenterable, making the execution count
more atomic and preventing session resets when cells are executed concurrently.
This allows frontends to run multiple cells in parallel without interfering with
each other's execution context or history tracking. The execution count is now
incremented before running the user code, ensuring consistent behavior across
concurrent executions.


History Magic Improvements
---------------------------

The :magic:`history` magic now supports open-ended line ranges using ``-`` as the end
marker. For example, you can use ``%history 1/10-`` to retrieve all commands from
line 10 onwards in session 1, or ``%history ~5-`` to get the last 5 commands and
onwards from the current session. This makes it easier to retrieve ranges of
commands without needing to know the exact ending line number.


Tab Completion Enhancements
----------------------------

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
------

Thanks as well to the `D. E. Shaw group <https://deshaw.com/>`_ for sponsoring
work on IPython.

As usual, you can find the full list of PRs on GitHub under `the 9.8
<https://github.com/ipython/ipython/milestone/156?closed=1>`__ milestone.


.. _version 9.7:

IPython 9.7
===========

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
------------------

Gruvbox Dark is now available as a terminal syntax theme for IPython.

Respect PYTHONSAFEPATH
----------------------

IPython now respects the value of Python's flag ``sys.flags.safe_path``, a flag which is most often set by the ``PYTHONSAFEPATH`` environment variable. Setting this causes Python not to automatically include the current working directory in the sys.path.

IPython can already be configured to do this via the ``--ignore_cwd`` command-line flag or by setting ``c.InteractiveShellApp.ignore_cwd=True``. Now, IPython can also be configured by setting ``PYTHONSAFEPATH=1`` or by calling python with ``-P``.

The behavior of ``safe_path`` was described in `what's new in 3.11`_ and in `PyConfig.safe_path <https://docs.python.org/3/c-api/init_config.html#c.PyConfig.safe_path>`_.


.. _what's new in 3.11: https://docs.python.org/3/whatsnew/3.11.html#whatsnew311-pythonsafepath


Tab Completion
--------------

Multiple improvements were made to the tab completer.
The tab completions now work for more complex code, even when jedi is disabled, using a hybrid evaluation procedure
which infers available completions from both the typing information, runtime values, and static code analysis.
The paths to hidden files are no longer suggested when attempting attribute completion.


As usual, you can find the full list of PRs on GitHub under `the 9.7
<https://github.com/ipython/ipython/milestone/155?closed=1>`__ milestone.


.. _version 9.6:

IPython 9.6
===========

This version brings improvements to tab completion, ``%notebook`` magic, module ignoring functionality to debugger.

- :ghpull:`14973` Add module ignoring functionality to debugger
- :ghpull:`14982` Extract code from line magics for attribute completion
- :ghpull:`14998` Fix matplotlib plots displaying in wrong cells during ``%notebook`` export
- :ghpull:`14996` Respect ``DisplayFormatter.active_types`` trait configuration
- :ghpull:`15001` Fix ``%notebook`` magic creating multiple display_data outputs for single widgets
- :ghpull:`14997` Make ``%notebook`` magic notarise exported notebooks (mark as trusted)
- :ghpull:`14993` Type-guided partial evaluation for completion of uninitialized variables
- :ghpull:`14978` deduperreload: patch NULL for empty closure rather than None
- :ghpull:`14994` Bump minimum version (spec-0) and whitespace update

The ``%notebook`` magic can now reliably export plots generated by ``matplotlib``, whether with the default ``inline`` or the interactive ``ipympl`` backend.
For the plots to display when using the ``inline`` backend the ``c.DisplayFormatter.active_types`` needs to include ``image/png`` (or another image media type, depending on the backend configuration).

Tab completion now works on multi-line buffers with unevaluated code even when jedi is disabled.
Additionally, completion works when writing code as an argument to ``%timeit`` and ``%debug``.

As usual, you can find the full list of PRs on GitHub under `the 9.6
<https://github.com/ipython/ipython/milestone/154?closed=1>`__ milestone.


.. _version 9.5:

IPython 9.5
===========

Featuring improvements for numerous magics (``%autoreload``, ``%whos``, ``%%script``, ``%%notebook``), a streaming performance regression fix, completer policy overrides improvements, and initial support for Python 3.14.

- :ghpull:`14938` Fix printing long strings in ``%whos`` magic command
- :ghpull:`14941` Fix performance of streaming long text
- :ghpull:`14943` Simplify overriding selective evaluation policy settings for modules
- :ghpull:`14955` Populate notebook metadata when exporting with ``%notebook`` magic
- :ghpull:`14960` Better handling in deduperreload for patching functions with freevars
- :ghpull:`14964` Fix traceback logic for non-SyntaxError exceptions in plain mode
- :ghpull:`14966` Do not warn repeatedly if policy overrides are not applicable
- :ghpull:`14967` Support Python 3.14.0rc2, test on CI
- :ghpull:`14969` Fix truncated output in ``%script`` magic
- :ghpull:`14970` Fix exceptions in ``%whos`` magic command

The ``%notebook`` magic now stores the language and kernel information in notebook metadata, allowing users to quickly open the exported notebook with syntax highlighting and an appropriate kernel.

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

- ``%autoreload`` now again shows the correct module name in traceback
- standard output/error streaming of long text/logs is now as fast as in IPython 9.0
- in the ``%whos`` magic handling of long strings and class objects that implement ``__len__`` was fixed.

As usual, you can find the full list of PRs on GitHub under `the 9.5
<https://github.com/ipython/ipython/milestone/153?closed=1>`__ milestone.


.. _version 9.4:

IPython 9.4
===========

Featuring ``%autoreload``, ``%whos``, ``%%script``, ``%%time`` magic improvements, along with a fix for use of list comprehensions and generators in the interactive debugger (and ipdb).

- :ghpull:`14922` Improved reloading of decorated functions when using ``%autoreload``
- :ghpull:`14872` Do not always import all variables with ``%autoreload 3``
- :ghpull:`14906` Changed behaviour of ``%time`` magic to always interrupt execution on exception and always show execution time
- :ghpull:`14926` Support data frames, series, and objects with ``__len__`` in the ``%whos`` magic
- :ghpull:`14933` List comprehensions and generators now work reliably in debugger on all supported Python versions
- :ghpull:`14931` Fix streaming multi-byte Unicode characters in the ``%script`` magic and its derivatives

The ``%time`` magic no longer swallows exceptions raised by the measured code, and always prints the time of execution. If you wish the execution to continue after measuring time to execute code that is meant to raise an exception, pass the new ``--no-raise-error`` flag.
The ``--no-raise-error`` flag does not affect ``KeyboardInterrupt`` as this exception is used to signal intended interruption of execution flow.

Previously the debugger (ipdb) evaluation of list comprehensions and generators could fail with ``NameError`` due to generator implementation detail in CPython. This was recently fixed in Python 3.13. Because IPython is often used for interactive debugging, this release includes a backport of that fix, providing users who cannot yet update from Python 3.11 or 3.12 with a smoother debugging experience.

The ``%autoreload`` magic is now more reliable. The behaviour around decorators has been improved and `%autoreload 3` no longer imports all symbols when reloading the module, however, the heuristic used to determine which symbols to reload can sometimes lead to addition of imports from non-evaluated code branches, see `issue #14934 <https://github.com/ipython/ipython/issues/14934>`__.


As usual, you can find the full list of PRs on GitHub under `the 9.4
<https://github.com/ipython/ipython/milestone/151?closed=1>`__ milestone.



.. _version 9.3:

IPython 9.3
===========

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
===========

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
===========

This is a small release that introduces enhancements to ``%notebook`` and ``%%timeit`` magics,
and a number of bug fixes related to colors/formatting, performance, and completion.

``%notebook`` saves outputs
---------------------------

The ``%notebook`` magic can be used to create a Jupyter notebook from the
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
------------------------

New ``-v`` argument allows users to save the timing result
directly to a specified variable, e.g.

.. code::

   %%timeit -v timing_result
   2**32


Completer improvements
----------------------

The LLM-based completer will now receive the request number for each subsequent
execution.

The tab completer used when jedi is turned off now correctly completes
variables in lines where it previously was incorrectly attempting to complete
attributes due to simplistic context detection based on the presence of a dot.

Thanks
------

A big thank you to everyone who contributed towards the 9.1 release,
including new contributors: @Darshan808, @kwinkunks, @carschandler,
returning contributors (shout out to @wjandrea!), and of course
@Carreau whom I would like to thank for the guidance in the preparation
of this release and stewardship of IPython over the years - Mike.

As usual, you can find the full list of PRs on GitHub under `the 9.1
<https://github.com/ipython/ipython/milestone/142?closed=1>`__ milestone.


.. _version90:

IPython 9.0
===========

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
-----------------------

I am not going to list the removals and deprecations, but anything deprecated since before IPython 8.16 is gone, 
including many shim modules and indirect imports that would just re-expose IPykernel, qtconsole, etc. 

A number of new deprecations have been added (run your test suites with `-Werror`), as those will be removed in the future. 


Color and theme rewrite
-----------------------

IPython's color handling had grown many options through the years, and it was
quite entrenched in the codebase, directly emitting ansi escape sequences deep
in traceback printing and other places. 

This made developing new color schemes difficult, and limited us to the 16 colors
of the original ansi standard defined by your terminal. 

Syntax highlighting was also inconsistent, and not all syntax elements were
always using the same theme.

Using (style, token) pairs 
~~~~~~~~~~~~~~~~~~~~~~~~~~

Starting with 9.0, the color and theme handling has been rewritten, and
internally all the printing is done by yielding pairs of Style and token objects
(compatible with pygments and prompt_toolkit), then as much as possible, IPython
formats these objects at the last moment, using the current theme.

256-bit colors and unicode symbols
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This means that new themes can now use all of pygments's color names and
functionalities, and you can define for each token style, the foreground,
background, underline, bold, italic and likely a few other options. 

In addition, themes now provide a number of `symbols`, that can be used when
rendering traceback or debugger prompts. This let you customize the appearance a
bit more. For example, instead of using dash and greater-than sign, The arrow
pointing the current frame can actually use horizontal line and right arrow
unicode symbol, for a more refined experience.


New themes using colors and symbols
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the existing themes (Linux, LightBG, Neutral and NoColor) should not see any
changes, but I added two new *pride themes*, that show the use of 256bits colors
and unicode symbols. I'm not a designer, so feel free to suggest updates and new
themes to add. 

Themes  currently still require writing a bit of Python, but I hope to get
contributions for IPython to be able to load them from text files, for easier
redistribution.

Tips at startup
---------------

IPython now displays a few tips at startup (1 line), to help you discover new features.
All those are in the codebase, and can be displayed randomly or based on date. 
You can disable it via a configuration option or the ``--no-tips`` flag. 

Please contribute more tips by sending pull requests!

Out-of-tree tests
-----------------

And more generally I have changed the folder structure and what is packaged in
the wheel to reduce the file size. The wheel is down from 825kb to 590kb
(-235kb) which is about a 28% reduction. This should help when you run IPython
via Pyodide – when your browser needs to download it.

According to https://pypistats.org/packages/ipython, IPython is downloaded about
13 million times per week, so this should reduce PyPI bandwidth by about 2Tb each
week, which is small compared to the total download, but still, trying to reduce
resource usage is a worthy goal.

Integration with Jupyter-AI LLM
-------------------------------

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
----------------------------------

Ruth Bader Ginsburg 1933-2020 was an American lawyer and jurist who served on
the Supreme Court of the United States. Ginsburg spent much of her legal career
as an advocate for gender equality, women's rights, abortion rights, and religious
freedom.

Thanks
------

Thanks to everyone who helped with the 9.0 release and working toward 9.0.

As usual you can find the full list of PRs on GitHub under `the 9.0
<https://github.com/ipython/ipython/milestone/138?closed=1>`__ milestone.




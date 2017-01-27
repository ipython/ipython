============
 5.x Series
============


IPython 5.2
===========

* restore IPython's debugger to raise on quit. :ghpull:`10009`
* Add a ``catch_signal`` configuration option to
  :any:`TerminalInteractiveShell` and try to cleanly exit on SIGTERM and
  SIGHUP. :ghpull:`10185`


IPython 5.1
===========

* Broken ``%timeit`` on Python2 due to the use of ``__qualname__``. :ghpull:`9804`
* Restore ``%gui qt`` to create and return a ``QApplication`` if necessary. :ghpull:`9789`
* Don't set terminal title by default. :ghpull:`9801`
* Preserve indentation when inserting newlines with ``Ctrl-O``. :ghpull:`9770`
* Restore completion in debugger. :ghpull:`9785`
* Deprecate ``IPython.core.debugger.Tracer()`` in favor of simpler, newer, APIs. :ghpull:`9731`
* Restore ``NoOpContext`` context manager removed by mistake, and add `DeprecationWarning`. :ghpull:`9765`
* Add option allowing ``Prompt_toolkit`` to use 24bits colors. :ghpull:`9736`
* Fix for closing interactive matplotlib windows on OS X. :ghpull:`9854`
* An embedded interactive shell instance can be used more than once. :ghpull:`9843`
* More robust check for whether IPython is in a terminal. :ghpull:`9833`
* Better pretty-printing of dicts on PyPy. :ghpull:`9827`
* Some coloured output now looks better on dark background command prompts in Windows.
  :ghpull:`9838`
* Improved tab completion of paths on Windows . :ghpull:`9826`
* Fix tkinter event loop integration on Python 2 with ``future`` installed. :ghpull:`9824`
* Restore ``Ctrl-\`` as a shortcut to quit IPython.
* Make ``get_ipython()`` accessible when modules are imported by startup files. :ghpull:`9818`
* Add support for running directories containing a ``__main__.py`` file with the
  ``ipython`` command. :ghpull:`9813`


True Color feature
------------------

``prompt_toolkit`` uses pygments styles for syntax highlighting. By default, the
colors specified in the style are approximated using a standard 256-color
palette. ``prompt_toolkit`` also supports 24bit, a.k.a. "true", a.k.a. 16-million
color escape sequences which enable compatible terminals to display the exact
colors specified instead of an approximation. This true_color option exposes
that capability in prompt_toolkit to the IPython shell.

Here is a good source for the current state of true color support in various
terminal emulators and software projects: https://gist.github.com/XVilka/8346728



IPython 5.0
===========

Released July 7, 2016

New terminal interface
----------------------

IPython 5 features a major upgrade to the terminal interface, bringing live
syntax highlighting as you type, proper multiline editing and multiline paste,
and tab completions that don't clutter up your history.

.. image:: ../_images/ptshell_features.png
    :alt: New terminal interface features
    :align: center
    :target: ../_images/ptshell_features.png

These features are provided by the Python library `prompt_toolkit
<http://python-prompt-toolkit.readthedocs.io/en/stable/>`__, which replaces
``readline`` throughout our terminal interface.

Relying on this pure-Python, cross platform module also makes it simpler to
install IPython. We have removed dependencies on ``pyreadline`` for Windows and
``gnureadline`` for Mac.

Backwards incompatible changes
------------------------------

- The ``%install_ext`` magic function, deprecated since 4.0, has now been deleted.
  You can distribute and install extensions as packages on PyPI.
- Callbacks registered while an event is being handled will now only be called
  for subsequent events; previously they could be called for the current event.
  Similarly, callbacks removed while handling an event *will* always get that
  event. See :ghissue:`9447` and :ghpull:`9453`.
- Integration with pydb has been removed since pydb development has been stopped
  since 2012, and pydb is not installable from PyPI.
- The ``autoedit_syntax`` option has apparently been broken for many years.
  It has been removed.

New terminal interface
~~~~~~~~~~~~~~~~~~~~~~

The overhaul of the terminal interface will probably cause a range of minor
issues for existing users.
This is inevitable for such a significant change, and we've done our best to
minimise these issues.
Some changes that we're aware of, with suggestions on how to handle them:

IPython no longer uses readline configuration (``~/.inputrc``). We hope that
the functionality you want (e.g. vi input mode) will be available by configuring
IPython directly (see :doc:`/config/options/terminal`).
If something's missing, please file an issue.

The ``PromptManager`` class has been removed, and the prompt machinery simplified.
See :ref:`custom_prompts` to customise prompts with the new machinery.

:mod:`IPython.core.debugger` now provides a plainer interface.
:mod:`IPython.terminal.debugger` contains the terminal debugger using
prompt_toolkit.

There are new options to configure the colours used in syntax highlighting.
We have tried to integrate them with our classic  ``--colors`` option and
``%colors`` magic, but there's a mismatch in possibilities, so some configurations
may produce unexpected results. See :ref:`termcolour` for more information.

The new interface is not compatible with Emacs 'inferior-shell' feature. To
continue using this, add the ``--simple-prompt`` flag to the command Emacs
runs. This flag disables most IPython features, relying on Emacs to provide
things like tab completion.

Provisional Changes
-------------------

Provisional changes are experimental functionality that may, or may not, make
it into a future version of IPython, and which API may change without warnings.
Activating these features and using these API are at your own risk, and may have
security implication for your system, especially if used with the Jupyter notebook,

When running via the Jupyter notebook interfaces, or other compatible client,
you can enable rich documentation experimental functionality:

When the ``docrepr`` package is installed setting the boolean flag
``InteractiveShell.sphinxify_docstring`` to ``True``, will process the various
object through sphinx before displaying them (see the ``docrepr`` package
documentation for more information.

You need to also enable the IPython pager display rich HTML representation
using the ``InteractiveShell.enable_html_pager`` boolean configuration option.
As usual you can set these configuration options globally in your configuration
files, alternatively you can turn them on dynamically using the following
snippet:

.. code-block:: python

    ip = get_ipython()
    ip.sphinxify_docstring = True
    ip.enable_html_pager = True


You can test the effect of various combinations of the above configuration in
the Jupyter notebook, with things example like :

.. code-block:: ipython

    import numpy as np
    np.histogram?


This is part of an effort to make Documentation in Python richer and provide in
the long term if possible dynamic examples that can contain math, images,
widgets... As stated above this is nightly experimental feature with a lot of
(fun) problem to solve. We would be happy to get your feedback and expertise on
it.



Deprecated Features
-------------------

Some deprecated features are listed in this section. Don't forget to enable
``DeprecationWarning`` as an error if you are using IPython in a Continuous
Integration setup or in your testing in general:

.. code-block:: python

    import warnings
    warnings.filterwarnings('error', '.*', DeprecationWarning, module='yourmodule.*')


- ``hooks.fix_error_editor`` seems unused and is pending deprecation.
- `IPython/core/excolors.py:ExceptionColors` is  deprecated.
- `IPython.core.InteractiveShell:write()` is deprecated; use `sys.stdout` instead.
- `IPython.core.InteractiveShell:write_err()` is deprecated; use `sys.stderr` instead.
- The `formatter` keyword argument to `Inspector.info` in `IPython.core.oinspec` has no effect.
- The `global_ns` keyword argument of IPython Embed was deprecated, and has no effect. Use `module` keyword argument instead.


Known Issues:
-------------

- ``<Esc>`` Key does not dismiss the completer and does not clear the current
  buffer. This is an on purpose modification due to current technical
  limitation. Cf :ghpull:`9572`. Escape the control character which is used
  for other shortcut, and there is no practical way to distinguish. Use Ctr-G
  or Ctrl-C as an alternative.

- Cannot use ``Shift-Enter`` and ``Ctrl-Enter`` to submit code in terminal. cf
  :ghissue:`9587` and :ghissue:`9401`. In terminal there is no practical way to
  distinguish these key sequences from a normal new line return.

- ``PageUp`` and ``pageDown`` do not move through completion menu.

- Color styles might not adapt to terminal emulator themes. This will need new
  version of Pygments to be released, and can be mitigated with custom themes.



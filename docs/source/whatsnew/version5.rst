============
 5.x Series
============

IPython 5.0
===========

Released June, 2016

IPython 5.0 now uses `prompt-toolkit` for the command line interface, thus
allowing real multi-line editing and syntactic coloration as you type.


When using IPython as a subprocess, like for emacs inferior-shell, IPython can
be started with --simple-prompt flag, which will bypass the prompt_toolkit
input layer. In this mode completion, prompt color and many other features are
disabled.

Backwards incompatible changes
------------------------------


The `install_ext magic` function which was deprecated since 4.0 have now been deleted.
You can still distribute and install extension as packages on PyPI.

Update IPython event triggering to ensure callback registration and
unregistration only affects the set of callbacks the *next* time that event is
triggered. See :ghissue:`9447` and :ghpull:`9453`.

This is a change to the existing semantics, wherein one callback registering a
second callback when triggered for an event would previously be invoked for
that same event.

Integration with pydb has been removed since pydb development has been stopped
since 2012, and pydb is not installable from PyPI



Replacement of readline in TerminalInteractiveShell and PDB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython 5.0 now uses ``prompt_toolkit``. The
``IPython.terminal.interactiveshell.TerminalInteractiveShell`` now uses
``prompt_toolkit``. It is an almost complete rewrite, so many settings have
thus changed or disappeared. The class keep the same name to avoid breaking
user configuration for the options which names is unchanged.

The usage of ``prompt_toolkit`` is accompanied by a complete removal of all
code, using ``readline``. A particular effect of not using `readline` anymore
is that `.inputrc` settings are note effective anymore. Options having similar
effects have likely been replaced by a configuration option on IPython itself
(e.g: vi input mode).

The `PromptManager` class have been removed, and the prompt machinery simplified.
See `TerminalInteractiveShell.prompts` configurable for how to setup your prompts.

.. note::

    During developement and beta cycle, ``TerminalInteractiveShell`` was
    temporarly moved to ``IPtyhon.terminal.ptshell``.


Most of the above remarks also affect `IPython.core.debugger.Pdb`, the `%debug`
and `%pdb` magic which do not use readline anymore either.

The color handling has been slightly changed and is now exposed
through, in particular the colors of prompts and as you type
highlighting can be affected by :
``TerminalInteractiveShell.highlight_style``. With default
configuration the ``--colors`` flag and ``%colors`` magic behavior
should be mostly unchanged. See the `colors <termcolour>`_ section of
our documentation

Provisional Changes
-------------------

Provisional changes are in experimental functionality that may, or may not make
it to future version of IPython, and which API may change without warnings.
Activating these feature and using these API is at your own risk, and may have
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


Removed Feature
---------------

- ``TerminalInteractiveShell.autoedit_syntax`` Has been broken for many years now
  apparently. It has been removed.


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



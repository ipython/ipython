============
 5.x Series
============

IPython 5.0
===========

Released June, 2016

IPython 5.0 now uses `promt-toolkit` for the command line interface, thus
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

IPython 5.0 now uses prompt_toolkit, so any setting that affects ``readline`` will
have no effect, and has likely been replaced by a configuration option on
IPython itself.

the `PromptManager` class have been removed, and the prompt machinery simplified. 
See `TerminalINteractiveShell.prompts` configurable for how to setup your prompts. 



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

.. code-block:: python

    import numpy as np
    np.histogram?

This is part of an effort to make Documentation in Python richer and provide in
the long term if possible dynamic examples that can contain math, images,
widgets... As stated above this is nightly experimental feature with a lot of
(fun) problem to solve. We would be happy to get your feedback and expertise on
it.

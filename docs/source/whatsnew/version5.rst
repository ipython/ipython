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


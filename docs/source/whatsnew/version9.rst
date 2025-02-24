============
 9.x Series
============

.. _version90:

IPython 9.0
===========

Welcome to IPython 9.0, as for amny version of IPython befoer this release, it
should not be majorly different from the previous version, at least on the surface. 
We still hope you can upgrade as soon as possible amd look forward to your feedback. 

As a short overview of the changes, we have over 100 PRs merged between 8.x and
9.0, many of those are refactor, cleanup and simplifications.

 - (optional) LLM interation in the CLI. 
 - Complete rewrite of color and theme handling, wich now supports more colors, and symbols. 
 - Move tests out of tree in the wheel with a massive reductin in filesize. 
 - Tips at startup
 - Removel of (almost) all deprecated functionalities and options.
 - Stricter and more stable codebase.


Removal and deprecations
------------------------

I am not going to list of the removal and deprecations, but anything deprecated since before IPython 8.16 is gone, 
this include many shim modules, and indirect imports that would just reexpose IPykernel, qtconsole, etc. 

A number of new deprecations have been added (run your test suites with `-Werror`), as those will be removed in the future. 


Color and theme rewrite
-----------------------

IPython's color handeling had grown many options through the years, and it was
quite entranched in the codebase, directly emitting ansi escape sequences deep
in traceback printing and other places. 

This made developping new color scheme difficult, and limtted us the the 16 colors
of the original ansi standard defined by your terminal. 

Syntax highlighting was also inconsistant, and not all syntax elements were
always using the same theme.

Using (style, token) pairs 
~~~~~~~~~~~~~~~~~~~~~~~~~~

Starting with 9.0, the color and theme handling has been rewritten, in
internally all the printing is done by yielding pairs of Style and token objects
(compatible with pygments and prompt_toolkit), then as much as possible, IPython
format these objects at the last moment, using the current theme.

256 bits colors and unicode symbols
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This means that new themes can now use all of pygments's color names, and
functionalities, andyou can define for each toke style, the foreground,
background, underline, bold, italic and likely a few other options. 

In addition, themes now provide a number of `symbols`, that can be used when
redering traceback or debugger prompts, this let yuo customize the appearance a
bt more. FOr example, instead of using dash and greater than sign, The arrow
pointing the current fframe can actully use horizontal line and right arrow
unicode symbol, for a more refined exprience.


New themes using colors and symbols
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the existing themes (Linux, LightBG, Neutral and Nocolor) should not see any
changes, but I added two new *pride themes*, that show the use of 256bits colors
and unicode symbols. I' not a designer, so feel free to suggest updates, and new
themes to add. 

Themes  currently still requires writing a bit of Python, but I hope to get
contributions for IPython to be able to load them from text files, for eaier
redistribution.

Tips at startup
---------------

IPython now displays a few tips at startup (1 line), to help you discover new features.
All those are in the codebase, and can be displayed randomly or based on date. 
You can disable it, via a configuration option, or the ``--no-tips`` flag. 

Please contribute more tips by sending pull requests !























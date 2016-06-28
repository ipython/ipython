=======================
Specific config details
=======================

.. _termcolour:

Terminal Colors
===============

The default IPython configuration has most bells and whistles turned on
(they're pretty safe). But there's one that may cause problems on some
systems: the use of color on screen for displaying information. This is
very useful, since IPython can show prompts and exception tracebacks
with various colors, display syntax-highlighted source code, and in
general make it easier to visually parse information.

The following terminals seem to handle the color sequences fine:

    * Linux main text console, KDE Konsole, Gnome Terminal, E-term,
      rxvt, xterm.
    * CDE terminal (tested under Solaris). This one boldfaces light colors.
    * (X)Emacs buffers. See the :ref:`emacs` section for more details on
      using IPython with (X)Emacs.
    * A Windows (XP/2k) CygWin shell. Although some users have reported
      problems; it is not clear whether there is an issue for everyone
      or only under specific configurations. If you have full color
      support under cygwin, please post to the IPython mailing list so
      this issue can be resolved for all users.

These have shown problems:

    * Windows command prompt in WinXP/2k logged into a Linux machine via
      telnet or ssh.
    * Windows native command prompt in WinXP/2k, without Gary Bishop's
      extensions. Once Gary's readline library is installed, the normal
      WinXP/2k command prompt works perfectly.

IPython uses colors for various groups of things that may be
controlled by different configuration options: prompts, tracebacks, "as
you type" in the terminal, and the object introspection system which
passes large sets of data through a pager. There are various way to
change the colors.

We can distinguish the coloration into 2 main categories:

- The one that affects only the terminal client.
- The ones that also affect clients connected through the Jupyter
  protocol.

Traceback, debugger, and pager are highlighted kernel-side so they fall into
the second category. For historical reasons they are often governed by a
``colors`` attribute or configuration option that can take one of 3 case
insensitive values: ``Neutral``, ``NoColors``, ``Linux`` and ``LightBG``.

Colors that affect only the terminal client are governed mainly by
``TerminalInteractiveShell.highlight_style`` taking the name of a
``Pygments`` style.

As of IPython 5.0 the color configuration works as follows:

  - by default, ``TerminalInteractiveShell.highlight_style`` is set to
    ``legacy`` with a default colors scheme of ``Neutral`` that should be
    readable both on light and dark background terminals.
    
    This setting also **trys to** emulate the colors of IPython pre 5.0 and
    respect the ``.color`` configuration option for ``Linux`` and ``LightBG``.
    The emulation is an approximation of the current version of Pygments (2.1)
    and only supports extended ANSI escape sequence, hence the theme cannot
    adapt to your terminal custom mapping if you have one.

    The last extra difference being that the "as you type" coloration
    is present using the theme "default" if `color` is `LightBG`, and
    using the theme "monokai" if `Linux`.

  - if ``TerminalInteractiveShell.highlight_style`` is set to any other
    themes, this theme is used for "as you type" highlighting. The
    prompt highlighting is then governed by
    ``--TerminalInteractiveShell.highlighting_style_overrides``

As a summary, by default IPython 5.0 should mostly behave unchanged
from IPython 4.x and before. Use
``TerminalInteractiveShell.highlight_style`` and
``--TerminalInteractiveShell.highlighting_style_overrides`` for extra
flexibility.

With default configuration, `--colors=[nocolors|linux|lightbg]` as well
as the `%colors` magic should behave identically as before.


Colors in the pager
-------------------

On some systems, the default pager has problems with ANSI colour codes.
To configure your default pager to allow these:

1. Set the environment PAGER variable to ``less``.
2. Set the environment LESS variable to ``-r`` (plus any other options
   you always want to pass to less by default). This tells less to
   properly interpret control sequences, which is how color
   information is given to your terminal.




.. _editors:

Editor configuration
====================

IPython can integrate with text editors in a number of different ways:

* Editors (such as `(X)Emacs`_, vim_ and TextMate_) can
  send code to IPython for execution.

* IPython's ``%edit`` magic command can open an editor of choice to edit
  a code block.

The %edit command (and its alias %ed) will invoke the editor set in your
environment as :envvar:`EDITOR`. If this variable is not set, it will default
to vi under Linux/Unix and to notepad under Windows. You may want to set this
variable properly and to a lightweight editor which doesn't take too long to
start (that is, something other than a new instance of Emacs). This way you
can edit multi-line code quickly and with the power of a real editor right
inside IPython.

You can also control the editor by setting :attr:`TerminalInteractiveShell.editor`
in :file:`ipython_config.py`.

Vim
---

Paul Ivanov's `vim-ipython <https://github.com/ivanov/vim-ipython>`_ provides
powerful IPython integration for vim.

.. _emacs:

(X)Emacs
--------

If you are a dedicated Emacs user, and want to use Emacs when IPython's
``%edit`` magic command is called you should set up the Emacs server so that
new requests are handled by the original process. This means that almost no
time is spent in handling the request (assuming an Emacs process is already
running). For this to work, you need to set your EDITOR environment variable
to 'emacsclient'. The code below, supplied by Francois Pinard, can then be
used in your :file:`.emacs` file to enable the server:

.. code-block:: common-lisp

    (defvar server-buffer-clients)
    (when (and (fboundp 'server-start) (string-equal (getenv "TERM") 'xterm))
      (server-start)
      (defun fp-kill-server-with-buffer-routine ()
        (and server-buffer-clients (server-done)))
      (add-hook 'kill-buffer-hook 'fp-kill-server-with-buffer-routine))

Thanks to the work of Alexander Schmolck and Prabhu Ramachandran,
currently (X)Emacs and IPython get along very well in other ways.

With (X)EMacs >= 24, You can enable IPython in python-mode with:

.. code-block:: common-lisp

    (require 'python)
    (setq python-shell-interpreter "ipython")

.. _`(X)Emacs`: http://www.gnu.org/software/emacs/
.. _TextMate: http://macromates.com/
.. _vim: http://www.vim.org/

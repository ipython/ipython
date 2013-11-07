=======================
Specific config details
=======================

Prompts
=======

In the terminal, the format of the input and output prompts can be
customised. This does not currently affect other frontends.

The following codes in the prompt string will be substituted into the
prompt string:

======  ===================================  =====================================================
Short   Long                                 Notes
======  ===================================  =====================================================
%n,\\#  {color.number}{count}{color.prompt}  history counter with bolding
\\N     {count}                              history counter without bolding
\\D     {dots}                               series of dots the same width as the history counter
\\T     {time}                               current time
\\w     {cwd}                                current working directory
\\W     {cwd_last}                           basename of CWD
\\Xn    {cwd_x[n]}                           Show the last n terms of the CWD. n=0 means show all.
\\Yn    {cwd_y[n]}                           Like \Xn, but show '~' for $HOME
\\h                                          hostname, up to the first '.'
\\H                                          full hostname
\\u                                          username (from the $USER environment variable)
\\v                                          IPython version
\\$                                          root symbol ("$" for normal user or "#" for root)
``\\``                                       escaped '\\'
\\n                                          newline
\\r                                          carriage return
n/a     {color.<Name>}                       set terminal colour - see below for list of names
======  ===================================  =====================================================

Available colour names are: Black, BlinkBlack, BlinkBlue, BlinkCyan,
BlinkGreen, BlinkLightGray, BlinkPurple, BlinkRed, BlinkYellow, Blue,
Brown, Cyan, DarkGray, Green, LightBlue, LightCyan, LightGray, LightGreen,
LightPurple, LightRed, Purple, Red, White, Yellow. The selected colour
scheme also defines the names *prompt* and *number*. Finally, the name
*normal* resets the terminal to its default colour.

So, this config::

     c.PromptManager.in_template = "{color.LightGreen}{time}{color.Yellow} \u{color.normal}>>>"

will produce input prompts with the time in light green, your username
in yellow, and a ``>>>`` prompt in the default terminal colour.


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
    * A Windows (XP/2k) command prompt with pyreadline_.
    * A Windows (XP/2k) CygWin shell. Although some users have reported
      problems; it is not clear whether there is an issue for everyone
      or only under specific configurations. If you have full color
      support under cygwin, please post to the IPython mailing list so
      this issue can be resolved for all users.

.. _pyreadline: https://code.launchpad.net/pyreadline
      
These have shown problems:

    * Windows command prompt in WinXP/2k logged into a Linux machine via
      telnet or ssh.
    * Windows native command prompt in WinXP/2k, without Gary Bishop's
      extensions. Once Gary's readline library is installed, the normal
      WinXP/2k command prompt works perfectly.

Currently the following color schemes are available:

    * NoColor: uses no color escapes at all (all escapes are empty '' ''
      strings). This 'scheme' is thus fully safe to use in any terminal.
    * Linux: works well in Linux console type environments: dark
      background with light fonts. It uses bright colors for
      information, so it is difficult to read if you have a light
      colored background.
    * LightBG: the basic colors are similar to those in the Linux scheme
      but darker. It is easy to read in terminals with light backgrounds.

IPython uses colors for two main groups of things: prompts and
tracebacks which are directly printed to the terminal, and the object
introspection system which passes large sets of data through a pager.

If you are seeing garbage sequences in your terminal and no colour, you
may need to disable colours: run ``%colors NoColor`` inside IPython, or
add this to a config file::

    c.InteractiveShell.colors = 'NoColor'

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

.. note::

    You will need to use a recent enough version of :file:`python-mode.el`,
    along with the file :file:`ipython.el`. You can check that the version you
    have of :file:`python-mode.el` is new enough by either looking at the
    revision number in the file itself, or asking for it in (X)Emacs via ``M-x
    py-version``. Versions 4.68 and newer contain the necessary fixes for
    proper IPython support.

The file :file:`ipython.el` is included with the IPython distribution, in the
directory :file:`docs/emacs`. Once you put these files in your Emacs path, all
you need in your :file:`.emacs` file is:

.. code-block:: common-lisp

    (require 'ipython)

This should give you full support for executing code snippets via
IPython, opening IPython as your Python shell via ``C-c !``, etc.

You can customize the arguments passed to the IPython instance at startup by
setting the ``py-python-command-args`` variable.  For example, to start always
with ``matplotlib`` integration and hardcoded light-background colors, you can use:

.. code-block:: common-lisp

    (setq py-python-command-args '("--matplotlib" "--colors" "LightBG"))

If you happen to get garbage instead of colored prompts as described in
the previous section, you may need to set also in your :file:`.emacs` file:

.. code-block:: common-lisp

    (setq ansi-color-for-comint-mode t)

Notes on emacs support:

.. This looks hopelessly out of date - can someone update it?

* There is one caveat you should be aware of: you must start the IPython shell
  before attempting to execute any code regions via ``C-c |``. Simply type
  ``C-c !`` to start IPython before passing any code regions to the
  interpreter, and you shouldn't experience any problems. This is due to a bug
  in Python itself, which has been fixed for Python 2.3, but exists as of
  Python 2.2.2 (reported as SF bug [ 737947 ]).

* The (X)Emacs support is maintained by Alexander Schmolck, so all
  comments/requests should be directed to him through the IPython mailing
  lists.

* This code is still somewhat experimental so it's a bit rough around the
  edges (although in practice, it works quite well).

* Be aware that if you customized ``py-python-command`` previously, this value
  will override what :file:`ipython.el` does (because loading the customization
  variables comes later).

.. _`(X)Emacs`: http://www.gnu.org/software/emacs/
.. _TextMate: http://macromates.com/
.. _vim: http://www.vim.org/

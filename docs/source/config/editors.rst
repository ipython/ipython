.. _editors:

====================
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

TextMate
========

Currently, TextMate support in IPython is broken.  It used to work well,
but the code has been moved to :mod:`IPython.quarantine` until it is updated.

Vim
===

Paul Ivanov's `vim-ipython <https://github.com/ivanov/vim-ipython>`_ provides
powerful IPython integration for vim.

.. _emacs:

(X)Emacs
========

If you are a dedicated Emacs user, and want to use Emacs when IPython's
``%edit`` magic command is called you should set up the Emacs server so that
new requests are handled by the original process. This means that almost no
time is spent in handling the request (assuming an Emacs process is already
running). For this to work, you need to set your EDITOR environment variable
to 'emacsclient'. The code below, supplied by Francois Pinard, can then be
used in your :file:`.emacs` file to enable the server::

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
you need in your :file:`.emacs` file is::

    (require 'ipython)

This should give you full support for executing code snippets via
IPython, opening IPython as your Python shell via ``C-c !``, etc.

You can customize the arguments passed to the IPython instance at startup by
setting the ``py-python-command-args`` variable.  For example, to start always
in ``pylab`` mode with hardcoded light-background colors, you can use::

    (setq py-python-command-args '("-pylab" "-colors" "LightBG"))

If you happen to get garbage instead of colored prompts as described in
the previous section, you may need to set also in your :file:`.emacs` file::

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

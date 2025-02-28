==============================
Specific configuration details
==============================

.. _llm_suggestions:

LLM Suggestions
===============

Starting with 9.0, IPython will be able to use LLM providers to suggest code in
the terminal. This requires a recent version of prompt_toolkit in order to allow
multiline suggestions. There are currently a number of limitations, and feedback
on the API is welcome.

Unlike many of IPython features, this is not enabled by default and requires
multiple configuration options to be set to properly work:

 - Set a keybinding to trigger LLM suggestions. Due to terminal limitations
   across platforms and emulators, it is difficult to provide a default
   keybinding. Note that not all keybindings are availables, in particular all
   the `Ctrl-Enter`, `Alt-backslash` and `Ctrl-Shift-Enter` are not available
   without integration with your terminal emulator.

 - Chose a LLM `provider`, usually from Jupyter-AI. This will be the interface
   between IPython itself, and the LLM – that may be local or in on a server.

 - Configure said provider with models, API keys, etc – this will depend on the
   provider, and you will have to refer to Jupyter-AI documentation, and/or your
   LLM documenatation.


While setting up IPython to use a real LLM, you can refer to
``examples/auto_suggest_llm.py`` that both provide an example of how to set up
IPython to use a Fake LLM provider, this can help ensure that the full setup is
working before switching to a real LLM provider.


Setup a keybinding
------------------

You may want to refer on how to setup a keybinding in IPython, but in short you
want to bind the ``IPython:auto_suggest.llm_autosuggestion`` command to a
keybinding, and have it active only when the default buffer isi focused, and
when using the NavigableSuggestions suggestter (this is the default suggestter,
the one that is history and LLM aware). Thus the ``navigable_suggestions &
default_buffer_focused`` filter should be used.

Usually ``Ctrl-Q`` on macos is an available shortcut, note that is does use
``Ctrl``, and not ``Command``.

The following example will bind ``Ctrl-Q`` to the ``llm_autosuggestion``
command, with the suggested filter::

    c.TerminalInteractiveShell.shortcuts = [
        {
            "new_keys": ["c-q"],
            "command": "IPython:auto_suggest.llm_autosuggestion",
            "new_filter": "navigable_suggestions & default_buffer_focused",
            "create": True,
        },
    ]


Choose a LLM provider
---------------------

Set the  ``TerminalInteractiveShell.llm_provider_class`` trait to the fully
qualified name of the Provider you like, when testing from inside the IPython
source tree, you can use
``"examples.auto_suggest_llm.ExampleCompletionProvider"`` This will always
stream an extract of the Little Prince by Antoine de Saint-Exupéry, and will not
require any API key or real LLM.


In your configuration file adapt the following line to your needs:

.. code-block:: python

    c.TerminalInteractiveShell.llm_provider_class = "examples.auto_suggest_llm.ExampleCompletionProvider"

Configure the provider
----------------------

It the provider needs to be passed parameters at initialization, you can do so
by setting the ``llm_construction_kwargs`` traitlet.

.. code-block:: python

    c.TerminalInteractiveShell.llm_constructor_kwargs = {"model": "skynet"}

This will depdend on the provider you chose, and you will have to refer to
the provider documentation.

Extra configuration may be needed by setting environment variables, this will
again depend on the provider you chose, and you will have to refer to the
provider documentation.

LLM Context
-----------

The option ``c.TerminalInteractiveShell.llm_prefix_from_history`` controls the
context the ``Provider`` gets when trying to complete. See the help of this
options (``ipython --help-all``)::

    Fully Qualifed name of a function that takes an IPython history manager and
    return a prefix to pass the llm provider in addition to the current buffer
    text.

    You can use:

     - no_prefix
     - input_history

    As default value. `input_history` (default),  will use all the input history
    of current IPython session






.. _custom_prompts:

Custom Prompts
==============

.. versionchanged:: 5.0

From IPython 5, prompts are produced as a list of Pygments tokens, which are
tuples of (token_type, text). You can customise prompts by writing a method
which generates a list of tokens.

There are four kinds of prompt:

* The **in** prompt is shown before the first line of input
  (default like ``In [1]:``).
* The **continuation** prompt is shown before further lines of input
  (default like ``...:``).
* The **rewrite** prompt is shown to highlight how special syntax has been
  interpreted (default like ``----->``).
* The **out** prompt is shown before the result from evaluating the input
  (default like ``Out[1]:``).

Custom prompts are supplied together as a class. If you want to customise only
some of the prompts, inherit from :class:`IPython.terminal.prompts.Prompts`,
which defines the defaults. The required interface is like this:

.. class:: MyPrompts(shell)

   Prompt style definition. *shell* is a reference to the
   :class:`~.TerminalInteractiveShell` instance.

   .. method:: in_prompt_tokens()
               continuation_prompt_tokens(self, width=None)
               rewrite_prompt_tokens()
               out_prompt_tokens()

      Return the respective prompts as lists of ``(token_type, text)`` tuples.

      For continuation prompts, *width* is an integer representing the width of
      the prompt area in terminal columns.


Here is an example Prompt class that will show the current working directory
in the input prompt:

.. code-block:: python

    from IPython.terminal.prompts import Prompts, Token
    import os

    class MyPrompt(Prompts):
         def in_prompt_tokens(self):
             return [(Token, os.getcwd()),
                     (Token.Prompt, ' >>>')]

To set the new prompt, assign it to the ``prompts`` attribute of the IPython
shell:

.. code-block:: python

    In [2]: ip = get_ipython()
       ...: ip.prompts = MyPrompt(ip)

    /home/bob >>> # it works

See ``IPython/example/utils/cwd_prompt.py`` for an example of how to write
extensions to customise prompts.

Inside IPython or in a startup script, you can use a custom prompts class
by setting ``get_ipython().prompts`` to an *instance* of the class.
In configuration, ``TerminalInteractiveShell.prompts_class`` may be set to
either the class object, or a string of its full importable name.

To include invisible terminal control sequences in a prompt, use
``Token.ZeroWidthEscape`` as the token type. Tokens with this type are ignored
when calculating the width.

Colours in the prompt are determined by the token types and the highlighting
style; see below for more details. The tokens used in the default prompts are
``Prompt``, ``PromptNum``, ``OutPrompt`` and ``OutPromptNum``.

.. _termcolour:

Terminal Colors
===============

.. versionchanged:: 9.0

IPython 9.0 changed almost all of the  color handling, which is now referred to
as **themes**. A Theme can do a bit more than purely colors, as it can handle
bold, italic and basically any style that ``pygments`` support.  Themes also
support a number of ``Symbols``, which allows you to – for example – change the
shape of the arrow that mark the current frame and line numbers in the debugger
and the tracebacks. 

Most of the various IPython options that were used pre 9.0 have been renamed,
with a exceptions a few, and most classes  that deal with themes can, now take a
``theme_name`` parameter.

To reflect this, the  ``--colors`` flag now is also aliased to ``--theme``.

The default themes included are the same, except lowercase, for ease of typing. 

``'nocolor', 'neutral', 'linux', 'lightbg'``, with the addition of ``'pride'``
to celebrate the inclusively of this project (I welcome update to the pride
theme as I'm not a designer myself). 

In addition, the ``--theme=pride`` theme, is the first to make use of unicode
symbols for the traceback separation line, and the debugger and traceback arrow, 
as well as making some use of ``bold``, and ``italic`` formatting, and not limit
itself to the 16 base ANSI colors.

Theme details
-------------

We encourage you to contribute themes, and to distribute them, 
while currently you need to modify source code to add a theme, it should be
possible to load theme from Json, Yaml, or any other declarative file type. 

Since IPython 9.0, most of IPython internal code emit a sequence of `(Token
Type, string)`, which is fed through pygments, and a theme is mapping from those
token types to a style. For example: ``Token.Prompt : '#ansired underline'``, or
``Token.Filename : 'bg:#A30262``.

For simplicity, a theme can be derived from from a pygments style (which will
give the basic code highlighting).

A theme can also define a few symbols (see the source for how), for example
``arrow_body``, and ``arrow_head``, can help customising line indicators.



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

.. _custom_keyboard_shortcuts:

Keyboard Shortcuts
==================

.. versionadded:: 8.11

You can modify, disable or modify keyboard shortcuts for IPython Terminal using
:std:configtrait:`TerminalInteractiveShell.shortcuts` traitlet.

The list of shortcuts is available in the Configuring IPython :ref:`terminal-shortcuts-list` section.

Advanced configuration
----------------------

.. versionchanged:: 5.0

Creating custom commands requires adding custom code to a
:ref:`startup file <startup_files>`::

    from IPython import get_ipython
    from prompt_toolkit.enums import DEFAULT_BUFFER
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.filters import HasFocus, HasSelection, ViInsertMode, EmacsInsertMode

    ip = get_ipython()
    insert_mode = ViInsertMode() | EmacsInsertMode()

    def insert_unexpected(event):
        buf = event.current_buffer
        buf.insert_text('The Spanish Inquisition')
    # Register the shortcut if IPython is using prompt_toolkit
    if getattr(ip, 'pt_app', None):
        registry = ip.pt_app.key_bindings
        registry.add_binding(Keys.ControlN,
                         filter=(HasFocus(DEFAULT_BUFFER)
                                 & ~HasSelection()
                                 & insert_mode))(insert_unexpected)


Here is a second example that bind the key sequence ``j``, ``k`` to switch to
VI input mode to ``Normal`` when in insert mode::

   from IPython import get_ipython
   from prompt_toolkit.enums import DEFAULT_BUFFER
   from prompt_toolkit.filters import HasFocus, ViInsertMode
   from prompt_toolkit.key_binding.vi_state import InputMode

   ip = get_ipython()

   def switch_to_navigation_mode(event):
      vi_state = event.cli.vi_state
      vi_state.input_mode = InputMode.NAVIGATION

   if getattr(ip, 'pt_app', None):
      registry = ip.pt_app.key_bindings
      registry.add_binding(u'j',u'k',
                           filter=(HasFocus(DEFAULT_BUFFER)
                                    & ViInsertMode()))(switch_to_navigation_mode)

For more information on filters and what you can do with the ``event`` object,
`see the prompt_toolkit docs
<https://python-prompt-toolkit.readthedocs.io/en/latest/pages/asking_for_input.html#adding-custom-key-bindings>`__.


Enter to execute
----------------

In the Terminal IPython shell – which by default uses the ``prompt_toolkit``
interface, the semantic meaning of pressing the :kbd:`Enter` key can be
ambiguous. In some case :kbd:`Enter` should execute code, and in others it
should add a new line. IPython uses heuristics to decide whether to execute or
insert a new line at cursor position. For example, if we detect that the current
code is not valid Python, then the user is likely editing code and the right
behavior is to likely to insert a new line. If the current code is a simple
statement like `ord('*')`, then the right behavior is likely to execute. Though
the exact desired semantics often varies from users to users.

As the exact behavior of :kbd:`Enter` is ambiguous, it has been special cased
to allow users to completely configure the behavior they like. Hence you can
have enter always execute code. If you prefer fancier behavior, you need to get
your hands dirty and read the ``prompt_toolkit`` and IPython documentation
though. See :ghpull:`10500`, set the
``c.TerminalInteractiveShell.handle_return`` option and get inspiration from the
following example that only auto-executes the input if it begins with a bang or
a modulo character (``!`` or ``%``). To use the following code, add it to your
IPython configuration::

    def custom_return(shell):

        """This function is required by the API. It takes a reference to
        the shell, which is the same thing `get_ipython()` evaluates to.
        This function must return a function that handles each keypress
        event. That function, named `handle` here, references `shell`
        by closure."""

        def handle(event):

            """This function is called each time `Enter` is pressed,
            and takes a reference to a Prompt Toolkit event object.
            If the current input starts with a bang or modulo, then
            the input is executed, otherwise a newline is entered,
            followed by any spaces needed to auto-indent."""

            # set up a few handy references to nested items...

            buffer = event.current_buffer
            document = buffer.document
            text = document.text

            if text.startswith('!') or text.startswith('%'): # execute the input...

                buffer.accept_action.validate_and_handle(event.cli, buffer)

            else: # insert a newline with auto-indentation...

                if document.line_count > 1: text = text[:document.cursor_position]
                indent = shell.check_complete(text)[1]
                buffer.insert_text('\n' + indent)
            
                # if you just wanted a plain newline without any indentation, you
                # could use `buffer.insert_text('\n')` instead of the lines above

        return handle

    c.TerminalInteractiveShell.handle_return = custom_return

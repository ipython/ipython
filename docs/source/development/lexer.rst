.. _console_lexer:

New IPython Console Lexer
-------------------------

.. versionadded:: 2.0.0

The IPython console lexer has been rewritten and now supports tracebacks
and customized input/output prompts. An entire suite of lexers is now
available at :mod:`IPython.nbconvert.utils.lexers`. These include:

IPythonLexer & IPython3Lexer
  Lexers for pure IPython (python + magic/shell commands)

IPythonPartialTracebackLexer & IPythonTracebackLexer
  Supports 2.x and 3.x via the keyword `python3`. The partial traceback
  lexer reads everything but the Python code appearing in a traceback.
  The full lexer combines the partial lexer with an IPython lexer.

IPythonConsoleLexer
  A lexer for IPython console sessions, with support for tracebacks.
  Supports 2.x and 3.x via the keyword `python3`.

IPyLexer
  A friendly lexer which examines the first line of text and from it,
  decides whether to use an IPython lexer or an IPython console lexer.
  Supports 2.x and 3.x via the keyword `python3`.

Previously, the :class:`IPythonConsoleLexer` class was available at
:mod:`IPython.sphinxext.ipython_console_hightlight`.  It was inserted
into Pygments' list of available lexers under the name `ipython`.  It should
be mentioned that this name is inaccurate, since an IPython console session
is not the same as IPython code (which itself is a superset of the Python
language).

Now, the Sphinx extension inserts two console lexers into Pygments' list of
available lexers. Both are IPyLexer instances under the names: `ipython` and
`ipython3`. Although the names can be confusing (as mentioned above), their
continued use is, in part, to maintain backwards compatibility and to
aid typical usage. If a project needs to make Pygments aware of more than just
the IPyLexer class, then one should not make the IPyLexer class available under
the name `ipython` and use `ipy` or some other non-conflicting value.

Code blocks such as:

.. code-block:: rst

    .. code-block:: ipython

        In [1]: 2**2
        Out[1]: 4

will continue to work as before, but now, they will also properly highlight
tracebacks.  For pure IPython code, the same lexer will also work:

.. code-block:: rst

    .. code-block:: ipython

        x = ''.join(map(str, range(10)))
        !echo $x

Since the first line of the block did not begin with a standard IPython console
prompt, the entire block is assumed to consist of IPython code instead.

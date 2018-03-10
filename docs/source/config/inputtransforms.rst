
===========================
Custom input transformation
===========================

IPython extends Python syntax to allow things like magic commands, and help with
the ``?`` syntax. There are several ways to customise how the user's input is
processed into Python code to be executed.

These hooks are mainly for other projects using IPython as the core of their
interactive interface. Using them carelessly can easily break IPython!

String based transformations
============================

.. currentmodule:: IPython.core.inputtransforms

When the user enters code, it is first processed as a string. By the
end of this stage, it must be valid Python syntax.

.. versionchanged:: 7.0

   The API for string and token-based transformations has been completely
   redesigned. Any third party code extending input transformation will need to
   be rewritten. The new API is, hopefully, simpler.

String based transformations are managed by
:class:`IPython.core.inputtransformer2.TransformerManager`, which is attached to
the :class:`~IPython.core.interactiveshell.InteractiveShell` instance as
``input_transformer_manager``. This passes the
data through a series of individual transformers. There are two kinds of
transformers stored in three groups:

* ``cleanup_transforms`` and ``line_transforms`` are lists of functions. Each
  function is called with a list of input lines (which include trailing
  newlines), and they return a list in the same format. ``cleanup_transforms``
  are run first; they strip prompts and leading indentation from input.
  The only default transform in ``line_transforms`` processes cell magics.
* ``token_transformers`` is a list of :class:`IPython.core.inputtransformer2.TokenTransformBase`
  subclasses (not instances). They recognise special syntax like
  ``%line magics`` and ``help?``, and transform them to Python syntax. The
  interface for these is more complex; see below.

These transformers may raise :exc:`SyntaxError` if the input code is invalid, but
in most cases it is clearer to pass unrecognised code through unmodified and let
Python's own parser decide whether it is valid.

.. versionchanged:: 2.0

   Added the option to raise :exc:`SyntaxError`.

Line based transformations
--------------------------

For example, imagine we want to obfuscate our code by reversing each line, so
we'd write ``)5(f =+ a`` instead of ``a += f(5)``. Here's how we could swap it
back the right way before IPython tries to run it::

    def reverse_line_chars(lines):
        new_lines = []
        for line in lines:
            chars = line[:-1]  # the newline needs to stay at the end
            new_lines.append(chars[::-1] + '\n')
        return new_lines

To start using this::

    ip = get_ipython()
    ip.input_transformer_manager.line_transforms.append(reverse_line_chars)

Token based transformations
---------------------------

These recognise special syntax like ``%magics`` and ``help?``, and transform it
into valid Python code. Using tokens makes it easy to avoid transforming similar
patterns inside comments or strings.

The API for a token-based transformation looks like this::

.. class:: MyTokenTransformer
   
   .. classmethod:: find(tokens_by_line)

      Takes a list of lists of :class:`tokenize.TokenInfo` objects. Each sublist
      is the tokens from one Python line, which may span several physical lines,
      because of line continuations, multiline strings or expressions. If it
      finds a pattern to transform, it returns an instance of the class.
      Otherwise, it returns None.

   .. attribute:: start_lineno
                  start_col
                  priority

      These attributes are used to select which transformation to run first.
      ``start_lineno`` is 0-indexed (whereas the locations on
      :class:`~tokenize.TokenInfo` use 1-indexed line numbers). If there are
      multiple matches in the same location, the one with the smaller
      ``priority`` number is used.

   .. method:: transform(lines)

      This should transform the individual recognised pattern that was
      previously found. As with line-based transforms, it takes a list of
      lines as strings, and returns a similar list.

Because each transformation may affect the parsing of the code after it,
``TransformerManager`` takes a careful approach. It calls ``find()`` on all
available transformers. If any find a match, the transformation which matched
closest to the start is run. Then it tokenises the transformed code again,
and starts the process again. This continues until none of the transformers
return a match. So it's important that the transformation removes the pattern
which ``find()`` recognises, otherwise it will enter an infinite loop.

For example, here's a transformer which will recognise ``¬`` as a prefix for a
new kind of special command::

    import tokenize
    from IPython.core.inputtransformer2 import TokenTransformBase

    class MySpecialCommand(TokenTransformBase):
        @classmethod
        def find(cls, tokens_by_line):
            """Find the first escaped command (¬foo) in the cell.
            """
            for line in tokens_by_line:
                ix = 0
                # Find the first token that's not INDENT/DEDENT
                while line[ix].type in {tokenize.INDENT, tokenize.DEDENT}:
                    ix += 1
                if line[ix].string == '¬':
                    return cls(line[ix].start)
    
        def transform(self, lines):   
            indent  = lines[self.start_line][:self.start_col]
            content = lines[self.start_line][self.start_col+1:]
    
            lines_before = lines[:self.start_line]
            call = "specialcommand(%r)" % content
            new_line = indent + call + '\n'
            lines_after = lines[self.start_line + 1:]
    
            return lines_before + [new_line] + lines_after

And here's how you'd use it::

    ip = get_ipython()
    ip.input_transformer_manager.token_transformers.append(MySpecialCommand)


AST transformations
===================

After the code has been parsed as Python syntax, you can use Python's powerful
*Abstract Syntax Tree* tools to modify it. Subclass :class:`ast.NodeTransformer`,
and add an instance to ``shell.ast_transformers``.

This example wraps integer literals in an ``Integer`` class, which is useful for
mathematical frameworks that want to handle e.g. ``1/3`` as a precise fraction::


    class IntegerWrapper(ast.NodeTransformer):
        """Wraps all integers in a call to Integer()"""
        def visit_Num(self, node):
            if isinstance(node.n, int):
                return ast.Call(func=ast.Name(id='Integer', ctx=ast.Load()),
                                args=[node], keywords=[])
            return node

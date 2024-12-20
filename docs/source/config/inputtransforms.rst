
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

.. currentmodule:: IPython.core.inputtransformers2

When the user enters code, it is first processed as a string. By the
end of this stage, it must be valid Python syntax.

.. versionchanged:: 7.0

   The API for string and token-based transformations has been completely
   redesigned. Any third party code extending input transformation will need to
   be rewritten. The new API is, hopefully, simpler.

String based transformations are functions which accept a list of strings:
each string is a single line of the input cell, including its line ending.
The transformation function should return output in the same structure.

These transformations are in two groups, accessible as attributes of
the :class:`~IPython.core.interactiveshell.InteractiveShell` instance.
Each group is a list of transformation functions.

* ``input_transformers_cleanup`` run first on input, to do things like stripping
  prompts and leading indents from copied code. It may not be possible at this
  stage to parse the input as valid Python code.
* Then IPython runs its own transformations to handle its special syntax, like
  ``%magics`` and ``!system`` commands. This part does not expose extension
  points.
* ``input_transformers_post`` run as the last step, to do things like converting
  float literals into decimal objects. These may attempt to parse the input as
  Python code.  

These transformers may raise :exc:`SyntaxError` if the input code is invalid, but
in most cases it is clearer to pass unrecognised code through unmodified and let
Python's own parser decide whether it is valid.

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
    ip.input_transformers_cleanup.append(reverse_line_chars)

.. versionadded:: 7.17

    input_transformers can now have an attribute ``has_side_effects`` set to
    `True`, which will prevent the transformers from being ran when IPython is
    trying to guess whether the user input is complete. 



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
            if isinstance(node.value, int):
                return ast.Call(func=ast.Name(id='Integer', ctx=ast.Load()),
                                args=[node], keywords=[])
            return node

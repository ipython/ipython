
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

When the user enters a line of code, it is first processed as a string. By the
end of this stage, it must be valid Python syntax.

These transformers all subclass :class:`IPython.core.inputtransformer.InputTransformer`,
and are used by :class:`IPython.core.inputsplitter.IPythonInputSplitter`.

These transformers act in three groups, stored separately as lists of instances
in attributes of :class:`~IPython.core.inputsplitter.IPythonInputSplitter`:

* ``physical_line_transforms`` act on the lines as the user enters them. For
  example, these strip Python prompts from examples pasted in.
* ``logical_line_transforms`` act on lines as connected by explicit line
  continuations, i.e. ``\`` at the end of physical lines. They are skipped
  inside multiline Python statements. This is the point where IPython recognises
  ``%magic`` commands, for instance.
* ``python_line_transforms`` act on blocks containing complete Python statements.
  Multi-line strings, lists and function calls are reassembled before being
  passed to these, but note that function and class *definitions* are still a
  series of separate statements. IPython does not use any of these by default.

An InteractiveShell instance actually has two
:class:`~IPython.core.inputsplitter.IPythonInputSplitter` instances, as the
attributes :attr:`~IPython.core.interactiveshell.InteractiveShell.input_splitter`,
to tell when a block of input is complete, and
:attr:`~IPython.core.interactiveshell.InteractiveShell.input_transformer_manager`,
to transform complete cells. If you add a transformer, you should make sure that
it gets added to both, e.g.::

    ip.input_splitter.logical_line_transforms.append(my_transformer())
    ip.input_transformer_manager.logical_line_transforms.append(my_transformer())

These transformers may raise :exc:`SyntaxError` if the input code is invalid, but
in most cases it is clearer to pass unrecognised code through unmodified and let
Python's own parser decide whether it is valid.

.. versionchanged:: 2.0

   Added the option to raise :exc:`SyntaxError`.

Stateless transformations
-------------------------

The simplest kind of transformations work one line at a time. Write a function
which takes a line and returns a line, and decorate it with
:meth:`StatelessInputTransformer.wrap`::

    @StatelessInputTransformer.wrap
    def my_special_commands(line):
        if line.startswith("¬"):
            return "specialcommand(" + repr(line) + ")"
        return line

The decorator returns a factory function which will produce instances of
:class:`~IPython.core.inputtransformer.StatelessInputTransformer` using your
function.

Transforming a full block
-------------------------

.. warning::

    Transforming a full block at once will break the automatic detection of
    whether a block of code is complete in interfaces relying on this
    functionality, such as terminal IPython. You will need to use a
    shortcut to force-execute your cells.

Transforming a full block of python code is possible by implementing a
:class:`~IPython.core.inputtransformer.Inputtransformer` and overwriting the
``push`` and ``reset`` methods. The reset method should send the full block of
transformed text. As an example a transformer the reversed the lines from last
to first.

    from IPython.core.inputtransformer import InputTransformer

    class ReverseLineTransformer(InputTransformer):

        def __init__(self):
            self.acc = []

        def push(self, line):
            self.acc.append(line)
            return None

        def reset(self):
            ret = '\n'.join(self.acc[::-1])
            self.acc = []
            return ret


Coroutine transformers
----------------------

More advanced transformers can be written as coroutines. The coroutine will be
sent each line in turn, followed by ``None`` to reset it. It can yield lines, or
``None`` if it is accumulating text to yield at a later point. When reset, it
should give up any code it has accumulated.

You may use :meth:`CoroutineInputTransformer.wrap` to simplify the creation of
such a transformer.

Here is a simple :class:`CoroutineInputTransformer` that can be thought of
being the identity::

    from IPython.core.inputtransformer import CoroutineInputTransformer

    @CoroutineInputTransformer.wrap
    def noop():
        line = ''
        while True:
            line = (yield line)

    ip = get_ipython()

    ip.input_splitter.logical_line_transforms.append(noop())
    ip.input_transformer_manager.logical_line_transforms.append(noop())

This code in IPython strips a constant amount of leading indentation from each
line in a cell::

    from IPython.core.inputtransformer import CoroutineInputTransformer

    @CoroutineInputTransformer.wrap
    def leading_indent():
        """Remove leading indentation.
        
        If the first line starts with a spaces or tabs, the same whitespace will be
        removed from each following line until it is reset.
        """
        space_re = re.compile(r'^[ \t]+')
        line = ''
        while True:
            line = (yield line)
            
            if line is None:
                continue
            
            m = space_re.match(line)
            if m:
                space = m.group(0)
                while line is not None:
                    if line.startswith(space):
                        line = line[len(space):]
                    line = (yield line)
            else:
                # No leading spaces - wait for reset
                while line is not None:
                    line = (yield line)


Token-based transformers
------------------------

There is an experimental framework that takes care of tokenizing and
untokenizing lines of code. Define a function that accepts a list of tokens, and
returns an iterable of output tokens, and decorate it with
:meth:`TokenInputTransformer.wrap`. These should only be used in
``python_line_transforms``.

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

Don't start a multiline cell with sunken parenthesis
----------------------------------------------------

From now on IPython will not ask for the next line of input when given a single
line with more closing than opening brackets. For example, this means that if
you (mis)type ']]' instead of '[]', a ``SyntaxError`` will show up, instead of
the ``...:`` prompt continuation.

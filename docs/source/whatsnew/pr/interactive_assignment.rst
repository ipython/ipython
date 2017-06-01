IPython can now trigger the display hook on last assignment of cells.
Up until 6.0 the following code wouldn't show the value of the assigned
variable::

    In[1]: xyz = "something"
    # nothing shown

You would have to actually make it the last statement::

    In [2]: xyz = "something else"
    ...   : xyz
    Out[2]: "something else"

With the option ``InteractiveShell.ast_node_interactivity='last_expr_or_assign'``
you can now do::

    In [2]: xyz = "something else"
    Out[2]: "something else"

This option can be toggled at runtime with the ``%config`` magic, and will
trigger on assignment ``a = 1``, augmented assignment ``+=``, ``-=``, ``|=`` ...
as well as type annotated assignments: ``a:int = 2``.

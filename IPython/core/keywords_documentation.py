import operator

class DocObject:
    def __init__(self, doc):
        self.__doc__ = doc

keywords_documentation = {
    "for": DocObject("""
    The ``for`` statement (for loops)

    The for statement is used to iterate over the elements of a
    sequence (such as a string, tuple or list) or other iterable
    object.

    Syntax:

        for variable in container:
            <code>

        for variable in container:
            <code>
        else:
            <code>

    Semantic:

        For each value in the container, assign that value to
        ``variable`` and execute <code>.

        A ``break`` statement executed in the code terminates the loop
        without executing the ``else`` clause's code. A ``continue``
        statement executed in the code skips the rest of the code and
        continues with the next item, or with the ``else`` clause if
        there was no next item.

    Seealso:

        - https://docs.python.org/3/tutorial/controlflow.html#for-statements
        - https://docs.python.org/3/reference/compound_stmts.html#the-for-statement

    Examples::

        for letter in ["a", "b", "c"]:
            print letter
        a
        b
        c

        for i in range(5):
            print i
        0
        1
        2
        3
        4
    """),

    "if": DocObject("""
    Conditionals

    Syntax:

        if condition:
            <code1>

        if condition:
            <code1>
        elif condition:
            <code2>
        else:
            <code3>

    Semantic:

    EXAMPLES::

        if x < 0:
            print "x is negative"
        elif x > 0:
            print "x is positive"
        else:
            print "x is null"
    """),

    "+": operator.add,
}

keywords_documentation["elif"] = keywords_documentation["if"]
keywords_documentation["else"] = keywords_documentation["if"]

keywords_documentation["break"] = keywords_documentation["for"]
keywords_documentation["continue"] = keywords_documentation["for"]

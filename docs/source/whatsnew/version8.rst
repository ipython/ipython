============
 8.x Series
============

IPython 8.0
-----------

IPython 8.0 is still in alpha/beta stage. Please help us improve those release notes
by sending PRs that modify docs/source/whatsnew/version8.rst

IPython 8.0 is bringing a large number of new features and improvements to both the
user of the terminal and of the kernel via Jupyter. The removal of compatibility
with older version of Python is also the opportunity to do a couple of
performance improvement in particular with respect to startup time.
The 8.x branch started diverging from its predecessor around IPython 7.12
(January 2020).

This release contains 250+ Pull Requests, in addition to many of the features
and backports that have made it to the 7.x branch. All PRs that went into this
released are properly tagged with the 8.0 milestone if you wish to have a more
in depth look at the changes.

Please fell free to send pull-requests to updates those notes after release, 
I have likely forgotten a few things reviewing 250+ PRs.

Dependencies changes/downstream packaging
-----------------------------------------

Note that most of our building step have been changes to be (mostly) declarative
and follow PEP 517, we are trying to completely remove ``setup.py`` (:ghpull:`13238`) and are
looking for help to do so.

 - Minimum supported ``traitlets`` version if now 5+
 - we now require ``stack_data``
 - Minimal Python is now 3.8
 - ``nose`` is not a testing requirement anymore
 - ``pytest`` replaces nose.
 - ``iptest``/``iptest3`` cli entrypoints do not exists anymore. 
 - minimum officially support ``numpy`` version has been bumped, but this should
   not have much effect on packaging.


Deprecation and removal
-----------------------

We removed almost all features, arguments, functions, and modules that were
marked as deprecated between IPython 1.0 and 5.0. As reminder 5.0 was released
in 2016, and 1.0 in 2013. Last release of the 5 branch was 5.10.0, in may 2020.
The few remaining deprecated features we left have better deprecation warnings
or have been turned into explicit errors for better error messages.

I will use this occasion to add the following requests to anyone emitting a
deprecation warning:

 - Please at at least ``stacklevel=2`` so that the warning is emitted into the
   caller context, and not the callee one.
 - Please add **since which version** something is deprecated.

As a side note it is much easier to deal with conditional comparing to versions
numbers than ``try/except`` when a functionality change with version. 

I won't list all the removed features here, but modules like ``IPython.kernel``,
which was just a shim module around ``ipykernel`` for the past 8 years have been
remove, and so many other similar things that pre-date the name **Jupyter**
itself.

We no longer need to add ``IPyhton.extensions`` to the PYTHONPATH because that is being
handled by ``load_extension``.

We are also removing ``Cythonmagic``, ``sympyprinting`` and ``rmagic`` as they are now in
other packages and no longer need to be inside IPython.


Documentation
-------------

Majority of our docstrings have now been reformatted and automatically fixed by
the experimental `Vélin <https://pypi.org/project/velin/>`_ project, to conform
to numpydoc.

Type annotations
----------------

While IPython itself is highly dynamic and can't be completely typed, many of
the function now have type annotation, and part of the codebase and now checked
by mypy.


Featured changes
----------------

Here is a features list of changes in IPython 8.0. This is of course non-exhaustive. 
Please note as well that many features have been added in the 7.x branch as well
(and hence why you want to read the 7.x what's new notes), in particular
features contributed by QuantStack (with respect to debugger protocol, and Xeus
Python), as well as many debugger features that I was please to implement as
part of my work at QuanSight and Sponsored by DE Shaw.

Better Tracebacks
~~~~~~~~~~~~~~~~~

The first on is the integration of the ``stack_data`` package;
which provide smarter informations in traceback; in particular it will highlight
the AST node where an error occurs which can help to quickly narrow down errors.

For example in the following snippet::

    def foo(i):
        x = [[[0]]]
        return x[0][i][0]


    def bar():
        return foo(0) + foo(
            1
        ) + foo(2)


Calling ``bar()`` would raise an ``IndexError`` on the return line of ``foo``,
IPython 8.0 is capable of telling you, where the index error occurs::


    IndexError
    Input In [2], in <module>
    ----> 1 bar()
            ^^^^^

    Input In [1], in bar()
          6 def bar():
    ----> 7     return foo(0) + foo(
                                ^^^^
          8         1
             ^^^^^^^^
          9     ) + foo(2)
             ^^^^

    Input In [1], in foo(i)
          1 def foo(i):
          2     x = [[[0]]]
    ----> 3     return x[0][i][0]
                       ^^^^^^^

Corresponding location marked here with ``^`` will show up highlighted in 
terminal and notebooks.


Autosuggestons
~~~~~~~~~~~~~~

Autosuggestion is a very useful feature available in `fish <https://fishshell.com/>`__, `zsh <https://en.wikipedia.org/wiki/Z_shell>`__, and `prompt-toolkit <https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#auto-suggestion>`__.

`Ptpython <https://github.com/prompt-toolkit/ptpython#ptpython>`__ allows users to enable this feature in
`ptpython/config.py <https://github.com/prompt-toolkit/ptpython/blob/master/examples/ptpython_config/config.py#L90>`__.

This feature allows users to accept autosuggestions with ctrl e, ctrl f,
or right arrow as described below.

1. Start ipython

.. image:: ../_images/8.0/auto_suggest_1_prompt_no_text.png

2. Run ``print("hello")``

.. image:: ../_images/8.0/auto_suggest_2_print_hello_suggest.png

3. start typing ``print`` again to see the autosuggestion

.. image:: ../_images/8.0/auto_suggest_3_print_hello_suggest.png

4. Press ``ctrl-f``, or ``ctrl-e``, or ``right-arrow`` to accept the suggestion

.. image:: ../_images/8.0/auto_suggest_4_print_hello.png

You can also complete word by word:

1. Run ``def say_hello(): print("hello")``

.. image:: ../_images/8.0/auto_suggest_second_prompt.png

2. Start typing  the first letter if ``def`` to see the autosuggestion

.. image:: ../_images/8.0/auto_suggest_d_phantom.png

3. Press ``alt-f`` (or ``escape`` followed by ``f``), to accept the first word of the suggestion

.. image:: ../_images/8.0/auto_suggest_def_phantom.png

Importantly, this feature does not interfere with tab completion:

1. After running ``def say_hello(): print("hello")``, press d

.. image:: ../_images/8.0/auto_suggest_d_phantom.png

2. Press Tab to start tab completion

.. image:: ../_images/8.0/auto_suggest_d_completions.png

3A. Press Tab again to select the first option

.. image:: ../_images/8.0/auto_suggest_def_completions.png

3B. Press ``alt f`` (``escape``, ``f``) to accept to accept the first word of the suggestion

.. image:: ../_images/8.0/auto_suggest_def_phantom.png

3C. Press ``ctrl-f`` or ``ctrl-e`` to accept the entire suggestion

.. image:: ../_images/8.0/auto_suggest_match_parens.png


Currently, autosuggestions are only shown in the emacs or vi insert editing modes:

- The ctrl e, ctrl f, and alt f shortcuts work by default in emacs mode.
- To use these shortcuts in vi insert mode, you will have to create `custom keybindings in your config.py <https://github.com/mskar/setup/commit/2892fcee46f9f80ef7788f0749edc99daccc52f4/>`__.


Show pinfo information in ipdb using "?" and "??"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In IPDB, it is now possible to show the information about an object using "?"
and "??", in much the same way it can be done when using the IPython prompt::

    ipdb> partial?
    Init signature: partial(self, /, *args, **kwargs)
    Docstring:
    partial(func, *args, **keywords) - new function with partial application
    of the given arguments and keywords.
    File:           ~/.pyenv/versions/3.8.6/lib/python3.8/functools.py
    Type:           type
    Subclasses:

Previously, ``pinfo`` or ``pinfo2`` command had to be used for this purpose.


Autoreload 3 feature
~~~~~~~~~~~~~~~~~~~~

Example: When an IPython session is ran with the 'autoreload' extension loaded,
you will now have the option '3' to select which means the following:

    1. replicate all functionality from option 2
    2. autoload all new funcs/classes/enums/globals from the module when they are added
    3. autoload all newly imported funcs/classes/enums/globals from external modules

Try ``%autoreload 3`` in an IPython session after running ``%load_ext autoreload``

For more information please see the following unit test : ``extensions/tests/test_autoreload.py:test_autoload_newly_added_objects``




History Range Glob feature
~~~~~~~~~~~~~~~~~~~~~~~~~~

Previously, when using ``%history``, users could specify either
a range of sessions and lines, for example:

.. code-block:: python

   ~8/1-~6/5   # see history from the first line of 8 sessions ago,
               # to the fifth line of 6 sessions ago.``

Or users could specify a glob pattern:

.. code-block:: python

   -g <pattern>  # glob ALL history for the specified pattern.

However users could *not* specify both.

If a user *did* specify both a range and a glob pattern,
then the glob pattern would be used (globbing *all* history) *and the range would be ignored*.

With this enhancement, if a user specifies both a range and a glob pattern, then the glob pattern will be applied to the specified range of history.

Don't start a multi line cell with sunken parenthesis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From now on IPython will not ask for the next line of input when given a single
line with more closing than opening brackets. For example, this means that if
you (mis)type ``]]`` instead of ``[]``, a ``SyntaxError`` will show up, instead of
the ``...:`` prompt continuation.

IPython shell for ipdb interact
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ipdb ``interact`` starts an IPython shell instead of Python's built-in ``code.interact()``.

Automatic Vi prompt stripping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When pasting code into IPython, it will strip the leading prompt characters if
there are any. For example, you can paste the following code into the console -
it will still work, even though each line is prefixed with prompts (`In`,
`Out`)::

    In [1]: 2 * 2 == 4
    Out[1]: True

    In [2]: print("This still works as pasted")


Previously, this was not the case for the Vi-mode prompts::

    In [1]: [ins] In [13]: 2 * 2 == 4
       ...: Out[13]: True
       ...:
      File "<ipython-input-1-727bb88eaf33>", line 1
        [ins] In [13]: 2 * 2 == 4
              ^
    SyntaxError: invalid syntax

This is now fixed, and Vi prompt prefixes - ``[ins]`` and ``[nav]`` -  are
skipped just as the normal ``In`` would be.

IPython shell can be started in the Vi mode using ``ipython --TerminalInteractiveShell.editing_mode=vi``, 
You should be able to change mode dynamically with ``%config TerminalInteractiveShell.editing_mode='vi'``

Empty History Ranges
~~~~~~~~~~~~~~~~~~~~

A number of magics that take history ranges can now be used with an empty
range. These magics are:

 * ``%save``
 * ``%load``
 * ``%pastebin``
 * ``%pycat``

Using them this way will make them take the history of the current session up
to the point of the magic call (such that the magic itself will not be
included).

Therefore it is now possible to save the whole history to a file using simple
``%save <filename>``, load and edit it using ``%load`` (makes for a nice usage
when followed with :kbd:`F2`), send it to dpaste.org using ``%pastebin``, or
view the whole thing syntax-highlighted with a single ``%pycat``.

Traceback improvements
~~~~~~~~~~~~~~~~~~~~~~


Previously, error tracebacks for errors happening in code cells were showing a hash, the one used for compiling the Python AST::

    In [1]: def foo():
    ...:     return 3 / 0
    ...:

    In [2]: foo()
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    <ipython-input-2-c19b6d9633cf> in <module>
    ----> 1 foo()

    <ipython-input-1-1595a74c32d5> in foo()
        1 def foo():
    ----> 2     return 3 / 0
        3

    ZeroDivisionError: division by zero

The error traceback is now correctly formatted, showing the cell number in which the error happened::

    In [1]: def foo():
    ...:     return 3 / 0
    ...:

    Input In [2]: foo()
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    input In [2], in <module>
    ----> 1 foo()

    Input In [1], in foo()
        1 def foo():
    ----> 2     return 3 / 0

    ZeroDivisionError: division by zero

Miscellaneous
~~~~~~~~~~~~~

 - ``~`` is now expanded when part of a path in most magics :ghpull:`13385`
 - ``%/%%timeit`` magic now adds comma every thousands to make reading long number easier :ghpull:`13379`
 - ``"info"`` messages can now be customised to hide some fields :ghpull:`13343`
 - ``collections.UserList`` now pretty-prints :ghpull:`13320`
 - The debugger now have a persistent history, which should make it less
   annoying to retype commands :ghpull:`13246`
 - ``!pip`` ``!conda`` ``!cd`` or ``!ls`` are likely doing the wrong thing, we
   now warn users if they use it. :ghpull:`12954`
 - make ``%precision`` work for ``numpy.float64`` type :ghpull:`12902`




Numfocus Small Developer Grant
------------------------------

To prepare for Python 3.10 we have also started working on removing reliance and
any dependency that is not Python 3.10 compatible; that include migrating our
test suite to pytest, and starting to remove nose. This also mean that the
``iptest`` command is now gone, and all testing is via pytest.

This was in bog part thanks the NumFOCUS Small Developer grant, we were able to
allocate 4000 to hire `Nikita Kniazev (@Kojoley) <https://github.com/Kojoley>`__
who did a fantastic job at updating our code base, migrating to pytest, pushing
our coverage, and fixing a large number of bugs. I highly recommend contacting
them if you need help with C++ and Python projects

You can find all relevant issues and PRs with the SDG 2021 tag `<https://github.com/ipython/ipython/issues?q=label%3A%22Numfocus+SDG+2021%22+>`__

Removing support for Older Python
---------------------------------


We are also removing support for Python up to 3.7 allowing internal code to use more
efficient ``pathlib``, and make better use of type annotations. 

.. image:: ../_images/8.0/pathlib_pathlib_everywhere.jpg
   :alt: "Meme image of Toy Story with Woody and Buzz, with the text 'pathlib, pathlib everywhere'"


We have about 34 PRs only to update some logic tu update some function from managing strings to
using Pathlib.

The completer has also seen significant updates and make use of newer Jedi API
offering faster and more reliable tab completion.


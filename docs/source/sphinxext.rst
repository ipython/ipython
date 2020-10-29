
.. _ipython_directive:

========================
IPython Sphinx Directive
========================

.. note::

   The IPython Sphinx Directive is in 'beta' and currently under
   active development. Improvements to the code or documentation are welcome!

.. |rst| replace:: reStructured text

The :rst:dir:`ipython` directive is a stateful shell that can be used
in |rst| files.

It knows about standard ipython prompts, and extracts the input and output
lines.  These prompts will be renumbered starting at ``1``.  The inputs will be
fed to an embedded ipython interpreter and the outputs from that interpreter
will be inserted as well.  For example, code blocks like the following::

  .. ipython::

     In [136]: x = 2

     In [137]: x**3
     Out[137]: 8

will be rendered as

.. ipython::

   In [136]: x = 2

   In [137]: x**3
   Out[137]: 8

.. note::

   This tutorial should be read side-by-side with the Sphinx source
   for this document because otherwise you will see only the rendered
   output and not the code that generated it.  Excepting the example
   above, we will not in general be showing the literal ReST in this
   document that generates the rendered output.


Directive and options
=====================

The IPython directive takes a number of options detailed here.

.. rst:directive:: ipython

   Create an IPython directive.

   .. rst:directive:option:: doctest

      Run a doctest on IPython code blocks in rst.

   .. rst:directive:option:: python

      Used to indicate that the relevant code block does not have IPython prompts.

   .. rst:directive:option:: okexcept

      Allow the code block to raise an exception.

   .. rst:directive:option:: okwarning

      Allow the code block to emit an warning.

   .. rst:directive:option:: suppress

      Silence any warnings or expected errors.

   .. rst:directive:option:: verbatim

      A noop that allows for any text to be syntax highlighted as valid IPython code.

   .. rst:directive:option:: savefig: OUTFILE [IMAGE_OPTIONS]

      Save output from matplotlib to *outfile*.

It's important to note that all of these options can be used for the entire
directive block or they can decorate individual lines of code as explained
in :ref:`pseudo-decorators`.


Persisting the Python session across IPython directive blocks
=============================================================

The state from previous sessions is stored, and standard error is
trapped. At doc build time, ipython's output and std err will be
inserted, and prompts will be renumbered. So the prompt below should
be renumbered in the rendered docs, and pick up where the block above
left off.

.. ipython::
  :verbatim:

  In [138]: z = x*3   # x is recalled from previous block

  In [139]: z
  Out[139]: 6

  In [142]: print(z)
  6

  In [141]: q = z[)   # this is a syntax error -- we trap ipy exceptions
  ------------------------------------------------------------
     File "<ipython console>", line 1
       q = z[)   # this is a syntax error -- we trap ipy exceptions
	     ^
  SyntaxError: invalid syntax


Adding documentation tests to your IPython directive
====================================================

The embedded interpreter supports some limited markup.  For example,
you can put comments in your ipython sessions, which are reported
verbatim.  There are some handy "pseudo-decorators" that let you
doctest the output.  The inputs are fed to an embedded ipython
session and the outputs from the ipython session are inserted into
your doc.  If the output in your doc and in the ipython session don't
match on a doctest assertion, an error will occur.


.. ipython::

   In [1]: x = 'hello world'

   # this will raise an error if the ipython output is different
   @doctest
   In [2]: x.upper()
   Out[2]: 'HELLO WORLD'

   # some readline features cannot be supported, so we allow
   # "verbatim" blocks, which are dumped in verbatim except prompts
   # are continuously numbered
   @verbatim
   In [3]: x.st<TAB>
   x.startswith  x.strip

For more information on @doctest decorator, please refer to the end of this page in Pseudo-Decorators section.

Multi-line input
================

Multi-line input is supported.

.. ipython::
   :verbatim:

   In [130]: url = 'http://ichart.finance.yahoo.com/table.csv?s=CROX\
      .....: &d=9&e=22&f=2009&g=d&a=1&br=8&c=2006&ignore=.csv'

   In [131]: print(url.split('&'))
   ['http://ichart.finance.yahoo.com/table.csv?s=CROX', 'd=9', 'e=22',

Testing directive outputs
=========================

The IPython Sphinx Directive makes it possible to test the outputs that you provide with your code. To do this,
decorate the contents in your directive block with one of the options listed
above.

If an IPython doctest decorator is found, it will take these steps when your documentation is built:

1. Run the *input* lines in your IPython directive block against the current Python kernel (remember that the session
persists across IPython directive blocks);

2. Compare the *output* of this with the output text that you've put in the IPython directive block (what comes
after `Out[NN]`);

3. If there is a difference, the directive will raise an error and your documentation build will fail.

You can do doctesting on multi-line output as well.  Just be careful
when using non-deterministic inputs like random numbers in the ipython
directive, because your inputs are run through a live interpreter, so
if you are doctesting random output you will get an error.  Here we
"seed" the random number generator for deterministic output, and we
suppress the seed line so it doesn't show up in the rendered output

.. ipython::

   In [133]: import numpy.random

   @suppress
   In [134]: numpy.random.seed(2358)

   @doctest
   In [135]: numpy.random.rand(10,2)
   Out[135]:
   array([[0.64524308, 0.59943846],
          [0.47102322, 0.8715456 ],
          [0.29370834, 0.74776844],
          [0.99539577, 0.1313423 ],
          [0.16250302, 0.21103583],
          [0.81626524, 0.1312433 ],
          [0.67338089, 0.72302393],
          [0.7566368 , 0.07033696],
          [0.22591016, 0.77731835],
          [0.0072729 , 0.34273127]])

For more information on @supress and @doctest decorators, please refer to the end of this file in
Pseudo-Decorators section.

Another demonstration of multi-line input and output

.. ipython::
   :verbatim:

   In [106]: print(x)
   jdh

   In [109]: for i in range(10):
      .....:     print(i)
      .....:
      .....:
   0
   1
   2
   3
   4
   5
   6
   7
   8
   9


Most of the "pseudo-decorators" can be used an options to ipython
mode.  For example, to setup matplotlib pylab but suppress the output,
you can do.  When using the matplotlib ``use`` directive, it should
occur before any import of pylab.  This will not show up in the
rendered docs, but the commands will be executed in the embedded
interpreter and subsequent line numbers will be incremented to reflect
the inputs::


  .. ipython::
     :suppress:

     In [144]: from matplotlib.pylab import *

     In [145]: ion()

.. ipython::
   :suppress:

   In [144]: from matplotlib.pylab import *

   In [145]: ion()

Likewise, you can set ``:doctest:`` or ``:verbatim:`` to apply these
settings to the entire block.  For example,

.. ipython::
   :verbatim:

   In [9]: cd mpl/examples/
   /home/jdhunter/mpl/examples

   In [10]: pwd
   Out[10]: '/home/jdhunter/mpl/examples'


   In [14]: cd mpl/examples/<TAB>
   mpl/examples/animation/        mpl/examples/misc/
   mpl/examples/api/              mpl/examples/mplot3d/
   mpl/examples/axes_grid/        mpl/examples/pylab_examples/
   mpl/examples/event_handling/   mpl/examples/widgets

   In [14]: cd mpl/examples/widgets/
   /home/msierig/mpl/examples/widgets

   In [15]: !wc *
       2    12    77 README.txt
      40    97   884 buttons.py
      26    90   712 check_buttons.py
      19    52   416 cursor.py
     180   404  4882 menu.py
      16    45   337 multicursor.py
      36   106   916 radio_buttons.py
      48   226  2082 rectangle_selector.py
      43   118  1063 slider_demo.py
      40   124  1088 span_selector.py
     450  1274 12457 total

You can create one or more pyplot plots and insert them with the
``@savefig`` decorator.

For more information on @savefig decorator, please refer to the end of this page in Pseudo-Decorators section.

.. ipython::

   @savefig plot_simple.png width=4in
   In [151]: plot([1,2,3]);

   # use a semicolon to suppress the output
   @savefig hist_simple.png width=4in
   In [151]: hist(np.random.randn(10000), 100);

In a subsequent session, we can update the current figure with some
text, and then resave

.. ipython::


   In [151]: ylabel('number')

   In [152]: title('normal distribution')

   @savefig hist_with_text.png width=4in
   In [153]: grid(True)

You can also have function definitions included in the source.

.. ipython::

   In [3]: def square(x):
      ...:     """
      ...:     An overcomplicated square function as an example.
      ...:     """
      ...:     if x < 0:
      ...:         x = abs(x)
      ...:     y = x * x
      ...:     return y
      ...:

Then call it from a subsequent section.

.. ipython::

   In [4]: square(3)
   Out [4]: 9

   In [5]: square(-2)
   Out [5]: 4


Writing Pure Python Code
------------------------

Pure python code is supported by the optional argument `python`. In this pure
python syntax you do not include the output from the python interpreter. The
following markup::

   .. ipython:: python

      foo = 'bar'
      print(foo)
      foo = 2
      foo**2

Renders as

.. ipython:: python

   foo = 'bar'
   print(foo)
   foo = 2
   foo**2

We can even plot from python, using the savefig decorator, as well as, suppress
output with a semicolon

.. ipython:: python

   @savefig plot_simple_python.png width=4in
   plot([1,2,3]);

For more information on @savefig decorator, please refer to the end of this page in Pseudo-Decorators section.

Similarly, std err is inserted

.. ipython:: python
   :okexcept:

   foo = 'bar'
   foo[)

Handling Comments
==================

Comments are handled and state is preserved

.. ipython:: python

   # comments are handled
   print(foo)

If you don't see the next code block then the options work.

.. ipython:: python
   :suppress:

   ioff()
   ion()

Splitting Python statements across lines
========================================

Multi-line input is handled.

.. ipython:: python

   line = 'Multi\
           line &\
           support &\
           works'
   print(line.split('&'))

Functions definitions are correctly parsed

.. ipython:: python

   def square(x):
       """
       An overcomplicated square function as an example.
       """
       if x < 0:
           x = abs(x)
       y = x * x
       return y

And persist across sessions

.. ipython:: python

   print(square(3))
   print(square(-2))

Pretty much anything you can do with the ipython code, you can do with
a simple python script. Obviously, though it doesn't make sense
to use the doctest option.

.. _pseudo-decorators:

Pseudo-Decorators
=================

Here are the supported decorators, and any optional arguments they
take.  Some of the decorators can be used as options to the entire
block (eg ``verbatim`` and ``suppress``), and some only apply to the
line just below them (eg ``savefig``).

@suppress

    execute the ipython input block, but suppress the input and output
    block from the rendered output.  Also, can be applied to the entire
    ``.. ipython`` block as a directive option with ``:suppress:``.

@verbatim

    insert the input and output block in verbatim, but auto-increment
    the line numbers. Internally, the interpreter will be fed an empty
    string, so it is a no-op that keeps line numbering consistent.
    Also, can be applied to the entire ``.. ipython`` block as a
    directive option with ``:verbatim:``.

@savefig OUTFILE [IMAGE_OPTIONS]

    save the figure to the static directory and insert it into the
    document, possibly binding it into a minipage and/or putting
    code/figure label/references to associate the code and the
    figure. Takes args to pass to the image directive (*scale*,
    *width*, etc can be kwargs); see `image options
    <http://docutils.sourceforge.net/docs/ref/rst/directives.html#image>`_
    for details.

@doctest

    Compare the pasted in output in the ipython block with the output
    generated at doc build time, and raise errors if they don't
    match. Also, can be applied to the entire ``.. ipython`` block as a
    directive option with ``:doctest:``.

Configuration Options
=====================

ipython_savefig_dir

    The directory in which to save the figures. This is relative to the
    Sphinx source directory. The default is `html_static_path`.

ipython_rgxin

    The compiled regular expression to denote the start of IPython input
    lines. The default is `re.compile('In \[(\d+)\]:\s?(.*)\s*')`. You
    shouldn't need to change this.

ipython_rgxout

    The compiled regular expression to denote the start of IPython output
    lines. The default is `re.compile('Out\[(\d+)\]:\s?(.*)\s*')`. You
    shouldn't need to change this.


ipython_promptin

    The string to represent the IPython input prompt in the generated ReST.
    The default is `'In [%d]:'`. This expects that the line numbers are used
    in the prompt.

ipython_promptout

    The string to represent the IPython prompt in the generated ReST. The
    default is `'Out [%d]:'`. This expects that the line numbers are used
    in the prompt.


Automatically generated documentation
=====================================

.. automodule:: IPython.sphinxext.ipython_directive


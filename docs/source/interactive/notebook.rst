.. _htmlnotebook:

The IPython Notebook
====================

The IPython Notebook is part of the IPython package, which aims to provide a 
powerful, interactive approach to scientific computation.
The IPython Notebook extends the previous text-console-based approach, and the 
later Qt console, in a qualitatively new diretion, providing a web-based
application suitable for capturing the whole scientific computation process.

.. seealso::

    :ref:`Installation requirements <installnotebook>` for the Notebook.


.. Basic structure
.. ---------------

Introduction
------------

The IPython Notebook combines two components:

* **The IPython Notebook web application**:

      The *IPython Notebook web app* is a browser-based tool for interactive 
      authoring of literate computations, in which explanatory text, 
      mathematics, computations and rich media output may be combined. Input 
      and output are stored in persistent cells that may be edited in-place.

* **Notebook documents**:

      *Notebook documents*, or *notebooks*, are plain text documents which 
      record all inputs and outputs of the computations, interspersed with 
      text, mathematics and HTML 5 representations of objects, in a literate 
      style.

Since the similarity in names can lead to some confusion, in this 
documentation we will  use capitalization of the word "notebook" to 
distinguish the Notebook app and notebook documents, thinking of the 
Notebook app as being a proper noun. We will also always refer to the 
"Notebook app" when we are referring to the browser-based interface, 
and usually to "notebook documents", instead of "notebooks", for added
precision.

We refer to the current state of the computational process taking place in the 
Notebook app, i.e. the (numbered) sequence of input and output cells, as the 
*notebook space*. Notebook documents provide an *exact*, *one-to-one* record 
of all the content in the notebook space, as a plain text file in JSON format. 
The Notebook app automatically saves, at certain intervals, the contents of 
the notebook space to a notebook document stored on disk, with the same name 
as the title of the notebook space, and the file extension ``.ipynb``. For 
this reason, there is no confusion about using the same word "notebook" for 
both the notebook space and the corresponding notebook document, since they are 
really one and the same concept (we could say that they are "isomorphic").


Main features of the IPython Notebook web app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The main features of the IPython Notebook app include:

* In-browser editing for code, with automatic syntax highlighting and 
  indentation and tab completion/introspection.

* Literate combination of code with rich text using the Markdown_ markup 
  language.

* Mathematics is easily included within the Markdown using LaTeX notation, and 
  rendered natively by MathJax_.

* Displays rich data representations (e.g. HTML / LaTeX / SVG) as the result 
  of computations.

* Publication-quality figures in a range of formats (SVG / PNG), rendered by 
  the matplotlib_ library, may be included inline and exported.


.. _MathJax: http://www.mathjax.org/
.. _matplotlib: http://matplotlib.org/
.. _Markdown: http://daringfireball.net/projects/markdown/syntax


Notebook documents
~~~~~~~~~~~~~~~~~~

Notebook document files are simple JSON_ files with the 
extension ``.ipynb``.
Since JSON is just plain text, they can be easily version-controlled and shared with colleagues.
The notebook stores a *complete*, *reproducible*, *one-to-one* copy of the state of the
computational state as it is inside the Notebook app. All computations
carried out, and the corresponding results obtained, can be combined in
a literate way, interleaving executable code with rich text, mathematics, 
and rich representations of objects.

.. _JSON: http://en.wikipedia.org/wiki/JSON

Notebooks may easily be exported to a range of static formats, including 
HTML (for example, for blog posts), PDF and slide shows, 
via the new nbconvert_ command.

Furthermore, any  ``.ipynb`` notebook document available from a public 
URL can be shared via the `IPython Notebook Viewer <nbviewer>`_ service.
This service loads the notebook document from the URL and will 
render it as a static web page. The results may thus be shared with a 
colleague, or as a public blog post, without other users needing to install 
IPython themselves.  NbViewer is simply NbConvert as a simple heroku webservice.

See the :ref:`installation documentation <install_index>` for directions on
how to install the notebook and its dependencies.

.. _nbviewer: http://nbviewer.ipython.org

.. note::

   You can start more than one notebook server at the same time, if you want 
   to work on notebooks in different directories.  By default the first 
   notebook server starts on port 8888, and later notebook servers search for  
   ports near that one.  You can also manually specify the port with the 
   ``--port`` option.
   

Basic workflow in the IPython Notebook web app
----------------------------------------------

Starting up
~~~~~~~~~~~~

You can start running the Notebook web app using the following command::

    $ ipython notebook

(Here, and in the sequel, the initial ``$`` represents the shell prompt, 
indicating that the command is to be run from the command line in a shell.)

The landing page of the IPython Notebook application, the *dashboard*, shows 
the notebooks currently available in the *notebook directory* (By default, the directory 
from which the notebook was started).
You can create new notebooks from the dashboard with the ``New Notebook``
button, or open existing ones by clicking on their name.
You can also drag and drop ``.ipynb`` notebooks and standard ``.py`` Python 
source code files into the notebook list area.


You can open an existing notebook directly, without having to go via the 
dashboard, with:

  ipython notebook my_notebook

The `.ipynb` extension is assumed if no extension is given.

The `File | Open...` menu option will open the dashboard in a new browser tab, 
to allow you to select a current notebook 
from the notebook directory or to create a new notebook.



Notebook user interface
~~~~~~~~~~~~~~~~~~~~~~~

When you open a new notebook document in the Notebook, you will be presented 
with the title associated to the notebook space/document, a *menu bar*, a 
*toolbar* and an empty *input cell*.

Notebook title
^^^^^^^^^^^^^^
The title of the notebook document that is currently being edited is displayed 
at the top of the page, next to the ``IP[y]: Notebook`` logo. This title may 
be edited directly by clicking on it. The title is reflected in the name of 
the ``.ipynb`` notebook document file that is saved.

Menu bar
^^^^^^^^
The menu bar presents different options that may be used to manipulate the way 
the Notebook functions.

Toolbar
^^^^^^^
The tool bar gives a quick way of accessing the most-used operations within 
the Notebook, by clicking on an icon.


Creating a new notebook document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A new notebook space/document may be created at any time, either from the 
dashboard, or using the `File | New` menu option from within an active 
notebook. The new notebook is created within the same directory and 
will open in a new browser tab. It will also be reflected as a new entry in 
the notebook list on the dashboard.


Structure of a notebook document
--------------------------------

Input cells
~~~~~~~~~~~
Input cells are at the core of the functionality of the IPython Notebook.
They are regions in the document in which you can enter different types of 
text and commands. To *execute* or *run* the *current cell*, i.e. the cell 
under the cursor, you can use the :kbd:`Shift-Enter` key combination. 
This tells the Notebook app to perform the relevant operation for each type of 
cell (see below), and then to display the resulting output.

The notebook consists of a sequence of input cells, labelled ``In[n]``, which 
may be executed in a non-linear way, and outputs ``Out[n]``, where ``n`` is a 
number which denotes the order in which the cells were executed over the 
history of the computational process. The contents of all of these cells are 
accessible as Python variables with the same names, forming a complete record 
of the history of the computation.



Input cell types
~~~~~~~~~~~~~~~~
Each IPython input cell has a *cell type*, of which there is a restricted 
number. The type of a cell may be set by using the cell type dropdown on the 
toolbar, or via the following keyboard shortcuts:

* **code**: :kbd:`Ctrl-m y`
* **markdown**: :kbd:`Ctrl-m m`
* **raw**: :kbd:`Ctrl-m t`
* **heading**: :kbd:`Ctrl-m 1` - :kbd:`Ctrl-m 6`

Upon initial creation, each input cell is by default a code cell.


Code cells
^^^^^^^^^^
A *code input cell* allows you to edit code inline within the cell, with full 
syntax highlighting and autocompletion/introspection. By default, the language 
associated to a code cell is Python, but other languages, such as ``julia`` 
and ``R``, can be handled using magic commands (see below).

When a code cell is executed with :kbd:`Shift-Enter`, the code that it 
contains is transparently exported and run in that language (with automatic 
compiling, etc., if necessary). The result that is returned from this 
computation  is then displayed in the notebook space as the cell's 
*output*. If this output is of a textual nature, it is placed into a 
numbered *output cell*. However, many other possible forms of output are also 
possible, including ``matplotlib`` figures and HTML tables (as used, for 
example, in the ``pandas`` data analyis package). This is known as IPython's 
*rich display* capability.


Markdown cells
^^^^^^^^^^^^^^
You can document the computational process in a literate way, alternating 
descriptive text with code, using *rich text*. In IPython this is accomplished 
by marking up text with the Markdown language. The corresponding cells are 
called *Markdown input cells*. The Markdown language provides a simple way to 
perform this text markup, that is, to specify which parts of the text should 
be emphasized (italics), bold, form lists, etc. 


When a Markdown input cell is executed, the Markdown code is converted into 
the corresponding formatted rich text. This output then *replaces* the 
original Markdown input cell, leaving just the visually-significant marked up 
rich text.  Markdown allows arbitrary HTML code for formatting.

Within Markdown cells, you can also include *mathematics* in a straightforward 
way, using standard LaTeX notation: ``$...$`` for inline mathematics and 
``$$...$$`` for displayed mathematics. When the Markdown cell is executed, 
the LaTeX portions are automatically rendered in the HTML output as equations 
with high quality typography. This is made possible by MathJax_, which 
supports a `large subset <mathjax_tex>`_ of LaTeX functionality 

.. _mathjax_tex: http://docs.mathjax.org/en/latest/tex.html

Standard mathematics environments defined by LaTeX and AMS-LaTeX (the 
`amsmath` package) also work, such as 
``\begin{equation}...\end{equation}``, and ``\begin{align}...\end{align}``.
New LaTeX macros may be defined using standard methods, 
such as ``\newcommand``, by placing them anywhere *between math delimiters* in 
a Markdown cell. These definitions are then available throughout the rest of 
the IPython session. (Note, however, that more care must be taken when using 
nbconvert_ to output to LaTeX).

Raw input cells
~~~~~~~~~~~~~~~

*Raw* input cells provide a place in which you can write *output* directly.
Raw cells are not evaluated by the Notebook, and have no output.
When passed through nbconvert, Raw cells arrive in the destination format unmodified,
allowing you to type full latex into a raw cell, which will only be rendered
by latex after conversion by nbconvert.

Heading cells
~~~~~~~~~~~~~

You can provide a conceptual structure for your computational document as a 
whole using different levels of headings; there are 6 levels available, from 
level 1 (top level) down to level 6 (paragraph). These can be used later for 
constructing tables of contents, etc.

As with Markdown cells, a heading input cell is replaced by a rich text 
rendering of the heading when the cell is executed.


Basic workflow
--------------

The normal workflow in a notebook is, then, quite similar to a standard 
IPython session, with the difference that you can edit cells in-place multiple 
times until you obtain the desired results, rather than having to 
rerun separate scripts with the ``%run`` magic command. (Magic commands do, 
however, also work in the notebook; see below).   

Typically, you will work on a computational problem in pieces, organizing 
related ideas into cells and moving forward once previous parts work 
correctly. This is much more convenient for interactive exploration than 
breaking up a computation into scripts that must be executed together, as was 
previously necessary, especially if parts of them take a long time to run

The only significant limitation that the Notebook currently has, compared to 
the Qt console, is that it cannot run any code that expects input from the 
kernel (such as scripts that call :func:`raw_input`).  Very importantly, this 
means that the ``%debug`` magic does *not* currently work in the notebook!  

This limitation will be overcome in the future, but in the meantime, there is 
a simple solution for debugging: you can attach a Qt console to your existing 
notebook kernel, and run ``%debug`` from the Qt console.
If your notebook is running on a local computer (i.e. if you are accessing it 
via your localhost address at ``127.0.0.1``), then you can just type 
``%qtconsole`` in the notebook and a Qt console will open up, connected to 
that same kernel.

At certain moments, it may be necessary to interrupt a calculation which is 
taking too long to complete. This may be done with the ``Kernel | Interrupt`` 
menu option, or the :kbd:``Ctrl-i`` keyboard shortcut.
Similarly, it may be necessary or desirable to restart the whole computational 
process, with the ``Kernel | Restart`` menu option or :kbd:``Ctrl-.`` 
shortcut. This gives an equivalent state to loading the notebook document 
afresh.

    
.. warning::

   While in simple cases you can "roundtrip" a notebook to Python, edit the
   Python file, and then import it back without loss of main content, this is 
   in general *not guaranteed to work*.  First, there is extra metadata
   saved in the notebook that may not be saved to the ``.py`` format.  And as
   the notebook format evolves in complexity, there will be attributes of the
   notebook that will not survive a roundtrip through the Python form.  You
   should think of the Python format as a way to output a script version of a
   notebook and the import capabilities as a way to load existing code to get 
   a notebook started.  But the Python version is *not* an alternate notebook
   format.


Keyboard shortcuts
~~~~~~~~~~~~~~~~~~
All actions in the notebook can be performed with the mouse, but keyboard 
shortcuts are also available for the most common ones. The essential shortcuts
to remember are the following:

* :kbd:`Shift-Enter`:  run cell
    Execute the current cell, show output (if any), and jump to the next cell 
    below. If :kbd:`Shift-Enter` is invoked on the last input cell, a new code 
    cell will also be created. Note that in the notebook, typing :kbd:`Enter` 
    on its own *never* forces execution, but rather just inserts a new line in 
    the current input cell. :kbd:`Shift-Enter` is equivalent to clicking the 
    ``Cell | Run`` menu item.

* :kbd:`Ctrl-Enter`: run cell in-place
    Execute the current cell as if it were in "terminal mode", where any 
    output is shown, but the cursor *remains* in the current cell. The cell's
    entire contents are selected after execution, so you can just start typing
    and only the new input will be in the cell. This is convenient for doing
    quick experiments in place, or for querying things like filesystem
    content, without needing to create additional cells that you may not want
    to be saved in the notebook.

* :kbd:`Alt-Enter`: run cell, insert below
    Executes the current cell, shows the output, and inserts a *new* input 
    cell between the current cell and the cell below (if one exists). This  
    is thus a shortcut for the sequence :kbd:`Shift-Enter`, :kbd:`Ctrl-m a`.
    (:kbd:`Ctrl-m a` adds a new cell above the current one.)
  
* :kbd:`Ctrl-m`: 
  This is the prefix for *all* other shortcuts, which consist of :kbd:`Ctrl-m` 
  followed by a single letter or character. For example, if you type 
  :kbd:`Ctrl-m h` (that is, the sole letter :kbd:`h` after :kbd:`Ctrl-m`), 
  IPython will show you all the available keyboard shortcuts.


..
    TODO: these live in IPython/html/static/notebook/js/quickhelp.js
    They were last updated for IPython 1.0 release, so update them again for
    future releases.

Here is the complete set of keyboard shortcuts available:

============  ==========================
**Shortcut**        **Action**
------------  --------------------------
Shift-Enter    run cell
Ctrl-Enter     run cell in-place
Alt-Enter      run cell, insert below
Ctrl-m x       cut cell
Ctrl-m c       copy cell
Ctrl-m v       paste cell
Ctrl-m d       delete cell
Ctrl-m z       undo last cell deletion
Ctrl-m -       split cell
Ctrl-m a       insert cell above
Ctrl-m b       insert cell below
Ctrl-m o       toggle output
Ctrl-m O       toggle output scroll
Ctrl-m l       toggle line numbers
Ctrl-m s       save notebook
Ctrl-m j       move cell down
Ctrl-m k       move cell up
Ctrl-m y       code cell
Ctrl-m m       markdown cell
Ctrl-m t       raw cell
Ctrl-m 1-6     heading 1-6 cell
Ctrl-m p       select previous
Ctrl-m n       select next
Ctrl-m i       interrupt kernel
Ctrl-m .       restart kernel
Ctrl-m h       show keyboard shortcuts
============  ==========================

   

Magic commands
--------------
Magic commands, or *magics*, are commands for controlling IPython itself.
They all begin with ``%`` and are entered into code input cells; the code 
cells are executed as usual with :kbd:`Shift-Enter`.

The magic commands call special functions defined by IPython which manipulate 
the computational state in certain ways.

There are two types of magics:

  - **line magics**:

     These begin with a single ``%`` and take as arguments the rest of the 
     *same line* of the code cell. Any other lines of the code cell are 
     treated as if they were part of a standard code cell.

  - **cell magics**:

      These begin with ``%%`` and operate on the *entire* remaining contents 
      of the code cell.

Line magics
~~~~~~~~~~~
Some of the available line magics are the following:

  * ``%load filename``:

        Loads the contents of the file ``filename`` into a new code cell. This 
        can be a URL for a remote file.

  * ``%timeit code``: 

      An easy way to time how long the single line of code ``code`` takes to 
      run

  * ``%config``:

      Configuration of the IPython Notebook

  * ``%lsmagic``:

      Provides a list of all available magic commands

Cell magics
~~~~~~~~~~~

  * ``%%latex``:

      Renders the entire contents of the cell in LaTeX, without needing to use 
      explicit LaTeX delimiters.

  * ``%%bash``:

      The code cell is executed by sending it to be executed by ``bash``. The 
      output of the ``bash`` commands is captured and displayed in the 
      notebook.

  * ``%%file filename``:

      Writes the contents of the cell to the file ``filename``.
      **Caution**: The file is over-written without warning!

  * ``%%R``:

      Execute the contents of the cell using the R language.

  * ``%%timeit``:

      Version of ``%timeit`` which times the entire block of code in the 
      current code cell.



Several of the cell magics provide functionality to manipulate the filesystem 
of a remote server to which you otherwise do not have access.  


Plotting
--------
One major feature of the Notebook is the ability to interact with 
plots that are the output of running code cells. IPython is designed to work 
seamlessly with the ``matplotlib`` plotting library to provide this 
functionality. 

To set this up, before any plotting is performed you must execute the
``%matplotlib`` magic command. This performs the necessary behind-the-scenes 
setup for IPython to work correctly hand in hand with ``matplotlib``; it does 
*not*, however, actually execute any Python ``import`` commands, that is, no 
names are added to the namespace.

If the ``%matplotlib`` magic is called without an argument, the 
output of a plotting command is displayed using the default ``matplotlib`` 
backend in a separate window. Alternatively, the backend can be explicitly 
requested using, for example::

  %matplotlib gtk

A particularly interesting backend is the ``inline`` backend.
This is applicable only for the IPython Notebook and the IPython QtConsole.
It can be invoked as follows::

  %matplotlib inline

With this backend, output of plotting commands is displayed *inline* within 
the notebook format, directly below the input cell that produced it. The 
resulting plots will then also be stored in the notebook document. This 
provides a key part of the functionality for reproducibility_ that the IPython 
Notebook provides.

.. _reproducibility: https://en.wikipedia.org/wiki/Reproducibility



Configuring the IPython Notebook
--------------------------------
The IPython Notebook can be run with a variety of command line arguments. 
To see a list of available options enter::

  $ ipython notebook --help 

Defaults for these options can also be set by creating a file named 
``ipython_notebook_config.py`` in your IPython *profile folder*. The profile 
folder is a subfolder of your IPython directory; to find out where it is 
located, run::

  $ ipython locate

To create a new set of default configuration files, with lots of information 
on available options, use::

  $ ipython profile create

.. seealso:

    :ref:`config_overview`, in particular :ref:`Profiles`.


Importing `.py` files
----------------------


``.py`` files will be imported into the IPython Notebook as a notebook with 
the same basename, but an ``.ipynb`` extension, located in the notebook 
directory. The notebook created will have just one cell, which will contain 
all the code in the ``.py`` file. You can later manually partition this into 
individual cells using the ``Edit | Split Cell`` menu option, or the 
:kbd:`Ctrl-m -` keyboard shortcut.

.. Alternatively, prior to importing the ``.py``, you can manually add ``# <
nbformat>2</nbformat>`` at the start of the file, and then add separators for 
text and code cells, to get a cleaner import with the file already broken into 
individual cells.


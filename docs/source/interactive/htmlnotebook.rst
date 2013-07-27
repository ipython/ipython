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


Basic structure
---------------

The IPython Notebook combines two components:

* **The IPython Notebook web application**:

      The *IPython Notebook web app* is a browser-based tool for interactive 
      authoring of literate computations, in which explanatory text, mathematics,
      computations and rich media output may be combined. Input and output are 
      stored in persistent cells that may be edited in-place.

* **Notebook documents**:

      *Notebook documents*, or *notebooks*, are plain text documents which record 
      all inputs and outputs of the computations, interspersed with text, 
      mathematics and HTML 5 representations of objects, in a literate style.

Since the similarity in names can lead to some confusion, in this documentation 
we will  use capitalization of the word "notebook" to distinguish the 
*N*otebook app and *n*otebook documents, thinking of the Notebook app as being 
a proper noun. We will also always refer to the "Notebook app" when we are 
referring to the browser-based interface, and usually to "notebook documents", 
instead of "notebooks", for added precision.

We refer to the current state of the computational process taking place in the 
Notebook app, i.e. the (numbered) sequence of input and output cells, as the 
*notebook space*. Notebook documents provide an *exact*, *one-to-one* record 
of all the content in the notebook space, as a plain text file in JSON format. 
The Notebook app automatically saves, at certain intervals, the contents of 
the notebook space to a notebook document stored on disk, with the same name 
as the title of the notebook space, and the file extension ``.ipynb``. For 
this reason, there is no confusion about using the same word "notebook" for 
both the notebook space and the corresonding notebook document, since they are 
really one and the same concept (we could say that they are "isomorphic").


Main features of the IPython Notebook web app
---------------------------------------------

The main features of the IPython Notebook app include:

* In-browser editing for code, with automatic syntax highlighting and indentation and tab completion/introspection.

* Literate combination of code with rich text using the Markdown_ markup language.

* Mathematics is easily included within the Markdown using LaTeX notation, and rendered natively by MathJax_.

* Displays rich data representations (e.g. HTML / LaTeX / SVG) as the result of computations.

* Publication-quality figures in a range of formats (SVG / PNG), rendered by the matplotlib_ library, may be included inline and exported.


.. _MathJax: http://www.mathjax.org/
.. _matplotlib: http://matplotlib.org/
.. _Markdown: http://daringfireball.net/projects/markdown/syntax


Notebook documents
------------------

Notebook document files are just standard, ASCII-coded text files with the extension ``.ipynb``, stored in the working directory on your computer. Since the contents of the files are just plain text, they can be easily version-controlled and shared with colleagues.

Internally, notebook document files use the JSON_ format, allowing them to 
store a *complete*, *reproducible*, *one-to-one* copy of the state of the computational state as it is inside the Notebook app. 
All computations carried out, and the corresponding results obtained, can be 
combined in a literate way, interleaving executable code with rich text, mathematics, and HTML 5 representations of objects.

.. _JSON: http://en.wikipedia.org/wiki/JSON

Notebooks may easily be exported to a range of static formats, including 
HTML (for example, for blog posts), PDF and slide shows, via the newly-included `nbconvert script`_ functionality.

Furthermore, any  ``.ipynb`` notebook document with a publicly-available URL can be shared via the `IPython Notebook Viewer`_ service. This service loads the notebook document from the URL  which will 
provide it as a static web page. The results may thus be shared with a colleague, or as a public blog post, without other users needing to install IPython themselves.

See the :ref:`installation documentation <install_index>` for directions on
how to install the notebook and its dependencies.

.. _`Ipython Notebook Viewer`: http://nbviewer.ipython.org

.. note::

   You can start more than one notebook server at the same time, if you want to
   work on notebooks in different directories.  By default the first notebook
   server starts on port 8888, and later notebook servers search for  ports 
   near that one.  You can also manually specify the port with the ``--port``
   option.
   

Starting up the IPython Notebook web app
----------------------------------------

You can start running the Notebook web app using the following command::

    $ ipython notebook

(Here, and in the sequel, the initial ``$`` represents the shell prompt, indicating that the command is to be run from the command line in a shell.)

The landing page of the notebook server application, the *dashboard*, shows 
the notebooks currently available in the *working directory* (the directory 
from which the notebook was started).
You can create new notebooks from the dashboard with the ``New Notebook``
button, or open existing ones by clicking on their name.
You can also drag and drop ``.ipynb`` notebooks and standard ``.py`` Python 
source code files into the notebook list area.

``.py`` files will be imported into the IPython Notebook as a notebook with 
the same name, but an ``.ipynb`` extension, located in the working directory.  
The notebook created will have just one cell, which will contain all the 
code in the ``.py`` file. You can later manually partition this into 
individual cells using the ``Edit | Split Cell`` menu option, or the 
:kbd:`Ctrl-m -` keyboard shortcut.

.. Alternatively, prior to importing the ``.py``, you can manually add ``# <
nbformat>2</nbformat>`` at the start of the file, and then add separators for 
text and code cells, to get a cleaner import with the file already broken into 
individual cells.

When you open or create a new notebook, your browser tab will reflect the name 
of that notebook, prefixed by the "IPy" icon denoting that the tab corresponds to the IPython Notebook.
The URL is currently not meant to be human-readable and is not persistent 
across invocations of the notebook server; however, this will change in a 
future version of IPython.


The IPython Notebook web app is based on a server-client structure. 
This server uses a two-process kernel architecture based on ZeroMQ, as well as 
Tornado for serving HTTP requests. Other clients may connect to the same 
underlying IPython kernel; see below.


Notebook user interface
-----------------------

When you open a new notebook document in the Notebook, you will be presented 
with the title associated to the notebook space/document, a *menu bar*, a 
*toolbar* and an empty *input cell*.

Notebook title
~~~~~~~~~~~~~~
The title of the notebook document that is currently being edited is displayed 
at the top of the page, next to the ``IP[y]: Notebook`` logo. This title may 
be edited directly by clicking on it. The title is reflected in the name of 
the ``.ipynb`` notebook document file that is saved.

Menu bar
~~~~~~~~
The menu bar presents different options that may be used to manipulate the way 
the Notebook functions.

Toolbar
~~~~~~~
The tool bar gives a quick way of accessing the most-used operations within 
the Notebook, by clicking on an icon.

Creating a new notebook document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A new notebook space/document may be created at any time, either from the dashboard, or using the `File | New` menu option from within an active notebook. The new notebook is created within the same working directory and will open in a new browser tab. It will also be reflected as a new entry in the notebook list on the dashboard.


Input cells
-----------
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
process, with the ``Kernel | Restart`` menu option or :kbd:``Ctrl-.`` shortcut.
This gives an equivalent state to loading the notebook document afresh.

    
.. warning::

   While in simple cases you can "roundtrip" a notebook to Python, edit the
   Python file, and then import it back without loss of main content, this is 
   in general *not guaranteed to work*.  First, there is extra metadata
   saved in the notebook that may not be saved to the ``.py`` format.  And as
   the notebook format evolves in complexity, there will be attributes of the
   notebook that will not survive a roundtrip through the Python form.  You
   should think of the Python format as a way to output a script version of a
   notebook and the import capabilities as a way to load existing code to get a
   notebook started.  But the Python version is *not* an alternate notebook
   format.


Keyboard shortcuts
------------------
All actions in the notebook can be achieved with the mouse, but keyboard 
shortcuts are also available for the most common ones, so that productive use 
of the notebook can be achieved with minimal mouse usage. The main shortcuts 
to remember are the following:

* :kbd:`Shift-Enter`: 

    Execute the current cell, show output (if any), and jump to the next cell 
    below. If :kbd:`Shift-Enter` is invoked on the last input cell, a new code 
    cell will also be created. Note that in the notebook, typing :kbd:`Enter` 
    on its own *never* forces execution, but rather just inserts a new line in 
    the current input cell. In the Notebook it is thus always necessary to use 
    :kbd:`Shift-Enter` to execute the cell (or use the ``Cell | Run`` menu 
    item).

* :kbd:`Ctrl-Enter`: 
    Execute the current cell as if it were in "terminal mode", where any 
    output is shown, but the cursor *remains* in the current cell. This is 
    convenient for doing quick experiments in place, or for querying things 
    like filesystem content, without needing to create additional cells that 
    you may not want to be saved in the notebook.

* :kbd:`Alt-Enter`: 
    Executes the current cell, shows the output, and inserts a *new* input 
    cell between the current cell and the adjacent cell (if one exists). This  
    is thus a shortcut for the sequence :kbd:`Shift-Enter`, :kbd:`Ctrl-m a`.
    (:kbd:`Ctrl-m a` adds a new cell above the current one.)
  
* :kbd:`Ctrl-m`: 
  This is the prefix for *all* other shortcuts, which consist of :kbd:`Ctrl-m` followed by a single letter or character. For example, if you type :kbd:`Ctrl-m h` (that is, the sole letter :kbd:`h` after :kbd:`Ctrl-m`), IPython will show you all the available keyboard shortcuts.
   

Input cell types
----------------
Each IPython input cell has a *cell type*, of which there is a restricted 
number. The type of a cell may be set by using the cell type dropdown on the 
toolbar, or via the following keyboard shortcuts:

* **code**: :kbd:`Ctrl-m y`
* **markdown**: :kbd:`Ctrl-m m`
* **raw**: :kbd:`Ctrl-m t`
* **heading**: :kbd:`Ctrl-m 1` - :kbd:`Ctrl-m 6`

Upon initial creation, each input cell is by default a code cell.


Code cells
~~~~~~~~~~
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


Rich text using Markdown
~~~~~~~~~~~~~~~~~~~~~~~~
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
``$$...$$`` for displayed mathematics. When the Markdown cell is executed, the LaTeX portions are automatically rendered in the HTML output as equations with high quality typography. This is made possible by MathJax_, which supports a `large subset`_ of LaTeX functionality 

.. _`large subset`: http://docs.mathjax.org/en/latest/tex.html

Standard mathematics environments defined by LaTeX and AMS-LaTeX (the `amsmath` package) also work, such as 
``\begin{equation}...\end{equation}``, and ``\begin{align}...\end{align}``.
New LaTeX macros may be defined using standard methods, 
such as ``\newcommand``, by placing them anywhere *between math delimiters* in a Markdown cell. These definitions are then available throughout the rest of the IPython session. (Note, however, that more care must be taken when using the `nbconvert script`_ to output to LaTeX).

Raw input cells
~~~~~~~~~~~~~~~
*Raw* input cells provide a place in which you can put additional information 
which you do not want to evaluated by the Notebook. This can be used, for 
example, to include extra information that is needed when exporting to a 
certain format. The output after evaluating a raw cell is just a verbatim copy 
of the input.

Heading cells
~~~~~~~~~~~~~
You can provide a conceptual structure for your computational document as a 
whole using different levels of headings; there are 6 levels available, from 
level 1 (top level) down to level 6 (paragraph). These can be used later for 
constructing tables of contents, etc.

As with Markdown cells, a heading input cell is replaced by a rich text 
rendering of the heading when the cell is executed.


Magic commands
~~~~~~~~~~~~~~
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

      These begin with ``%%`` and operate on the *entire* remaining contents of 
      the code cell.

Line magics
~~~~~~~~~~~
Some of the available line magics are the following:

  * ``%load filename``:

        Loads the contents of the file ``filename`` into a new code cell. This 
        can be a URL for a remote file.

  * ``%timeit code``: 

      An easy way to time how long the single line of code ``code`` takes to run

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
      output of the ``bash`` commands is captured and displayed in the notebook.

  * ``%%file filename``:

      Writes the contents of the cell to the file ``filename``.
      **Caution**: The file is over-written without warning!

  * ``%%R``:

      Execute the contents of the cell using the R language.

  * ``%%timeit``:

      Version of ``%timeit`` which times the entire block of code in the current code cell.



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

For more agile *interactive* use of the notebook space, an alternative magic, 
``%pylab``, is provided. This does the same work as the ``%matplotlib`` magic, 
but *in addition* it automatically executes a standard sequence of ``import`` 
statements required to work with the ``%matplotlib`` library, importing the 
following names into the namespace:

  ``numpy`` as ``np``; ``matplotlib.pyplot`` as ``plt``;
  ``matplotlib``, ``pylab`` and ``mlab`` from ``matplotlib``; and *all names* 
  from within ``numpy`` and ``pylab``. 

However, the use of ``%pylab`` is discouraged, since names coming from 
different packages may collide. In general, the use of ``from package import 
*`` is discouraged. A better option is then::
  
    %pylab --no-import-all

which imports the  names listed above, but does *not* perform this ``import *`` 
imports.

If the ``%matplotlib`` or ``%pylab` magics are called without an argument, the 
output of a plotting command is displayed using the default ``matplotlib`` 
backend in a separate window. Alternatively, the backend can be explicitly 
requested using, for example::

  %matplotlib gtk

A particularly interesting backend is the ``inline`` backend.
This is applicable only for the IPython Notebook and the IPython Qtconsole. 
It can be invoked as follows::

  %matplotlib inline

With this backend, output of plotting commands is displayed *inline* within 
the notebook format, directly below the input cell that produced it. The resulting plots will then also be stored in the notebook document. This provides a key part of the functionality for reproducibility_ that the IPython Notebook provides.

.. _reproducibility: https://en.wikipedia.org/wiki/Reproducibility

.. _`nbconvert script`:

Converting notebooks to other formats
-------------------------------------
Newly added in the 1.0 release of IPython is the ``nbconvert`` tool, which 
allows you to convert an ``.ipynb`` notebook document file into various static 
formats. 

Currently, ``nbconvert`` is provided as a command line tool, run as a script using IPython. In the future, a direct export capability from within the IPython Notebook web app is planned. 

The command-line syntax to run the ``nbconvert`` script is::

  $ ipython nbconvert --format=FORMAT notebook.ipynb

This will convert the IPython document file ``notebook.ipynb`` into the output 
format given by the ``FORMAT`` string.

The default output format is HTML, for which the ``--format`` modifier may be omitted::
  
  $ ipython nbconvert notebook.ipynb

The currently supported export formats are the following:

* HTML:

  - **full_html**:
    Standard HTML

  - **simple_html**:
    Simplified HTML

  - **reveal**:
    HTML slideshow presentation for use with the ``reveal.js`` package

* PDF:

  - **sphinx_howto**:
    The format for Sphinx_ HOWTOs; similar to an ``article`` in LaTeX

  - **sphinx_manual**:
    The format for Sphinx_ manuals; similar to a ``book`` in LaTeX 

  - **latex**:
    An article formatted completely using LaTeX

* Markup:

  - **rst**:
    reStructuredText_ markup

  - **markdown**:
    Markdown_ markup

.. _Sphinx: http://sphinx-doc.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html

* Python:

    Comments out all the non-Python code to produce a ``.py`` Python
    script with just the code content. Currently the output includes IPython magics, and so can be run with ``ipython``, after changing the extension of the script to ``.ipy``.
    
The files output file created by ``nbconvert`` will have the same base name as
the notebook and will be placed in the current working directory. Any
supporting files (graphics, etc) will be placed in a new directory with the
same base name as the notebook, suffixed with ``_files``::

  $ ipython nbconvert notebook.ipynb
  $ ls
  notebook.ipynb   notebook.html    notebook_files/

Each of the options for PDF export produces as an intermediate step a LaTeX 
``.tex`` file with the same basename as the notebook, as well as individual 
files for each figure, and ``.text`` files with textual output from running
code cells.

To actually produce the final PDF file, run the following commands::
  
  $ ipython nbconvert --format=latex notebook.ipynb
  $ pdflatex notebook

This requires a local installation of LaTeX on your machine.
The output is a PDF file ``notebook.pdf``, also placed inside the ``nbconvert_build`` subdirectory.

Alternatively, the output may be sent to standard output with::
    
  $ ipython nbconvert notebook.ipynb --stdout
    
Multiple notebooks can be specified from the command line::
    
  $ ipython nbconvert notebook*.ipynb
  $ ipython nbconvert notebook1.ipynb notebook2.ipynb
    
or via a list in a configuration file, say ``mycfg.py``, containing the text::

  c = get_config()
  c.NbConvertApp.notebooks = ["notebook1.ipynb", "notebook2.ipynb"]

and using the command::

  $ ipython nbconvert --config mycfg.py


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


Extracting standard Python files from notebooks
-----------------------------------------------
``.ipynb`` notebook document files are plain text files which store a 
representation in JSON format of the contents of a notebook space. As such, 
they are not valid ``.py`` Python scripts, and so can be neither imported 
directly with ``import`` in Python, nor run directly as a standard Python 
script (though both of these are possible with simple workarounds).


To extract the Python code from within a notebook document, the simplest method is to use the ``File | Download as | Python (.py)`` menu item; the resulting ``.py`` script will be downloaded to your browser's  default download location.

An alternative is to pass an argument to the IPython Notebook, from the moment 
when it is originally started, specifying that whenever it saves an ``.ipynb`` 
notebook document, it should, at the same time, save the corresponding 
 ``.py`` script. To do so, you can execute the following command::

  $ ipython notebook --script

or you can set this option permanently in your configuration file with::

  c = get_config()
  c.NotebookManager.save_script=True

The result is that standard ``.py`` files are also now generated, which 
can be ``%run``, imported from regular IPython sessions or other notebooks, or 
executed at the command line, as usual.  Since the raw code you have typed is 
exported, you must avoid using syntax such as IPython magics and other IPython-
specific extensions to the language for the files to be able to be 
successfully imported; or you can change the script's extension to ``.ipy`` and run it with::

  $ ipython script.ipy

In normal Python practice, the standard way to differentiate importable code 
in a Python script from the "executable" part of a script is to use the 
following idiom at the start of the executable part of the code::


  if __name__ == '__main__'

    # rest of the code...
  
Since all cells in the notebook are run as top-level code, you will need to
similarly protect *all* cells that you do not want executed when other scripts
try to import your notebook.  A convenient shortand for this is to define early
on::

  script = __name__ == '__main__'

Then in any cell that you need to protect, use::

  if script:
    # rest of the cell...


.. _notebook_security:

Security
--------

You can protect your Notebook server with a simple single password by
setting the :attr:`NotebookApp.password` configurable. You can prepare a
hashed password using the function :func:`IPython.lib.security.passwd`:

.. sourcecode:: ipython

    In [1]: from IPython.lib import passwd
    In [2]: passwd()
    Enter password: 
    Verify password: 
    Out[2]: 'sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed'
    
.. note::

  :func:`~IPython.lib.security.passwd` can also take the password as a string
  argument. **Do not** pass it as an argument inside an IPython session, as it
  will be saved in your input history.

You can then add this to your :file:`ipython_notebook_config.py`, e.g.::

    # Password to use for web authentication
    c = get_config()
    c.NotebookApp.password = 
    u'sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed'

When using a password, it is a good idea to also use SSL, so that your password
is not sent unencrypted by your browser. You can start the notebook to
communicate via a secure protocol mode using a self-signed certificate with 
the command::

    $ ipython notebook --certfile=mycert.pem

.. note::

    A self-signed certificate can be generated with ``openssl``.  For example, 
    the following command will create a certificate valid for 365 days with 
    both the key and certificate data written to the same file::

        $ openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.
        pem -out mycert.pem

Your browser will warn you of a dangerous certificate because it is
self-signed.  If you want to have a fully compliant certificate that will not
raise warnings, it is possible (but rather involved) to obtain one,
`as explained in detailed in this tutorial`__.

.. __: http://arstechnica.com/security/news/2009/12/how-to-get-set-with-a-
secure-sertificate-for-free.ars
	
Keep in mind that when you enable SSL support, you will need to access the
notebook server over ``https://``, not over plain ``http://``.  The startup
message from the server prints this, but it is easy to overlook and think the
server is for some reason non-responsive.


Connecting to an existing kernel
---------------------------------

The notebook server always prints to the terminal the full details of 
how to connect to each kernel, with messages such as the following::

    [IPKernelApp] To connect another client to this kernel, use:
    [IPKernelApp] --existing kernel-3bb93edd-6b5a-455c-99c8-3b658f45dde5.json

This long string is the name of a JSON file that contains all the port and 
validation information necessary to connect to the kernel.  You can then, for 
example, manually start a Qt console connected to the *same* kernel with::

    $ ipython qtconsole --existing 
    kernel-3bb93edd-6b5a-455c-99c8-3b658f45dde5.json

If you have only a single kernel running, simply typing::

    $ ipython qtconsole --existing

will automatically find it. (It will always find the most recently 
started kernel if there is more than one.)  You can also request this 
connection data by typing ``%connect_info``; this will print the same 
file information as well as the content of the JSON data structure it contains.


Running a public notebook server
--------------------------------

If you want to access your notebook server remotely via a web browser,
you can do the following.  

Start by creating a certificate file and a hashed password, as explained 
above.  Then create a custom profile for the notebook, with the following 
command line, type::

  $ ipython profile create nbserver

In the profile directory just created, edit the file 
``ipython_notebook_config.py``.  By default, the file has all fields 
commented; the minimum set you need to uncomment and edit is the following::

     c = get_config()

     # Kernel config
     c.IPKernelApp.pylab = 'inline'  # if you want plotting support always

     # Notebook config
     c.NotebookApp.certfile = u'/absolute/path/to/your/certificate/mycert.pem'
     c.NotebookApp.ip = '*'
     c.NotebookApp.open_browser = False
     c.NotebookApp.password = u'sha1:bcd259ccf...[your hashed password here]'
     # It is a good idea to put it on a known, fixed port
     c.NotebookApp.port = 9999

You can then start the notebook and access it later by pointing your browser to
``https://your.host.com:9999`` with ``ipython notebook --profile=nbserver``.

Running with a different URL prefix
-----------------------------------

The notebook dashboard (the landing page with an overview
of the notebooks in your working directory) typically lives at the URL
``http://localhost:8888/``. If you prefer that it lives, together with the 
rest of the notebook, under a sub-directory,
e.g. ``http://localhost:8888/ipython/``, you can do so with
configuration options like the following (see above for instructions about
modifying ``ipython_notebook_config.py``)::

    c.NotebookApp.base_project_url = '/ipython/'
    c.NotebookApp.base_kernel_url = '/ipython/'
    c.NotebookApp.webapp_settings = {'static_url_prefix':'/ipython/static/'}

Using a different notebook store
--------------------------------

By default, the Notebook app stores the notebook documents that it saves as 
files in the working directory of the Notebook app, also known as the 
``notebook_dir``. This  logic is implemented in the 
:class:`FileNotebookManager` class. However, the server can be configured to 
use a different notebook manager class, which can 
store the notebooks in a different format. 

Currently, we ship a :class:`AzureNotebookManager` class that stores notebooks 
in Azure blob storage. This can be used by adding the following lines to your 
``ipython_notebook_config.py`` file::

    c.NotebookApp.notebook_manager_class = 
    'IPython.html.services.notebooks.azurenbmanager.AzureNotebookManager'
    c.AzureNotebookManager.account_name = u'paste_your_account_name_here'
    c.AzureNotebookManager.account_key = u'paste_your_account_key_here'
    c.AzureNotebookManager.container = u'notebooks'

In addition to providing your Azure Blob Storage account name and key, you 
will have to provide a container name; you can use multiple containers to 
organize your notebooks.

.. _notebook_format:

Notebook JSON file format
-------------------------
Notebook documents are JSON files with an ``.ipynb`` extension, formatted
as legibly as possible with minimal extra indentation and cell content broken
across lines to make them reasonably friendly to use in version-control
workflows.  You should be very careful if you ever manually edit this JSON
data, as it is extremely easy to corrupt its internal structure and make the
file impossible to load.  In general, you should consider the notebook as a
file meant only to be edited by the IPython Notebook app itself, not for 
hand-editing.

.. note::

     Binary data such as figures are also saved directly in the JSON file.  
     This provides convenient single-file portability, but means that the 
     files can be large; a ``diff`` of binary data is also not very 
     meaningful.  Since the binary blobs are encoded in a single line, they 
     affect only one line of the ``diff`` output, but they are typically very 
     long lines.  You can use the ``Cell | All Output | Clear`` menu option to 
     remove all output from a notebook prior to committing it to version 
     control, if this is a concern.

The notebook server can also generate a pure Python version of your notebook, 
using the ``File | Download as`` menu option. The resulting ``.py`` file will 
contain all the code cells from your notebook verbatim, and all Markdown cells 
prepended with a comment marker.  The separation between code and Markdown
cells is indicated with special comments and there is a header indicating the
format version.  All output is removed when exporting to Python.

As an example, consider a simple notebook called ``simple.ipynb`` which 
contains one Markdown cell, with the content ``The simplest notebook.``, one 
code input cell with the content ``print "Hello, IPython!"``, and the 
corresponding output.

The contents of the notebook document ``simple.ipynb`` is the following JSON 
container::

  {
   "metadata": {
    "name": "simple"
   },
   "nbformat": 3,
   "nbformat_minor": 0,
   "worksheets": [
    {
     "cells": [
      {
       "cell_type": "markdown",
       "metadata": {},
       "source": "The simplest notebook."
      },
      {
       "cell_type": "code",
       "collapsed": false,
       "input": "print \"Hello, IPython\"",
       "language": "python",
       "metadata": {},
       "outputs": [
        {
         "output_type": "stream",
         "stream": "stdout",
         "text": "Hello, IPython\n"
        }
       ],
       "prompt_number": 1
      }
     ],
     "metadata": {}
    }
   ]
  }


The corresponding Python script is::

  # -*- coding: utf-8 -*-
  # <nbformat>3.0</nbformat>

  # <markdowncell>

  # The simplest notebook.

  # <codecell>

  print "Hello, IPython"

Note that indeed the output of the code cell, which is present in the JSON 
container, has been removed in the ``.py`` script.


Known issues
------------

When behind a proxy, especially if your system or browser is set to autodetect
the proxy, the Notebook app might fail to connect to the server's websockets,
and present you with a warning at startup. In this case, you need to configure
your system not to use the proxy for the server's address.

For example, in Firefox, go to the Preferences panel, Advanced section,
Network tab, click 'Settings...', and add the address of the notebook server
to the 'No proxy for' field.

    
.. _Markdown: http://daringfireball.net/projects/markdown/basics

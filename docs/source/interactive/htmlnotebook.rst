.. _htmlnotebook:

The IPython Notebook
====================

The IPython Notebook is part of the IPython package, which aims to provide a powerful, interactive approach to scientific computation.
The IPython Notebook extends the previous text-console-based approach, and the later Qt console, in a qualitatively new diretion, providing a web-based application suitable for capturing the whole scientific computation process.


.. seealso::

    :ref:`Installation requirements <installnotebook>` for the Notebook.


Basic structure
---------------

The IPython Notebook combines two components:

* **The *IPython Notebook* web application**:

  The IPython Notebook web app is a browser-based tool for interactive authoring of literate computations, in which explanatory text, mathematics,computations and rich media output may be combined. Input and output are stored in persistent cells that may be edited in-place.

* **Notebook documents**:

  *Notebook documents*, or *notebooks*, are plain text documents which record all inputs and outputs of the computations, interspersed with text, mathematics and HTML 5 representations of objects, in a literate style.

Since the similarity in names can lead to some confusion, in the documentation we will  use capitalization of the word "notebook" to distinguish the *N*otebook app and *n*otebook documents, thinking of the Notebook app as being a proper noun. We will also always refer to the "Notebook app" when we are referring to the browser-based interface, and usually to "notebook documents", instead of "notebooks", for added precision.

We refer to the current state of the computational process taking place in the Notebook app, i.e. the (numbered) sequence of input and output cells, as the 
*notebook space*. Notebook documents provide an *exact*, *one-to-one* record of all the content in the notebook space, as a plain text file in JSON format. The Notebook app automatically saves, at certain intervals, the contents of the notebook space to a notebook document stored on disk, with the same name as the title of the notebook space, and the file extension ".ipynb". For this reason, there is no confusion about using the same word "notebook" for both the notebook space and the corresonding notebook document, since they are really one and the same concept ("isomorphic").


Main features of the IPython Notebook web app
---------------------------------------------

The main features of the IPython Notebook app include:

* In-browser editing for code, with automatic syntax highlighting, tab completion and autoindentation.
* Literate combination of code with rich text using the Markdown markup language.
* Mathematics is easily included within the Markdown using LaTeX notation, and rendered natively by MathJax.
* Displays rich data representations (e.g. HTML / LaTeX / SVG) as the result of computations.
* Publication-quality figures in a range of formats (SVG / PNG), rendered by the ``matplotlib`` library, may be included inline and exported.


Notebook documents
------------------

Notebook document files are just standard text files with the extension 
``.ipynb``, stored in the working directory on your computer. This file can be easily put under version control and shared with colleagues.

Despite the fact that the notebook documents are plain text files, they use 
the JSON format in order to store a *complete*, *reproducible*, *one-to-one* copy of the state of the computational state as it is inside the Notebook app. 
All computations carried out, and the corresponding results obtained, can be 
combined in a literate way, mixing them with descriptive text, mathematics, 
and HTML 5 representations of objects.

Notebooks may easily be exported to a range of static formats, including 
HTML (for example, for blog posts), PDF and slide shows.
Furthermore, any publicly available notebook may be shared via the 
`IPython Notebook Viewer <http://nbviewer.ipython.org>`_ service, which will 
provide it as a static web page. The results may thus be shared without having to install anything.

See :ref:`our installation documentation <install_index>` for directions on
how to install the notebook and its dependencies.

.. note::

   You can start more than one notebook server at the same time, if you want to
   work on notebooks in different directories.  By default the first notebook
   server starts on port 8888, and later notebook servers search for  ports near
   that one.  You can also manually specify the port with the ``--port``
   option.
   

Starting up the IPython Notebook web app
----------------------------------------

The Notebook web app is started with the command::

    $ ipython notebook

The landing page of the notebook server application, the *dashboard*, shows the notebooks currently available in the *working directory* (the directory from which the notebook was started).
You can create new notebooks from the dashboard with the ``New Notebook``
button, or open existing ones by clicking on their name.
You can also drag and drop ``.ipynb`` notebooks and standard ``.py`` Python source code files into the notebook list area.

``.py`` files will be imported into the IPython Notebook as a notebook with the same name, but an ``.ipynb`` extension, located in the working directory.  The notebook will consist of a single cell containing all the 
code in the ``.py`` file, which you can later manually partition into individual cells. 

.. Alternatively, prior to importing the ``.py``, you can manually add ``# <nbformat>2</nbformat>`` at the start of the file, and then add separators for text and code cells, to get a cleaner import with the file already broken into individual cells.


When you open or create a new notebook, your browser tab will reflect the name of that notebook, prefixed with "IPy".
The URL is currently not meant to be human-readable and is not persistent across invocations of the notebook server; however, this will change in a future version of IPython.


The IPython Notebook web app is based on a server-client structure. 
This server uses a two-process kernel architecture based on ZeroMQ, as well as Tornado for serving HTTP requests. Other clients may connect to the same underlying IPython kernel; see below.




Notebook user interface
-----------------------

When you open a new notebook document in the Notebook, you will be presented with the title associated to the notebook space/document, a *menu bar*, a *toolbar* and an empty *input cell*.

Notebook title
~~~~~~~~~~~~~~
The title of the notebook document that is currently being edited is displayed at the top of the page, next to the ``IP[y]: Notebook`` logo. This title may be edited directly by clicking on it. The title is reflected in the name of the ``.ipynb`` notebook document file that is saved.

Menu bar
~~~~~~~~
The menu bar presents different options that may be used to manipulate the way the Notebook functions.

Toolbar
~~~~~~~
The tool bar gives a quick way of accessing the most-used operations within the Notebook, by clicking on an icon.


Input cells
-----------
Input cells are at the core of the functionality of the IPython Notebook.
They are regions in the document in which you can enter different types of text and commands. To *execute* or *run* the *current cell*, i.e. the cell under the cursor, you can use the:kbd:`Shift-Enter` key combination. 
This tells the Notebook app to perform the relevant operation for each type of cell (see below), and then to display the resulting output.

The notebook consists of a sequence of input cells, labelled ``In[n]``, which may be executed in a non-linear way, and outpus ``Out[n]``, where ``n`` is a number which denotes the order in which the cells were executed over the history of the computational process.


Basic workflow
--------------
The normal workflow in a notebook is, then, quite similar to a standard IPython session, with the difference that you can edit cells in-place multiple 
times until you obtain the desired results, rather than having to 
rerun separate scripts with the ``%run`` magic command. (Magic commands do, however, also work in the notebook; see below).   Typically, you'll work on a problem in pieces, 
organizing related pieces into cells and moving forward as previous 
parts work correctly.  This is much more convenient for interactive exploration than breaking up a computation into scripts that must be 
executed together, especially if parts of them take a long time to run

The only significant limitation that the notebook currently has, compared to the Qt console, is that it cannot run any code that 
expects input from the kernel (such as scripts that call 
:func:`raw_input`).  Very importantly, this means that the ``%debug`` 
magic does *not* currently work in the notebook!  This limitation will 
be overcome in the future, but in the meantime, there is a way to debug problems in the notebook: you can attach a Qt console to your existing notebook kernel, and run ``%debug`` from the Qt console.  
If your notebook is running on a local
computer (i.e. if you are accessing it via your localhost address at ``127.0.0.1``), you can just type ``%qtconsole`` in the notebook and a Qt console will open up, connected to that same kernel.

At certain moments, it may be necessary to interrupt a particularly long calculation, or even to kill the entire computational process. This may be achieved by interrupting or restarting the kernel, respectively.
After a restart, all relevant cells must be re-evaluated


A notebook may be downloaded in either ``.ipynb`` or raw ``.py`` form from the menu option ``File -> Download as``
Choosing the ``.py`` option removes all output and saves the text cells
in comment areas.  See ref:`below <notebook_format>` for more details on the
notebook format.

    
.. warning::

   While in simple cases you can "roundtrip" a notebook to Python, edit the
   Python file, and then import it back without loss of main content, this is in general *not guaranteed to work*.  First, there is extra metadata
   saved in the notebook that may not be saved to the ``.py`` format.  And as
   the notebook format evolves in complexity, there will be attributes of the
   notebook that will not survive a roundtrip through the Python form.  You
   should think of the Python format as a way to output a script version of a
   notebook and the import capabilities as a way to load existing code to get a
   notebook started.  But the Python version is *not* an alternate notebook
   format.


Keyboard shortcuts
------------------
All actions in the notebook can be achieved with the mouse, but 
keyboard shortcuts are also available for the most common ones, so that productive use of the notebook can be achieved with minimal mouse usage. The main shortcuts to remember are the following:

* :kbd:`Shift-Enter`: 
    Execute the current cell, show output (if any), and jump to the next cell below. If :kbd:`Shift-Enter` is invoked on the last input cell, a new code cell will also be created. Note that in the notebook, typing :kbd:`Enter` on its own *never* forces execution, but rather just inserts a new line in the current input cell. In the Notebook it is thus always necessary to use :kbd:`Shift-Enter` to execute the cell (or use the ``Cell -> Run`` menu item).

* :kbd:`Ctrl-Enter`: 
    Execute the current cell as if it were in "terminal mode", where any output is shown, but the cursor *remains* in the current cell. This is convenient for doing quick experiments in place, or for querying things like filesystem content, without needing to create additional cells that you may not want to be saved in the notebook.

* :kbd:`Alt-Enter`: 
    Executes the current cell, shows the output, and inserts a *new* input cell between the current cell and the adjacent cell (if one exists). This  is thus a shortcut for the sequence :kbd:`Shift-Enter`, :kbd:`Ctrl-m a`.
  


* :kbd:`Ctrl-m`: 
  This is the prefix for all of the other shortcuts, which consist of an additional single letter or character. If you type :kbd:`Ctrl-m h` (that is, the sole letter :kbd:`h` after :kbd:`Ctrl-m`), IPython will show you all the available keyboard shortcuts.



   

Cell types
----------
Each IPython input cell has a *cell type*.
There is a restricted number of possible cell types, which may be set by using the cell type dropdown on the toolbar, or via the following keyboard shortcuts:

* **code**: :kbd:`Ctrl-m y`
* **markdown**: :kbd:`Ctrl-m m`
* **raw**: :kbd:`Ctrl-m t`
* **heading**: :kbd:`Ctrl-m 1` - :kbd:`Ctrl-m 6`


Code cells
~~~~~~~~~~
Code cells contain code written in some computer language, which is Python by default. When the cell is executed with :kbd:`Shift-Enter`, this code is executed, and the result returned by Python (or the corresponding language) after running the code will be displayed as its output.

Code may be edited inline in the cell, with full syntax highlighting.


Rich text using Markdown
~~~~~~~~~~~~~~~~~~~~~~~~
The computational process may be documented in a literate way using rich text. 
For this purpose, the Notebook provides markdown cells. Text is entered using Markdown_ syntax, allowing for italics, bold, ordered and unordered lists, etc. This is rendered using Markdown syntax to a rich HTML representation when the cell is executed. In this case, the output *replaces* the input cell.

Within markdown cells, mathematics can be included in a straightforward manner using LaTeX notation: ``$...$`` for inline math and ``$$...$$`` for displayed math. Standard LaTeX environments, such as ``\begin{equation}...\end{equation}``, also work. New commands may be defined using standard LaTeX commands, placed anywhere in a markdown cell.

Raw cells
~~~~~~~~~
Raw cells provide a place to put additional information which is not evaluated by the Notebook. This can be used, for example, for extra information to be used when the notebook is exported to a certain format.


Magic commands
--------------
Magic commands, or *magics*, are one-word commands beginning with the symbol ``%``, which send commands to IPython itself (as opposed to standard Python commands which are exported to be run in a Python interpreter).

Magics control different elements of the way that the IPython notebook operates. They are entered into standard code cells and executed as usual with :kbd:`Shift-Enter`.

There are two types of magics: *line magics*, which begin with a single ``%`` and operate on a single line of the code cell; and *cell magics*, which begin with ``%%`` and operate on the entire contents of the cell.

Line magics
˜˜˜˜˜˜˜˜˜˜˜
Some of the available line magics are the following:

* ``%load``:
  Loads a file and places its content into a new code cell.

* ``%timeit``:
  A simple way to time how long a single line of code takes to run

* ``%config``:
  Configuration of the IPython Notebook

* ``%lsmagic``:
  Provides a list of all available magic commands

Cell magics
˜˜˜˜˜˜˜˜˜˜˜

* ``%%bash``:
  Send the contents of the code cell to be executed by ``bash``

* ``%%file``:
  Writes a file with with contents of the cell. *Caution*: The file is ovewritten without asking.

* ``%%R``:
  Execute the contents of the cell using the R language.

* ``%%cython``:
  Execute the contents of the cell using ``Cython``.
  


Plotting
--------
One major feature of the Notebook is the ability to capture the result of plots as inline output. IPython is designed to work seamlessly together with
the ``%matplotlib`` plotting library. In order to set this up, the 
``%matplotlib`` magic command must be run before any plotting takes place.

Note that ``%matplotlib`` only sets up IPython to work correctly with ``matplotlib``; it does not actually execute any ``import`` commands and does not add anything to the namespace.

There is an alternative magic, ``%pylab``, which, in addition, also executes a sequence of standard ``import`` statements required for working with the 
``%matplotlib`` library. In particular, it automatically imports all names in the ``numpy`` and ``matplotlib`` packages to the namespace. A less invasive solution is ``%pylab --no-import-all``, which imports just the standard names 
``np`` for the ``numpy`` module and ``plt`` for the ``matplotlib.pyplot`` module.

When the default ``%matplotlib`` or ``%pylab`` magics are used, the output of a plotting command is captured in a *separate* window. An alternative is to use::
  ``%matplotlib inline``
which captures the output inline within the notebook format. This has the benefit that the resulting plots will be stored in the notebook document.


Converting notebooks to other formats
-------------------------------------
Newly added in the 1.0 release of IPython is the ``nbconvert`` tool, which allows you to convert an ``.ipynb`` notebook document file into another static format. 

Currently, only a command line tool is provided; at present, this functionality is not available for direct exports from within the Notebook app. The syntax is::

  $ ipython nbconvert --format=FORMAT notebook.ipynb

which will convert the IPython document file `notebook.ipynb` into the output format specified by the `FORMAT` string.

The default output format is HTML, for which the `--format`` modifier is not required::
  
  $ ipython nbconvert notebook.ipynb

Otherwise, the following `FORMAT`

where ``FORMAT`` is the desired export format. The currently export format options available are the following:

* HTML:

  - ``full_html``:
    Standard HTML

  - ``simple_html``:
    Simplified HTML

  - ``reveal``:
    HTML slideshow presentation for use with the ``reveal.js`` package

* PDF:

  - ``sphinx_howto``:
    The format for Sphinx HOWTOs; similar to `article` in LaTeX

  - ``sphinx_manual``:
    The format for Sphinx manuals; similar to `book` in LaTeX 

  - ``latex``:
    LaTeX article

* Markup:

  - ``rst``:
    reStructuredText

  - ``markdown``:
    Markdown

* Python:

    Produces a standard ``.py`` script, with the non-Python code commented out.
    
The output files are currently placed in a new subdirectory called 
``nbconvert_build``. 

The PDF options produce a root LaTeX `.tex` file with the same name as the notebook, as well as individual files for each figure, and `.text` files with textual output from running code cells; all of these files are located together in the `nbconvert_build` subdirectory.

To actually produce the final PDF file, simply run::
  
  $ pdflatex notebook

which produces `notebook.pdf`, also inside the `nbconvert_build` subdirectory.

Alternatively, the output may be piped to standard output `stdout` with::
    
    $ ipython nbconvert mynotebook.ipynb --stdout
    
Multiple notebooks can be specified at the command line in a couple of 
different ways::
    
    $ ipython nbconvert notebook*.ipynb
    $ ipython nbconvert notebook1.ipynb notebook2.ipynb
    
or via a list in a configuration file, containing::
    
    c.NbConvertApp.notebooks = ["notebook1.ipynb", "notebook2.ipynb"]

and using the command::

    > ipython nbconvert --config mycfg.py


Configuration
-------------
The IPython Notebook can be run with a variety of command line arguments. 
To see a list of available options enter::

  $ ipython notebook --help 

Defaults for these options can also be set by creating a file named 
`ipython_notebook_config.py`` in your IPython *profile folder*. The profile folder is a subfolder of your IPython directory; to find out where it is located, run::

  $ ipython locate

To create a new set of default configuration files, with lots of information on available options, use::

  $ ipython profile create

.. seealso:

    :ref:`config_overview`, in particular :ref:`Profiles`.


Extracting standard Python files from notebooks
-----------------------------------------------

The native format of the notebook, a file with a ``.ipynb`` `extension, is a
JSON container of all the input and output of the notebook, and therefore not
valid Python by itself.  This means that by default, you cannot directly 
import a notebook from Python, nor execute it as a normal python script.  

But if you want to be able to use notebooks also as regular Python files, you can start the notebook server with::

  ipython notebook --script

or you can set this option permanently in your configuration file with::

    c.NotebookManager.save_script=True

This will instruct the notebook server to save the ``.py`` export of each
notebook, in addition to the ``.ipynb``, at every save.  These are standard 
``.py`` files, and so they can be ``%run``, imported from regular IPython 
sessions or other notebooks, or executed at the command line.  Since we export 
the raw code you have typed, for these files to be importable from other code, 
you will have to avoid using syntax such as ``%magic``s and other IPython-specific extensions to the language.

In regular practice, the standard way to differentiate importable code from the
'executable' part of a script is to put at the bottom::

  if __name__ == '__main__':
    # rest of the code...

Since all cells in the notebook are run as top-level code, you will need to
similarly protect *all* cells that you do not want executed when other scripts
try to import your notebook.  A convenient shortand for this is to define early
on::

  script = __name__ == '__main__'

and then on any cell that you need to protect, use::

  if script:
    # rest of the cell...


.. _notebook_security:

Security
--------

You can protect your Notebook server with a simple singlepassword by
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
    c.NotebookApp.password = u'sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed'

When using a password, it is a good idea to also use SSL, so that your password
is not sent unencrypted by your browser. You can start the notebook to
communicate via a secure protocol mode using a self-signed certificate with the command::

    $ ipython notebook --certfile=mycert.pem

.. note::

    A self-signed certificate can be generated with ``openssl``.  For example, the following command will create a certificate valid for 365 days with both the key and certificate data written to the same file::

        $ openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.pem -out mycert.pem

Your browser will warn you of a dangerous certificate because it is
self-signed.  If you want to have a fully compliant certificate that will not
raise warnings, it is possible (but rather involved) to obtain one for free,
`as explained in detailed in this tutorial`__.

.. __: http://arstechnica.com/security/news/2009/12/how-to-get-set-with-a-secure-sertificate-for-free.ars
	
Keep in mind that when you enable SSL support, you'll need to access the
notebook server over ``https://``, not over plain ``http://``.  The startup
message from the server prints this, but it's easy to overlook and think the
server is for some reason non-responsive.


Connecting to an existing kernel
---------------------------------

The notebook server always prints to the terminal the full details of 
how to connect to each kernel, with lines like::

    [IPKernelApp] To connect another client to this kernel, use:
    [IPKernelApp] --existing kernel-3bb93edd-6b5a-455c-99c8-3b658f45dde5.json

This is the name of a JSON file that contains all the port and 
validation information necessary to connect to the kernel.  You can 
manually start a Qt console with::

    ipython qtconsole --existing kernel-3bb93edd-6b5a-455c-99c8-3b658f45dde5.json

and if you only have a single kernel running, simply typing::

    ipython qtconsole --existing

will automatically find it (it will always find the most recently 
started kernel if there is more than one).  You can also request this 
connection data by typing ``%connect_info``; this will print the same 
file information as well as the content of the JSON data structure it contains.


Running a public notebook server
--------------------------------

If you want to access your notebook server remotely with just a web browser,
here is a quick set of instructions.  Start by creating a certificate file and
a hashed password as explained above.  Then, create a custom profile for the
notebook.  At the command line, type::

  ipython profile create nbserver

In the profile directory, edit the file ``ipython_notebook_config.py``.  By
default the file has all fields commented, the minimum set you need to
uncomment and edit is here::

     c = get_config()

     # Kernel config
     c.IPKernelApp.pylab = 'inline'  # if you want plotting support always

     # Notebook config
     c.NotebookApp.certfile = u'/absolute/path/to/your/certificate/mycert.pem'
     c.NotebookApp.ip = '*'
     c.NotebookApp.open_browser = False
     c.NotebookApp.password = u'sha1:bcd259ccf...your hashed password here'
     # It's a good idea to put it on a known, fixed port
     c.NotebookApp.port = 9999

You can then start the notebook and access it later by pointing your browser to
``https://your.host.com:9999`` with ``ipython notebook --profile=nbserver``.

Running with a different URL prefix
-----------------------------------

The notebook dashboard (i.e. the default landing page with an overview
of all your notebooks) typically lives at a URL path of
"http://localhost:8888/". If you want to have it, and the rest of the
notebook, live under a sub-directory,
e.g. "http://localhost:8888/ipython/", you can do so with
configuration options like these (see above for instructions about
modifying ``ipython_notebook_config.py``)::

    c.NotebookApp.base_project_url = '/ipython/'
    c.NotebookApp.base_kernel_url = '/ipython/'
    c.NotebookApp.webapp_settings = {'static_url_prefix':'/ipython/static/'}

Using a different notebook store
--------------------------------

By default the notebook server stores notebooks as files in the working 
directory of the notebook server, also known as the ``notebook_dir``. This 
logic is implemented in the :class:`FileNotebookManager` class. However, the 
server can be configured to use a different notebook manager class, which can 
store the notebooks in a different format. Currently, we ship a 
:class:`AzureNotebookManager` class that stores notebooks in Azure blob 
storage. This can be used by adding the following lines to your 
``ipython_notebook_config.py`` file::

    c.NotebookApp.notebook_manager_class = 'IPython.html.services.notebooks.azurenbmanager.AzureNotebookManager'
    c.AzureNotebookManager.account_name = u'paste_your_account_name_here'
    c.AzureNotebookManager.account_key = u'paste_your_account_key_here'
    c.AzureNotebookManager.container = u'notebooks'

In addition to providing your Azure Blob Storage account name and key, you will 
have to provide a container name; you can use multiple containers to organize 
your Notebooks.

.. _notebook_format:

Notebook JSON format
====================

Notebooks are JSON files with an ``.ipynb`` extension, formatted
as legibly as possible with minimal extra indentation and cell content broken
across lines to make them reasonably friendly to use in version-control
workflows.  You should be very careful if you ever manually edit this JSON
data, as it is extremely easy to corrupt its internal structure and make the
file impossible to load.  In general, you should consider the notebook as a
file meant only to be edited by the IPython Notebook app itself, not for hand-editing.

.. note::

     Binary data such as figures are directly saved in the JSON file.  This
     provides convenient single-file portability, but means that the files can 
     be large; ``diff``s of binary data also are not very meaningful.  Since the 
     binary blobs are encoded in a single line, they affect only one line of 
     the ``diff`` output, but they are typically very long lines.  You can use the ``Cell -> All Output -> Clear`` menu option to remove all output from a notebook prior to committing it to version control, if this is a concern.

The notebook server can also generate a pure Python version of your notebook, 
using the ``File -> Download as`` menu option. The resulting ``.py`` file will 
contain all the code cells from your notebook verbatim, and all text cells 
prepended with a comment marker.  The separation between code and text
cells is indicated with special comments and there is a header indicating the
format version.  All output is stripped out when exporting to Python.

Here is an example of the Python output from a simple notebook with one text cell and one code input cell::

    # <nbformat>2</nbformat>

    # <markdowncell>

    # A text cell

    # <codecell>

    print "Hello, IPython!"


Known issues
============

When behind a proxy, especially if your system or browser is set to autodetect
the proxy, the Notebook app might fail to connect to the server's websockets,
and present you with a warning at startup. In this case, you need to configure
your system not to use the proxy for the server's address.

In Firefox, for example, go to the Preferences panel, Advanced section,
Network tab, click 'Settings...', and add the address of the notebook server
to the 'No proxy for' field.

    
.. _Markdown: http://daringfireball.net/projects/markdown/basics

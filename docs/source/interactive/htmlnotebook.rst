.. _htmlnotebook:

The IPython Notebook
====================

.. seealso::

    :ref:`Installation requirements <installnotebook>` for the Notebook.

The IPython Notebook combines two components:

* A web application, called the *IPython Notebook web app*, for interactive authoring of literate computations, in which explanatory text, mathematics, computations and rich media output may be combined. Input and output are stored  in persistent cells that may be edited in-place.

* Plain text documents, called *notebook documents*, or *notebooks*, for recording and distributing the results of the rich computations.

In the documentation, the distinction between the *N*otebook app and *n*otebook documents is made by capitalization.

The Notebook app automatically saves the current state of the computation in the web browser to the corresponding notebook document.

It is also common to refer to the current state of the computation, as represented by the sequence of input cells in the Notebook app, as a 
*notebook*. There is no problem with confounding these two concepts, since 
there is actually a one-to-one correspondence between what you see on the
 screen inside the app, and what is stored in the corresponding ``.ipynb`` notebook document.



Features of the IPython Notebook web app
----------------------------------------

Some of the main
features of the IPython Notebook app include:

* Display rich data representations (e.g. HTML / LaTeX / SVG) in the browser as a result of computations.
* Compose text cells using Markdown and HTML.
* Include mathematical equations, rendered directly in the browser by MathJax.
* Import standard Python scripts
* In-browser editing, syntax highlighting, tab completion and autoindentation.
* Inline figures rendered by the ``matplotlib`` library with publication quality, in a range of formats (SVG / PDF / PNG).

If you have ever used the Mathematica or SAGE notebooks (the latter is also
web-based__) you should feel right at home.  If you have not, you will be
able to learn how to use the IPython Notebook in just a few minutes.

.. __: http://sagenb.org


Notebook documents
------------------

Notebook document files are just  standard text files with the extension 
``.ipynb``, stored in the working directory on your computer. This file can be easily put under version control and shared with colleagues.

Despite the fact that the notebook documents are plain text files, they use 
the JSON format in order to store a *complete*, *reproducible* copy of the
state of the computation as it is inside the Notebook app. 
That is, they record all computations carried out and the results obtained in a literate way; inputs and  outputs of computations can be freely mixed  with descriptive text, mathematics, and HTML 5 objects.

Notebooks may easily be exported to a range of static formats, including HTML (for example, for blog posts), PDF and slide shows.
Furthermore, any publicly
available notebook may be shared via the `IPython Notebook Viewer
<http://nbviewer.ipython.org>`_ service, which will provide it as a static web
page. The results may thus be shared without having to install anything.


See :ref:`our installation documentation <install_index>` for directions on
how to install the notebook and its dependencies.

.. note::

   You can start more than one notebook server at the same time, if you want to
   work on notebooks in different directories.  By default the first notebook
   server starts on port 8888, and later notebook servers search for  ports near
   that one.  You can also manually specify the port with the ``--port``
   option.
   

Running the IPython Notebook web app
====================================

The Notebook web app is started with the command::

    $ ipython notebook

The landing page of the notebook server application, the *dashboard*, shows the notebooks currently available in the *working directory* (the directory from which the notebook was started).
You can create new notebooks from the dashboard with the ``New Notebook``
button, or open existing ones by clicking on their name.
You can also drag and drop ``.ipynb`` notebooks and standard ``.py`` Python source code files into the notebook list area.

 ``.py`` files will be imported into the IPython Notebook as a notebook with the same name, but an ``.ipynb`` extension, located in the working directory.  The notebook will consist of a single cell containing all the 
 code in the ``.py`` file, which you can later manually partition into individual cells. 

 .. Alternatively, prior to importing the ``.py``, you can manually add ``# <nbformat>2</nbformat>`` at the start of the file, and then add separators for text and code cells, to get a cleaner import with the file already broken into individual cells.


The IPython Notebook web app is based on a server-client structure. 
This server uses a two-process kernel architecture based on ZeroMQ, as well as Tornado for serving HTTP requests. Other clients may connect to the same underlying IPython kernel.


When you open or create a new notebook, your browser tab will reflect the name of that notebook, prefixed with "IPy".
The URL is currently not meant to be human-readable and is not persistent across invocations of the notebook server; however, this will change in a future version of IPython.


Basic concepts in the Notebook app
----------------------------------

When you finally start editing a notebook document in the Notebook, you will be presented with the title of the notebook, a *menu bar*, a *toolbar* and an empty *input cell*.

Notebook title
ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ

The title of the notebook document that is currently being edited is displayed at the top of the page, next to the ``IP[y]: Notebook`` logo. This title may be edited directly by clicking on it. The title is reflected in the name of the ``.ipynb`` notebook document file that is saved.

Menu bar
ˆˆˆˆˆˆˆˆˆ

The menu bar presents different options that may be used to manipulate the way the Notebook functions.

Toolbar
ˆˆˆˆˆˆˆˆ

The tool bar gives handy icons for the most-used operations within the Notebook.


Input cells
-----------

Input cells are the core of the functionality of the IPython Notebook.
They are regions in the document where you can enter different types of text and commands. These regions are then executed using :kbd:`Shift-Enter`, at which point the Notebook executes the current input cell, displays the resulting output beneath it, and adds a new input cell below.

The notebook consists of a sequence of input cells, 
providing the means to direct the computational process.


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


Cell types
----------

Each IPython input cell has a cell type.
There is a limited number of possible cell types, which may be set by using the cell type dropdown on the toolbar, or via the following keyboard shortcuts:

* code :kbd:`Ctrl-m y`
* markdown :kbd:`Ctrl-m m`
* raw :kbd:`Ctrl-m t`
* heading :kbd:`Ctrl-m 1` - :kbd:`Ctrl-m 6`


Code cells
ˆˆˆˆˆˆˆˆˆˆˆ

Code cells contain code, which is Python by default. This code is executed when :kbd:`Shift-Enter` is typed, and the result of running the code will then be displayed as its output just below the cell. For example, the output may be a figure, which can be displayed inline (see below).

Code may be edited inline in the cell, with full syntax highlighting.


Rich text using markdown
ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ

The computational process may be documented using rich text by using a markdown cell. Rich text is entered using Markdown_ syntax, allowing for italics, bold, ordered and unordered lists, etc. 


Mathematics using LaTeX
ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ

You can write mathematics by including LaTeX code in markdown cells.
 Use ``$...$`` for inline math and ``$$...$$`` for displayed math. Standard LaTeX environments, such as ``\begin{equation}...\end{equation}`` also work.
 New commands may be defined using standard LaTeX commands, placed anywhere in a markdown cell.

Raw cells
ˆˆˆˆˆˆˆˆˆˆ



Raw cells provide a place to put additional information which is not evaluated by the Notebook. This can be used, for example, for extra information to be used when the notebook is exported to a certain format.


Plotting
--------

The Notebook allows 

`%matplotlib` and `%pylab` magics

Inline versus non inline

%config 


Magic commands
--------------


Exporting a notebook and importing existing scripts
---------------------------------------------------

If you want to provide others with a static HTML or PDF view of your notebook,
use the ``Print`` button.  This opens a static view of the document, which you
can print to PDF using your operating system's facilities, or save to a file
with your web browser's 'Save' option (note that typically, this will create
both an html file *and* a directory called `notebook_name_files` next to it
that contains all the necessary style information, so if you intend to share
this, you must send the directory along with the main html file).

The `Download` button lets you save a notebook file to the Download area
configured by your web browser (particularly useful if you are running the
notebook server on a remote host and need a file locally).  The notebook is
saved by default with the ``.ipynb`` extension and the files contain JSON data
that is not meant for human editing or consumption.  But you can always export
the input part of a notebook to a plain python script by choosing Python format
in the `Download` drop list.  This removes all output and saves the text cells
in comment areas.  See ref:`below <notebook_format>` for more details on the
notebook format.

    
.. warning::

   While in simple cases you can roundtrip a notebook to Python, edit the
   python file and import it back without loss of main content, this is in
   general *not guaranteed to work at all*.  First, there is extra metadata
   saved in the notebook that may not be saved to the ``.py`` format.  And as
   the notebook format evolves in complexity, there will be attributes of the
   notebook that will not survive a roundtrip through the Python form.  You
   should think of the Python format as a way to output a script version of a
   notebook and the import capabilities as a way to load existing code to get a
   notebook started.  But the Python version is *not* an alternate notebook
   format.

   
Importing or executing a notebook as a normal Python file
---------------------------------------------------------

The native format of the notebook, a file with a ``.ipynb`` `extension, is a
JSON container of all the input and output of the notebook, and therefore not
valid Python by itself.  This means that by default, you cannot directly 
import a notebook from Python, nor execute it as a normal python script.  

But if you want to be able to use notebooks also as regular Python files, you can start the notebook server with::

  ipython notebook --script

or you can set this option permanently in your configuration file with::

    c.NotebookManager.save_script=True

This will instruct the notebook server to save the ``.py`` export of each
notebook, in addition to the ``.ipynb``, at every save.  These are standard ``.py`` files, and so they can be
``%run``, imported from regular IPython sessions or other notebooks, or
executed at the command-line.  Since we export the raw
code you have typed, for these files to be importable from other code you will
have to avoid using syntax such as ``%magics`` and other IPython-specific
extensions to the language.

In regular practice, the standard way to differentiate importable code from the
'executable' part of a script is to put at the bottom::

  if __name__ == '__main__':
    # rest of the code...

Since all cells in the notebook are run as top-level code, you'll need to
similarly protect *all* cells that you do not want executed when other scripts
try to import your notebook.  A convenient shortand for this is to define early
on::

  script = __name__ == '__main__'

and then on any cell that you need to protect, use::

  if script:
    # rest of the cell...

Configuration
-------------

The IPython notebook server can be run with a variety of command line arguments. 
To see a list of available options enter::

  $ ipython notebook --help 

Defaults for these options can also be set by creating a file named 
``ipython_notebook_config.py`` in your IPython profile folder. The profile folder is a subfolder of your IPython directory; ``ipython locate`` will show you where it is located. 

To create a new set of default configuration files, with lots of information on available options, use::

  $ ipython profile create

.. seealso:

    :ref:`config_overview`, in particular :ref:`Profiles`.


Keyboard shortcuts
------------------

All actions in the notebook can be achieved with the mouse, but we have also
added keyboard shortcuts for the most common ones, so that productive use of
the notebook can be achieved with minimal mouse intervention.  The main
key bindings you need to remember are:

* :kbd:`Shift-Enter`: execute the current cell (similar to the Qt console),
  show output (if any) and jump to the next cell below. If :kbd:`Shift-Enter` 
  was invoked on the last input line, a new code cell will also be created. Note 
  that in the notebook, simply using :kbd:`Enter` *never* forces execution, 
  it simply inserts a new line in the current cell. Therefore, in the notebook 
  you must always use :kbd:`Shift-Enter` to get execution (or use the mouse and 
  click on the ``Run Selected`` button).

* :kbd:`Alt-Enter`: this combination is similar to the previous one, with the 
  exception that, if the next cell below is not empty, a new code cell will be 
  added to the notebook, even if the cell execution happens not in the last cell. 
  In this regard, :kbd:`Alt-Enter`: is simply a shortcut for the :kbd:`Shift-Enter`, 
  :kbd:`Ctrl-m a` sequence. 
  
* :kbd:`Ctrl-Enter`: execute the current cell in "terminal mode", where any
  output is shown but the cursor stays in the current cell, whose input
  area is flushed empty.  This is convenient to do quick in-place experiments
  or query things like filesystem content without creating additional cells you
  may not want saved in your notebook.

* :kbd:`Ctrl-m`: this is the prefix for all other keybindings, which consist
  of an additional single letter.  Type :kbd:`Ctrl-m h` (that is, the sole
  letter :kbd:`h` after :kbd:`Ctrl-m`) and IPython will show you the remaining
  available keybindings.


.. _notebook_security:

Security
========

You can protect your notebook server with a simple single-password by
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
communicate via a secure protocol mode using a self-signed certificate by
typing::

    $ ipython notebook --certfile=mycert.pem

.. note::

    A self-signed certificate can be generated with openssl.  For example, the
    following command will create a certificate valid for 365 days with both
    the key and certificate data written to the same file::

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

Quick how to's
==============

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

The notebook format
===================

The notebooks themselves are JSON files with an ``ipynb`` extension, formatted
as legibly as possible with minimal extra indentation and cell content broken
across lines to make them reasonably friendly to use in version-control
workflows.  You should be very careful if you ever edit manually this JSON
data, as it is extremely easy to corrupt its internal structure and make the
file impossible to load.  In general, you should consider the notebook as a
file meant only to be edited by IPython itself, not for hand-editing.

.. note::

     Binary data such as figures are directly saved in the JSON file.  This
     provides convenient single-file portability but means the files can be
     large and diffs of binary data aren't very meaningful.  Since the binary
     blobs are encoded in a single line they only affect one line of the diff
     output, but they are typically very long lines.  You can use the
     'ClearAll' button to remove all output from a notebook prior to
     committing it to version control, if this is a concern.

The notebook server can also generate a pure-python version of your notebook,
by clicking on the 'Download' button and selecting ``py`` as the format.  This
file will contain all the code cells from your notebook verbatim, and all text
cells prepended with a comment marker.  The separation between code and text
cells is indicated with special comments and there is a header indicating the
format version.  All output is stripped out when exporting to python.

Here is an example of a simple notebook with one text cell and one code input
cell, when exported to python format::

    # <nbformat>2</nbformat>

    # <markdowncell>

    # A text cell

    # <codecell>

    print "hello IPython"


Known issues
============

When behind a proxy, especially if your system or browser is set to autodetect
the proxy, the html notebook might fail to connect to the server's websockets,
and present you with a warning at startup. In this case, you need to configure
your system not to use the proxy for the server's address.

In Firefox, for example, go to the Preferences panel, Advanced section,
Network tab, click 'Settings...', and add the address of the notebook server
to the 'No proxy for' field.

    
.. _Markdown: http://daringfireball.net/projects/markdown/basics

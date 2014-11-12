.. _issues_list_200:

Issues closed in the 2.x development cycle
==========================================


Issues closed in 2.3.1
----------------------

Just one bugfix: fixed bad CRCRLF line-endings in notebooks on Windows

Pull Requests (1):

* :ghpull:`6911`: don't use text mode in mkstemp

Issues (1):

* :ghissue:`6599`: Notebook.ipynb CR+LF turned into CR+CR+LF

Issues closed in 2.3.0
----------------------

GitHub stats for 2014/08/06 - 2014/10/01 (tag: rel-2.2.0)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 6 authors contributed 31 commits.

* Benjamin Ragan-Kelley
* David Hirschfeld
* Eric Firing
* Jessica B. Hamrick
* Matthias Bussonnier
* Thomas Kluyver

We closed 16 issues and merged 9 pull requests;
this is the full list (generated with the script 
:file:`tools/github_stats.py`):

Pull Requests (16):

* :ghpull:`6587`: support ``%matplotlib qt5`` and ``%matplotlib nbagg``
* :ghpull:`6583`: Windows symlink test fixes
* :ghpull:`6585`: fixes :ghissue:`6473`
* :ghpull:`6581`: Properly mock winreg functions for test
* :ghpull:`6556`: Use some more informative asserts in inprocess kernel tests
* :ghpull:`6514`: Fix for copying metadata flags
* :ghpull:`6453`: Copy file metadata in atomic save
* :ghpull:`6480`: only compare host:port in Websocket.check_origin
* :ghpull:`6483`: Trim anchor link in heading cells, fixes :ghissue:`6324`
* :ghpull:`6410`: Fix relative import in appnope
* :ghpull:`6395`: update mathjax CDN url in nbconvert template
* :ghpull:`6269`: Implement atomic save
* :ghpull:`6374`: Rename ``abort_queues`` --> ``_abort_queues``
* :ghpull:`6321`: Use appnope in qt and wx gui support from the terminal; closes :ghissue:`6189`
* :ghpull:`6318`: use write_error instead of get_error_html
* :ghpull:`6303`: Fix error message when failing to load a notebook

Issues (9):

* :ghissue:`6057`: ``%matplotlib`` + qt5
* :ghissue:`6518`: Test failure in atomic save on Windows
* :ghissue:`6473`: Switching between "Raw Cell Format" and "Edit Metadata" does not work
* :ghissue:`6405`: Creating a notebook should respect directory permissions; saving should respect prior permissions
* :ghissue:`6324`: Anchors in Heading don't work.
* :ghissue:`6409`: No module named '_dummy'
* :ghissue:`6392`: Mathjax library link broken
* :ghissue:`6329`: IPython Notebook Server URL now requires "tree" at the end of the URL? (version 2.2)
* :ghissue:`6189`: ipython console freezes for increasing no of seconds in %pylab mode

Issues closed in 2.2.0
----------------------

GitHub stats for 2014/05/21 - 2014/08/06 (tag: rel-2.1.0)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 13 authors contributed 36 commits.

* Adam Hodgen
* Benjamin Ragan-Kelley
* Björn Grüning
* Dara Adib
* Eric Galloway
* Jonathan Frederic
* Kyle Kelley
* Matthias Bussonnier
* Paul Ivanov
* Shayne Hodge
* Steven Anton
* Thomas Kluyver
* Zahari

We closed 23 issues and merged 11 pull requests;
this is the full list (generated with the script 
:file:`tools/github_stats.py`):

Pull Requests (23):

* :ghpull:`6279`: minor updates to release scripts
* :ghpull:`6273`: Upgrade default mathjax version.
* :ghpull:`6249`: always use HTTPS getting mathjax from CDN
* :ghpull:`6114`: update hmac signature comparison
* :ghpull:`6195`: Close handle on new temporary files before returning filename
* :ghpull:`6143`: pin tornado to < 4 on travis js tests
* :ghpull:`6134`: remove rackcdn https workaround for mathjax cdn
* :ghpull:`6120`: Only allow iframe embedding on same origin.
* :ghpull:`6117`: Remove / from route of TreeRedirectHandler.
* :ghpull:`6105`: only set allow_origin_pat if defined
* :ghpull:`6102`: Add newline if missing to end of script magic cell
* :ghpull:`6077`: allow unicode keys in dicts in json_clean
* :ghpull:`6061`: make CORS configurable
* :ghpull:`6081`: don’t modify dict keys while iterating through them
* :ghpull:`5803`: unify visual line handling
* :ghpull:`6005`: Changed right arrow key movement function to mirror left arrow key
* :ghpull:`6029`: add pickleutil.PICKLE_PROTOCOL
* :ghpull:`6003`: Set kernel_id before checking websocket
* :ghpull:`5994`: Fix ssh tunnel for Python3
* :ghpull:`5973`: Do not create checkpoint_dir relative to current dir
* :ghpull:`5933`: fix qt_loader import hook signature
* :ghpull:`5944`: Markdown rendering bug fix.
* :ghpull:`5917`: use shutil.move instead of os.rename

Issues (11):

* :ghissue:`6246`: Include MathJax by default or access the CDN over a secure connection
* :ghissue:`5525`: Websocket origin check fails when used with Apache WS proxy
* :ghissue:`5901`: 2 test failures in Python 3.4 in parallel group
* :ghissue:`5926`: QT console: text selection cannot be made from left to right with keyboard
* :ghissue:`5998`: use_dill does not work in Python 3.4
* :ghissue:`5964`: Traceback on Qt console exit
* :ghissue:`5787`: Error in Notebook-Generated latex (nbconvert)
* :ghissue:`5950`: qtconsole truncates help
* :ghissue:`5943`: 2.x: notebook fails to load when using HTML comments
* :ghissue:`5932`: Qt ImportDenier Does Not Adhere to PEP302
* :ghissue:`5898`: OSError when moving configuration file

Issues closed in 2.1.0
----------------------

GitHub stats for 2014/04/02 - 2014/05/21 (since 2.0.0)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 35 authors contributed 145 commits.

* Adrian Price-Whelan
* Aron Ahmadia
* Benjamin Ragan-Kelley
* Benjamin Schultz
* Björn Linse
* Blake Griffith
* chebee7i
* Damián Avila
* Dav Clark
* dexterdev
* Erik Tollerud
* Grzegorz Rożniecki
* Jakob Gager
* jdavidheiser
* Jessica B. Hamrick
* Jim Garrison
* Jonathan Frederic
* Matthias Bussonnier
* Maximilian Albert
* Mohan Raj Rajamanickam
* ncornette
* Nikolay Koldunov
* Nile Geisinger
* Pankaj Pandey
* Paul Ivanov
* Pierre Haessig
* Raffaele De Feo
* Renaud Richardet
* Spencer Nelson
* Steve Chan
* sunny
* Susan Tan
* Thomas Kluyver
* Yaroslav Halchenko
* zah

We closed a total of 129 issues, 92 pull requests and 37 regular issues;
this is the full list (generated with the script 
:file:`tools/github_stats.py --milestone 2.1`):

Pull Requests (92):

* :ghpull:`5871`: specify encoding in msgpack.unpackb
* :ghpull:`5869`: Catch more errors from clipboard access on Windows
* :ghpull:`5866`: Make test robust against differences in line endings
* :ghpull:`5605`: Two cell toolbar fixes.
* :ghpull:`5843`: remove Firefox-specific CSS workaround
* :ghpull:`5845`: Pass Windows interrupt event to kernels as an environment variable
* :ghpull:`5835`: fix typo in v2 convert
* :ghpull:`5841`: Fix writing history with output to a file in Python 2
* :ghpull:`5842`: fix typo in nbconvert help
* :ghpull:`5846`: Fix typos in Cython example
* :ghpull:`5839`: Close graphics dev in finally clause
* :ghpull:`5837`: pass on install docs
* :ghpull:`5832`: Fixed example to work with python3
* :ghpull:`5826`: allow notebook tour instantiation to fail
* :ghpull:`5560`: Minor expansion of Cython example
* :ghpull:`5818`: interpret any exception in getcallargs as not callable
* :ghpull:`5816`: Add output to IPython directive when in verbatim mode.
* :ghpull:`5822`: Don't overwrite widget description in interact
* :ghpull:`5782`: Silence exception thrown by completer when dir() does not return a list
* :ghpull:`5807`: Drop log level to info for Qt console shutdown
* :ghpull:`5814`: Remove -i options from mv, rm and cp aliases
* :ghpull:`5812`: Fix application name when printing subcommand help.
* :ghpull:`5804`: remove an inappropriate ``!``
* :ghpull:`5805`: fix engine startup files
* :ghpull:`5806`: Don't auto-move .config/ipython if symbolic link
* :ghpull:`5716`: Add booktabs package to latex base.tplx
* :ghpull:`5669`: allows threadsafe sys.stdout.flush from background threads
* :ghpull:`5668`: allow async output on the most recent request
* :ghpull:`5768`: fix cursor keys in long lines wrapped in markdown
* :ghpull:`5788`: run cells with ``silent=True`` in ``%run nb.ipynb``
* :ghpull:`5715`: log all failed ajax API requests
* :ghpull:`5769`: Don't urlescape the text that goes into a title tag
* :ghpull:`5762`: Fix check for pickling closures
* :ghpull:`5766`: View.map with empty sequence should return empty list
* :ghpull:`5758`: Applied bug fix: using fc and ec did not properly set the figure canvas ...
* :ghpull:`5754`: Format command name into subcommand_description at run time, not import
* :ghpull:`5744`: Describe using PyPI/pip to distribute & install extensions
* :ghpull:`5712`: monkeypatch inspect.findsource only when we use it
* :ghpull:`5708`: create checkpoints dir in notebook subdirectories
* :ghpull:`5714`: log error message when API requests fail
* :ghpull:`5732`: Quick typo fix in nbformat/convert.py
* :ghpull:`5713`: Fix a NameError in IPython.parallel
* :ghpull:`5704`: Update nbconvertapp.py
* :ghpull:`5534`: cleanup some ``pre`` css inheritance
* :ghpull:`5699`: don't use common names in require decorators
* :ghpull:`5692`: Update notebook.rst fixing broken reference to notebook examples readme
* :ghpull:`5693`: Update parallel_intro.rst to fix a broken link to examples
* :ghpull:`5486`: disambiguate to location when no IPs can be determined
* :ghpull:`5574`: Remove the outdated keyboard shortcuts from notebook docs
* :ghpull:`5568`: Use ``__qualname__`` in pretty reprs for Python 3
* :ghpull:`5678`: Fix copy & paste error in docstring of ImageWidget class
* :ghpull:`5677`: Fix %bookmark -l for Python 3
* :ghpull:`5670`: nbconvert: Fix CWD imports
* :ghpull:`5647`: Mention git hooks in install documentation
* :ghpull:`5671`: Fix blank slides issue in Reveal slideshow pdf export
* :ghpull:`5657`: use 'localhost' as default for the notebook server
* :ghpull:`5584`: more semantic icons
* :ghpull:`5594`: update components with marked-0.3.2
* :ghpull:`5500`: check for Python 3.2
* :ghpull:`5582`: reset readline after running PYTHONSTARTUP
* :ghpull:`5630`: Fixed Issue :ghissue:`4012` Added Help menubar link to Github markdown doc
* :ghpull:`5613`: Fixing bug :ghissue:`5607`
* :ghpull:`5633`: Provide more help if lessc is not found.
* :ghpull:`5620`: fixed a typo in IPython.core.formatters
* :ghpull:`5619`: Fix typo in storemagic module docstring
* :ghpull:`5592`: add missing ``browser`` to notebook_aliases list
* :ghpull:`5506`: Fix ipconfig regex pattern
* :ghpull:`5581`: Fix rmagic for cells ending in comment.
* :ghpull:`5576`: only process cr if it's found
* :ghpull:`5478`: Add git-hooks install script. Update README.md
* :ghpull:`5546`: do not shutdown notebook if 'n' is part of answer
* :ghpull:`5527`: Don't remove upload items from nav tree unless explicitly requested.
* :ghpull:`5501`: remove inappropriate wheel tag override
* :ghpull:`5548`: FileNotebookManager: Use shutil.move() instead of os.rename()
* :ghpull:`5524`: never use ``for (var i in array)``
* :ghpull:`5459`: Fix interact animation page jump FF
* :ghpull:`5559`: Minor typo fix in "Cython Magics.ipynb"
* :ghpull:`5507`: Fix typo in interactive widgets examples index notebook
* :ghpull:`5554`: Make HasTraits pickleable
* :ghpull:`5535`: fix n^2 performance issue in coalesce_streams preprocessor
* :ghpull:`5522`: fix iteration over Client
* :ghpull:`5488`: Added missing require and jquery from cdn.
* :ghpull:`5516`: ENH: list generated config files in generated, and rm them upon clean
* :ghpull:`5493`: made a minor fix to one of the widget examples
* :ghpull:`5512`: Update tooltips to refer to shift-tab
* :ghpull:`5505`: Make backport_pr work on Python 3
* :ghpull:`5503`: check explicitly for 'dev' before adding the note to docs
* :ghpull:`5498`: use milestones to indicate backport
* :ghpull:`5492`: Polish whatsnew docs
* :ghpull:`5495`: Fix various broken things in docs
* :ghpull:`5496`: Exclude whatsnew/pr directory from docs builds
* :ghpull:`5489`: Fix required Python versions

Issues (37):

* :ghissue:`5364`: Horizontal scrollbar hides cell's last line on Firefox
* :ghissue:`5192`: horisontal scrollbar overlaps output or touches next cell
* :ghissue:`5840`: Third-party Windows kernels don't get interrupt signal
* :ghissue:`2412`: print history to file using qtconsole and notebook
* :ghissue:`5703`: Notebook doesn't render with "ask me every time" cookie setting in Firefox
* :ghissue:`5817`: calling mock object in IPython 2.0.0 under Python 3.4.0 raises AttributeError
* :ghissue:`5499`: Error running widgets nbconvert example
* :ghissue:`5654`: Broken links from ipython documentation
* :ghissue:`5019`: print in QT event callback doesn't show up in ipython notebook.
* :ghissue:`5800`: Only last In prompt number set ?
* :ghissue:`5801`: startup_command specified in ipengine_config.py is not executed
* :ghissue:`5690`: ipython 2.0.0 and pandoc 1.12.2.1 problem
* :ghissue:`5408`: Add checking/flushing of background output from kernel in mainloop
* :ghissue:`5407`: clearing message handlers on status=idle loses async output
* :ghissue:`5467`: Incorrect behavior of up/down keyboard arrows in code cells on wrapped lines
* :ghissue:`3085`: nicer notebook error message when lacking permissions
* :ghissue:`5765`: map_sync over empty list raises IndexError
* :ghissue:`5553`: Notebook matplotlib inline backend: can't set figure facecolor
* :ghissue:`5710`: inspect.findsource monkeypatch raises wrong exception for C extensions
* :ghissue:`5706`: Multi-Directory notebooks overwrite each other's checkpoints
* :ghissue:`5698`: can't require a function named ``f``
* :ghissue:`5569`: Keyboard shortcuts in documentation are out of date
* :ghissue:`5566`: Function name printing should use ``__qualname__`` instead of ``__name__`` (Python 3)
* :ghissue:`5676`: "bookmark -l" not working in ipython 2.0
* :ghissue:`5555`: Differentiate more clearly between Notebooks and Folders in new UI
* :ghissue:`5590`: Marked double escape 
* :ghissue:`5514`: import tab-complete fail with ipython 2.0 shell
* :ghissue:`4012`: Notebook: link to markdown formatting reference
* :ghissue:`5611`: Typo in 'storemagic' documentation
* :ghissue:`5589`: Kernel start fails when using --browser argument
* :ghissue:`5491`: Bug in Windows ipconfig ip address regular expression  
* :ghissue:`5579`: rmagic extension throws 'Error while parsing the string.' when last line is comment
* :ghissue:`5518`: Ipython2 will not open ipynb in example directory
* :ghissue:`5561`: New widget documentation has missing notebook link
* :ghissue:`5128`: Page jumping when output from widget interaction replaced
* :ghissue:`5519`: IPython.parallel.Client behavior as iterator
* :ghissue:`5510`: Tab-completion for function argument list


Issues closed in 2.0.0
----------------------


GitHub stats for 2013/08/09 - 2014/04/01 (since 1.0.0)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 94 authors contributed 3949 commits.

* Aaron Meurer
* Abhinav Upadhyay
* Adam Riggall
* Alex Rudy
* Andrew Mark
* Angus Griffith
* Antony Lee
* Aron Ahmadia
* Arun Persaud
* Benjamin Ragan-Kelley
* Bing Xia
* Blake Griffith
* Bouke van der Bijl
* Bradley M. Froehle
* Brian E. Granger
* Carlos Cordoba
* chapmanb
* chebee7i
* Christoph Gohlke
* Christophe Pradal
* Cyrille Rossant
* Damián Avila
* Daniel B. Vasquez
* Dav Clark
* David Hirschfeld
* David P. Sanders
* David Wyde
* David Österberg
* Doug Blank
* Dražen Lučanin
* epifanio
* Fernando Perez
* Gabriel Becker
* Geert Barentsen
* Hans Meine
* Ingolf Becker
* Jake Vanderplas
* Jakob Gager
* James Porter
* Jason Grout
* Jeffrey Tratner
* Jonah Graham
* Jonathan Frederic
* Joris Van den Bossche
* Juergen Hasch
* Julian Taylor
* Katie Silverio
* Kevin Burke
* Kieran O'Mahony
* Konrad Hinsen
* Kyle Kelley
* Lawrence Fu
* Marc Molla
* Martín Gaitán
* Matt Henderson
* Matthew Brett
* Matthias Bussonnier
* Michael Droettboom
* Mike McKerns
* Nathan Goldbaum
* Pablo de Oliveira
* Pankaj Pandey
* Pascal Schetelat
* Paul Ivanov
* Paul Moore
* Pere Vilas
* Peter Davis
* Philippe Mallet-Ladeira
* Preston Holmes
* Puneeth Chaganti
* Richard Everson
* Roberto Bonvallet
* Samuel Ainsworth
* Sean Vig
* Shashi Gowda
* Skipper Seabold
* Stephan Rave
* Steve Fox
* Steven Silvester
* stonebig
* Susan Tan
* Sylvain Corlay
* Takeshi Kanmae
* Ted Drain
* Thomas A Caswell
* Thomas Kluyver
* Théophile Studer
* Volker Braun
* Wieland Hoffmann
* Yaroslav Halchenko
* Yoval P.
* Yung Siang Liau
* Zachary Sailer
* zah


We closed a total of 1121 issues, 687 pull requests and 434 regular issues;
this is the full list (generated with the script 
:file:`tools/github_stats.py`):

Pull Requests (687):

* :ghpull:`5487`: remove weird unicode space in the new copyright header
* :ghpull:`5476`: For 2.0: Fix links in Notebook Help Menu
* :ghpull:`5337`: Examples reorganization
* :ghpull:`5436`: CodeMirror shortcuts in QuickHelp
* :ghpull:`5444`: Fix numeric verification for Int and Float text widgets.
* :ghpull:`5449`: Stretch keyboard shortcut dialog
* :ghpull:`5473`: Minor corrections of git-hooks setup instructions
* :ghpull:`5471`: Add coding magic comment to nbconvert Python template
* :ghpull:`5452`: print_figure returns unicode for svg
* :ghpull:`5450`: proposal: remove codename
* :ghpull:`5462`: DOC : fixed minor error in using topological sort
* :ghpull:`5463`: make spin_thread tests more forgiving of slow VMs
* :ghpull:`5464`: Fix starting notebook server with file/directory at command line.
* :ghpull:`5453`: remove gitwash
* :ghpull:`5454`: Improve history API docs
* :ghpull:`5431`: update github_stats and gh_api for 2.0
* :ghpull:`5290`: Add dual mode JS tests
* :ghpull:`5451`: check that a handler is actually registered in ShortcutManager.handles
* :ghpull:`5447`: Add %%python2 cell magic
* :ghpull:`5439`: Point to the stable SymPy docs, not the dev docs
* :ghpull:`5437`: Install jquery-ui images
* :ghpull:`5434`: fix check for empty cells in rst template
* :ghpull:`5432`: update links in notebook help menu
* :ghpull:`5435`: Update whatsnew (notebook tour)
* :ghpull:`5433`: Document extraction of octave and R magics
* :ghpull:`5428`: Update COPYING.txt
* :ghpull:`5426`: Separate get_session_info between HistoryAccessor and HistoryManager
* :ghpull:`5419`: move prompts from margin to main column on small screens
* :ghpull:`5430`: Make sure `element` is correct in the context of displayed JS
* :ghpull:`5396`: prevent saving of partially loaded notebooks
* :ghpull:`5429`: Fix tooltip pager feature
* :ghpull:`5330`: Updates to shell reference doc
* :ghpull:`5404`: Fix broken accordion widget
* :ghpull:`5339`: Don't use fork to start the notebook in js tests
* :ghpull:`5320`: Fix for Tooltip & completer click focus bug.
* :ghpull:`5421`: Move configuration of Python test controllers into setup()
* :ghpull:`5418`: fix typo in ssh launcher send_file
* :ghpull:`5403`: remove alt-- shortcut
* :ghpull:`5389`: better log message in deprecated files/ redirect
* :ghpull:`5333`: Fix filenbmanager.list_dirs fails for Windows user profile directory
* :ghpull:`5390`: finish PR #5333
* :ghpull:`5326`: Some gardening on iptest result reporting
* :ghpull:`5375`: remove unnecessary onload hack from mathjax macro
* :ghpull:`5368`: Flexbox classes specificity fixes
* :ghpull:`5331`: fix raw_input CSS
* :ghpull:`5395`: urlencode images for rst files
* :ghpull:`5049`: update quickhelp on adding and removing shortcuts
* :ghpull:`5391`: Fix Gecko (Netscape) keyboard handling
* :ghpull:`5387`: Respect '\r' characters in nbconvert.
* :ghpull:`5399`: Revert PR #5388
* :ghpull:`5388`: Suppress output even when a comment follows ;. Fixes #4525.
* :ghpull:`5394`: nbconvert doc update
* :ghpull:`5359`: do not install less sources
* :ghpull:`5346`: give hint on where to find custom.js
* :ghpull:`5357`: catch exception in copystat
* :ghpull:`5380`: Remove DefineShortVerb... line from latex base template
* :ghpull:`5376`: elide long containers in pretty
* :ghpull:`5310`: remove raw cell placeholder on focus, closes #5238
* :ghpull:`5332`: semantic names for indicator icons
* :ghpull:`5386`: Fix import of socketserver on Python 3
* :ghpull:`5360`: remove some redundant font-family: monospace
* :ghpull:`5379`: don't instantiate Application just for default logger
* :ghpull:`5372`: Don't autoclose strings
* :ghpull:`5296`: unify keyboard shortcut and codemirror interaction
* :ghpull:`5349`: Make Hub.registration_timeout configurable
* :ghpull:`5340`: install bootstrap-tour css
* :ghpull:`5335`: Update docstring for deepreload module
* :ghpull:`5321`: Improve assignment regex to match more tuple unpacking syntax
* :ghpull:`5325`: add NotebookNotary to NotebookApp's class list
* :ghpull:`5313`: avoid loading preprocessors twice
* :ghpull:`5308`: fix HTML capitalization in Highlight2HTML
* :ghpull:`5295`: OutputArea.append_type functions are not prototype methods
* :ghpull:`5318`: Fix local import of select_figure_formats
* :ghpull:`5300`: Fix NameError: name '_rl' is not defined
* :ghpull:`5292`: focus next cell on shift+enter
* :ghpull:`5291`: debug occasional error in test_queue_status
* :ghpull:`5289`: Finishing up #5274 (widget paths fixes)
* :ghpull:`5232`: Make nbconvert html full output like notebook's html.
* :ghpull:`5288`: Correct initial state of kernel status indicator
* :ghpull:`5253`: display any output from this session in terminal console
* :ghpull:`4802`: Tour of the notebook UI (was UI elements inline with highlighting)
* :ghpull:`5285`: Update signature presentation in pinfo classes
* :ghpull:`5268`: Refactoring Notebook.command_mode
* :ghpull:`5226`: Don't run PYTHONSTARTUP file if a file or code is passed
* :ghpull:`5283`: Remove Widget.closed attribute
* :ghpull:`5279`: nbconvert: Make sure node is atleast version 0.9.12
* :ghpull:`5281`: fix a typo introduced by a rebased PR
* :ghpull:`5280`: append Firefox overflow-x fix
* :ghpull:`5277`: check that PIL can save JPEG to BytesIO
* :ghpull:`5044`: Store timestamps for modules to autoreload
* :ghpull:`5278`: Update whatsnew doc from pr files
* :ghpull:`5276`: Fix kernel restart in case connection file is deleted.
* :ghpull:`5272`: allow highlighting language to be set from notebook metadata
* :ghpull:`5158`: log refusal to serve hidden directories
* :ghpull:`5188`: New events system
* :ghpull:`5265`: Missing class def for TimeoutError
* :ghpull:`5267`: normalize unicode in notebook API tests
* :ghpull:`5076`: Refactor keyboard handling
* :ghpull:`5241`: Add some tests for utils
* :ghpull:`5261`: Don't allow edit mode up arrow to continue past index == 0
* :ghpull:`5223`: use on-load event to trigger resizable images
* :ghpull:`5252`: make one strptime call at import of jsonutil
* :ghpull:`5153`: Dashboard sorting
* :ghpull:`5169`: Allow custom header
* :ghpull:`5242`: clear _reply_content cache before using it
* :ghpull:`5194`: require latex titles to be ascii
* :ghpull:`5244`: try to avoid EADDRINUSE errors on travis
* :ghpull:`5245`: support extracted output in HTML template
* :ghpull:`5209`: make input_area css generic to cells
* :ghpull:`5246`: less %pylab, more cowbell!
* :ghpull:`4895`: Improvements to %run completions
* :ghpull:`5243`: Add Javscript to base display priority list.
* :ghpull:`5175`: Audit .html() calls take #2
* :ghpull:`5146`: Dual mode bug fixes.
* :ghpull:`5207`: Children fire event
* :ghpull:`5215`: Dashboard "Running" Tab
* :ghpull:`5240`: Remove unused IPython.nbconvert.utils.console module
* :ghpull:`5239`: Fix exclusion of tests directories from coverage reports
* :ghpull:`5203`: capture some logging/warning output in some tests
* :ghpull:`5216`: fixup positional arg handling in notebook app
* :ghpull:`5229`: get _ipython_display_ method safely
* :ghpull:`5234`: DOC : modified docs is HasTraits.traits and HasTraits.class_traits
* :ghpull:`5221`: Change widget children List to Tuple.
* :ghpull:`5231`: don't forget base_url when updating address bar in rename
* :ghpull:`5173`: Moved widget files into static/widgets/*
* :ghpull:`5222`: Unset PYTHONWARNINGS envvar before running subprocess tests.
* :ghpull:`5172`: Prevent page breaks when printing notebooks via print-view.
* :ghpull:`4985`: Add automatic Closebrackets function to Codemirror.
* :ghpull:`5220`: Make traitlets notify check more robust against classes redefining equality and bool
* :ghpull:`5197`: If there is an error comparing traitlet values when setting a trait, default to go ahead and notify of the new value.
* :ghpull:`5210`: fix pyreadline import in rlineimpl
* :ghpull:`5212`: Wrap nbconvert Markdown/Heading cells in live divs
* :ghpull:`5200`: Allow to pass option to jinja env
* :ghpull:`5202`: handle nodejs executable on debian
* :ghpull:`5112`: band-aid for completion
* :ghpull:`5187`: handle missing output metadata in nbconvert
* :ghpull:`5181`: use gnureadline on OS X
* :ghpull:`5136`: set default value from signature defaults in interact
* :ghpull:`5132`: remove application/pdf->pdf transform in javascript
* :ghpull:`5116`: reorganize who knows what about paths
* :ghpull:`5165`: Don't introspect __call__ for simple callables
* :ghpull:`5170`: Added msg_throttle sync=True widget traitlet
* :ghpull:`5191`: Translate markdown link to rst
* :ghpull:`5037`: FF Fix: alignment and scale of text widget
* :ghpull:`5179`: remove websocket url
* :ghpull:`5110`: add InlineBackend.print_figure_kwargs
* :ghpull:`5147`: Some template URL changes
* :ghpull:`5100`: remove base_kernel_url
* :ghpull:`5163`: Simplify implementation of TemporaryWorkingDirectory.
* :ghpull:`5166`: remove mktemp usage
* :ghpull:`5133`: don't use combine option on ucs package
* :ghpull:`5089`: Remove legacy azure nbmanager
* :ghpull:`5159`: remove append_json reference
* :ghpull:`5095`: handle image size metadata in nbconvert html
* :ghpull:`5156`: fix IPython typo, closes #5155
* :ghpull:`5150`: fix a link that was broken
* :ghpull:`5114`: use non-breaking space for button with no description
* :ghpull:`4778`: add APIs for installing notebook extensions
* :ghpull:`5125`: Fix the display of functions with keyword-only arguments on Python 3.
* :ghpull:`5097`: minor notebook logging changes
* :ghpull:`5047`: only validate package_data when it might be used
* :ghpull:`5121`: fix remove event in KeyboardManager.register_events
* :ghpull:`5119`: Removed 'list' view from Variable Inspector example
* :ghpull:`4925`: Notebook manager api fixes
* :ghpull:`4996`: require print_method to be a bound method
* :ghpull:`5108`: require specifying the version for gh-pages
* :ghpull:`5111`: Minor typo in docstring of IPython.parallel DirectView
* :ghpull:`5098`: mostly debugging changes for IPython.parallel
* :ghpull:`5087`: trust cells with no output
* :ghpull:`5059`: Fix incorrect `Patch` logic in widget code
* :ghpull:`5075`: More flexible box model fixes
* :ghpull:`5091`: Provide logging messages in ipcluster log when engine or controllers fail to start
* :ghpull:`5090`: Print a warning when iptest is run from the IPython source directory
* :ghpull:`5077`: flush replies when entering an eventloop
* :ghpull:`5055`: Minimal changes to import IPython from IronPython
* :ghpull:`5078`: Updating JS tests README.md
* :ghpull:`5083`: don't create js test directories unless they are being used
* :ghpull:`5062`: adjust some events in nb_roundtrip
* :ghpull:`5043`: various unicode / url fixes
* :ghpull:`5066`: remove (almost) all mentions of pylab from our examples
* :ghpull:`4977`: ensure scp destination directories exist (with mkdir -p)
* :ghpull:`5053`: Move&rename JS tests
* :ghpull:`5067`: show traceback in widget handlers
* :ghpull:`4920`: Adding PDFFormatter and kernel side handling of PDF display data
* :ghpull:`5048`: Add edit/command mode indicator
* :ghpull:`5061`: make execute button in menu bar match shift-enter
* :ghpull:`5052`: Add q to toggle the pager.
* :ghpull:`5070`: fix flex: auto
* :ghpull:`5065`: Add example of using annotations in interact
* :ghpull:`5063`: another pass on Interact example notebooks
* :ghpull:`5051`: FF Fix: code cell missing hscroll (2)
* :ghpull:`4960`: Interact/Interactive for widget
* :ghpull:`5045`: Clear timeout in multi-press keyboard shortcuts.
* :ghpull:`5060`: Change 'bind' to 'link'
* :ghpull:`5039`: Expose kernel_info method on inprocess kernel client
* :ghpull:`5058`: Fix iopubwatcher.py example script.
* :ghpull:`5035`: FF Fix: code cell missing hscroll
* :ghpull:`5040`: Polishing some docs
* :ghpull:`5001`: Add directory navigation to dashboard
* :ghpull:`5042`: Remove duplicated Channel ABC classes.
* :ghpull:`5036`: FF Fix: ext link icon same line as link text in help menu
* :ghpull:`4975`: setup.py changes for 2.0
* :ghpull:`4774`: emit event on appended element on dom
* :ghpull:`5023`: Widgets- add ability to pack and unpack arrays on JS side.
* :ghpull:`5003`: Fix pretty reprs of super() objects
* :ghpull:`4974`: make paste focus the pasted cell
* :ghpull:`5012`: Make `SelectionWidget.values` a dict
* :ghpull:`5018`: Prevent 'iptest IPython' from trying to run.
* :ghpull:`5025`: citation2latex filter (using HTMLParser)
* :ghpull:`5027`: pin lessc to 1.4
* :ghpull:`4952`: Widget test inconsistencies
* :ghpull:`5014`: Fix command mode & popup view bug
* :ghpull:`4842`: more subtle kernel indicator
* :ghpull:`5017`: Add notebook examples link to help menu.
* :ghpull:`5015`: don't write cell.trusted to disk
* :ghpull:`5007`: Update whatsnew doc from PR files
* :ghpull:`5010`: Fixes for widget alignment in FF
* :ghpull:`4901`: Add a convenience class to sync traitlet attributes
* :ghpull:`5008`: updated explanation of 'pyin' messages
* :ghpull:`5004`: Fix widget vslider spacing
* :ghpull:`4933`: Small Widget inconsistency fixes
* :ghpull:`4979`: add versioning notes to small message spec changes
* :ghpull:`4893`: add font-awesome 3.2.1
* :ghpull:`4982`: Live readout for slider widgets
* :ghpull:`4813`: make help menu a template
* :ghpull:`4939`: Embed qtconsole docs (continued)
* :ghpull:`4964`: remove shift-= merge keyboard shortcut
* :ghpull:`4504`: Allow input transformers to raise SyntaxError
* :ghpull:`4929`: Fixing various modal/focus related bugs
* :ghpull:`4971`: Fixing issues with js tests
* :ghpull:`4972`: Work around problem in doctest discovery in Python 3.4 with PyQt
* :ghpull:`4937`: pickle arrays with dtype=object
* :ghpull:`4934`: `ipython profile create` respects `--ipython-dir`
* :ghpull:`4954`: generate unicode filename
* :ghpull:`4845`: Add Origin Checking.
* :ghpull:`4916`: Fine tuning the behavior of the modal UI
* :ghpull:`4966`: Ignore sys.argv for NotebookNotary in tests
* :ghpull:`4967`: Fix typo in warning about web socket being closed
* :ghpull:`4965`: Remove mention of iplogger from setup.py
* :ghpull:`4962`: Fixed typos in quick-help text
* :ghpull:`4953`: add utils.wait_for_idle in js tests
* :ghpull:`4870`: ipython_directive, report except/warn in block and add :okexcept: :okwarning: options to suppress
* :ghpull:`4662`: Menu cleanup
* :ghpull:`4824`: sign notebooks
* :ghpull:`4943`: Docs shotgun 4
* :ghpull:`4848`: avoid import of nearby temporary with %edit
* :ghpull:`4950`: Two fixes for file upload related bugs
* :ghpull:`4927`: there shouldn't be a 'files/' prefix in FileLink[s]
* :ghpull:`4928`: use importlib.machinery when available
* :ghpull:`4949`: Remove the docscrape modules, which are part of numpydoc
* :ghpull:`4849`: Various unicode fixes (mostly on Windows)
* :ghpull:`4932`: always point py3compat.input to builtin_mod.input
* :ghpull:`4807`: Correct handling of ansi colour codes when nbconverting to latex
* :ghpull:`4922`: Python nbconvert output shouldn't have output
* :ghpull:`4912`: Skip some Windows io failures
* :ghpull:`4919`: flush output before showing tracebacks
* :ghpull:`4915`: ZMQCompleter inherits from IPCompleter
* :ghpull:`4890`: better cleanup channel FDs
* :ghpull:`4880`: set profile name from profile_dir
* :ghpull:`4853`: fix setting image height/width from metadata
* :ghpull:`4786`: Reduce spacing of heading cells
* :ghpull:`4680`: Minimal pandoc version warning
* :ghpull:`4908`: detect builtin docstrings in oinspect
* :ghpull:`4911`: Don't use `python -m package` on Windows Python 2
* :ghpull:`4909`: sort dictionary keys before comparison, ordering is not guaranteed
* :ghpull:`4374`: IPEP 23: Backbone.js Widgets
* :ghpull:`4903`: use https for all embeds
* :ghpull:`4894`: Shortcut changes
* :ghpull:`4897`: More detailed documentation about kernel_cmd
* :ghpull:`4891`: Squash a few Sphinx warnings from nbconvert.utils.lexers docstrings
* :ghpull:`4679`: JPG compression for inline pylab
* :ghpull:`4708`: Fix indent and center
* :ghpull:`4789`: fix IPython.embed
* :ghpull:`4655`: prefer marked to pandoc for markdown2html
* :ghpull:`4876`: don't show tooltip if object is not found
* :ghpull:`4873`: use 'combine' option to ucs package
* :ghpull:`4732`: Accents in notebook names and in command-line (nbconvert)
* :ghpull:`4867`: Update URL for Lawrence Hall of Science webcam image
* :ghpull:`4868`: Static path fixes
* :ghpull:`4858`: fix tb_offset when running a file
* :ghpull:`4826`: some $.html( -> $.text(
* :ghpull:`4847`: add js kernel_info request
* :ghpull:`4832`: allow NotImplementedError in formatters
* :ghpull:`4803`: BUG: fix cython magic support in ipython_directive
* :ghpull:`4865`: `build` listed twice in .gitignore. Removing one.
* :ghpull:`4851`: fix tooltip token regex for single-character names
* :ghpull:`4846`: Remove some leftover traces of irunner
* :ghpull:`4820`: fix regex for cleaning old logs with ipcluster
* :ghpull:`4844`: adjustments to notebook app logging
* :ghpull:`4840`: Error in Session.send_raw()
* :ghpull:`4819`: update CodeMirror to 3.21
* :ghpull:`4823`: Minor fixes for typos/inconsistencies in parallel docs
* :ghpull:`4811`: document code mirror tab and shift-tab
* :ghpull:`4795`: merge reveal templates
* :ghpull:`4796`: update components
* :ghpull:`4806`: Correct order of packages for unicode in nbconvert to LaTeX
* :ghpull:`4800`: Qt frontend: Handle 'aborted' prompt replies.
* :ghpull:`4794`: Compatibility fix for Python3 (Issue #4783 )
* :ghpull:`4799`: minor js test fix
* :ghpull:`4788`: warn when notebook is started in pylab mode
* :ghpull:`4772`: Notebook server info files
* :ghpull:`4797`: be conservative about kernel_info implementation
* :ghpull:`4787`: non-python kernels run python code with qtconsole
* :ghpull:`4565`: various display type validations
* :ghpull:`4703`: Math macro in jinja templates.
* :ghpull:`4781`: Fix "Source" text for the "Other Syntax" section of the "Typesetting Math" notebook
* :ghpull:`4776`: Manually document py3compat module.
* :ghpull:`4533`: propagate display metadata to all mimetypes
* :ghpull:`4785`: Replacing a for-in loop by an index loop on an array
* :ghpull:`4780`: Updating CSS for UI example.
* :ghpull:`3605`: Modal UI
* :ghpull:`4758`: Python 3.4 fixes
* :ghpull:`4735`: add some HTML error pages
* :ghpull:`4775`: Update whatsnew doc from PR files
* :ghpull:`4760`: Make examples and docs more Python 3 aware
* :ghpull:`4773`: Don't wait forever for notebook server to launch/die for tests
* :ghpull:`4768`: Qt console: Fix _prompt_pos accounting on timer flush output.
* :ghpull:`4727`: Remove Nbconvert template loading magic
* :ghpull:`4763`: Set numpydoc options to produce fewer Sphinx warnings.
* :ghpull:`4770`: alway define aliases, even if empty
* :ghpull:`4766`: add `python -m` entry points for everything
* :ghpull:`4767`: remove manpages for irunner, iplogger
* :ghpull:`4751`: Added --post-serve explanation into the nbconvert docs.
* :ghpull:`4762`: whitelist alphanumeric characters for cookie_name
* :ghpull:`4625`: Deprecate %profile magic
* :ghpull:`4745`: warn on failed formatter calls
* :ghpull:`4746`: remove redundant cls alias on Windows
* :ghpull:`4749`: Fix bug in determination of public ips.
* :ghpull:`4715`: restore use of tornado static_url in templates
* :ghpull:`4748`: fix race condition in profiledir creation.
* :ghpull:`4720`: never use ssh multiplexer in tunnels
* :ghpull:`4658`: Bug fix for #4643: Regex object needs to be reset between calls in toolt...
* :ghpull:`4561`: Add Formatter.pop(type)
* :ghpull:`4712`: Docs shotgun 3
* :ghpull:`4713`: Fix saving kernel history in Python 2
* :ghpull:`4744`: don't use lazily-evaluated rc.ids in wait_for_idle
* :ghpull:`4740`: %env can't set variables
* :ghpull:`4737`: check every link when detecting virutalenv
* :ghpull:`4738`: don't inject help into user_ns
* :ghpull:`4739`: skip html nbconvert tests when their dependencies are missing
* :ghpull:`4730`: Fix stripping continuation prompts when copying from Qt console
* :ghpull:`4725`: Doc fixes
* :ghpull:`4656`: Nbconvert HTTP service
* :ghpull:`4710`: make @interactive decorator friendlier with dill
* :ghpull:`4722`: allow purging local results as long as they are not outstanding
* :ghpull:`4549`: Updated IPython console lexers.
* :ghpull:`4570`: Update IPython directive
* :ghpull:`4719`: Fix comment typo in prefilter.py
* :ghpull:`4575`: make sure to encode URL components for API requests
* :ghpull:`4718`: Fixed typo in displaypub
* :ghpull:`4716`: Remove input_prefilter hook
* :ghpull:`4691`: survive failure to bind to localhost in zmq.iostream
* :ghpull:`4696`: don't do anything if add_anchor fails
* :ghpull:`4711`: some typos in the docs
* :ghpull:`4700`: use if main block in entry points
* :ghpull:`4692`: setup.py symlink improvements
* :ghpull:`4265`: JSON configuration file
* :ghpull:`4505`: Nbconvert latex markdown images2
* :ghpull:`4608`: transparent background match ... all colors
* :ghpull:`4678`: allow ipython console to handle text/plain display
* :ghpull:`4706`: remove irunner, iplogger
* :ghpull:`4701`: Delete an old dictionary available for selecting the aligment of text.
* :ghpull:`4702`: Making reveal font-size a relative unit.
* :ghpull:`4649`: added a quiet option to %cpaste to suppress output
* :ghpull:`4690`: Option to spew subprocess streams during tests
* :ghpull:`4688`: Fixed various typos in docstrings.
* :ghpull:`4645`: CasperJs utility functions.
* :ghpull:`4670`: Stop bundling the numpydoc Sphinx extension
* :ghpull:`4675`: common IPython prefix for ModIndex
* :ghpull:`4672`: Remove unused 'attic' module
* :ghpull:`4671`: Fix docstrings in utils.text
* :ghpull:`4669`: add missing help strings to HistoryManager configurables
* :ghpull:`4668`: Make non-ASCII docstring unicode
* :ghpull:`4650`: added a note about sharing of nbconvert tempates
* :ghpull:`4646`: Fixing various output related things:
* :ghpull:`4665`: check for libedit in readline on OS X
* :ghpull:`4606`: Make running PYTHONSTARTUP optional
* :ghpull:`4654`: Fixing left padding of text cells to match that of code cells.
* :ghpull:`4306`: add raw_mimetype metadata to raw cells
* :ghpull:`4576`: Tighten up the vertical spacing on cells and make the padding of cells more consistent
* :ghpull:`4353`: Don't reset the readline completer after each prompt
* :ghpull:`4567`: Adding prompt area to non-CodeCells to indent content.
* :ghpull:`4446`: Use SVG plots in OctaveMagic by default due to lack of Ghostscript on Windows Octave
* :ghpull:`4613`: remove configurable.created
* :ghpull:`4631`: Use argument lists for command help tests
* :ghpull:`4633`: Modifies test_get_long_path_name_winr32() to allow for long path names in temp dir
* :ghpull:`4642`: Allow docs to build without PyQt installed.
* :ghpull:`4641`: Don't check for wx in the test suite.
* :ghpull:`4622`: make QtConsole Lexer configurable
* :ghpull:`4594`: Fixed #2923 Move Save Away from Cut in toolbar
* :ghpull:`4593`: don't interfere with set_next_input contents in qtconsole
* :ghpull:`4640`: Support matplotlib's Gtk3 backend in --pylab mode
* :ghpull:`4639`: Minor import fix to get qtconsole with --pylab=qt working
* :ghpull:`4637`: Fixed typo in links.txt.
* :ghpull:`4634`: Fix nbrun in notebooks with non-code cells.
* :ghpull:`4632`: Restore the ability to run tests from a function.
* :ghpull:`4624`: Fix crash when $EDITOR is non-ASCII
* :ghpull:`4453`: Play nice with App Nap
* :ghpull:`4541`: relax ipconfig matching on Windows
* :ghpull:`4552`: add pickleutil.use_dill
* :ghpull:`4590`: Font awesome for IPython slides
* :ghpull:`4589`: Inherit the width of pre code inside the input code cells.
* :ghpull:`4588`: Update reveal.js CDN to 2.5.0.
* :ghpull:`4569`: store cell toolbar preset in notebook metadata
* :ghpull:`4609`: Fix bytes regex for Python 3.
* :ghpull:`4581`: Writing unicode to stdout
* :ghpull:`4591`: Documenting codemirror shorcuts.
* :ghpull:`4607`: Tutorial doc should link to user config intro
* :ghpull:`4601`: test that rename fails with 409 if it would clobber
* :ghpull:`4599`: re-cast int/float subclasses to int/float in json_clean
* :ghpull:`4542`: new `ipython history clear` subcommand
* :ghpull:`4568`: don't use lazily-evaluated rc.ids in wait_for_idle
* :ghpull:`4572`: DOC: %profile docstring should reference %prun
* :ghpull:`4571`: no longer need 3 suffix on travis, tox
* :ghpull:`4566`: Fixing cell_type in CodeCell constructor.
* :ghpull:`4563`: Specify encoding for reading notebook file.
* :ghpull:`4452`: support notebooks in %run
* :ghpull:`4546`: fix warning condition on notebook startup
* :ghpull:`4540`: Apidocs3
* :ghpull:`4553`: Fix Python 3 handling of urllib
* :ghpull:`4543`: make hiding of initial namespace optional
* :ghpull:`4517`: send shutdown_request on exit of `ipython console`
* :ghpull:`4528`: improvements to bash completion
* :ghpull:`4532`: Hide dynamically defined metaclass base from Sphinx.
* :ghpull:`4515`: Spring Cleaning, and  Load speedup
* :ghpull:`4529`: note routing identities needed for input requests
* :ghpull:`4514`: allow restart in `%run -d`
* :ghpull:`4527`: add redirect for 1.0-style 'files/' prefix links
* :ghpull:`4526`: Allow unicode arguments to passwd_check on Python 2
* :ghpull:`4403`: Global highlight language selection.
* :ghpull:`4250`: outputarea.js: Wrap inline SVGs inside an iframe
* :ghpull:`4521`: Read wav files in binary mode
* :ghpull:`4444`: Css cleaning
* :ghpull:`4523`: Use username and password for MongoDB on ShiningPanda
* :ghpull:`4510`: Update whatsnew from PR files
* :ghpull:`4441`: add `setup.py jsversion`
* :ghpull:`4518`: Fix for race condition in url file decoding.
* :ghpull:`4497`: don't automatically unpack datetime objects in the message spec
* :ghpull:`4506`: wait for empty queues as well as load-balanced tasks
* :ghpull:`4492`: Configuration docs refresh
* :ghpull:`4508`: Fix some uses of map() in Qt console completion code.
* :ghpull:`4498`: Daemon StreamCapturer
* :ghpull:`4499`: Skip clipboard test on unix systems if headless.
* :ghpull:`4460`: Better clipboard handling, esp. with pywin32
* :ghpull:`4496`: Pass nbformat object to write call to save .py script
* :ghpull:`4466`: various pandoc latex fixes
* :ghpull:`4473`: Setup for Python 2/3
* :ghpull:`4459`: protect against broken repr in lib.pretty
* :ghpull:`4457`: Use ~/.ipython as default config directory
* :ghpull:`4489`: check realpath of env in init_virtualenv
* :ghpull:`4490`: fix possible race condition in test_await_data
* :ghpull:`4476`: Fix: Remove space added by display(JavaScript) on page reload
* :ghpull:`4398`: [Notebook] Deactivate tooltip on tab by default.
* :ghpull:`4480`: Docs shotgun 2
* :ghpull:`4488`: fix typo in message spec doc
* :ghpull:`4479`: yet another JS race condition fix
* :ghpull:`4477`: Allow incremental builds of the html_noapi docs target
* :ghpull:`4470`: Various Config object cleanups
* :ghpull:`4410`: make close-and-halt work on new tabs in Chrome
* :ghpull:`4469`: Python 3 & getcwdu
* :ghpull:`4451`: fix: allow JS test to run after shutdown test
* :ghpull:`4456`: Simplify StreamCapturer for subprocess testing
* :ghpull:`4464`: Correct description for Bytes traitlet type
* :ghpull:`4465`: Clean up MANIFEST.in
* :ghpull:`4461`: Correct TypeError message in svg2pdf
* :ghpull:`4458`: use signalstatus if exit status is undefined
* :ghpull:`4438`: Single codebase Python 3 support (again)
* :ghpull:`4198`: Version conversion, support for X to Y even if Y < X (nbformat)
* :ghpull:`4415`: More tooltips in the Notebook menu
* :ghpull:`4450`: remove monkey patch for older versions of tornado
* :ghpull:`4423`: Fix progress bar and scrolling bug.
* :ghpull:`4435`: raise 404 on not found static file
* :ghpull:`4442`: fix and add shim for change introduce by #4195
* :ghpull:`4436`: allow `require("nbextensions/extname")` to load from IPYTHONDIR/nbextensions
* :ghpull:`4437`: don't compute etags in static file handlers
* :ghpull:`4427`: notebooks should always have one checkpoint
* :ghpull:`4425`: fix js pythonisme
* :ghpull:`4195`: IPEP 21:  widget messages
* :ghpull:`4434`: Fix broken link for Dive Into Python.
* :ghpull:`4428`: bump minimum tornado version to 3.1.0
* :ghpull:`4302`: Add an Audio display class
* :ghpull:`4285`: Notebook javascript test suite using CasperJS
* :ghpull:`4420`: Allow checking for backports via milestone
* :ghpull:`4426`: set kernel cwd to notebook's directory
* :ghpull:`4389`: By default, Magics inherit from Configurable
* :ghpull:`4393`: Capture output from subprocs during test, and display on failure
* :ghpull:`4419`: define InlineBackend configurable in its own file
* :ghpull:`4303`: Multidirectory support for the Notebook
* :ghpull:`4371`: Restored ipython profile locate dir and fixed typo. (Fixes #3708).
* :ghpull:`4414`: Specify unicode type properly in rmagic
* :ghpull:`4413`: don't instantiate IPython shell as class attr
* :ghpull:`4400`: Remove 5s wait on inactivity on GUI inputhook loops
* :ghpull:`4412`: Fix traitlet _notify_trait by-ref issue
* :ghpull:`4378`: split adds new cell above, rather than below
* :ghpull:`4405`: Bring display of builtin types and functions in line with Py 2
* :ghpull:`4367`: clean up of documentation files
* :ghpull:`4401`: Provide a name of the HistorySavingThread
* :ghpull:`4384`: fix menubar height measurement
* :ghpull:`4377`: fix tooltip cancel
* :ghpull:`4293`: Factorise code in tooltip for julia monkeypatching
* :ghpull:`4292`: improve js-completer logic.
* :ghpull:`4363`: set_next_input: keep only last input when repeatedly called in a single cell
* :ghpull:`4382`: Use safe_hasattr in dir2
* :ghpull:`4379`: fix (CTRL-M -) shortcut for splitting cell in FF
* :ghpull:`4380`: Test and fixes for localinterfaces
* :ghpull:`4372`: Don't assume that SyntaxTB is always called with a SyntaxError
* :ghpull:`4342`: Return value directly from the try block and avoid a variable
* :ghpull:`4154`: Center LaTeX and figures in markdown
* :ghpull:`4311`: %load -s to load specific functions or classes
* :ghpull:`4350`: WinHPC launcher fixes
* :ghpull:`4345`: Make irunner compatible with upcoming pexpect 3.0 interface
* :ghpull:`4276`: Support container methods in config
* :ghpull:`4359`: test_pylabtools also needs to modify matplotlib.rcParamsOrig
* :ghpull:`4355`: remove hardcoded box-orient
* :ghpull:`4333`: Add Edit Notebook Metadata to Edit menu
* :ghpull:`4349`: Script to update What's New file
* :ghpull:`4348`: Call PDF viewer after latex compiling (nbconvert)
* :ghpull:`4346`: getpass() on Windows & Python 2 needs bytes prompt
* :ghpull:`4304`: use netifaces for faster IPython.utils.localinterfaces
* :ghpull:`4305`: Add even more ways to populate localinterfaces
* :ghpull:`4313`: remove strip_math_space
* :ghpull:`4325`: Some changes to improve readability.
* :ghpull:`4281`: Adjust tab completion widget if too close to bottom of page.
* :ghpull:`4347`: Remove pycolor script
* :ghpull:`4322`: Scroll to the top after change of slides in the IPython slides
* :ghpull:`4289`: Fix scrolling output (not working post clear_output changes)
* :ghpull:`4343`: Make parameters for kernel start method more general
* :ghpull:`4237`: Keywords should shadow magic functions
* :ghpull:`4338`: adjust default value of level in sync_imports
* :ghpull:`4328`: Remove unused loop variable.
* :ghpull:`4340`: fix mathjax download url to new GitHub format
* :ghpull:`4336`: use simple replacement rather than string formatting in format_kernel_cmd
* :ghpull:`4264`: catch unicode error listing profiles
* :ghpull:`4314`: catch EACCES when binding notebook app
* :ghpull:`4324`: Remove commented addthis toolbar
* :ghpull:`4327`: Use the with statement to open a file.
* :ghpull:`4318`: fix initial sys.path
* :ghpull:`4315`: Explicitly state what version of Pandoc is supported in docs/install
* :ghpull:`4316`: underscore missing on notebook_p4
* :ghpull:`4295`: Implement boundary option for load magic (#1093) 
* :ghpull:`4300`: traits defauts are strings not object
* :ghpull:`4297`: Remove an unreachable return statement.
* :ghpull:`4260`: Use subprocess for system_raw
* :ghpull:`4277`: add nbextensions
* :ghpull:`4294`: don't require tornado 3 in `--post serve`
* :ghpull:`4270`: adjust Scheduler timeout logic
* :ghpull:`4278`: add `-a` to easy_install command in libedit warning
* :ghpull:`4282`: Enable automatic line breaks in MathJax.
* :ghpull:`4279`: Fixing line-height of list items in tree view.
* :ghpull:`4253`: fixes #4039.
* :ghpull:`4131`: Add module's name argument in %%cython magic
* :ghpull:`4269`: Add mathletters option and longtable package to latex_base.tplx
* :ghpull:`4230`: Switch correctly to the user's default matplotlib backend after inline.
* :ghpull:`4271`: Hopefully fix ordering of output on ShiningPanda
* :ghpull:`4239`: more informative error message for bad serialization
* :ghpull:`4263`: Fix excludes for IPython.testing
* :ghpull:`4112`: nbconvert: Latex template refactor
* :ghpull:`4261`: Fixing a formatting error in the custom display example notebook.
* :ghpull:`4259`: Fix Windows test exclusions
* :ghpull:`4229`: Clear_output: Animation & widget related changes.
* :ghpull:`4151`: Refactor alias machinery
* :ghpull:`4153`: make timeit return an object that contains values
* :ghpull:`4258`: to-backport label is now 1.2
* :ghpull:`4242`: Allow passing extra arguments to iptest through for nose
* :ghpull:`4257`: fix unicode argv parsing
* :ghpull:`4166`: avoid executing code in utils.localinterfaces at import time
* :ghpull:`4214`: engine ID metadata should be unicode, not bytes
* :ghpull:`4232`: no highlight if no language specified
* :ghpull:`4218`: Fix display of SyntaxError when .py file is modified
* :ghpull:`4207`: add `setup.py css` command
* :ghpull:`4224`: clear previous callbacks on execute
* :ghpull:`4180`: Iptest refactoring
* :ghpull:`4105`: JS output area misaligned
* :ghpull:`4220`: Various improvements to docs formatting
* :ghpull:`4187`: Select adequate highlighter for cell magic languages
* :ghpull:`4228`: update -dev docs to reflect latest stable version
* :ghpull:`4219`: Drop bundled argparse
* :ghpull:`3851`: Adds an explicit newline for pretty-printing.
* :ghpull:`3622`: Drop fakemodule
* :ghpull:`4080`: change default behavior of database task storage
* :ghpull:`4197`: enable cython highlight in notebook
* :ghpull:`4225`: Updated docstring for core.display.Image
* :ghpull:`4175`: nbconvert: Jinjaless exporter base
* :ghpull:`4208`: Added a lightweight "htmlcore" Makefile entry
* :ghpull:`4209`: Magic doc fixes
* :ghpull:`4217`: avoid importing numpy at the module level
* :ghpull:`4213`: fixed dead link in examples/notebooks readme to Part 3
* :ghpull:`4183`: ESC should be handled by CM if tooltip is not on
* :ghpull:`4193`: Update for #3549: Append Firefox overflow-x fix
* :ghpull:`4205`: use TextIOWrapper when communicating with pandoc subprocess
* :ghpull:`4204`: remove some extraneous print statements from IPython.parallel
* :ghpull:`4201`: HeadingCells cannot be split or merged
* :ghpull:`4048`: finish up speaker-notes PR
* :ghpull:`4079`: trigger `Kernel.status_started` after websockets open
* :ghpull:`4186`: moved DummyMod to proper namespace to enable dill pickling
* :ghpull:`4190`: update version-check message in setup.py and IPython.__init__
* :ghpull:`4188`: Allow user_ns trait to be None
* :ghpull:`4189`: always fire LOCAL_IPS.extend(PUBLIC_IPS)
* :ghpull:`4174`: various issues in markdown and rst templates
* :ghpull:`4178`: add missing data_javascript
* :ghpull:`4168`: Py3 failing tests
* :ghpull:`4181`: nbconvert: Fix, sphinx template not removing new lines from headers
* :ghpull:`4043`: don't 'restore_bytes' in from_JSON
* :ghpull:`4149`: reuse more kernels in kernel tests
* :ghpull:`4163`: Fix for incorrect default encoding on Windows.
* :ghpull:`4136`: catch javascript errors in any output
* :ghpull:`4171`: add nbconvert config file when creating profiles
* :ghpull:`4172`: add ability to check what PRs should be backported in backport_pr
* :ghpull:`4167`: --fast flag for test suite!
* :ghpull:`4125`: Basic exercise of `ipython [subcommand] -h` and help-all
* :ghpull:`4085`: nbconvert: Fix sphinx preprocessor date format string for Windows
* :ghpull:`4159`: don't split `.cell` and `div.cell` CSS
* :ghpull:`4165`: Remove use of parametric tests
* :ghpull:`4158`: generate choices for `--gui` configurable from real mapping
* :ghpull:`4083`: Implement a better check for hidden values for %who etc.
* :ghpull:`4147`: Reference notebook examples, fixes #4146.
* :ghpull:`4065`: do not include specific css in embedable one
* :ghpull:`4092`: nbconvert: Fix for unicode html headers, Windows + Python 2.x
* :ghpull:`4074`: close Client sockets if connection fails
* :ghpull:`4064`: Store default codemirror mode in only 1 place
* :ghpull:`4104`: Add way to install MathJax to a particular profile
* :ghpull:`4161`: Select name when renaming a notebook
* :ghpull:`4160`: Add quotes around ".[notebook]" in readme
* :ghpull:`4144`: help_end transformer shouldn't pick up ? in multiline string
* :ghpull:`4090`: Add LaTeX citation handling to nbconvert
* :ghpull:`4143`: update example custom.js
* :ghpull:`4142`: DOC: unwrap openssl line in public_server doc
* :ghpull:`4126`: update tox.ini
* :ghpull:`4141`: add files with a separate `add` call in backport_pr
* :ghpull:`4137`: Restore autorestore option for storemagic
* :ghpull:`4098`: pass profile-dir instead of profile name to Kernel
* :ghpull:`4120`: support `input` in Python 2 kernels
* :ghpull:`4088`: nbconvert: Fix coalescestreams line with incorrect nesting causing strange behavior
* :ghpull:`4060`: only strip continuation prompts if regular prompts seen first
* :ghpull:`4132`: Fixed name error bug in function safe_unicode in module py3compat.
* :ghpull:`4121`: move test_kernel from IPython.zmq to IPython.kernel
* :ghpull:`4118`: ZMQ heartbeat channel: catch EINTR exceptions and continue.
* :ghpull:`4070`: New changes should go into pr/ folder
* :ghpull:`4054`: use unicode for HTML export
* :ghpull:`4106`: fix a couple of default block values
* :ghpull:`4107`: update parallel magic tests with capture_output API
* :ghpull:`4102`: Fix clashes between debugger tests and coverage.py
* :ghpull:`4115`: Update docs on declaring a magic function
* :ghpull:`4101`: restore accidentally removed EngineError
* :ghpull:`4096`: minor docs changes
* :ghpull:`4094`: Update target branch before backporting PR
* :ghpull:`4069`: Drop monkeypatch for pre-1.0 nose
* :ghpull:`4056`: respect `pylab_import_all` when `--pylab` specified at the command-line
* :ghpull:`4091`: Make Qt console banner configurable
* :ghpull:`4086`: fix missing errno import
* :ghpull:`4084`: Use msvcrt.getwch() for Windows pager.
* :ghpull:`4073`: rename ``post_processors`` submodule to ``postprocessors``
* :ghpull:`4075`: Update supported Python versions in tools/test_pr
* :ghpull:`4068`: minor bug fix, define 'cell' in dialog.js.
* :ghpull:`4044`: rename call methods to transform and postprocess
* :ghpull:`3744`: capture rich output as well as stdout/err in capture_output
* :ghpull:`3969`: "use strict" in most (if not all) our javascript
* :ghpull:`4030`: exclude `.git` in MANIFEST.in
* :ghpull:`4047`: Use istype() when checking if canned object is a dict
* :ghpull:`4031`: don't close_fds on Windows
* :ghpull:`4029`: bson.Binary moved
* :ghpull:`3883`: skip test on unix when x11 not available
* :ghpull:`3863`: Added working speaker notes for slides.
* :ghpull:`4035`: Fixed custom jinja2 templates being ignored when setting template_path
* :ghpull:`4002`: Drop Python 2.6 and 3.2
* :ghpull:`4026`: small doc fix in nbconvert
* :ghpull:`4016`: Fix IPython.start_* functions
* :ghpull:`4021`: Fix parallel.client.View map() on numpy arrays
* :ghpull:`4022`: DOC: fix links to matplotlib, notebook docs
* :ghpull:`4018`: Fix warning when running IPython.kernel tests
* :ghpull:`4017`: Add REPL-like printing of final/return value to %%R cell magic
* :ghpull:`4019`: Test skipping without unicode paths
* :ghpull:`4008`: Transform code before %prun/%%prun runs
* :ghpull:`4014`: Fix typo in ipapp
* :ghpull:`3997`: DOC: typos + rewording in examples/notebooks/Cell Magics.ipynb
* :ghpull:`3914`: nbconvert: Transformer tests
* :ghpull:`3987`: get files list in backport_pr
* :ghpull:`3923`: nbconvert: Writer tests
* :ghpull:`3974`: nbconvert: Fix app tests on Window7 w/ Python 3.3
* :ghpull:`3937`: make tab visible in codemirror and light red background
* :ghpull:`3933`: nbconvert: Post-processor tests
* :ghpull:`3978`: fix `--existing` with non-localhost IP
* :ghpull:`3939`: minor checkpoint cleanup
* :ghpull:`3955`: complete on % for magic in notebook
* :ghpull:`3981`: BF: fix nbconert rst input prompt spacing
* :ghpull:`3960`: Don't make sphinx a dependency for importing nbconvert
* :ghpull:`3973`: logging.Formatter is not new-style in 2.6

Issues (434):

* :ghissue:`5476`: For 2.0: Fix links in Notebook Help Menu
* :ghissue:`5337`: Examples reorganization
* :ghissue:`5436`: CodeMirror shortcuts in QuickHelp
* :ghissue:`5444`: Fix numeric verification for Int and Float text widgets.
* :ghissue:`5443`: Int and Float Widgets don't allow negative signs
* :ghissue:`5449`: Stretch keyboard shortcut dialog
* :ghissue:`5471`: Add coding magic comment to nbconvert Python template
* :ghissue:`5470`: UTF-8 Issue When Converting Notebook to a Script.
* :ghissue:`5369`: FormatterWarning for SVG matplotlib output in notebook
* :ghissue:`5460`: Can't start the notebook server specifying a notebook
* :ghissue:`2918`: CodeMirror related issues.
* :ghissue:`5431`: update github_stats and gh_api for 2.0
* :ghissue:`4887`: Add tests for modal UI
* :ghissue:`5290`: Add dual mode JS tests
* :ghissue:`5448`: Cmd+/ shortcut doesn't work in IPython master
* :ghissue:`5447`: Add %%python2 cell magic
* :ghissue:`5442`: Make a "python2" alias or rename the "python"cell magic.
* :ghissue:`2495`: non-ascii characters in the path
* :ghissue:`4554`: dictDB: Exception due to str to datetime comparission
* :ghissue:`5006`: Comm code is not run in the same context as notebook code
* :ghissue:`5118`: Weird interact behavior
* :ghissue:`5401`: Empty code cells in nbconvert rst output cause problems
* :ghissue:`5434`: fix check for empty cells in rst template
* :ghissue:`4944`: Trouble finding ipynb path in Windows 8
* :ghissue:`4605`: Change the url of Editor Shorcuts in the notebook menu.
* :ghissue:`5425`: Update COPYING.txt
* :ghissue:`5348`: BUG: HistoryAccessor.get_session_info(0) - exception
* :ghissue:`5293`: Javascript("element.append()") looks broken.
* :ghissue:`5363`: Disable saving if notebook has stopped loading
* :ghissue:`5189`: Tooltip pager mode is broken
* :ghissue:`5330`: Updates to shell reference doc
* :ghissue:`5397`: Accordion widget broken
* :ghissue:`5106`: Flexbox CSS specificity bugs
* :ghissue:`5297`: tooltip triggers focus bug
* :ghissue:`5417`: scp checking for existence of directories: directory names are incorrect
* :ghissue:`5302`: Parallel engine registration fails for slow engines
* :ghissue:`5334`: notebook's split-cell shortcut dangerous / incompatible with Neo layout (for instance)
* :ghissue:`5324`: Style of `raw_input` UI is off in notebook
* :ghissue:`5350`: Converting notebooks with spaces in their names to RST gives broken images
* :ghissue:`5049`: update quickhelp on adding and removing shortcuts
* :ghissue:`4941`: Eliminating display of intermediate stages in progress bars
* :ghissue:`5345`: nbconvert to markdown does not use backticks
* :ghissue:`5357`: catch exception in copystat
* :ghissue:`5351`: Notebook saving fails on smb share
* :ghissue:`4946`: TeX produced cannot be converted to PDF
* :ghissue:`5347`: pretty print list too slow
* :ghissue:`5238`: Raw cell placeholder is not removed when you edit the cell
* :ghissue:`5382`: Qtconsole doesn't run in Python 3
* :ghissue:`5378`: Unexpected and new conflict between PyFileConfigLoader and IPythonQtConsoleApp
* :ghissue:`4945`: Heading/cells positioning problem and cell output wrapping
* :ghissue:`5084`: Consistent approach for HTML/JS output on nbviewer
* :ghissue:`4902`: print preview does not work, custom.css not found
* :ghissue:`5336`: TypeError in bootstrap-tour.min.js
* :ghissue:`5303`: Changed Hub.registration_timeout to be a config input.
* :ghissue:`995`: Paste-able mode in terminal
* :ghissue:`5305`: Tuple unpacking for shell escape
* :ghissue:`5232`: Make nbconvert html full output like notebook's html.
* :ghissue:`5224`: Audit nbconvert HTML output
* :ghissue:`5253`: display any output from this session in terminal console
* :ghissue:`5251`: ipython console ignoring some stream messages?
* :ghissue:`4802`: Tour of the notebook UI (was UI elements inline with highlighting)
* :ghissue:`5103`: Moving Constructor definition to the top like a Function definition
* :ghissue:`5264`: Test failures on master with Anaconda
* :ghissue:`4833`: Serve /usr/share/javascript at /_sysassets/javascript/ in notebook
* :ghissue:`5071`: Prevent %pylab from clobbering interactive
* :ghissue:`5282`: Exception in widget __del__ methods in Python 3.4.
* :ghissue:`5280`: append Firefox overflow-x fix
* :ghissue:`5120`: append Firefox overflow-x fix, again
* :ghissue:`4127`: autoreload shouldn't rely on .pyc modification times
* :ghissue:`5272`: allow highlighting language to be set from notebook metadata
* :ghissue:`5050`: Notebook cells truncated with Firefox
* :ghissue:`4839`: Error in Session.send_raw()
* :ghissue:`5188`: New events system
* :ghissue:`5076`: Refactor keyboard handling
* :ghissue:`4886`: Refactor and consolidate different keyboard logic in JavaScript code
* :ghissue:`5002`: the green cell border moving forever in Chrome, when there are many code cells.
* :ghissue:`5259`: Codemirror still active in command mode
* :ghissue:`5219`: Output images appear as small thumbnails (Notebook)
* :ghissue:`4829`: Not able to connect qtconsole in Windows 8
* :ghissue:`5152`: Hide __pycache__ in dashboard directory list
* :ghissue:`5151`: Case-insesitive sort for dashboard list
* :ghissue:`4603`: Warn when overwriting a notebook with upload
* :ghissue:`4895`: Improvements to %run completions
* :ghissue:`3459`: Filename completion when run script with %run
* :ghissue:`5225`: Add JavaScript to nbconvert HTML display priority
* :ghissue:`5034`: Audit the places where we call `.html(something)`
* :ghissue:`5094`: Dancing cells in notebook
* :ghissue:`4999`: Notebook focus effects
* :ghissue:`5149`: Clicking on a TextBoxWidget in FF completely breaks dual mode.
* :ghissue:`5207`: Children fire event
* :ghissue:`5227`: display_method of objects with custom __getattr__
* :ghissue:`5236`: Cursor keys do not work to leave Markdown cell while it's being edited
* :ghissue:`5205`: Use CTuple traitlet for Widget children
* :ghissue:`5230`: notebook rename does not respect url prefix
* :ghissue:`5218`: Test failures with Python 3 and enabled warnings
* :ghissue:`5115`: Page Breaks for Print Preview Broken by display: flex - Simple CSS Fix
* :ghissue:`5024`: Make nbconvert HTML output smart about page breaking
* :ghissue:`4985`: Add automatic Closebrackets function to Codemirror.
* :ghissue:`5184`: print '\xa' crashes the interactive shell
* :ghissue:`5214`: Downloading notebook as Python (.py) fails
* :ghissue:`5211`: AttributeError: 'module' object has no attribute '_outputfile'
* :ghissue:`5206`: [CSS?] Inconsistencies in nbconvert divs and IPython Notebook divs?
* :ghissue:`5201`: node != nodejs within Debian packages
* :ghissue:`5112`: band-aid for completion
* :ghissue:`4860`: Completer As-You-Type Broken
* :ghissue:`5116`: reorganize who knows what about paths
* :ghissue:`4973`: Adding security.js with 1st attempt at is_safe
* :ghissue:`5164`: test_oinspect.test_calltip_builtin failure with python3.4
* :ghissue:`5127`: Widgets: skip intermediate callbacks during throttling
* :ghissue:`5013`: Widget alignment differs between FF and Chrome
* :ghissue:`5141`: tornado error static file
* :ghissue:`5160`: TemporaryWorkingDirectory incompatible with python3.4
* :ghissue:`5140`: WIP: %kernels magic
* :ghissue:`4987`: Widget lifecycle problems
* :ghissue:`5129`: UCS package break latex export on non-ascii 
* :ghissue:`4986`: Cell horizontal scrollbar is missing in FF but not in Chrome
* :ghissue:`4685`: nbconvert ignores image size metadata
* :ghissue:`5155`: Notebook logout button does not work (source typo)
* :ghissue:`2678`: Ctrl-m keyboard shortcut clash on Chrome OS
* :ghissue:`5113`: ButtonWidget without caption wrong height.
* :ghissue:`4778`: add APIs for installing notebook extensions
* :ghissue:`5046`: python setup.py failed vs git submodule update worked
* :ghissue:`4925`: Notebook manager api fixes
* :ghissue:`5073`: Cannot align widgets horizontally in the notebook
* :ghissue:`4996`: require print_method to be a bound method
* :ghissue:`4990`: _repr_html_ exception reporting corner case when using type(foo)
* :ghissue:`5099`: Notebook: Changing base_project_url results in failed WebSockets call
* :ghissue:`5096`: Client.map is not fault tolerant
* :ghissue:`4997`: Inconsistent %matplotlib qt behavior
* :ghissue:`5041`: Remove more .html(...) calls.
* :ghissue:`5078`: Updating JS tests README.md
* :ghissue:`4977`: ensure scp destination directories exist (with mkdir -p)
* :ghissue:`3411`: ipython parallel: scp failure.
* :ghissue:`5064`: Errors during interact display at the terminal, not anywhere in the notebook
* :ghissue:`4921`: Add PDF formatter and handling
* :ghissue:`4920`: Adding PDFFormatter and kernel side handling of PDF display data
* :ghissue:`5048`: Add edit/command mode indicator
* :ghissue:`4889`: Add UI element for indicating command/edit modes
* :ghissue:`5052`: Add q to toggle the pager.
* :ghissue:`5000`: Closing pager with keyboard in modal UI
* :ghissue:`5069`: Box model changes broke the Keyboard Shortcuts help modal
* :ghissue:`4960`: Interact/Interactive for widget
* :ghissue:`4883`: Implement interact/interactive for widgets
* :ghissue:`5038`: Fix multiple press keyboard events
* :ghissue:`5054`: UnicodeDecodeError: 'ascii' codec can't decode byte 0xc6 in position 1: ordinal not in range(128)
* :ghissue:`5031`: Bug during integration of IPython console in Qt application
* :ghissue:`5057`: iopubwatcher.py example is broken.
* :ghissue:`4747`: Add event for output_area adding an output
* :ghissue:`5001`: Add directory navigation to dashboard
* :ghissue:`5016`: Help menu external-link icons break layout in FF
* :ghissue:`4885`: Modal UI behavior changes
* :ghissue:`5009`: notebook signatures don't work
* :ghissue:`4975`: setup.py changes for 2.0
* :ghissue:`4774`: emit event on appended element on dom
* :ghissue:`5020`: Python Lists translated to javascript objects in widgets
* :ghissue:`5003`: Fix pretty reprs of super() objects
* :ghissue:`5012`: Make `SelectionWidget.values` a dict
* :ghissue:`4961`: Bug when constructing a selection widget with both values and labels
* :ghissue:`4283`: A `<` in a markdown cell strips cell content when converting to latex
* :ghissue:`4006`: iptest IPython broken
* :ghissue:`4251`: & escaped to &amp; in tex ?
* :ghissue:`5027`: pin lessc to 1.4
* :ghissue:`4323`: Take 2: citation2latex filter (using HTMLParser)
* :ghissue:`4196`: Printing notebook from browser gives 1-page truncated output
* :ghissue:`4842`: more subtle kernel indicator
* :ghissue:`4057`: No path to notebook examples from Help menu
* :ghissue:`5015`: don't write cell.trusted to disk
* :ghissue:`4617`: Changed url link in Help dropdown menu.
* :ghissue:`4976`: Container widget layout broken on Firefox
* :ghissue:`4981`: Vertical slider layout broken
* :ghissue:`4793`: Message spec changes related to `clear_output`
* :ghissue:`4982`: Live readout for slider widgets
* :ghissue:`4813`: make help menu a template
* :ghissue:`4989`: Filename tab completion completely broken
* :ghissue:`1380`: Tab should insert 4 spaces in # comment lines
* :ghissue:`2888`: spaces vs tabs
* :ghissue:`1193`: Allow resizing figures in notebook
* :ghissue:`4504`: Allow input transformers to raise SyntaxError
* :ghissue:`4697`: Problems with height after toggling header and toolbar...
* :ghissue:`4951`: TextWidget to code cell command mode bug.
* :ghissue:`4809`: Arbitrary scrolling (jumping) in clicks in modal UI for notebook
* :ghissue:`4971`: Fixing issues with js tests
* :ghissue:`4972`: Work around problem in doctest discovery in Python 3.4 with PyQt
* :ghissue:`4892`: IPython.qt test failure with python3.4
* :ghissue:`4863`: BUG: cannot create an OBJECT array from memory buffer
* :ghissue:`4704`: Subcommand `profile` ignores --ipython-dir 
* :ghissue:`4845`: Add Origin Checking.
* :ghissue:`4870`: ipython_directive, report except/warn in block and add :okexcept: :okwarning: options to suppress
* :ghissue:`4956`: Shift-Enter does not move to next cell
* :ghissue:`4662`: Menu cleanup
* :ghissue:`4824`: sign notebooks
* :ghissue:`4848`: avoid import of nearby temporary with %edit
* :ghissue:`4731`: %edit files mistakenly import modules in /tmp
* :ghissue:`4950`: Two fixes for file upload related bugs
* :ghissue:`4871`: Notebook upload fails after Delete
* :ghissue:`4825`: File Upload URL set incorrectly
* :ghissue:`3867`: display.FileLinks should work in the exported html verion of a notebook
* :ghissue:`4948`: reveal: ipython css overrides reveal themes
* :ghissue:`4947`: reveal: slides that are too big?
* :ghissue:`4051`: Test failures with Python 3 and enabled warnings
* :ghissue:`3633`: outstanding issues over in ipython/nbconvert repo
* :ghissue:`4087`: Sympy printing in the example notebook
* :ghissue:`4627`: Document various QtConsole embedding approaches.
* :ghissue:`4849`: Various unicode fixes (mostly on Windows)
* :ghissue:`3653`: autocompletion in "from package import <tab>"
* :ghissue:`4583`: overwrite? prompt gets EOFError in 2 process
* :ghissue:`4807`: Correct handling of ansi colour codes when nbconverting to latex
* :ghissue:`4611`: Document how to compile .less files in dev docs.
* :ghissue:`4618`: "Editor Shortcuts" link is broken in help menu dropdown notebook
* :ghissue:`4522`: DeprecationWarning: the sets module is deprecated
* :ghissue:`4368`: No symlink from ipython to ipython3 when inside a python3 virtualenv
* :ghissue:`4234`: Math without $$ doesn't show up when converted to slides
* :ghissue:`4194`: config.TerminalIPythonApp.nosep does not work
* :ghissue:`1491`: prefilter not called for multi-line notebook cells
* :ghissue:`4001`: Windows IPython executable /scripts/ipython not working
* :ghissue:`3959`: think more carefully about text wrapping in nbconvert
* :ghissue:`4907`: Test for traceback depth fails on Windows
* :ghissue:`4906`: Test for IPython.embed() fails on Windows
* :ghissue:`4912`: Skip some Windows io failures
* :ghissue:`3700`: stdout/stderr should be flushed printing exception output... 
* :ghissue:`1181`: greedy completer bug in terminal console
* :ghissue:`2032`: check for a few places we should be using DEFAULT_ENCODING
* :ghissue:`4882`: Too many files open when starting and stopping kernel repeatedly
* :ghissue:`4880`: set profile name from profile_dir
* :ghissue:`4238`: parallel.Client() not using profile that notebook was run with?
* :ghissue:`4853`: fix setting image height/width from metadata
* :ghissue:`4786`: Reduce spacing of heading cells
* :ghissue:`4680`: Minimal pandoc version warning
* :ghissue:`3707`: nbconvert: Remove IPython magic commands from --format="python" output
* :ghissue:`4130`: PDF figures as links from png or svg figures
* :ghissue:`3919`: Allow --profile to be passed a dir.
* :ghissue:`2136`: Handle hard newlines in pretty printer
* :ghissue:`4790`: Notebook modal UI: "merge cell below" key binding, `shift+=`, does not work with some keyboard layouts
* :ghissue:`4884`: Keyboard shortcut changes
* :ghissue:`1184`: slow handling of keyboard input
* :ghissue:`4913`: Mathjax, Markdown, tex, env* and italic
* :ghissue:`3972`: nbconvert: Template output testing
* :ghissue:`4903`: use https for all embeds
* :ghissue:`4874`: --debug does not work if you set .kernel_cmd
* :ghissue:`4679`: JPG compression for inline pylab
* :ghissue:`4708`: Fix indent and center
* :ghissue:`4789`: fix IPython.embed
* :ghissue:`4759`: Application._load_config_files log parameter default fails
* :ghissue:`3153`: docs / file menu: explain how to exit the notebook
* :ghissue:`4791`: Did updates to ipython_directive bork support for cython magic snippets?
* :ghissue:`4385`: "Part 4 - Markdown Cells.ipynb" nbviewer example seems not well referenced in current online documentation page http://ipython.org/ipython-doc/stable/interactive/notebook.htm
* :ghissue:`4655`: prefer marked to pandoc for markdown2html
* :ghissue:`3441`: Fix focus related problems in the notebook
* :ghissue:`3402`: Feature Request: Save As (latex, html,..etc) as a menu option in Notebook rather than explicit need to invoke nbconvert
* :ghissue:`3224`: Revisit layout of notebook area
* :ghissue:`2746`: rerunning a cell with long output (exception) scrolls to much (html notebook)
* :ghissue:`2667`: can't save opened notebook if accidently delete the notebook in the dashboard
* :ghissue:`3026`: Reporting errors from _repr_<type>_ methods
* :ghissue:`1844`: Notebook does not exist and permalinks
* :ghissue:`2450`: [closed PR] Prevent jumping of window to input when output is clicked.
* :ghissue:`3166`: IPEP 16: Notebook multi directory dashboard and URL mapping
* :ghissue:`3691`: Slight misalignment of Notebook menu bar with focus box
* :ghissue:`4875`: Empty tooltip with `object_found = false` still being shown
* :ghissue:`4432`: The SSL cert for the MathJax CDN is invalid and URL is not protocol agnostic
* :ghissue:`2633`: Help text should leave current cell active
* :ghissue:`3976`: DOC: Pandas link on the notebook help menu?
* :ghissue:`4082`: /new handler redirect cached by browser
* :ghissue:`4298`: Slow ipython --pylab and ipython notebook startup
* :ghissue:`4545`: %store magic not working
* :ghissue:`4610`: toolbar UI enhancements
* :ghissue:`4782`: New modal UI
* :ghissue:`4732`: Accents in notebook names and in command-line (nbconvert)
* :ghissue:`4752`: link broken in docs/examples
* :ghissue:`4835`: running ipython on python files adds an extra traceback frame
* :ghissue:`4792`: repr_html exception warning on qtconsole with pandas  #4745 
* :ghissue:`4834`: function tooltip issues
* :ghissue:`4808`: Docstrings in Notebook not displayed properly and introspection
* :ghissue:`4846`: Remove some leftover traces of irunner
* :ghissue:`4810`: ipcluster bug in clean_logs flag
* :ghissue:`4812`: update CodeMirror for the notebook
* :ghissue:`671`: add migration guide for old IPython config
* :ghissue:`4783`: ipython 2dev  under windows / (win)python 3.3 experiment
* :ghissue:`4772`: Notebook server info files
* :ghissue:`4765`: missing build script for highlight.js
* :ghissue:`4787`: non-python kernels run python code with qtconsole
* :ghissue:`4703`: Math macro in jinja templates.
* :ghissue:`4595`: ipython notebook XSS vulnerable
* :ghissue:`4776`: Manually document py3compat module.
* :ghissue:`4686`: For-in loop on an array in cell.js
* :ghissue:`3605`: Modal UI
* :ghissue:`4769`: Ipython 2.0 will not startup on py27 on windows
* :ghissue:`4482`: reveal.js converter not including CDN by default?
* :ghissue:`4761`: ipv6 address triggers cookie exception
* :ghissue:`4580`: rename or remove %profile magic
* :ghissue:`4643`: Docstring does not open properly
* :ghissue:`4714`: Static URLs are not auto-versioned
* :ghissue:`2573`: document code mirror keyboard shortcuts
* :ghissue:`4717`: hang in parallel.Client when using SSHAgent
* :ghissue:`4544`: Clarify the requirement for pyreadline on Windows
* :ghissue:`3451`: revisit REST /new handler to avoid systematic crawling.
* :ghissue:`2922`: File => Save as '.py' saves magic as code 
* :ghissue:`4728`: Copy/Paste stripping broken in version > 0.13.x in QTConsole
* :ghissue:`4539`: Nbconvert: Latex to PDF conversion fails on notebooks with accented letters
* :ghissue:`4721`: purge_results with jobid crashing - looking for insight
* :ghissue:`4620`: Notebook with ? in title defies autosave, renaming and deletion.
* :ghissue:`4574`: Hash character in notebook name breaks a lot of things
* :ghissue:`4709`: input_prefilter hook not called
* :ghissue:`1680`: qtconsole should support --no-banner and custom banner
* :ghissue:`4689`: IOStream IP address configurable
* :ghissue:`4698`: Missing "if __name__ == '__main__':" check in /usr/bin/ipython
* :ghissue:`4191`: NBConvert: markdown inline and locally referenced files have incorrect file location for latex 
* :ghissue:`2865`: %%!? does not display the shell execute docstring
* :ghissue:`1551`: Notebook should be saved before printing
* :ghissue:`4612`: remove `Configurable.created` ?
* :ghissue:`4629`: Lots of tests fail due to space in sys.executable
* :ghissue:`4644`: Fixed URLs for notebooks
* :ghissue:`4621`: IPython 1.1.0 Qtconsole syntax highlighting highlights python 2 only built-ins when using python 3
* :ghissue:`2923`: Move Delete Button Away from Save Button in the HTML notebook toolbar
* :ghissue:`4615`: UnicodeDecodeError
* :ghissue:`4431`: ipython slow in os x mavericks?
* :ghissue:`4538`: DOC: document how to change ipcontroller-engine.json in case controller was started with --ip="*"
* :ghissue:`4551`: Serialize methods and closures
* :ghissue:`4081`: [Nbconvert][reveal] link to font awesome ?
* :ghissue:`4602`: "ipcluster stop" fails after "ipcluster start --daemonize" using python3.3
* :ghissue:`4578`: NBconvert fails with unicode errors when `--stdout` and file redirection is specified and HTML entities are present
* :ghissue:`4600`: Renaming new notebook to an exist name silently deletes the old one
* :ghissue:`4598`: Qtconsole docstring pop-up fails on method containing defaulted enum argument
* :ghissue:`951`: Remove Tornado monkeypatch
* :ghissue:`4564`: Notebook save failure
* :ghissue:`4562`: nbconvert: Default encoding problem on OS X
* :ghissue:`1675`: add file_to_run=file.ipynb capability to the notebook
* :ghissue:`4516`: `ipython console` doesn't send a `shutdown_request`
* :ghissue:`3043`: can't restart pdb session in ipython
* :ghissue:`4524`: Fix bug with non ascii passwords in notebook login
* :ghissue:`1866`: problems rendering an SVG?
* :ghissue:`4520`: unicode error when trying Audio('data/Bach Cello Suite #3.wav') 
* :ghissue:`4493`: Qtconsole cannot print an ISO8601 date at nanosecond precision
* :ghissue:`4502`: intermittent parallel test failure test_purge_everything 
* :ghissue:`4495`: firefox 25.0: notebooks report "Notebook save failed", .py script save fails, but .ipynb save succeeds
* :ghissue:`4245`: nbconvert latex: code highlighting causes error
* :ghissue:`4486`: Test for whether inside virtualenv does not work if directory is symlinked
* :ghissue:`4485`: Incorrect info in "Messaging in IPython" documentation. 
* :ghissue:`4447`: Ipcontroller broken in current HEAD on windows
* :ghissue:`4241`: Audio display object
* :ghissue:`4463`: Error on empty c.Session.key
* :ghissue:`4454`: UnicodeDecodeError when starting Ipython notebook on a directory containing a file with a non-ascii character
* :ghissue:`3801`: Autocompletion: Fix issue #3723 -- ordering of completions for magic commands and variables with same name
* :ghissue:`3723`: Code completion: 'matplotlib' and '%matplotlib'
* :ghissue:`4396`: Always checkpoint al least once ?
* :ghissue:`2524`: [Notebook] Clear kernel queue
* :ghissue:`2292`: Client side tests for the notebook
* :ghissue:`4424`: Dealing with images in multidirectory environment
* :ghissue:`4388`: Make writing configurable magics easier
* :ghissue:`852`: Notebook should be saved before downloading
* :ghissue:`3708`: ipython profile locate should also work
* :ghissue:`1349`: `?` may generate hundreds of cell 
* :ghissue:`4381`: Using hasattr for trait_names instead of just looking for it directly/using __dir__?
* :ghissue:`4361`: Crash Ultratraceback/ session history
* :ghissue:`3044`: IPython notebook autocomplete for filename string converts multiple spaces to a single space
* :ghissue:`3346`: Up arrow history search shows duplicates in Qtconsole
* :ghissue:`3496`: Fix import errors when running tests from the source directory
* :ghissue:`4114`: If default profile doesn't exist, can't install mathjax to any location
* :ghissue:`4335`: TestPylabSwitch.test_qt fails
* :ghissue:`4291`: serve like option for nbconvert --to latex
* :ghissue:`1824`: Exception before prompting for password during ssh connection
* :ghissue:`4309`: Error in nbconvert - closing </code> tag is not inserted in HTML under some circumstances
* :ghissue:`4351`: /parallel/apps/launcher.py error
* :ghissue:`3603`: Upcoming issues with nbconvert
* :ghissue:`4296`: sync_imports() fails in python 3.3
* :ghissue:`4339`: local mathjax install doesn't work
* :ghissue:`4334`: NotebookApp.webapp_settings static_url_prefix causes crash
* :ghissue:`4308`: Error when use "ipython notebook" in win7 64 with python2.7.3 64.
* :ghissue:`4317`: Relative imports broken in the notebook (Windows)
* :ghissue:`3658`: Saving Notebook clears "Kernel Busy" status from the page and titlebar
* :ghissue:`4312`: Link broken on ipython-doc stable
* :ghissue:`1093`: Add boundary options to %load
* :ghissue:`3619`: Multi-dir webservice design
* :ghissue:`4299`: Nbconvert, default_preprocessors to list of dotted name not list of obj
* :ghissue:`3210`: IPython.parallel tests seem to hang on ShiningPanda
* :ghissue:`4280`: MathJax Automatic Line Breaking
* :ghissue:`4039`: Celltoolbar example issue
* :ghissue:`4247`: nbconvert --to latex: error when converting greek letter
* :ghissue:`4273`: %%capture not capturing rich objects like plots (IPython 1.1.0)
* :ghissue:`3866`: Vertical offsets in LaTeX output for nbconvert
* :ghissue:`3631`: xkcd mode for the IPython notebook
* :ghissue:`4243`: Test exclusions not working on Windows
* :ghissue:`4256`: IPython no longer handles unicode file names 
* :ghissue:`3656`: Audio displayobject
* :ghissue:`4223`: Double output on Ctrl-enter-enter
* :ghissue:`4184`: nbconvert: use r pygmentize backend when highlighting "%%R" cells 
* :ghissue:`3851`: Adds an explicit newline for pretty-printing.
* :ghissue:`3622`: Drop fakemodule
* :ghissue:`4122`: Nbconvert [windows]: Inconsistent line endings in markdown cells exported to latex 
* :ghissue:`3819`: nbconvert add extra blank line to code block on Windows.
* :ghissue:`4203`: remove spurious print statement from parallel annoted functions
* :ghissue:`4200`: Notebook: merging a heading cell and markdown cell cannot be undone
* :ghissue:`3747`: ipynb -> ipynb transformer
* :ghissue:`4024`: nbconvert markdown issues
* :ghissue:`3903`: on Windows, 'ipython3 nbconvert "C:/blabla/first_try.ipynb" --to slides' gives an unexpected result, and '--post serve' fails
* :ghissue:`4095`: Catch js error in append html in stream/pyerr
* :ghissue:`1880`: Add parallelism to test_pr 
* :ghissue:`4085`: nbconvert: Fix sphinx preprocessor date format string for Windows
* :ghissue:`4156`: Specifying --gui=tk at the command line
* :ghissue:`4146`: Having to prepend 'files/' to markdown image paths is confusing 
* :ghissue:`3818`: nbconvert can't handle Heading with Chinese characters on Japanese Windows OS.
* :ghissue:`4134`: multi-line parser fails on ''' in comment, qtconsole and notebook.
* :ghissue:`3998`: sample custom.js needs to be updated
* :ghissue:`4078`: StoreMagic.autorestore not working in 1.0.0
* :ghissue:`3990`: Buitlin `input` doesn't work over zmq
* :ghissue:`4015`: nbconvert fails to convert all the content of a notebook
* :ghissue:`4059`: Issues with Ellipsis literal in Python 3
* :ghissue:`2310`: "ZMQError: Interrupted system call" from RichIPythonWidget
* :ghissue:`3807`: qtconsole ipython 0.13.2 - html/xhtml export fails
* :ghissue:`4103`: Wrong default argument of DirectView.clear
* :ghissue:`4100`: parallel.client.client references undefined error.EngineError
* :ghissue:`484`: Drop nosepatch
* :ghissue:`3350`: Added longlist support in ipdb.
* :ghissue:`1591`: Keying 'q' doesn't quit the interactive help in Wins7
* :ghissue:`40`: The tests in test_process fail under Windows
* :ghissue:`3744`: capture rich output as well as stdout/err in capture_output
* :ghissue:`3742`: %%capture to grab rich display outputs
* :ghissue:`3863`: Added working speaker notes for slides.
* :ghissue:`4013`: Iptest fails in dual python installation
* :ghissue:`4005`: IPython.start_kernel doesn't work.
* :ghissue:`4020`: IPython parallel map fails on numpy arrays
* :ghissue:`3914`: nbconvert: Transformer tests
* :ghissue:`3923`: nbconvert: Writer tests
* :ghissue:`3945`: nbconvert: commandline tests fail Win7x64 Py3.3
* :ghissue:`3937`: make tab visible in codemirror and light red background
* :ghissue:`3935`: No feedback for mixed tabs and spaces
* :ghissue:`3933`: nbconvert: Post-processor tests
* :ghissue:`3977`: unable to complete remote connections for two-process 
* :ghissue:`3939`: minor checkpoint cleanup
* :ghissue:`3955`: complete on % for magic in notebook
* :ghissue:`3954`: all magics should be listed when completing on %
* :ghissue:`3980`: nbconvert rst output lacks needed blank lines
* :ghissue:`3968`: TypeError: super() argument 1 must be type, not classobj (Python 2.6.6)
* :ghissue:`3880`: nbconvert: R&D remaining tests
* :ghissue:`2440`: IPEP 4: Python 3 Compatibility

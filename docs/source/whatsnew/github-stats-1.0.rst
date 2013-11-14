.. _issues_list_100:

Issues closed in the 1.0 development cycle
==========================================

Issues closed in 1.1
--------------------

GitHub stats for 2013/08/08 - 2013/09/09 (since 1.0)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 25 authors contributed 337 commits.

* Benjamin Ragan-Kelley
* Bing Xia
* Bradley M. Froehle
* Brian E. Granger
* Damián Avila
* dhirschfeld
* Dražen Lučanin
* gmbecker
* Jake Vanderplas
* Jason Grout
* Jonathan Frederic
* Kevin Burke
* Kyle Kelley
* Matt Henderson
* Matthew Brett
* Matthias Bussonnier
* Pankaj Pandey
* Paul Ivanov
* rossant
* Samuel Ainsworth
* Stephan Rave
* stonebig
* Thomas Kluyver
* Yaroslav Halchenko
* Zachary Sailer


We closed a total of 76 issues, 58 pull requests and 18 regular issues;
this is the full list (generated with the script :file:`tools/github_stats.py`):

Pull Requests (58):

* :ghpull:`4188`: Allow user_ns trait to be None
* :ghpull:`4189`: always fire LOCAL_IPS.extend(PUBLIC_IPS)
* :ghpull:`4174`: various issues in markdown and rst templates
* :ghpull:`4178`: add missing data_javascript
* :ghpull:`4181`: nbconvert: Fix, sphinx template not removing new lines from headers
* :ghpull:`4043`: don't 'restore_bytes' in from_JSON
* :ghpull:`4163`: Fix for incorrect default encoding on Windows.
* :ghpull:`4136`: catch javascript errors in any output
* :ghpull:`4171`: add nbconvert config file when creating profiles
* :ghpull:`4125`: Basic exercise of `ipython [subcommand] -h` and help-all
* :ghpull:`4085`: nbconvert: Fix sphinx preprocessor date format string for Windows
* :ghpull:`4159`: don't split `.cell` and `div.cell` CSS
* :ghpull:`4158`: generate choices for `--gui` configurable from real mapping
* :ghpull:`4065`: do not include specific css in embedable one
* :ghpull:`4092`: nbconvert: Fix for unicode html headers, Windows + Python 2.x
* :ghpull:`4074`: close Client sockets if connection fails
* :ghpull:`4064`: Store default codemirror mode in only 1 place
* :ghpull:`4104`: Add way to install MathJax to a particular profile
* :ghpull:`4144`: help_end transformer shouldn't pick up ? in multiline string
* :ghpull:`4143`: update example custom.js
* :ghpull:`4142`: DOC: unwrap openssl line in public_server doc
* :ghpull:`4141`: add files with a separate `add` call in backport_pr
* :ghpull:`4137`: Restore autorestore option for storemagic
* :ghpull:`4098`: pass profile-dir instead of profile name to Kernel
* :ghpull:`4120`: support `input` in Python 2 kernels
* :ghpull:`4088`: nbconvert: Fix coalescestreams line with incorrect nesting causing strange behavior
* :ghpull:`4060`: only strip continuation prompts if regular prompts seen first
* :ghpull:`4132`: Fixed name error bug in function safe_unicode in module py3compat.
* :ghpull:`4121`: move test_kernel from IPython.zmq to IPython.kernel
* :ghpull:`4118`: ZMQ heartbeat channel: catch EINTR exceptions and continue.
* :ghpull:`4054`: use unicode for HTML export
* :ghpull:`4106`: fix a couple of default block values
* :ghpull:`4115`: Update docs on declaring a magic function
* :ghpull:`4101`: restore accidentally removed EngineError
* :ghpull:`4096`: minor docs changes
* :ghpull:`4056`: respect `pylab_import_all` when `--pylab` specified at the command-line
* :ghpull:`4091`: Make Qt console banner configurable
* :ghpull:`4086`: fix missing errno import
* :ghpull:`4030`: exclude `.git` in MANIFEST.in
* :ghpull:`4047`: Use istype() when checking if canned object is a dict
* :ghpull:`4031`: don't close_fds on Windows
* :ghpull:`4029`: bson.Binary moved
* :ghpull:`4035`: Fixed custom jinja2 templates being ignored when setting template_path
* :ghpull:`4026`: small doc fix in nbconvert
* :ghpull:`4016`: Fix IPython.start_* functions
* :ghpull:`4021`: Fix parallel.client.View map() on numpy arrays
* :ghpull:`4022`: DOC: fix links to matplotlib, notebook docs
* :ghpull:`4018`: Fix warning when running IPython.kernel tests
* :ghpull:`4019`: Test skipping without unicode paths
* :ghpull:`4008`: Transform code before %prun/%%prun runs
* :ghpull:`4014`: Fix typo in ipapp
* :ghpull:`3987`: get files list in backport_pr
* :ghpull:`3974`: nbconvert: Fix app tests on Window7 w/ Python 3.3
* :ghpull:`3978`: fix `--existing` with non-localhost IP
* :ghpull:`3939`: minor checkpoint cleanup
* :ghpull:`3981`: BF: fix nbconvert rst input prompt spacing
* :ghpull:`3960`: Don't make sphinx a dependency for importing nbconvert
* :ghpull:`3973`: logging.Formatter is not new-style in 2.6

Issues (18):

* :ghissue:`4024`: nbconvert markdown issues
* :ghissue:`4095`: Catch js error in append html in stream/pyerr
* :ghissue:`4156`: Specifying --gui=tk at the command line
* :ghissue:`3818`: nbconvert can't handle Heading with Chinese characters on Japanese Windows OS.
* :ghissue:`4134`: multi-line parser fails on ''' in comment, qtconsole and notebook.
* :ghissue:`3998`: sample custom.js needs to be updated
* :ghissue:`4078`: StoreMagic.autorestore not working in 1.0.0
* :ghissue:`3990`: Buitlin `input` doesn't work over zmq
* :ghissue:`4015`: nbconvert fails to convert all the content of a notebook
* :ghissue:`4059`: Issues with Ellipsis literal in Python 3
* :ghissue:`4103`: Wrong default argument of DirectView.clear
* :ghissue:`4100`: parallel.client.client references undefined error.EngineError
* :ghissue:`4005`: IPython.start_kernel doesn't work.
* :ghissue:`4020`: IPython parallel map fails on numpy arrays
* :ghissue:`3945`: nbconvert: commandline tests fail Win7x64 Py3.3
* :ghissue:`3977`: unable to complete remote connections for two-process 
* :ghissue:`3980`: nbconvert rst output lacks needed blank lines
* :ghissue:`3968`: TypeError: super() argument 1 must be type, not classobj (Python 2.6.6)

Issues closed in 1.0
--------------------

GitHub stats for 2012/06/30 - 2013/08/08 (since 0.13)

These lists are automatically generated, and may be incomplete or contain duplicates.

The following 155 authors contributed 4258 commits.

* Aaron Meurer
* Adam Davis
* Ahmet Bakan
* Alberto Valverde
* Allen Riddell
* Anders Hovmöller
* Andrea Bedini
* Andrew Spiers
* Andrew Vandever
* Anthony Scopatz
* Anton Akhmerov
* Anton I. Sipos
* Antony Lee
* Aron Ahmadia
* Benedikt Sauer
* Benjamin Jones
* Benjamin Ragan-Kelley
* Benjie Chen
* Boris de Laage
* Brad Reisfeld
* Bradley M. Froehle
* Brian E. Granger
* Cameron Bates
* Cavendish McKay
* chapmanb
* Chris Beaumont
* Chris Laumann
* Christoph Gohlke
* codebraker
* codespaced
* Corran Webster
* DamianHeard
* Damián Avila
* Dan Kilman
* Dan McDougall
* Danny Staple
* David Hirschfeld
* David P. Sanders
* David Warde-Farley
* David Wolever
* David Wyde
* debjan
* Diane Trout
* dkua
* Dominik Dabrowski
* Donald Curtis
* Dražen Lučanin
* drevicko
* Eric O. LEBIGOT
* Erik M. Bray
* Erik Tollerud
* Eugene Van den Bulke
* Evan Patterson
* Fernando Perez
* Francesco Montesano
* Frank Murphy
* Greg Caporaso
* Guy Haskin Fernald
* guziy
* Hans Meine
* Harry Moreno
* henryiii
* Ivan Djokic
* Jack Feser
* Jake Vanderplas
* jakobgager
* James Booth
* Jan Schulz
* Jason Grout
* Jeff Knisley
* Jens Hedegaard Nielsen
* jeremiahbuddha
* Jerry Fowler
* Jessica B. Hamrick
* Jez Ng
* John Zwinck
* Jonathan Frederic
* Jonathan Taylor
* Joon Ro
* Joseph Lansdowne
* Juergen Hasch
* Julian Taylor
* Jussi Sainio
* Jörgen Stenarson
* kevin
* klonuo
* Konrad Hinsen
* Kyle Kelley
* Lars Solberg
* Lessandro Mariano
* Mark Sienkiewicz at STScI
* Martijn Vermaat
* Martin Spacek
* Matthias Bussonnier
* Maxim Grechkin
* Maximilian Albert
* MercuryRising
* Michael Droettboom
* Michael Shuffett
* Michał Górny
* Mikhail Korobov
* mr.Shu
* Nathan Goldbaum
* ocefpaf
* Ohad Ravid
* Olivier Grisel
* Olivier Verdier
* Owen Healy
* Pankaj Pandey
* Paul Ivanov
* Pawel Jasinski
* Pietro Berkes
* Piti Ongmongkolkul
* Puneeth Chaganti
* Rich Wareham
* Richard Everson
* Rick Lupton
* Rob Young
* Robert Kern
* Robert Marchman
* Robert McGibbon
* Rui Pereira
* Rustam Safin
* Ryan May
* s8weber
* Samuel Ainsworth
* Sean Vig
* Siyu Zhang
* Skylar Saveland
* slojo404
* smithj1
* Stefan Karpinski
* Stefan van der Walt
* Steven Silvester
* Takafumi Arakaki
* Takeshi Kanmae
* tcmulcahy
* teegaar
* Thomas Kluyver
* Thomas Robitaille
* Thomas Spura
* Thomas Weißschuh
* Timothy O'Donnell
* Tom Dimiduk
* ugurthemaster
* urielshaolin
* v923z
* Valentin Haenel
* Victor Zverovich
* W. Trevor King
* y-p
* Yoav Ram
* Zbigniew Jędrzejewski-Szmek
* Zoltán Vörös


We closed a total of 1484 issues, 793 pull requests and 691 regular issues;
this is the full list (generated with the script 
:file:`tools/github_stats.py`):

Pull Requests (793):

* :ghpull:`3958`: doc update
* :ghpull:`3965`: Fix ansi color code for background yellow
* :ghpull:`3964`: Fix casing of message.
* :ghpull:`3942`: Pass on install docs
* :ghpull:`3962`: exclude IPython.lib.kernel in iptest
* :ghpull:`3961`: Longpath test fix
* :ghpull:`3905`: Remove references to 0.11 and 0.12 from config/overview.rst
* :ghpull:`3951`: nbconvert: fixed latex characters not escaped properly in nbconvert
* :ghpull:`3949`: log fatal error when PDF conversion fails
* :ghpull:`3947`: nbconvert: Make writer & post-processor aliases case insensitive.
* :ghpull:`3938`: Recompile css.
* :ghpull:`3948`: sphinx and PDF tweaks
* :ghpull:`3943`: nbconvert: Serve post-processor Windows fix
* :ghpull:`3934`: nbconvert: fix logic of verbose flag in PDF post processor
* :ghpull:`3929`: swallow enter event in rename dialog
* :ghpull:`3924`: nbconvert: Backport fixes
* :ghpull:`3925`: Replace --pylab flag with --matplotlib in usage
* :ghpull:`3910`: Added explicit error message for missing configuration arguments.
* :ghpull:`3913`: grffile to support spaces in notebook names
* :ghpull:`3918`: added check_for_tornado, closes #3916
* :ghpull:`3917`: change docs/examples refs to be just examples
* :ghpull:`3908`: what's new tweaks
* :ghpull:`3896`: two column quickhelp dialog, closes #3895
* :ghpull:`3911`: explicitly load python mode before IPython mode
* :ghpull:`3901`: don't force . relative path, fix #3897
* :ghpull:`3891`: fix #3889
* :ghpull:`3892`: Fix documentation of Kernel.stop_channels
* :ghpull:`3888`: posixify paths for Windows latex
* :ghpull:`3882`: quick fix for #3881
* :ghpull:`3877`: don't use `shell=True` in PDF export
* :ghpull:`3878`: minor template loading cleanup
* :ghpull:`3855`: nbconvert: Filter tests
* :ghpull:`3879`: finish 3870
* :ghpull:`3870`: Fix for converting notebooks that contain unicode characters.
* :ghpull:`3876`: Update parallel_winhpc.rst
* :ghpull:`3872`: removing vim-ipython, since it has it's own repo
* :ghpull:`3871`: updating docs
* :ghpull:`3873`: remove old examples
* :ghpull:`3868`: update CodeMirror component to 3.15
* :ghpull:`3865`: Escape filename for pdflatex in nbconvert
* :ghpull:`3861`: remove old external.js
* :ghpull:`3864`: add keyboard shortcut to docs
* :ghpull:`3834`: This PR fixes a few issues with nbconvert tests
* :ghpull:`3840`: prevent profile_dir from being undefined
* :ghpull:`3859`: Add "An Afternoon Hack" to docs
* :ghpull:`3854`: Catch errors filling readline history on startup
* :ghpull:`3857`: Delete extra auto
* :ghpull:`3845`: nbconvert: Serve from original build directory
* :ghpull:`3846`: Add basic logging to nbconvert
* :ghpull:`3850`: add missing store_history key to Notebook execute_requests
* :ghpull:`3844`: update payload source
* :ghpull:`3830`: mention metadata / display_data similarity in pyout spec
* :ghpull:`3848`: fix incorrect `empty-docstring`
* :ghpull:`3836`: Parse markdown correctly when mathjax is disabled
* :ghpull:`3849`: skip a failing test on windows
* :ghpull:`3828`: signature_scheme lives in Session
* :ghpull:`3831`: update nbconvert doc with new CLI
* :ghpull:`3822`: add output flag to nbconvert
* :ghpull:`3780`: Added serving the output directory if html-based format are selected.
* :ghpull:`3764`: Cleanup nbconvert templates
* :ghpull:`3829`: remove now-duplicate 'this is dev' note
* :ghpull:`3814`: add `ConsoleWidget.execute_on_complete_input` flag
* :ghpull:`3826`: try rtfd
* :ghpull:`3821`: add sphinx prolog
* :ghpull:`3817`: relax timeouts in terminal console and tests
* :ghpull:`3825`: fix more tests that fail when pandoc is missing
* :ghpull:`3824`: don't set target on internal markdown links
* :ghpull:`3816`: s/pylab/matplotlib in docs
* :ghpull:`3812`: Describe differences between start_ipython and embed
* :ghpull:`3805`: Print View has been removed
* :ghpull:`3820`: Make it clear that 1.0 is not released yet
* :ghpull:`3784`: nbconvert: Export flavors & PDF writer (ipy dev meeting)
* :ghpull:`3800`: semantic-versionify version number for non-releases
* :ghpull:`3802`: Documentation .txt to .rst
* :ghpull:`3765`: cleanup terminal console iopub handling
* :ghpull:`3720`: Fix for #3719
* :ghpull:`3787`: re-raise KeyboardInterrupt in raw_input
* :ghpull:`3770`: Organizing reveal's templates.
* :ghpull:`3751`: Use link(2) when possible in nbconvert
* :ghpull:`3792`: skip tests that require pandoc
* :ghpull:`3782`: add Importing Notebooks example
* :ghpull:`3752`: nbconvert: Add cwd to sys.path
* :ghpull:`3789`: fix raw_input in qtconsole
* :ghpull:`3756`: document the wire protocol
* :ghpull:`3749`: convert IPython syntax to Python syntax in nbconvert python template
* :ghpull:`3793`: Closes #3788
* :ghpull:`3794`: Change logo link to ipython.org
* :ghpull:`3746`: Raise a named exception when pandoc is missing
* :ghpull:`3781`: comply with the message spec in the notebook
* :ghpull:`3779`: remove bad `if logged_in` preventing new-notebook without login
* :ghpull:`3743`: remove notebook read-only view
* :ghpull:`3732`: add delay to autosave in beforeunload
* :ghpull:`3761`: Added rm_math_space to markdown cells in the basichtml.tpl to be rendered ok by mathjax after the nbconvertion.
* :ghpull:`3758`: nbconvert: Filter names cleanup
* :ghpull:`3769`: Add configurability to  tabcompletion timeout
* :ghpull:`3771`: Update px pylab test to match new output of pylab
* :ghpull:`3741`: better message when notebook format is not supported
* :ghpull:`3753`: document Ctrl-C not working in ipython kernel
* :ghpull:`3766`: handle empty metadata in pyout messages more gracefully.
* :ghpull:`3736`: my attempt to fix #3735
* :ghpull:`3759`: nbconvert: Provide a more useful error for invalid use case.
* :ghpull:`3760`: nbconvert: Allow notebook filenames without their extensions
* :ghpull:`3750`: nbconvert: Add cwd to default templates search path.
* :ghpull:`3748`: Update nbconvert docs
* :ghpull:`3734`: Nbconvert: Export extracted files into `nbname_files` subdirectory
* :ghpull:`3733`: Nicer message when pandoc is missing, closes #3730
* :ghpull:`3722`: fix two failing test in IPython.lib
* :ghpull:`3704`: Start what's new for 1.0
* :ghpull:`3705`: Complete rewrite of IPython Notebook documentation: docs/source/interactive/htmlnotebook.txt
* :ghpull:`3709`: Docs cleanup
* :ghpull:`3716`: raw_input fixes for kernel restarts
* :ghpull:`3683`: use `%matplotlib` in example notebooks
* :ghpull:`3686`: remove quarantine
* :ghpull:`3699`: svg2pdf unicode fix
* :ghpull:`3695`: fix SVG2PDF
* :ghpull:`3685`: fix Pager.detach
* :ghpull:`3675`: document new dependencies
* :ghpull:`3690`: Fixing some css minors in full_html and reveal.
* :ghpull:`3671`: nbconvert tests
* :ghpull:`3692`: Fix rename notebook - show error with invalid name
* :ghpull:`3409`: Prevent qtconsole frontend freeze on lots of output.
* :ghpull:`3660`: refocus active cell on dialog close
* :ghpull:`3598`: Statelessify mathjaxutils
* :ghpull:`3673`: enable comment/uncomment selection
* :ghpull:`3677`: remove special-case in get_home_dir for frozen dists
* :ghpull:`3674`: add CONTRIBUTING.md
* :ghpull:`3670`: use Popen command list for ipexec
* :ghpull:`3568`: pylab import adjustments
* :ghpull:`3559`: add create.Cell and delete.Cell js events
* :ghpull:`3606`: push cell magic to the head of the transformer line
* :ghpull:`3607`: NbConvert: Writers, No YAML, and stuff...
* :ghpull:`3665`: Pywin32 skips
* :ghpull:`3669`: set default client_class for QtKernelManager
* :ghpull:`3662`: add strip_encoding_cookie transformer
* :ghpull:`3641`: increase patience for slow kernel startup in tests
* :ghpull:`3651`: remove a bunch of unused `default_config_file` assignments
* :ghpull:`3630`: CSS adjustments
* :ghpull:`3645`: Don't require HistoryManager to have a shell
* :ghpull:`3643`: don't assume tested ipython is on the PATH
* :ghpull:`3654`: fix single-result AsyncResults
* :ghpull:`3601`: Markdown in heading cells (take 2)
* :ghpull:`3652`: Remove old `docs/examples`
* :ghpull:`3621`: catch any exception appending output
* :ghpull:`3585`: don't blacklist builtin names
* :ghpull:`3647`: Fix `frontend` deprecation warnings in several examples
* :ghpull:`3649`: fix AsyncResult.get_dict for single result
* :ghpull:`3648`: Fix store magic test 
* :ghpull:`3650`: Fix, config_file_name was ignored
* :ghpull:`3640`: Gcf.get_active() can return None
* :ghpull:`3571`: Added shorcuts to split cell, merge cell above and merge cell below.
* :ghpull:`3635`: Added missing slash to print-pdf call.
* :ghpull:`3487`: Drop patch for compatibility with pyreadline 1.5
* :ghpull:`3338`: Allow filename with extension in find_cmd in Windows.
* :ghpull:`3628`: Fix test for Python 3 on Windows.
* :ghpull:`3642`: Fix typo in docs
* :ghpull:`3627`: use DEFAULT_STATIC_FILES_PATH in a test instead of package dir
* :ghpull:`3624`: fix some unicode in zmqhandlers
* :ghpull:`3460`: Set calling program to UNKNOWN, when argv not in sys
* :ghpull:`3632`: Set calling program to UNKNOWN, when argv not in sys (take #2)
* :ghpull:`3629`: Use new entry point for python -m IPython
* :ghpull:`3626`: passing cell to showInPager, closes #3625
* :ghpull:`3618`: expand terminal color support
* :ghpull:`3623`: raise UsageError for unsupported GUI backends
* :ghpull:`3071`: Add magic function %drun to run code in debugger
* :ghpull:`3608`: a nicer error message when using %pylab magic
* :ghpull:`3592`: add extra_config_file
* :ghpull:`3612`: updated .mailmap
* :ghpull:`3616`: Add examples for interactive use of MPI.
* :ghpull:`3615`: fix regular expression for ANSI escapes
* :ghpull:`3586`: Corrected a typo in the format string for strftime the sphinx.py transformer of nbconvert
* :ghpull:`3611`: check for markdown no longer needed, closes #3610
* :ghpull:`3555`: Simplify caching of modules with %run
* :ghpull:`3583`: notebook small things
* :ghpull:`3594`: Fix duplicate completion in notebook
* :ghpull:`3600`: parallel: Improved logging for errors during BatchSystemLauncher.stop
* :ghpull:`3595`: Revert "allow markdown in heading cells"
* :ghpull:`3538`: add IPython.start_ipython
* :ghpull:`3562`: Allow custom nbconvert template loaders
* :ghpull:`3582`: pandoc adjustments
* :ghpull:`3560`: Remove max_msg_size
* :ghpull:`3591`: Refer to Setuptools instead of Distribute
* :ghpull:`3590`: IPython.sphinxext needs an __init__.py
* :ghpull:`3581`: Added the possibility to read a custom.css file for tweaking the final html in full_html and reveal templates.
* :ghpull:`3576`: Added support for markdown in heading cells when they are nbconverted.
* :ghpull:`3575`: tweak `run -d` message to 'continue execution'
* :ghpull:`3569`: add PYTHONSTARTUP to startup files
* :ghpull:`3567`: Trigger a single event on js app initilized
* :ghpull:`3565`: style.min.css shoudl always exist...
* :ghpull:`3531`: allow markdown in heading cells
* :ghpull:`3577`: Simplify codemirror ipython-mode
* :ghpull:`3495`: Simplified regexp, and suggestions for clearer regexps.
* :ghpull:`3578`: Use adjustbox to specify figure size in nbconvert -> latex
* :ghpull:`3572`: Skip import irunner test on Windows.
* :ghpull:`3574`: correct static path for CM modes autoload
* :ghpull:`3558`: Add IPython.sphinxext
* :ghpull:`3561`: mention double-control-C to stop notebook server
* :ghpull:`3566`: fix event names
* :ghpull:`3564`: Remove trivial nbconvert example
* :ghpull:`3540`: allow cython cache dir to be deleted
* :ghpull:`3527`: cleanup stale, unused exceptions in parallel.error
* :ghpull:`3529`: ensure raw_input returns str in zmq shell
* :ghpull:`3541`: respect image size metadata in qtconsole
* :ghpull:`3550`: Fixing issue preventing the correct read of images by full_html and reveal exporters.
* :ghpull:`3557`: open markdown links in new tabs
* :ghpull:`3556`: remove mention of nonexistent `_margv` in macro
* :ghpull:`3552`: set overflow-x: hidden on Firefox only
* :ghpull:`3554`: Fix missing import os in latex exporter.
* :ghpull:`3546`: Don't hardcode **latex** posix paths in nbconvert
* :ghpull:`3551`: fix path prefix in nbconvert
* :ghpull:`3533`: Use a CDN to get reveal.js library.
* :ghpull:`3498`: When a notebook is written to file, name the metadata name u''.
* :ghpull:`3548`: Change to standard save icon in Notebook toolbar
* :ghpull:`3539`: Don't hardcode posix paths in nbconvert
* :ghpull:`3508`: notebook supports raw_input and %debug now
* :ghpull:`3526`: ensure 'default' is first in cluster profile list
* :ghpull:`3525`: basic timezone info
* :ghpull:`3532`: include nbconvert templates in installation
* :ghpull:`3515`: update CodeMirror component to 3.14
* :ghpull:`3513`: add 'No Checkpoints' to Revert menu
* :ghpull:`3536`: format positions are required in Python 2.6.x
* :ghpull:`3521`: Nbconvert fix, silent fail if template doesn't exist
* :ghpull:`3530`: update %store magic docstring
* :ghpull:`3528`: fix local mathjax with custom base_project_url
* :ghpull:`3518`: Clear up unused imports
* :ghpull:`3506`: %store -r restores saved aliases and directory history, as well as variables
* :ghpull:`3516`: make css highlight style configurable
* :ghpull:`3523`: Exclude frontend shim from docs build
* :ghpull:`3514`: use bootstrap `disabled` instead of `ui-state-disabled`
* :ghpull:`3520`: Added relative import of RevealExporter to __init__.py inside exporters module
* :ghpull:`3507`: fix HTML capitalization in nbconvert exporter classes
* :ghpull:`3512`: fix nbconvert filter validation
* :ghpull:`3511`: Get Tracer working after ipapi.get replaced with get_ipython
* :ghpull:`3510`: use `window.onbeforeunload=` for nav-away warning
* :ghpull:`3504`: don't use parent=self in handlers
* :ghpull:`3500`: Merge nbconvert into IPython
* :ghpull:`3478`: restore "unsaved changes" warning on unload
* :ghpull:`3493`: add a dialog when the kernel is auto-restarted
* :ghpull:`3488`: Add test suite for autoreload extension
* :ghpull:`3484`: Catch some pathological cases inside oinspect
* :ghpull:`3481`: Display R errors without Python traceback
* :ghpull:`3468`: fix `%magic` output
* :ghpull:`3430`: add parent to Configurable
* :ghpull:`3491`: Remove unexpected keyword parameter to remove_kernel
* :ghpull:`3485`: SymPy has changed its recommended way to initialize printing
* :ghpull:`3486`: Add test for non-ascii characters in docstrings
* :ghpull:`3483`: Inputtransformer: Allow classic prompts without space
* :ghpull:`3482`: Use an absolute path to iptest, because the tests are not always run from $IPYTHONDIR.
* :ghpull:`3381`: enable 2x (retina) display
* :ghpull:`3450`: Flatten IPython.frontend
* :ghpull:`3477`: pass config to subapps
* :ghpull:`3466`: Kernel fails to start when username has non-ascii characters
* :ghpull:`3465`: Add HTCondor bindings to IPython.parallel
* :ghpull:`3463`: fix typo, closes #3462
* :ghpull:`3456`: Notice for users who disable javascript
* :ghpull:`3453`: fix cell execution in firefox, closes #3447
* :ghpull:`3393`: [WIP] bootstrapify
* :ghpull:`3440`: Fix installing mathjax from downloaded file via command line
* :ghpull:`3431`: Provide means for starting the Qt console maximized and with the menu bar hidden
* :ghpull:`3425`: base IPClusterApp inherits from BaseIPythonApp
* :ghpull:`3433`: Update IPython\external\path\__init__.py
* :ghpull:`3298`: Some fixes in IPython Sphinx directive
* :ghpull:`3428`: process escapes in mathjax
* :ghpull:`3420`: thansk -> thanks
* :ghpull:`3416`: Fix doc: "principle" not "principal"
* :ghpull:`3413`: more unique filename for test
* :ghpull:`3364`: Inject requirejs in notebook and start using it.
* :ghpull:`3390`: Fix %paste with blank lines
* :ghpull:`3403`: fix creating config objects from dicts
* :ghpull:`3401`: rollback #3358
* :ghpull:`3373`: make cookie_secret configurable
* :ghpull:`3307`: switch default ws_url logic to js side
* :ghpull:`3392`: Restore anchor link on h2-h6
* :ghpull:`3369`: Use different treshold for (auto)scroll in output
* :ghpull:`3370`: normalize unicode notebook filenames
* :ghpull:`3372`: base default cookie name on request host+port
* :ghpull:`3378`: disable CodeMirror drag/drop on Safari
* :ghpull:`3358`: workaround spurious CodeMirror scrollbars
* :ghpull:`3371`: make setting the notebook dirty flag an event
* :ghpull:`3366`: remove long-dead zmq frontend.py and completer.py
* :ghpull:`3382`: cull Session digest history
* :ghpull:`3330`: Fix get_ipython_dir when $HOME is /
* :ghpull:`3319`: IPEP 13: user-expressions and user-variables
* :ghpull:`3384`: comments in tools/gitwash_dumper.py changed (''' to """)
* :ghpull:`3387`: Make submodule checks work under Python 3.
* :ghpull:`3357`: move anchor-link off of heading text
* :ghpull:`3351`: start basic tests of ipcluster Launchers
* :ghpull:`3377`: allow class.__module__ to be None
* :ghpull:`3340`: skip submodule check in package managers
* :ghpull:`3328`: decode subprocess output in launchers
* :ghpull:`3368`: Reenable bracket matching
* :ghpull:`3356`: Mpr fixes
* :ghpull:`3336`: Use new input transformation API in %time magic
* :ghpull:`3325`: Organize the JS and less files by component.
* :ghpull:`3342`: fix test_find_cmd_python
* :ghpull:`3354`: catch socket.error in utils.localinterfaces
* :ghpull:`3341`: fix default cluster count
* :ghpull:`3286`: don't use `get_ipython` from builtins in library code
* :ghpull:`3333`: notebookapp: add missing whitespace to warnings
* :ghpull:`3323`: Strip prompts even if the prompt isn't present on the first line.
* :ghpull:`3321`: Reorganize the python/server side of the notebook
* :ghpull:`3320`: define `__file__` in config files
* :ghpull:`3317`: rename `%%file` to `%%writefile`
* :ghpull:`3304`: set unlimited HWM for all relay devices
* :ghpull:`3315`: Update Sympy_printing extension load
* :ghpull:`3310`: further clarify Image docstring
* :ghpull:`3285`: load extensions in builtin trap
* :ghpull:`3308`: Speed up AsyncResult._wait_for_outputs(0)
* :ghpull:`3294`: fix callbacks as optional in js kernel.execute
* :ghpull:`3276`: Fix: "python ABS/PATH/TO/ipython.py" fails
* :ghpull:`3301`: allow python3 tests without python installed
* :ghpull:`3282`: allow view.map to work with a few more things
* :ghpull:`3284`: remove `ipython.py` entry point
* :ghpull:`3281`: fix ignored IOPub messages with no parent
* :ghpull:`3275`: improve submodule messages / git hooks
* :ghpull:`3239`: Allow "x" icon and esc key to close pager in notebook
* :ghpull:`3290`: Improved heartbeat controller to engine monitoring for long running tasks
* :ghpull:`3142`: Better error message when CWD doesn't exist on startup
* :ghpull:`3066`: Add support for relative import to %run -m (fixes #2727)
* :ghpull:`3269`: protect highlight.js against unknown languages
* :ghpull:`3267`: add missing return
* :ghpull:`3101`: use marked / highlight.js instead of pagedown and prettify
* :ghpull:`3264`: use https url for submodule
* :ghpull:`3263`: fix set_last_checkpoint when no checkpoint
* :ghpull:`3258`: Fix submodule location in setup.py
* :ghpull:`3254`: fix a few URLs from previous PR
* :ghpull:`3240`: remove js components from the repo
* :ghpull:`3158`: IPEP 15: autosave the notebook
* :ghpull:`3252`: move images out of _static folder into _images
* :ghpull:`3251`: Fix for cell magics in Qt console
* :ghpull:`3250`: Added a simple __html__() method to the HTML class
* :ghpull:`3249`: remove copy of sphinx inheritance_diagram.py
* :ghpull:`3235`: Remove the unused print notebook view
* :ghpull:`3238`: Improve the design of the tab completion UI
* :ghpull:`3242`: Make changes of Application.log_format effective
* :ghpull:`3219`: Workaround so only one CTRL-C is required for a new prompt in --gui=qt
* :ghpull:`3190`: allow formatters to specify metadata
* :ghpull:`3231`: improve discovery of public IPs
* :ghpull:`3233`: check prefixes for swallowing kernel args
* :ghpull:`3234`: Removing old autogrow JS code.
* :ghpull:`3232`: Update to CodeMirror 3 and start to ship our components
* :ghpull:`3229`: The HTML output type accidentally got removed from the OutputArea.
* :ghpull:`3228`: Typo in IPython.Parallel documentation
* :ghpull:`3226`: Text in rename dialog was way too big - making it <p>.
* :ghpull:`3225`: Removing old restuctured text handler and web service.
* :ghpull:`3222`: make BlockingKernelClient the default Client
* :ghpull:`3223`: add missing mathjax_url to new settings dict
* :ghpull:`3089`: add stdin to the notebook
* :ghpull:`3221`: Remove references to HTMLCell (dead code)
* :ghpull:`3205`: add ignored ``*args`` to HasTraits constructor
* :ghpull:`3088`: cleanup IPython handler settings
* :ghpull:`3201`: use much faster regexp for ansi coloring
* :ghpull:`3220`: avoid race condition in profile creation
* :ghpull:`3011`: IPEP 12: add KernelClient
* :ghpull:`3217`: informative error when trying to load directories
* :ghpull:`3174`: Simple class
* :ghpull:`2979`: CM configurable Take 2
* :ghpull:`3215`: Updates storemagic extension to allow for specifying variable name to load
* :ghpull:`3181`: backport If-Modified-Since fix from tornado
* :ghpull:`3200`: IFrame (VimeoVideo, ScribdDocument, ...) 
* :ghpull:`3186`: Fix small inconsistency in nbconvert: etype -> ename
* :ghpull:`3212`: Fix issue #2563, "core.profiledir.check_startup_dir() doesn't work inside py2exe'd installation"
* :ghpull:`3211`: Fix inheritance_diagram Sphinx extension for Sphinx 1.2
* :ghpull:`3208`: Update link to extensions index
* :ghpull:`3203`: Separate InputSplitter for transforming whole cells
* :ghpull:`3189`: Improve completer
* :ghpull:`3194`: finish up PR #3116
* :ghpull:`3188`: Add new keycodes
* :ghpull:`2695`: Key the root modules cache by sys.path entries.
* :ghpull:`3182`: clarify %%file docstring
* :ghpull:`3163`: BUG: Fix the set and frozenset pretty printer to handle the empty case correctly
* :ghpull:`3180`: better UsageError for cell magic with no body
* :ghpull:`3184`: Cython cache
* :ghpull:`3175`: Added missing s
* :ghpull:`3173`: Little bits of documentation cleanup
* :ghpull:`2635`: Improve Windows start menu shortcuts (#2)
* :ghpull:`3172`: Add missing import in IPython parallel magics example
* :ghpull:`3170`: default application logger shouldn't propagate
* :ghpull:`3159`: Autocompletion for zsh
* :ghpull:`3105`: move DEFAULT_STATIC_FILES_PATH to IPython.html
* :ghpull:`3144`: minor bower tweaks
* :ghpull:`3141`: Default color output for ls on OSX
* :ghpull:`3137`: fix dot syntax error in inheritance diagram
* :ghpull:`3072`: raise UnsupportedOperation on iostream.fileno()
* :ghpull:`3147`: Notebook support for a reverse proxy which handles SSL
* :ghpull:`3152`: make qtconsole size at startup configurable
* :ghpull:`3162`: adding stream kwarg to current.new_output
* :ghpull:`2981`: IPEP 10: kernel side filtering of display formats
* :ghpull:`3058`: add redirect handler for notebooks by name
* :ghpull:`3041`: support non-modules in @require
* :ghpull:`2447`: Stateful line transformers
* :ghpull:`3108`: fix some O(N) and O(N^2) operations in parallel.map
* :ghpull:`2791`: forward stdout from forked processes
* :ghpull:`3157`: use Python 3-style for pretty-printed sets
* :ghpull:`3148`: closes #3045, #3123 for tornado < version 3.0
* :ghpull:`3143`: minor heading-link tweaks
* :ghpull:`3136`: Strip useless ANSI escape codes in notebook
* :ghpull:`3126`: Prevent errors when pressing arrow keys in an empty notebook
* :ghpull:`3135`: quick dev installation instructions
* :ghpull:`2889`: Push pandas dataframes to R magic
* :ghpull:`3068`: Don't monkeypatch doctest during IPython startup.
* :ghpull:`3133`: fix argparse version check
* :ghpull:`3102`: set `spellcheck=false` in CodeCell inputarea
* :ghpull:`3064`: add anchors to heading cells
* :ghpull:`3097`: PyQt 4.10: use self._document = self.document()
* :ghpull:`3117`: propagate automagic change to shell
* :ghpull:`3118`: don't give up on weird os names
* :ghpull:`3115`: Fix example
* :ghpull:`2640`: fix quarantine/ipy_editors.py
* :ghpull:`3070`: Add info make target that was missing in old Sphinx
* :ghpull:`3082`: A few small patches to image handling
* :ghpull:`3078`: fix regular expression for detecting links in stdout
* :ghpull:`3054`: restore default behavior for automatic cluster size
* :ghpull:`3073`: fix ipython usage text
* :ghpull:`3083`: fix DisplayMagics.html docstring
* :ghpull:`3080`: noted sub_channel being renamed to iopub_channel
* :ghpull:`3079`: actually use IPKernelApp.kernel_class
* :ghpull:`3076`: Improve notebook.js documentation
* :ghpull:`3063`: add missing `%%html` magic
* :ghpull:`3075`: check for SIGUSR1 before using it, closes #3074
* :ghpull:`3051`: add width:100% to vbox for webkit / FF consistency
* :ghpull:`2999`: increase registration timeout
* :ghpull:`2997`: fix DictDB default size limit
* :ghpull:`3033`: on resume, print server info again
* :ghpull:`3062`: test double pyximport
* :ghpull:`3046`: cast kernel cwd to bytes on Python 2 on Windows
* :ghpull:`3038`: remove xml from notebook magic docstrings
* :ghpull:`3032`: fix time format to international time format
* :ghpull:`3022`: Fix test for Windows
* :ghpull:`3024`: changed instances of 'outout' to 'output' in alt texts
* :ghpull:`3013`: py3 workaround for reload in cythonmagic
* :ghpull:`2961`: time magic: shorten unnecessary output on windows
* :ghpull:`2987`: fix local files examples in markdown
* :ghpull:`2998`: fix css in .output_area pre
* :ghpull:`3003`: add $include /etc/inputrc to suggested ~/.inputrc
* :ghpull:`2957`: Refactor qt import logic. Fixes #2955
* :ghpull:`2994`: expanduser on %%file targets
* :ghpull:`2983`: fix run-all (that-> this)
* :ghpull:`2964`: fix count when testing composite error output
* :ghpull:`2967`: shows entire session history when only startsess is given
* :ghpull:`2942`: Move CM IPython theme out of codemirror folder
* :ghpull:`2929`: Cleanup cell insertion
* :ghpull:`2933`: Minordocupdate
* :ghpull:`2968`: fix notebook deletion.
* :ghpull:`2966`: Added assert msg to extract_hist_ranges()
* :ghpull:`2959`: Add command to trim the history database.
* :ghpull:`2681`: Don't enable pylab mode, when matplotlib is not importable
* :ghpull:`2901`: Fix inputhook_wx on osx
* :ghpull:`2871`: truncate potentially long CompositeErrors
* :ghpull:`2951`: use istype on lists/tuples
* :ghpull:`2946`: fix qtconsole history logic for end-of-line
* :ghpull:`2954`: fix logic for append_javascript
* :ghpull:`2941`: fix baseUrl
* :ghpull:`2903`: Specify toggle value on cell line number
* :ghpull:`2911`: display order in output area configurable
* :ghpull:`2897`: Dont rely on BaseProjectUrl data in body tag
* :ghpull:`2894`: Cm configurable
* :ghpull:`2927`: next release will be 1.0
* :ghpull:`2932`: Simplify using notebook static files from external code
* :ghpull:`2915`: added small config section to notebook docs page
* :ghpull:`2924`: safe_run_module: Silence SystemExit codes 0 and None.
* :ghpull:`2906`: Unpatch/Monkey patch CM
* :ghpull:`2921`: add menu item for undo delete cell
* :ghpull:`2917`: Don't add logging handler if one already exists.
* :ghpull:`2910`: Respect DB_IP and DB_PORT in mongodb tests
* :ghpull:`2926`: Don't die if stderr/stdout do not support set_parent() #2925
* :ghpull:`2885`: get monospace pager back
* :ghpull:`2876`: fix celltoolbar layout on FF
* :ghpull:`2904`: Skip remaining IPC test on Windows
* :ghpull:`2908`: fix last remaining KernelApp reference
* :ghpull:`2905`: fix a few remaining KernelApp/IPKernelApp changes
* :ghpull:`2900`: Don't assume test case for %time will finish in 0 time
* :ghpull:`2893`: exclude fabfile from tests
* :ghpull:`2884`: Correct import for kernelmanager on Windows
* :ghpull:`2882`: Utils cleanup
* :ghpull:`2883`: Don't call ast.fix_missing_locations unless the AST could have been modified
* :ghpull:`2855`: time(it) magic: Implement minutes/hour formatting and "%%time" cell magic
* :ghpull:`2874`: Empty cell warnings
* :ghpull:`2819`: tweak history prefix search (up/^p) in qtconsole
* :ghpull:`2868`: Import performance
* :ghpull:`2877`: minor css fixes
* :ghpull:`2880`: update examples docs with kernel move
* :ghpull:`2878`: Pass host environment on to kernel
* :ghpull:`2599`: func_kw_complete for builtin and cython with embededsignature=True using docstring
* :ghpull:`2792`: Add key "unique" to history_request protocol
* :ghpull:`2872`: fix payload keys
* :ghpull:`2869`: Fixing styling of toolbar selects on FF.
* :ghpull:`2708`: Less css
* :ghpull:`2854`: Move kernel code into IPython.kernel
* :ghpull:`2864`: Fix %run -t -N<N> TypeError
* :ghpull:`2852`: future pyzmq compatibility
* :ghpull:`2863`: whatsnew/version0.9.txt: Fix '~./ipython' -> '~/.ipython' typo
* :ghpull:`2861`: add missing KernelManager to ConsoleApp class list
* :ghpull:`2850`: Consolidate host IP detection in utils.localinterfaces
* :ghpull:`2859`: Correct docstring of ipython.py
* :ghpull:`2831`: avoid string version comparisons in external.qt
* :ghpull:`2844`: this should address the failure in #2732
* :ghpull:`2849`: utils/data: Use list comprehension for uniq_stable()
* :ghpull:`2839`: add jinja to install docs / setup.py
* :ghpull:`2841`: Miscellaneous docs fixes
* :ghpull:`2811`: Still more KernelManager cleanup
* :ghpull:`2820`: add '=' to greedy completer delims
* :ghpull:`2818`: log user tracebacks in the kernel (INFO-level)
* :ghpull:`2828`: Clean up notebook Javascript
* :ghpull:`2829`: avoid comparison error in dictdb hub history
* :ghpull:`2830`: BUG: Opening parenthesis after non-callable raises ValueError
* :ghpull:`2718`: try to fallback to pysqlite2.dbapi2 as sqlite3 in core.history
* :ghpull:`2816`: in %edit, don't save "last_call" unless last call succeeded
* :ghpull:`2817`: change ol format order
* :ghpull:`2537`: Organize example notebooks
* :ghpull:`2815`: update release/authors
* :ghpull:`2808`: improve patience for slow Hub in client tests
* :ghpull:`2812`: remove nonfunctional `-la` short arg in cython magic
* :ghpull:`2810`: remove dead utils.upgradedir
* :ghpull:`1671`: __future__ environments
* :ghpull:`2804`: skip ipc tests on Windows
* :ghpull:`2789`: Fixing styling issues with CellToolbar.
* :ghpull:`2805`: fix KeyError creating ZMQStreams in notebook
* :ghpull:`2775`: General cleanup of kernel manager code.
* :ghpull:`2340`: Initial Code to reduce parallel.Client caching
* :ghpull:`2799`: Exit code
* :ghpull:`2800`: use `type(obj) is cls` as switch when canning
* :ghpull:`2801`: Fix a breakpoint bug
* :ghpull:`2795`: Remove outdated code from extensions.autoreload
* :ghpull:`2796`: P3K: fix cookie parsing under Python 3.x (+ duplicate import is removed)
* :ghpull:`2724`: In-process kernel support (take 3)
* :ghpull:`2687`: [WIP] Metaui slideshow
* :ghpull:`2788`: Chrome frame awareness
* :ghpull:`2649`: Add version_request/reply messaging protocol
* :ghpull:`2753`: add `%%px --local` for local execution
* :ghpull:`2783`: Prefilter shouldn't touch execution_count
* :ghpull:`2333`: UI For Metadata
* :ghpull:`2396`: create a ipynbv3 json schema and a validator
* :ghpull:`2757`: check for complete pyside presence before trying to import
* :ghpull:`2782`: Allow the %run magic with '-b' to specify a file.
* :ghpull:`2778`: P3K: fix DeprecationWarning under Python 3.x 
* :ghpull:`2776`: remove non-functional View.kill method
* :ghpull:`2755`: can interactively defined classes
* :ghpull:`2774`: Removing unused code in the notebook MappingKernelManager.
* :ghpull:`2773`: Fixed minor typo causing AttributeError to be thrown.
* :ghpull:`2609`: Add 'unique' option to history_request messaging protocol
* :ghpull:`2769`: Allow shutdown when no engines are registered
* :ghpull:`2766`: Define __file__ when we %edit a real file.
* :ghpull:`2476`: allow %edit <variable> to work when interactively defined
* :ghpull:`2763`: Reset readline delimiters after loading rmagic.
* :ghpull:`2460`: Better handling of `__file__` when running scripts.
* :ghpull:`2617`: Fix for `units` argument. Adds a `res` argument.
* :ghpull:`2738`: Unicode content crashes the pager (console)
* :ghpull:`2749`: Tell Travis CI to test on Python 3.3 as well
* :ghpull:`2744`: Don't show 'try %paste' message while using magics
* :ghpull:`2728`: shift tab for tooltip
* :ghpull:`2741`: Add note to `%cython` Black-Scholes example warning of missing erf.
* :ghpull:`2743`: BUG: Octavemagic inline plots not working on Windows: Fixed
* :ghpull:`2740`: Following #2737 this error is now a name error
* :ghpull:`2737`: Rmagic: error message when moving an non-existant variable from python to R
* :ghpull:`2723`: diverse fixes for project url
* :ghpull:`2731`: %Rpush: Look for variables in the local scope first.
* :ghpull:`2544`: Infinite loop when multiple debuggers have been attached.
* :ghpull:`2726`: Add qthelp docs creation
* :ghpull:`2730`: added blockquote CSS
* :ghpull:`2729`: Fix Read the doc build, Again
* :ghpull:`2446`: [alternate 2267] Offline mathjax
* :ghpull:`2716`: remove unexisting headings level
* :ghpull:`2717`: One liner to fix debugger printing stack traces when lines of context are larger than source.
* :ghpull:`2713`: Doc bugfix: user_ns is not an attribute of Magic objects.
* :ghpull:`2690`: Fix 'import '... completion for py3 & egg files.
* :ghpull:`2691`: Document OpenMP in %%cython magic
* :ghpull:`2699`: fix jinja2 rendering for password protected notebooks
* :ghpull:`2700`: Skip notebook testing if jinja2 is not available.
* :ghpull:`2692`: Add %%cython magics to generated documentation.
* :ghpull:`2685`: Fix pretty print of types when `__module__` is not available.
* :ghpull:`2686`: Fix tox.ini
* :ghpull:`2604`: Backslashes are misinterpreted as escape-sequences by the R-interpreter.
* :ghpull:`2689`: fix error in doc (arg->kwarg) and pep-8
* :ghpull:`2683`: for downloads, replaced window.open with window.location.assign
* :ghpull:`2659`: small bugs in js are fixed
* :ghpull:`2363`: Refactor notebook templates to use Jinja2
* :ghpull:`2662`: qtconsole: wrap argument list in tooltip to match width of text body
* :ghpull:`2328`: addition of classes to generate a link or list of links from files local to the IPython HTML notebook
* :ghpull:`2668`: pylab_not_importable: Catch all exceptions, not just RuntimeErrors.
* :ghpull:`2663`: Fix issue #2660: parsing of help and version arguments
* :ghpull:`2656`: Fix irunner tests when $PYTHONSTARTUP is set
* :ghpull:`2312`: Add bracket matching to code cells in notebook
* :ghpull:`2571`: Start to document Javascript
* :ghpull:`2641`: undefinied that -> this
* :ghpull:`2638`: Fix %paste in Python 3 on Mac
* :ghpull:`2301`: Ast transfomers
* :ghpull:`2616`: Revamp API docs
* :ghpull:`2572`: Make 'Paste Above' the default paste behavior.
* :ghpull:`2574`: Fix #2244
* :ghpull:`2582`: Fix displaying history when output cache is disabled.
* :ghpull:`2591`: Fix for Issue #2584 
* :ghpull:`2526`: Don't kill paramiko tunnels when receiving ^C
* :ghpull:`2559`: Add psource, pfile, pinfo2 commands to ipdb.
* :ghpull:`2546`: use 4 Pythons to build 4 Windows installers
* :ghpull:`2561`: Fix display of plain text containing multiple carriage returns before line feed
* :ghpull:`2549`: Add a simple 'undo' for cell deletion.
* :ghpull:`2525`: Add event to kernel execution/shell reply.
* :ghpull:`2554`: Avoid stopping in ipdb until we reach the main script.
* :ghpull:`2404`: Option to limit search result in history magic command
* :ghpull:`2294`: inputhook_qt4: Use QEventLoop instead of starting up the QCoreApplication
* :ghpull:`2233`: Refactored Drag and Drop Support in Qt Console
* :ghpull:`1747`: switch between hsplit and vsplit paging (request for feedback)
* :ghpull:`2530`: Adding time offsets to the video
* :ghpull:`2542`: Allow starting IPython as `python -m IPython`.
* :ghpull:`2534`: Do not unescape backslashes in Windows (shellglob)
* :ghpull:`2517`: Improved MathJax, bug fixes
* :ghpull:`2511`: trigger default remote_profile_dir when profile_dir is set
* :ghpull:`2491`: color is supported in ironpython
* :ghpull:`2462`: Track which extensions are loaded
* :ghpull:`2464`: Locate URLs in text output and convert them to hyperlinks.
* :ghpull:`2490`: add ZMQInteractiveShell to IPEngineApp class list
* :ghpull:`2498`: Don't catch tab press when something selected
* :ghpull:`2527`: Run All Above and Run All Below
* :ghpull:`2513`: add GitHub uploads to release script
* :ghpull:`2529`: Windows aware tests for shellglob
* :ghpull:`2478`: Fix doctest_run_option_parser for Windows
* :ghpull:`2519`: clear In[ ] prompt numbers again
* :ghpull:`2467`: Clickable links
* :ghpull:`2500`: Add `encoding` attribute to `OutStream` class.
* :ghpull:`2349`: ENH: added StackExchange-style MathJax filtering
* :ghpull:`2503`: Fix traceback handling of SyntaxErrors without line numbers.
* :ghpull:`2492`: add missing 'qtconsole' extras_require
* :ghpull:`2480`: Add deprecation warnings for sympyprinting
* :ghpull:`2334`: Make the ipengine monitor the ipcontroller heartbeat and die if the ipcontroller goes down
* :ghpull:`2479`: use new _winapi instead of removed _subprocess
* :ghpull:`2474`: fix bootstrap name conflicts
* :ghpull:`2469`: Treat __init__.pyc same as __init__.py in module_list
* :ghpull:`2165`: Add -g option to %run to glob expand arguments
* :ghpull:`2468`: Tell git to ignore __pycache__ directories.
* :ghpull:`2421`: Some notebook tweaks.
* :ghpull:`2291`: Remove old plugin system
* :ghpull:`2127`: Ability to build toolbar in JS 
* :ghpull:`2445`: changes for ironpython
* :ghpull:`2420`: Pass ipython_dir to __init__() method of TerminalInteractiveShell's superclass.
* :ghpull:`2432`: Revert #1831, the `__file__` injection in safe_execfile / safe_execfile_ipy.
* :ghpull:`2216`: Autochange highlight with cell magics
* :ghpull:`1946`: Add image message handler in ZMQTerminalInteractiveShell
* :ghpull:`2424`: skip find_cmd when setting up script magics
* :ghpull:`2389`: Catch sqlite DatabaseErrors in more places when reading the history database
* :ghpull:`2395`: Don't catch ImportError when trying to unpack module functions
* :ghpull:`1868`: enable IPC transport for kernels
* :ghpull:`2437`: don't let log cleanup prevent engine start
* :ghpull:`2441`: `sys.maxsize` is the maximum length of a container.
* :ghpull:`2442`: allow iptest to be interrupted
* :ghpull:`2240`: fix message built for engine dying during task
* :ghpull:`2369`: Block until kernel termination after sending a kill signal
* :ghpull:`2439`: Py3k: Octal (0777 -> 0o777)
* :ghpull:`2326`: Detachable pager in notebook.
* :ghpull:`2377`: Fix installation of man pages in Python 3
* :ghpull:`2407`: add IPython version to message headers
* :ghpull:`2408`: Fix Issue #2366
* :ghpull:`2405`: clarify TaskScheduler.hwm doc
* :ghpull:`2399`: IndentationError display
* :ghpull:`2400`: Add scroll_to_cell(cell_number) to the notebook
* :ghpull:`2401`: unmock read-the-docs modules
* :ghpull:`2311`: always perform requested trait assignments
* :ghpull:`2393`: New option `n` to limit history search hits
* :ghpull:`2386`: Adapt inline backend to changes in matplotlib
* :ghpull:`2392`: Remove suspicious double quote
* :ghpull:`2387`: Added -L library search path to cythonmagic cell magic
* :ghpull:`2370`: qtconsole: Create a prompt newline by inserting a new block (w/o formatting)
* :ghpull:`1715`: Fix for #1688, traceback-unicode issue
* :ghpull:`2378`: use Singleton.instance() for embed() instead of manual global
* :ghpull:`2373`: fix missing imports in core.interactiveshell
* :ghpull:`2368`: remove notification widget leftover
* :ghpull:`2327`: Parallel: Support get/set of nested objects in view (e.g. dv['a.b'])
* :ghpull:`2362`: Clean up ProgressBar class in example notebook
* :ghpull:`2346`: Extra xterm identification in set_term_title
* :ghpull:`2352`: Notebook: Store the username in a cookie whose name is unique.
* :ghpull:`2358`: add backport_pr to tools
* :ghpull:`2365`: fix names of notebooks for download/save
* :ghpull:`2364`: make clients use 'location' properly (fixes #2361)
* :ghpull:`2354`: Refactor notebook templates to use Jinja2
* :ghpull:`2339`: add bash completion example
* :ghpull:`2345`: Remove references to 'version' no longer in argparse. Github issue #2343.
* :ghpull:`2347`: adjust division error message checking to account for Python 3
* :ghpull:`2305`: RemoteError._render_traceback_ calls self.render_traceback
* :ghpull:`2338`: Normalize line endings for ipexec_validate, fix for #2315.
* :ghpull:`2192`: Introduce Notification Area
* :ghpull:`2329`: Better error messages for common magic commands.
* :ghpull:`2337`: ENH: added StackExchange-style MathJax filtering
* :ghpull:`2331`: update css for qtconsole in doc
* :ghpull:`2317`: adding cluster_id to parallel.Client.__init__
* :ghpull:`2130`: Add -l option to %R magic to allow passing in of local namespace
* :ghpull:`2196`: Fix for bad command line argument to latex
* :ghpull:`2300`: bug fix: was crashing when sqlite3 is not installed
* :ghpull:`2184`: Expose store_history to execute_request messages.
* :ghpull:`2308`: Add welcome_message option to enable_pylab
* :ghpull:`2302`: Fix variable expansion on 'self'
* :ghpull:`2299`: Remove code from prefilter that duplicates functionality in inputsplitter
* :ghpull:`2295`: allow pip install from github repository directly
* :ghpull:`2280`: fix SSH passwordless check for OpenSSH
* :ghpull:`2290`: nbmanager
* :ghpull:`2288`: s/assertEquals/assertEqual (again)
* :ghpull:`2287`: Removed outdated dev docs.
* :ghpull:`2218`: Use redirect for new notebooks
* :ghpull:`2277`: nb: up/down arrow keys move to begin/end of line at top/bottom of cell
* :ghpull:`2045`: Refactoring notebook managers and adding Azure backed storage.
* :ghpull:`2271`: use display instead of send_figure in inline backend hooks
* :ghpull:`2278`: allow disabling SQLite history
* :ghpull:`2225`: Add "--annotate" option to `%%cython` magic.
* :ghpull:`2246`: serialize individual args/kwargs rather than the containers
* :ghpull:`2274`: CLN: Use name to id mapping of notebooks instead of searching.
* :ghpull:`2270`: SSHLauncher tweaks
* :ghpull:`2269`: add missing location when disambiguating controller IP
* :ghpull:`2263`: Allow docs to build on http://readthedocs.org/
* :ghpull:`2256`: Adding data publication example notebook.
* :ghpull:`2255`: better flush iopub with AsyncResults
* :ghpull:`2261`: Fix: longest_substr([]) -> ''
* :ghpull:`2260`: fix mpr again
* :ghpull:`2242`: Document globbing in `%history -g <pattern>`.
* :ghpull:`2250`: fix html in notebook example
* :ghpull:`2245`: Fix regression in embed() from pull-request #2096.
* :ghpull:`2248`: track sha of master in test_pr messages
* :ghpull:`2238`: Fast tests
* :ghpull:`2211`: add data publication message
* :ghpull:`2236`: minor test_pr tweaks
* :ghpull:`2231`: Improve Image format validation and add html width,height
* :ghpull:`2232`: Reapply monkeypatch to inspect.findsource()
* :ghpull:`2235`: remove spurious print statement from setupbase.py
* :ghpull:`2222`: adjust how canning deals with import strings
* :ghpull:`2224`: fix css typo
* :ghpull:`2223`: Custom tracebacks
* :ghpull:`2214`: use KernelApp.exec_lines/files in IPEngineApp
* :ghpull:`2199`: Wrap JS published by %%javascript in try/catch
* :ghpull:`2212`: catch errors in markdown javascript
* :ghpull:`2190`: Update code mirror 2.22 to 2.32
* :ghpull:`2200`: documentation build broken in bb429da5b
* :ghpull:`2194`: clean nan/inf in json_clean
* :ghpull:`2198`: fix mpr for earlier git version
* :ghpull:`2175`: add FileFindHandler for Notebook static files
* :ghpull:`1990`: can func_defaults
* :ghpull:`2069`: start improving serialization in parallel code
* :ghpull:`2202`: Create a unique & temporary IPYTHONDIR for each testing group.
* :ghpull:`2204`: Work around lack of os.kill in win32.
* :ghpull:`2148`: win32 iptest: Use subprocess.Popen() instead of os.system().
* :ghpull:`2179`: Pylab switch
* :ghpull:`2124`: Add an API for registering magic aliases.
* :ghpull:`2169`: ipdb: pdef, pdoc, pinfo magics all broken
* :ghpull:`2174`: Ensure consistent indentation in `%magic`.
* :ghpull:`1930`: add size-limiting to the DictDB backend
* :ghpull:`2189`: Fix IPython.lib.latextools for Python 3
* :ghpull:`2186`: removed references to h5py dependence in octave magic documentation
* :ghpull:`2183`: Include the kernel object in the event object passed to kernel events
* :ghpull:`2185`: added test for %store, fixed storemagic
* :ghpull:`2138`: Use breqn.sty in dvipng backend if possible
* :ghpull:`2182`: handle undefined param in notebooklist
* :ghpull:`1831`: fix #1814 set __file__ when running .ipy files
* :ghpull:`2051`: Add a metadata attribute to messages
* :ghpull:`1471`: simplify IPython.parallel connections and enable Controller Resume
* :ghpull:`2181`: add %%javascript, %%svg, and %%latex display magics
* :ghpull:`2116`: different images in 00_notebook-tour
* :ghpull:`2092`: %prun: Restore `stats.stream` after running `print_stream`.
* :ghpull:`2159`: show message on notebook list if server is unreachable
* :ghpull:`2176`: fix git mpr
* :ghpull:`2152`: [qtconsole] Namespace not empty at startup
* :ghpull:`2177`: remove numpy install from travis/tox scripts
* :ghpull:`2090`: New keybinding for code cell execution + cell insertion
* :ghpull:`2160`: Updating the parallel options pricing example
* :ghpull:`2168`: expand line in cell magics
* :ghpull:`2170`: Fix tab completion with IPython.embed_kernel().
* :ghpull:`2096`: embed(): Default to the future compiler flags of the calling frame.
* :ghpull:`2163`: fix 'remote_profie_dir' typo in SSH launchers
* :ghpull:`2158`: [2to3 compat ] Tuple params in func defs
* :ghpull:`2089`: Fix unittest DeprecationWarnings
* :ghpull:`2142`: Refactor test_pr.py
* :ghpull:`2140`: 2to3: Apply `has_key` fixer.
* :ghpull:`2131`: Add option append (-a) to %save
* :ghpull:`2117`: use explicit url in notebook example
* :ghpull:`2133`: Tell git that ``*.py`` files contain Python code, for use in word-diffs.
* :ghpull:`2134`: Apply 2to3 `next` fix.
* :ghpull:`2126`: ipcluster broken with any batch launcher (PBS/LSF/SGE)
* :ghpull:`2104`: Windows make file for Sphinx documentation
* :ghpull:`2074`: Make BG color of inline plot configurable
* :ghpull:`2123`: BUG: Look up the `_repr_pretty_` method on the class within the MRO rath...
* :ghpull:`2100`: [in progress] python 2 and 3 compatibility without 2to3, second try
* :ghpull:`2128`: open notebook copy in different tabs
* :ghpull:`2073`: allows password and prefix for notebook
* :ghpull:`1993`: Print View
* :ghpull:`2086`: re-aliad %ed to %edit in qtconsole
* :ghpull:`2110`: Fixes and improvements to the input splitter
* :ghpull:`2101`: fix completer deletting newline
* :ghpull:`2102`: Fix logging on interactive shell.
* :ghpull:`2088`: Fix (some) Python 3.2 ResourceWarnings
* :ghpull:`2064`: conform to pep 3110
* :ghpull:`2076`: Skip notebook 'static' dir in test suite.
* :ghpull:`2063`: Remove umlauts so py3 installations on LANG=C systems succeed.
* :ghpull:`2068`: record sysinfo in sdist
* :ghpull:`2067`: update tools/release_windows.py
* :ghpull:`2065`: Fix parentheses typo
* :ghpull:`2062`: Remove duplicates and auto-generated files from repo.
* :ghpull:`2061`: use explicit tuple in exception
* :ghpull:`2060`: change minus to \- or \(hy in manpages

Issues (691):

* :ghissue:`3940`: Install process documentation overhaul 
* :ghissue:`3946`: The PDF option for `--post` should work with lowercase 
* :ghissue:`3957`: Notebook help page broken in Firefox
* :ghissue:`3894`: nbconvert test failure
* :ghissue:`3887`: 1.0.0a1 shows blank screen in both firefox and chrome (windows 7)
* :ghissue:`3703`: `nbconvert`: Output options -- names and documentataion
* :ghissue:`3931`: Tab completion not working during debugging in the notebook
* :ghissue:`3936`: Ipcluster plugin is not working with Ipython 1.0dev
* :ghissue:`3941`: IPython Notebook kernel crash on Win7x64
* :ghissue:`3926`: Ending Notebook renaming dialog with return creates new-line
* :ghissue:`3932`: Incorrect empty docstring
* :ghissue:`3928`: Passing variables to script from the workspace
* :ghissue:`3774`: Notebooks with spaces in their names breaks nbconvert latex graphics
* :ghissue:`3916`: tornado needs its own check
* :ghissue:`3915`: Link to Parallel examples "found on GitHub" broken in docs
* :ghissue:`3895`: Keyboard shortcuts box in notebook doesn't fit the screen
* :ghissue:`3912`: IPython.utils fails automated test for RC1 1.0.0
* :ghissue:`3636`: Code cell missing highlight on load
* :ghissue:`3897`: under Windows, "ipython3 nbconvert "C:/blabla/first_try.ipynb" --to latex --post PDF" POST processing action fails because of a bad parameter
* :ghissue:`3900`: python3 install syntax errors (OS X 10.8.4)
* :ghissue:`3899`: nbconvert to latex fails on notebooks with spaces in file name
* :ghissue:`3881`: Temporary Working Directory Test Fails
* :ghissue:`2750`: A way to freeze code cells in the notebook
* :ghissue:`3893`: Resize Local Image Files in Notebook doesn't work
* :ghissue:`3823`: nbconvert on windows: tex and paths
* :ghissue:`3885`: under Windows, "ipython3 nbconvert "C:/blabla/first_try.ipynb" --to latex" write "\" instead of "/" to reference file path in the .tex file
* :ghissue:`3889`: test_qt fails due to assertion error 'qt4' != 'qt'
* :ghissue:`3890`: double post, disregard this issue
* :ghissue:`3689`: nbconvert, remaining tests
* :ghissue:`3874`: Up/Down keys don't work to "Search previous command history" (besides Ctrl-p/Ctrl-n)
* :ghissue:`3853`: CodeMirror locks up in the notebook
* :ghissue:`3862`: can only connect to an ipcluster started with v1.0.0-dev (master branch) using an older ipython (v0.13.2), but cannot connect using ipython (v1.0.0-dev)
* :ghissue:`3869`: custom css not working. 
* :ghissue:`2960`: Keyboard shortcuts
* :ghissue:`3795`: ipcontroller process goes to 100% CPU, ignores connection requests
* :ghissue:`3553`: Ipython and pylab crashes in windows and canopy
* :ghissue:`3837`: Cannot set custom mathjax url, crash notebook server.
* :ghissue:`3808`: "Naming" releases ?
* :ghissue:`2431`: TypeError: must be string without null bytes, not str
* :ghissue:`3856`: `?` at end of comment causes line to execute
* :ghissue:`3731`: nbconvert: add logging for the different steps of nbconvert
* :ghissue:`3835`: Markdown cells do not render correctly when mathjax is disabled
* :ghissue:`3843`: nbconvert to rst: leftover "In[ ]"
* :ghissue:`3799`: nbconvert: Ability to specify name of output file
* :ghissue:`3726`: Document when IPython.start_ipython() should be used versus IPython.embed()
* :ghissue:`3778`: Add no more readonly view in what's new
* :ghissue:`3754`: No Print View in Notebook in 1.0dev
* :ghissue:`3798`: IPython 0.12.1 Crashes on autocompleting sqlalchemy.func.row_number properties
* :ghissue:`3811`: Opening notebook directly from the command line with multi-directory support installed
* :ghissue:`3775`: Annoying behavior when clicking on cell after execution (Ctrl+Enter)
* :ghissue:`3809`: Possible to add some bpython features?
* :ghissue:`3810`: Printing the contents of an image file messes up shell text
* :ghissue:`3702`: `nbconvert`: Default help message should be that of --help
* :ghissue:`3735`: Nbconvert 1.0.0a1 does not take into account the pdf extensions in graphs
* :ghissue:`3719`: Bad strftime format, for windows, in nbconvert exporter 
* :ghissue:`3786`: Zmq errors appearing with `Ctrl-C` in console/qtconsole
* :ghissue:`3019`: disappearing scrollbar on tooltip in Chrome 24 on Ubuntu 12.04
* :ghissue:`3785`: ipdb completely broken in Qt console
* :ghissue:`3796`: Document the meaning of milestone/issues-tags for users.
* :ghissue:`3788`: Do not auto show tooltip if docstring empty.
* :ghissue:`1366`: [Web page] No link to front page from documentation
* :ghissue:`3739`: nbconvert (to slideshow) misses some of the math in markdown cells
* :ghissue:`3768`: increase and make timeout configurable in console completion.
* :ghissue:`3724`: ipcluster only running on one cpu
* :ghissue:`1592`: better message for unsupported nbformat
* :ghissue:`2049`: Can not stop "ipython kernel" on windows
* :ghissue:`3757`: Need direct entry point to given notebook 
* :ghissue:`3745`: ImportError: cannot import name check_linecache_ipython
* :ghissue:`3701`: `nbconvert`: Final output file should be in same directory as input file
* :ghissue:`3738`: history -o works but history with -n produces identical results
* :ghissue:`3740`: error when attempting to run 'make' in docs directory
* :ghissue:`3737`: ipython nbconvert crashes with ValueError: Invalid format string.
* :ghissue:`3730`: nbconvert: unhelpful error when pandoc isn't installed
* :ghissue:`3718`: markdown cell cursor misaligned in notebook
* :ghissue:`3710`: mutiple input fields for %debug in the notebook after resetting the kernel
* :ghissue:`3713`: PyCharm has problems with IPython working inside PyPy created by virtualenv
* :ghissue:`3712`: Code completion: Complete on dictionary keys
* :ghissue:`3680`: --pylab and --matplotlib flag
* :ghissue:`3698`: nbconvert: Unicode error with minus sign
* :ghissue:`3693`: nbconvert does not process SVGs into PDFs
* :ghissue:`3688`: nbconvert, figures not extracting with Python 3.x
* :ghissue:`3542`: note new dependencies in docs / setup.py
* :ghissue:`2556`: [pagedown] do not target_blank anchor link
* :ghissue:`3684`: bad message when %pylab fails due import *other* than matplotlib
* :ghissue:`3682`: ipython notebook pylab inline  import_all=False 
* :ghissue:`3596`: MathjaxUtils race condition?
* :ghissue:`1540`: Comment/uncomment selection in notebook
* :ghissue:`2702`: frozen setup: permission denied for default ipython_dir
* :ghissue:`3672`: allow_none on Number-like traits.
* :ghissue:`2411`: add CONTRIBUTING.md
* :ghissue:`481`: IPython terminal issue with Qt4Agg on XP SP3
* :ghissue:`2664`: How to preserve user variables from import clashing?
* :ghissue:`3436`: enable_pylab(import_all=False) still imports np
* :ghissue:`2630`: lib.pylabtools.figsize : NameError when using Qt4Agg backend and %pylab magic. 
* :ghissue:`3154`: Notebook: no event triggered when a Cell is created
* :ghissue:`3579`: Nbconvert: SVG are not transformed to PDF anymore
* :ghissue:`3604`: MathJax rendering problem in `%%latex` cell
* :ghissue:`3668`: AttributeError: 'BlockingKernelClient' object has no attribute 'started_channels'
* :ghissue:`3245`: SyntaxError: encoding declaration in Unicode string
* :ghissue:`3639`: %pylab inline in IPYTHON notebook throws "RuntimeError: Cannot activate multiple GUI eventloops"
* :ghissue:`3663`: frontend deprecation warnings
* :ghissue:`3661`: run -m not behaving like python -m 
* :ghissue:`3597`: re-do PR #3531 - allow markdown in Header cell
* :ghissue:`3053`: Markdown in header cells is not rendered
* :ghissue:`3655`: IPython finding its way into pasted strings. 
* :ghissue:`3620`: uncaught errors in HTML output
* :ghissue:`3646`: get_dict() error
* :ghissue:`3004`: `%load_ext rmagic` fails when legacy ipy_user_conf.py is installed (in ipython 0.13.1 / OSX 10.8)
* :ghissue:`3638`: setp() issue in ipython notebook with figure references
* :ghissue:`3634`: nbconvert reveal to pdf conversion ignores styling, prints only a single page.
* :ghissue:`1307`: Remove pyreadline workarounds, we now require pyreadline >= 1.7.1
* :ghissue:`3316`: find_cmd test failure on Windows
* :ghissue:`3494`: input() in notebook doesn't work in Python 3
* :ghissue:`3427`: Deprecate `$` as mathjax delimiter
* :ghissue:`3625`: Pager does not open from button
* :ghissue:`3149`: Miscellaneous small nbconvert feedback
* :ghissue:`3617`: 256 color escapes support
* :ghissue:`3609`: %pylab inline blows up for single process ipython
* :ghissue:`2934`: Publish the Interactive MPI Demo Notebook
* :ghissue:`3614`: ansi escapes broken in master (ls --color)
* :ghissue:`3610`: If you don't have markdown, python setup.py install says no pygments
* :ghissue:`3547`: %run modules clobber each other
* :ghissue:`3602`: import_item fails when one tries to use DottedObjectName instead of a string
* :ghissue:`3563`: Duplicate tab completions in the notebook
* :ghissue:`3599`: Problems trying to run IPython on python3 without installing...
* :ghissue:`2937`: too long completion in notebook
* :ghissue:`3479`: Write empty name for the notebooks
* :ghissue:`3505`: nbconvert: Failure in specifying user filter
* :ghissue:`1537`: think a bit about namespaces
* :ghissue:`3124`: Long multiline strings in Notebook
* :ghissue:`3464`: run -d message unclear
* :ghissue:`2706`: IPython 0.13.1 ignoring $PYTHONSTARTUP
* :ghissue:`3587`: LaTeX escaping bug in nbconvert when exporting to HTML
* :ghissue:`3213`: Long running notebook died with a coredump
* :ghissue:`3580`: Running ipython with pypy on windows
* :ghissue:`3573`: custom.js not working
* :ghissue:`3544`: IPython.lib test failure on Windows
* :ghissue:`3352`: Install Sphinx extensions
* :ghissue:`2971`: [notebook]user needs to press ctrl-c twice to stop notebook server should be put into terminal window
* :ghissue:`2413`: ipython3 qtconsole fails to install: ipython 0.13 has no such extra feature 'qtconsole' 
* :ghissue:`2618`: documentation is incorrect for install process
* :ghissue:`2595`: mac 10.8 qtconsole export history
* :ghissue:`2586`: cannot store aliases
* :ghissue:`2714`: ipython qtconsole print unittest messages in console instead his own window. 
* :ghissue:`2669`: cython magic failing to work with openmp.
* :ghissue:`3256`: Vagrant pandas instance of iPython Notebook does not respect additional plotting arguments
* :ghissue:`3010`: cython magic fail if cache dir is deleted while in session
* :ghissue:`2044`: prune unused names from parallel.error
* :ghissue:`1145`: Online help utility broken in QtConsole
* :ghissue:`3439`: Markdown links no longer open in new window (with change from pagedown to marked)
* :ghissue:`3476`:  _margv  for macros seems to be missing
* :ghissue:`3499`: Add reveal.js library (version 2.4.0) inside IPython
* :ghissue:`2771`: Wiki Migration to GitHub
* :ghissue:`2887`: ipcontroller purging some engines during connect
* :ghissue:`626`: Enable Resuming Controller
* :ghissue:`2824`: Kernel restarting after message "Kernel XXXX failed to respond to heartbeat"
* :ghissue:`2823`: %%cython magic gives ImportError: dlopen(long_file_name.so, 2): image not found
* :ghissue:`2891`: In IPython for Python 3, system site-packages comes before user site-packages
* :ghissue:`2928`: Add magic "watch" function (example)
* :ghissue:`2931`: Problem rendering pandas dataframe in  Firefox for Windows
* :ghissue:`2939`: [notebook] Figure legend not shown in inline backend if ouside the box of the axes
* :ghissue:`2972`: [notebook] in Markdown mode, press Enter key at the end of <some http link>, the next line is indented unexpectly
* :ghissue:`3069`: Instructions for installing IPython notebook on Windows
* :ghissue:`3444`: Encoding problem: cannot use if user's name is not ascii?
* :ghissue:`3335`: Reenable bracket matching
* :ghissue:`3386`: Magic %paste not working in Python 3.3.2. TypeError: Type str doesn't support the buffer API
* :ghissue:`3543`: Exception shutting down kernel from notebook dashboard (0.13.1)
* :ghissue:`3549`: Codecell size changes with selection
* :ghissue:`3445`: Adding newlines in %%latex cell
* :ghissue:`3237`: [notebook] Can't close a notebook without errors
* :ghissue:`2916`: colon invokes auto(un)indent in markdown cells
* :ghissue:`2167`: Indent and dedent in htmlnotebook
* :ghissue:`3545`: Notebook save button icon not clear
* :ghissue:`3534`: nbconvert incompatible with Windows?
* :ghissue:`3489`: Update example notebook that raw_input is allowed
* :ghissue:`3396`: Notebook checkpoint time is displayed an hour out
* :ghissue:`3261`: Empty revert to checkpoint menu if no checkpoint...
* :ghissue:`2984`: "print" magic does not work in Python 3
* :ghissue:`3524`: Issues with pyzmq and ipython on EPD update
* :ghissue:`2434`: %store magic not auto-restoring
* :ghissue:`2720`: base_url and static path
* :ghissue:`2234`: Update various low resolution graphics for retina displays
* :ghissue:`2842`: Remember passwords for pw-protected notebooks
* :ghissue:`3244`: qtconsole: ValueError('close_fds is not supported on Windows platforms if you redirect stdin/stdout/stderr',)
* :ghissue:`2215`: AsyncResult.wait(0) can hang waiting for the client to get results?
* :ghissue:`2268`: provide mean to retrieve static data path
* :ghissue:`1905`: Expose UI for worksheets within each notebook
* :ghissue:`2380`: Qt inputhook prevents modal dialog boxes from displaying
* :ghissue:`3185`: prettify on double //
* :ghissue:`2821`: Test failure: IPython.parallel.tests.test_client.test_resubmit_header
* :ghissue:`2475`: [Notebook] Line is deindented when typing eg a colon in markdown mode
* :ghissue:`2470`: Do not destroy valid notebooks
* :ghissue:`860`: Allow the standalone export of a notebook to HTML
* :ghissue:`2652`: notebook with qt backend crashes at save image location popup
* :ghissue:`1587`: Improve kernel restarting in the notebook
* :ghissue:`2710`: Saving a plot in Mac OS X backend crashes IPython
* :ghissue:`2596`: notebook "Last saved:" is misleading on file opening.
* :ghissue:`2671`: TypeError :NoneType when executed "ipython qtconsole" in windows console
* :ghissue:`2703`: Notebook scrolling breaks after pager is shown
* :ghissue:`2803`: KernelManager and KernelClient should be two separate objects
* :ghissue:`2693`: TerminalIPythonApp configuration fails without ipython_config.py
* :ghissue:`2531`: IPython 0.13.1 python 2 32-bit installer includes 64-bit ipython*.exe launchers in the scripts folder
* :ghissue:`2520`: Control-C kills port forwarding
* :ghissue:`2279`: Setting `__file__` to None breaks Mayavi import
* :ghissue:`2161`: When logged into notebook, long titles are incorrectly positioned
* :ghissue:`1292`: Notebook, Print view should not be editable...
* :ghissue:`1731`: test parallel launchers
* :ghissue:`3227`: Improve documentation of ipcontroller and possible BUG
* :ghissue:`2896`: IPController very unstable
* :ghissue:`3517`: documentation build broken in head
* :ghissue:`3522`: UnicodeDecodeError: 'ascii' codec can't decode byte on Pycharm on Windows
* :ghissue:`3448`: Please include MathJax fonts with IPython Notebook
* :ghissue:`3519`: IPython Parallel map mysteriously turns pandas Series into numpy ndarray
* :ghissue:`3345`: IPython embedded shells ask if I want to exit, but I set confirm_exit = False
* :ghissue:`3509`: IPython won't close without asking "Are you sure?" in Firefox 
* :ghissue:`3471`: Notebook jinja2/markupsafe depedencies in manual
* :ghissue:`3502`: Notebook broken in master
* :ghissue:`3302`: autoreload does not work in ipython 0.13.x, python 3.3
* :ghissue:`3475`: no warning when leaving/closing notebook on master without saved changes
* :ghissue:`3490`: No obvious feedback when kernel crashes
* :ghissue:`1912`: Move all autoreload tests to their own group
* :ghissue:`2577`: sh.py and ipython for python 3.3
* :ghissue:`3467`: %magic doesn't work
* :ghissue:`3501`: Editing markdown cells that wrap has off-by-one errors in cursor positioning
* :ghissue:`3492`: IPython for Python3
* :ghissue:`3474`: unexpected keyword argument to remove_kernel
* :ghissue:`2283`: TypeError when using '?' after a string in a %logstart session
* :ghissue:`2787`: rmagic and pandas DataFrame
* :ghissue:`2605`: Ellipsis literal triggers AttributeError
* :ghissue:`1179`: Test unicode source in pinfo
* :ghissue:`2055`: drop Python 3.1 support
* :ghissue:`2293`: IPEP 2: Input transformations
* :ghissue:`2790`: %paste and %cpaste not removing "..." lines
* :ghissue:`3480`: Testing fails because iptest.py cannot be found
* :ghissue:`2580`: will not run within PIL build directory
* :ghissue:`2797`: RMagic, Dataframe Conversion Problem 
* :ghissue:`2838`: Empty lines disappear from triple-quoted literals.
* :ghissue:`3050`: Broken link on IPython.core.display page
* :ghissue:`3473`: Config not passed down to subcommands
* :ghissue:`3462`: Setting log_format in config file results in error (and no format changes)
* :ghissue:`3311`: Notebook (occasionally) not working on windows (Sophos AV)
* :ghissue:`3461`: Cursor positioning off by a character in auto-wrapped lines
* :ghissue:`3454`:  _repr_html_ error
* :ghissue:`3457`: Space in long Paragraph Markdown cell with Chinese or Japanese
* :ghissue:`3447`: Run Cell Does not Work
* :ghissue:`1373`: Last lines in long cells are hidden
* :ghissue:`1504`: Revisit serialization in IPython.parallel
* :ghissue:`1459`: Can't connect to 2 HTTPS notebook servers on the same host
* :ghissue:`678`: Input prompt stripping broken with multiline data structures
* :ghissue:`3001`: IPython.notebook.dirty flag is not set when a cell has unsaved changes
* :ghissue:`3077`: Multiprocessing semantics in parallel.view.map
* :ghissue:`3056`: links across notebooks
* :ghissue:`3120`: Tornado 3.0
* :ghissue:`3156`: update pretty to use Python 3 style for sets
* :ghissue:`3197`: Can't escape multiple dollar signs in a markdown cell
* :ghissue:`3309`: `Image()` signature/doc improvements
* :ghissue:`3415`: Bug in IPython/external/path/__init__.py 
* :ghissue:`3446`: Feature suggestion: Download matplotlib figure to client browser
* :ghissue:`3295`: autoexported notebooks: only export explicitly marked cells
* :ghissue:`3442`: Notebook: Summary table extracted from markdown headers
* :ghissue:`3438`: Zooming notebook in chrome is broken in master 
* :ghissue:`1378`: Implement autosave in notebook
* :ghissue:`3437`: Highlighting matching parentheses
* :ghissue:`3435`: module search segfault
* :ghissue:`3424`: ipcluster --version
* :ghissue:`3434`: 0.13.2 Ipython/genutils.py doesn't exist
* :ghissue:`3426`: Feature request: Save by cell and not by line #: IPython %save magic
* :ghissue:`3412`: Non Responsive Kernel: Running a Django development server from an IPython Notebook
* :ghissue:`3408`: Save cell toolbar and slide type metadata in notebooks
* :ghissue:`3246`: %paste regression with blank lines
* :ghissue:`3404`: Weird error with $variable and grep in command line magic (!command)
* :ghissue:`3405`: Key auto-completion in dictionaries?
* :ghissue:`3259`: Codemirror linenumber css broken
* :ghissue:`3397`: Vertical text misalignment in Markdown cells
* :ghissue:`3391`: Revert #3358 once fix integrated into CM
* :ghissue:`3360`: Error 500 while saving IPython notebook
* :ghissue:`3375`: Frequent Safari/Webkit crashes
* :ghissue:`3365`: zmq frontend
* :ghissue:`2654`: User_expression issues
* :ghissue:`3389`: Store history as plain text
* :ghissue:`3388`: Ipython parallel: open TCP connection created for each result returned from engine
* :ghissue:`3385`: setup.py failure on Python 3
* :ghissue:`3376`: Setting `__module__` to None breaks pretty printing
* :ghissue:`3374`: ipython qtconsole does not display the prompt on OSX
* :ghissue:`3380`: simple call to kernel
* :ghissue:`3379`: TaskRecord key 'started' not set
* :ghissue:`3241`: notebook conection time out
* :ghissue:`3334`: magic interpreter interpretes non magic commands?
* :ghissue:`3326`: python3.3: Type error when launching SGE cluster in IPython notebook
* :ghissue:`3349`: pip3 doesn't run 2to3?
* :ghissue:`3347`: Longlist support in ipdb
* :ghissue:`3343`: Make pip install / easy_install faster
* :ghissue:`3337`: git submodules broke nightly PPA builds
* :ghissue:`3206`: Copy/Paste Regression in QtConsole
* :ghissue:`3329`: Buggy linewrap in Mac OSX Terminal (Mountain Lion)
* :ghissue:`3327`: Qt version check broken
* :ghissue:`3303`: parallel tasks never finish under heavy load
* :ghissue:`1381`: '\\' for equation continuations require an extra '\' in markdown cells
* :ghissue:`3314`: Error launching iPython
* :ghissue:`3306`: Test failure when running on a Vagrant VM
* :ghissue:`3280`: IPython.utils.process.getoutput returns stderr
* :ghissue:`3299`: variables named _ or __ exhibit incorrect behavior
* :ghissue:`3196`: add an "x" or similar to htmlnotebook pager
* :ghissue:`3293`: Several 404 errors for js files Firefox
* :ghissue:`3292`: syntax highlighting in chrome on OSX 10.8.3
* :ghissue:`3288`: Latest dev version hangs on page load
* :ghissue:`3283`: ipython dev retains directory information after directory change
* :ghissue:`3279`: custom.css is not overridden in the dev IPython (1.0)
* :ghissue:`2727`: %run -m doesn't support relative imports
* :ghissue:`3268`: GFM triple backquote and unknown language
* :ghissue:`3273`: Suppressing all plot related outputs
* :ghissue:`3272`: Backspace while completing load previous page
* :ghissue:`3260`: Js error in savewidget
* :ghissue:`3247`: scrollbar in notebook when not needed?
* :ghissue:`3243`: notebook: option to view json source from browser
* :ghissue:`3265`: 404 errors when running IPython 1.0dev 
* :ghissue:`3257`: setup.py not finding submodules
* :ghissue:`3253`: Incorrect Qt and PySide version comparison
* :ghissue:`3248`: Cell magics broken in Qt console
* :ghissue:`3012`: Problems with the less based style.min.css
* :ghissue:`2390`: Image width/height don't work in embedded images
* :ghissue:`3236`: cannot set TerminalIPythonApp.log_format
* :ghissue:`3214`: notebook kernel dies if started with invalid parameter
* :ghissue:`2980`: Remove HTMLCell ?
* :ghissue:`3128`: qtconsole hangs on importing pylab (using X forwarding)
* :ghissue:`3198`: Hitting recursive depth causing all notebook pages to hang
* :ghissue:`3218`: race conditions in profile directory creation
* :ghissue:`3177`: OverflowError execption in handlers.py
* :ghissue:`2563`: core.profiledir.check_startup_dir() doesn't work inside py2exe'd installation
* :ghissue:`3207`: [Feature] folders for ipython notebook dashboard
* :ghissue:`3178`: cell magics do not work with empty lines after #2447
* :ghissue:`3204`: Default plot() colors unsuitable for red-green colorblind users
* :ghissue:`1789`: ``:\n/*foo`` turns into ``:\n*(foo)`` in triple-quoted strings.
* :ghissue:`3202`: File cell magic fails with blank lines
* :ghissue:`3199`: %%cython -a stopped working?
* :ghissue:`2688`: obsolete imports in import autocompletion
* :ghissue:`3192`: Python2, Unhandled exception, __builtin__.True = False
* :ghissue:`3179`: script magic error message loop
* :ghissue:`3009`: use XDG_CACHE_HOME for cython objects
* :ghissue:`3059`: Bugs in 00_notebook_tour example.
* :ghissue:`3104`: Integrate a javascript file manager into the notebook front end
* :ghissue:`3176`: Particular equation not rendering  (notebook)
* :ghissue:`1133`: [notebook] readonly and upload files/UI
* :ghissue:`2975`: [notebook] python file and cell toolbar
* :ghissue:`3017`: SciPy.weave broken in IPython notebook/ qtconsole 
* :ghissue:`3161`: paste macro not reading spaces correctly
* :ghissue:`2835`: %paste not working on WinXpSP3/ipython-0.13.1.py2-win32-PROPER.exe/python27
* :ghissue:`2628`: Make transformers work for lines following decorators
* :ghissue:`2612`: Multiline String containing ":\n?foo\n" confuses interpreter to replace ?foo with get_ipython().magic(u'pinfo foo')
* :ghissue:`2539`: Request: Enable cell magics inside of .ipy scripts
* :ghissue:`2507`: Multiline string does not work (includes `...`) with doctest type input in IPython notebook
* :ghissue:`2164`: Request: Line breaks in line magic command
* :ghissue:`3106`: poor parallel performance with many jobs
* :ghissue:`2438`: print inside multiprocessing crashes Ipython kernel
* :ghissue:`3155`: Bad md5 hash for package 0.13.2
* :ghissue:`3045`: [Notebook] Ipython Kernel does not start if disconnected from internet(/network?)
* :ghissue:`3146`: Using celery in python 3.3
* :ghissue:`3145`: The notebook viewer is down
* :ghissue:`2385`: grep --color not working well with notebook
* :ghissue:`3131`: Quickly install from source in a clean virtualenv?
* :ghissue:`3139`: Rolling log for ipython
* :ghissue:`3127`: notebook with pylab=inline appears to call figure.draw twice
* :ghissue:`3129`: Walking up and down the call stack
* :ghissue:`3123`: Notebook crashed if unplugged ethernet cable
* :ghissue:`3121`: NB should use normalize.css? was #3049
* :ghissue:`3087`: Disable spellchecking in notebook
* :ghissue:`3084`: ipython pyqt 4.10 incompatibilty, QTextBlockUserData
* :ghissue:`3113`: Fails to install under Jython 2.7 beta
* :ghissue:`3110`: Render of h4 headers is not correct in notebook (error in renderedhtml.css)
* :ghissue:`3109`: BUG: read_csv: dtype={'id' : np.str}: Datatype not understood
* :ghissue:`3107`: Autocompletion of object attributes in arrays
* :ghissue:`3103`: Reset locale setting in qtconsole
* :ghissue:`3090`: python3.3 Entry Point not found
* :ghissue:`3081`: UnicodeDecodeError when using Image(data="some.jpeg")
* :ghissue:`2834`: url regexp only finds one link
* :ghissue:`3091`: qtconsole breaks doctest.testmod() in Python 3.3
* :ghissue:`3074`: SIGUSR1 not available on Windows
* :ghissue:`2996`: registration::purging stalled registration high occurrence in small clusters 
* :ghissue:`3065`: diff-ability of notebooks
* :ghissue:`3067`: Crash with pygit2
* :ghissue:`3061`: Bug handling Ellipsis
* :ghissue:`3049`: NB css inconsistent behavior between ff and webkit
* :ghissue:`3039`: unicode errors when opening a new notebook
* :ghissue:`3048`: Installning ipython qtConsole should be easyer att Windows
* :ghissue:`3042`: Profile creation fails on 0.13.2 branch
* :ghissue:`3035`: docstring typo/inconsistency: mention of an xml notebook format?
* :ghissue:`3031`: HDF5 library segfault (possibly due to mismatching headers?)
* :ghissue:`2991`: In notebook importing sympy closes ipython kernel
* :ghissue:`3027`: f.__globals__ causes an error in Python 3.3
* :ghissue:`3020`: Failing test test_interactiveshell.TestAstTransform on Windows
* :ghissue:`3023`: alt text for "click to expand output" has typo in alt text
* :ghissue:`2963`: %history to print all input history of a  previous session when line range is omitted
* :ghissue:`3018`: IPython installed within virtualenv. WARNING "Please install IPython inside the virtualtenv"
* :ghissue:`2484`: Completion in Emacs *Python* buffer causes prompt to be increased.
* :ghissue:`3014`: Ctrl-C finishes notebook immediately
* :ghissue:`3007`: cython_pyximport reload broken in python3
* :ghissue:`2955`: Incompatible Qt imports when running inprocess_qtconsole
* :ghissue:`3006`: [IPython 0.13.1] The check of PyQt version is wrong
* :ghissue:`3005`: Renaming a notebook to an existing notebook name overwrites the other file
* :ghissue:`2940`: Abort trap in IPython Notebook after installing matplotlib
* :ghissue:`3000`: issue #3000
* :ghissue:`2995`: ipython_directive.py fails on multiline when prompt number < 100
* :ghissue:`2993`: File magic (%%file) does not work with paths beginning with tilde (e.g., ~/anaconda/stuff.txt)
* :ghissue:`2992`: Cell-based input for console and qt frontends?
* :ghissue:`2425`: Liaise with Spyder devs to integrate newer IPython
* :ghissue:`2986`: requesting help in a loop can damage a notebook
* :ghissue:`2978`: v1.0-dev build errors on Arch with Python 3.
* :ghissue:`2557`: [refactor] Insert_cell_at_index()
* :ghissue:`2969`: ipython command does not work in terminal
* :ghissue:`2762`: OSX wxPython (osx_cocoa, 64bit) command "%gui wx" blocks the interpreter
* :ghissue:`2956`: Silent importing of submodules differs from standard Python3.2 interpreter's behavior
* :ghissue:`2943`: Up arrow key history search gets stuck in QTConsole
* :ghissue:`2953`: using 'nonlocal' declaration in global scope causes ipython3 crash
* :ghissue:`2952`: qtconsole ignores exec_lines
* :ghissue:`2949`: ipython crashes due to atexit()
* :ghissue:`2947`: From rmagic to  an R console
* :ghissue:`2938`: docstring pane not showing in notebook
* :ghissue:`2936`: Tornado assumes invalid signature for parse_qs on Python 3.1
* :ghissue:`2935`: unable to find python after easy_install / pip install
* :ghissue:`2920`: Add undo-cell deletion menu
* :ghissue:`2914`: BUG:saving a modified .py file after loading a module kills the kernel
* :ghissue:`2925`: BUG: kernel dies if user sets sys.stderr or sys.stdout to a file object
* :ghissue:`2909`: LaTeX sometimes fails to render in markdown cells with some curly bracket + underscore combinations
* :ghissue:`2898`: Skip ipc tests on Windows
* :ghissue:`2902`: ActiveState attempt to build ipython 0.12.1 for python 3.2.2 for Mac OS failed
* :ghissue:`2899`: Test failure in IPython.core.tests.test_magic.test_time
* :ghissue:`2890`: Test failure when fabric not installed
* :ghissue:`2892`: IPython tab completion bug for paths
* :ghissue:`1340`: Allow input cells to be collapsed
* :ghissue:`2881`: ? command in notebook does not show help in Safari
* :ghissue:`2751`: %%timeit should use minutes to format running time in long running cells
* :ghissue:`2879`: When importing a module with a wrong name, ipython crashes
* :ghissue:`2862`: %%timeit should warn of empty contents
* :ghissue:`2485`: History navigation breaks in qtconsole
* :ghissue:`2785`: gevent input hook
* :ghissue:`2843`: Sliently running code in clipboard (with paste, cpaste and variants)
* :ghissue:`2784`: %run -t -N<N> error
* :ghissue:`2732`: Test failure with FileLinks class on Windows
* :ghissue:`2860`: ipython help notebook -> KeyError: 'KernelManager'
* :ghissue:`2858`: Where is the installed `ipython` script?
* :ghissue:`2856`: Edit code entered from ipython in external editor
* :ghissue:`2722`: IPC transport option not taking effect ?
* :ghissue:`2473`: Better error messages in ipengine/ipcontroller
* :ghissue:`2836`: Cannot send builtin module definitions to IP engines
* :ghissue:`2833`: Any reason not to use super() ? 
* :ghissue:`2781`: Cannot interrupt infinite loops in the notebook
* :ghissue:`2150`: clippath_demo.py in matplotlib example does not work with inline backend
* :ghissue:`2634`: Numbered list in notebook markdown cell renders with Roman numerals instead of numbers
* :ghissue:`2230`: IPython crashing during startup with "AttributeError: 'NoneType' object has no attribute 'rstrip'"
* :ghissue:`2483`: nbviewer bug? with multi-file gists
* :ghissue:`2466`: mistyping `ed -p` breaks `ed -p`
* :ghissue:`2477`: Glob expansion tests fail on Windows
* :ghissue:`2622`: doc issue: notebooks that ship with Ipython .13 are written for python 2.x
* :ghissue:`2626`: Add "Cell -> Run All Keep Going" for notebooks
* :ghissue:`1223`: Show last modification date of each notebook
* :ghissue:`2621`: user request: put link to example notebooks in Dashboard
* :ghissue:`2564`: grid blanks plots in ipython pylab inline mode (interactive)
* :ghissue:`2532`: Django shell (IPython) gives NameError on dict comprehensions
* :ghissue:`2188`: ipython crashes on ctrl-c
* :ghissue:`2391`: Request: nbformat API to load/save without changing version
* :ghissue:`2355`: Restart kernel message even though kernel is perfectly alive
* :ghissue:`2306`: Garbled input text after reverse search on Mac OS X
* :ghissue:`2297`: ipdb with separate kernel/client pushing stdout to kernel process only
* :ghissue:`2180`: Have [kernel busy] overridden only by [kernel idle]
* :ghissue:`1188`: Pylab with OSX backend keyboard focus issue and hang
* :ghissue:`2107`: test_octavemagic.py[everything] fails 
* :ghissue:`1212`: Better understand/document browser compatibility
* :ghissue:`1585`: Refactor notebook templates to use Jinja2 and make each page a separate directory
* :ghissue:`1443`: xticks scaling factor partially obscured with qtconsole and inline plotting 
* :ghissue:`1209`: can't make %result work as in doc.
* :ghissue:`1200`: IPython 0.12 Windows install fails on Vista
* :ghissue:`1127`: Interactive test scripts for Qt/nb issues
* :ghissue:`959`: Matplotlib figures hide
* :ghissue:`2071`: win32 installer issue on Windows XP
* :ghissue:`2610`: ZMQInteractiveShell.colors being ignored
* :ghissue:`2505`: Markdown Cell incorrectly highlighting after "<"
* :ghissue:`165`: Installer fails to create Start Menu entries on Windows
* :ghissue:`2356`: failing traceback in terminal ipython for first exception
* :ghissue:`2145`: Have dashboad show when server disconect
* :ghissue:`2098`: Do not crash on kernel shutdow if json file is missing
* :ghissue:`2813`: Offline MathJax is broken on 0.14dev
* :ghissue:`2807`: Test failure: IPython.parallel.tests.test_client.TestClient.test_purge_everything
* :ghissue:`2486`: Readline's history search in ipython console does not clear properly after cancellation with Ctrl+C
* :ghissue:`2709`: Cython -la doesn't work
* :ghissue:`2767`: What is IPython.utils.upgradedir ?
* :ghissue:`2210`: Placing matplotlib legend outside axis bounds causes inline display to clip it
* :ghissue:`2553`: IPython Notebooks not robust against client failures
* :ghissue:`2536`: ImageDraw in Ipython notebook not drawing lines
* :ghissue:`2264`: Feature request: Versioning messaging protocol
* :ghissue:`2589`: Creation of ~300+ MPI-spawned engines causes instability in ipcluster
* :ghissue:`2672`: notebook: inline option without pylab
* :ghissue:`2673`: Indefinite Articles & Traitlets
* :ghissue:`2705`: Notebook crashes Safari with select and drag
* :ghissue:`2721`: dreload kills ipython when it hits zmq
* :ghissue:`2806`: ipython.parallel doesn't discover globals under Python 3.3
* :ghissue:`2794`: _exit_code behaves differently in terminal vs ZMQ frontends
* :ghissue:`2793`: IPython.parallel issue with pushing pandas TimeSeries
* :ghissue:`1085`: In process kernel for Qt frontend
* :ghissue:`2760`: IndexError: list index out of range with Python 3.2
* :ghissue:`2780`: Save and load notebooks from github
* :ghissue:`2772`: AttributeError: 'Client' object has no attribute 'kill'
* :ghissue:`2754`: Fail to send class definitions from interactive session to engines namespaces
* :ghissue:`2764`: TypeError while using 'cd'
* :ghissue:`2765`: name '__file__' is not defined
* :ghissue:`2540`: Wrap tooltip if line exceeds threshold?
* :ghissue:`2394`: Startup error on ipython qtconsole (version 0.13 and 0.14-dev
* :ghissue:`2440`: IPEP 4: Python 3 Compatibility
* :ghissue:`1814`: __file__ is not defined when file end with .ipy
* :ghissue:`2759`: R magic extension interferes with tab completion
* :ghissue:`2615`: Small change needed to rmagic extension.
* :ghissue:`2748`: collapse parts of a html notebook
* :ghissue:`1661`: %paste still bugs about IndentationError and says to use %paste
* :ghissue:`2742`: Octavemagic fails to deliver inline images in IPython (on Windows)
* :ghissue:`2739`: wiki.ipython.org contaminated with prescription drug spam
* :ghissue:`2588`: Link error while executing code from cython example notebook
* :ghissue:`2550`: Rpush magic doesn't find local variables and doesn't support comma separated lists of variables
* :ghissue:`2675`: Markdown/html blockquote need css.
* :ghissue:`2419`: TerminalInteractiveShell.__init__() ignores value of ipython_dir argument
* :ghissue:`1523`: Better LaTeX printing in the qtconsole with the sympy profile
* :ghissue:`2719`: ipython fails with `pkg_resources.DistributionNotFound: ipython==0.13`
* :ghissue:`2715`: url crashes nbviewer.ipython.org
* :ghissue:`2555`: "import" module completion on MacOSX
* :ghissue:`2707`: Problem installing the new version of IPython in Windows
* :ghissue:`2696`: SymPy magic bug in IPython Notebook
* :ghissue:`2684`: pretty print broken for types created with PyType_FromSpec
* :ghissue:`2533`: rmagic breaks on Windows
* :ghissue:`2661`: Qtconsole tooltip is too wide when the function has many arguments
* :ghissue:`2679`: ipython3 qtconsole via Homebrew on Mac OS X 10.8 - pyqt/pyside import error
* :ghissue:`2646`: pylab_not_importable
* :ghissue:`2587`: cython magic pops 2 CLI windows upon execution on Windows
* :ghissue:`2660`: Certain arguments (-h, --help, --version) never passed to scripts run with ipython
* :ghissue:`2665`: Missing docs for rmagic and some other extensions
* :ghissue:`2611`: Travis wants to drop 3.1 support
* :ghissue:`2658`: Incorrect parsing of raw multiline strings
* :ghissue:`2655`: Test fails if `from __future__ import print_function` in .pythonrc.py
* :ghissue:`2651`: nonlocal with no existing variable produces too many errors
* :ghissue:`2645`: python3 is a pain (minor unicode bug)
* :ghissue:`2637`: %paste in Python 3 on Mac doesn't work
* :ghissue:`2624`: Error on launching IPython on Win 7 and Python 2.7.3
* :ghissue:`2608`: disk IO activity on cursor press
* :ghissue:`1275`: Markdown parses LaTeX math symbols as its formatting syntax in notebook
* :ghissue:`2613`: display(Math(...)) doesn't render \tau correctly
* :ghissue:`925`: Tab-completion in Qt console needn't use pager
* :ghissue:`2607`: %load_ext sympy.interactive.ipythonprinting  dammaging output
* :ghissue:`2593`: Toolbar button to open qtconsole from notebook
* :ghissue:`2602`: IPython html documentation for downloading
* :ghissue:`2598`: ipython notebook --pylab=inline replaces built-in any()
* :ghissue:`2244`: small issue: wrong printout
* :ghissue:`2590`: add easier way to execute scripts in the current directory
* :ghissue:`2581`: %hist does not work when InteractiveShell.cache_size = 0
* :ghissue:`2584`: No file COPYING
* :ghissue:`2578`: AttributeError: 'module' object has no attribute 'TestCase'
* :ghissue:`2576`: One of my notebooks won't load any more -- is there a maximum notebook size?
* :ghissue:`2560`: Notebook output is invisible when printing strings with \r\r\n line endings
* :ghissue:`2566`: if pyside partially present ipython qtconsole fails to load even if pyqt4 present
* :ghissue:`1308`: ipython qtconsole  --ssh=server --existing ... hangs
* :ghissue:`1679`: List command doesn't work in ipdb debugger the first time
* :ghissue:`2545`: pypi win32 installer creates 64bit executibles
* :ghissue:`2080`: Event loop issues with IPython 0.12 and PyQt4 (``QDialog.exec_`` and more)
* :ghissue:`2541`: Allow `python -m IPython`
* :ghissue:`2508`: subplots_adjust() does not work correctly in ipython notebook
* :ghissue:`2289`: Incorrect mathjax rendering of certain arrays of equations
* :ghissue:`2487`: Selecting and indenting
* :ghissue:`2521`: more fine-grained 'run' controls, such as 'run from here' and 'run until here'
* :ghissue:`2535`: Funny bounding box when plot with text
* :ghissue:`2523`: History not working
* :ghissue:`2514`: Issue with zooming in qtconsole
* :ghissue:`2220`: No sys.stdout.encoding in kernel based IPython
* :ghissue:`2512`: ERROR: Internal Python error in the inspect module.
* :ghissue:`2496`: Function passwd does not work in QtConsole
* :ghissue:`1453`: make engines reconnect/die when controller was restarted
* :ghissue:`2481`: ipython notebook -- clicking in a code cell's output moves the screen to the top of the code cell
* :ghissue:`2488`: Undesired plot outputs in Notebook inline mode
* :ghissue:`2482`: ipython notebook -- download may not get the latest notebook
* :ghissue:`2471`: _subprocess module removed in Python 3.3
* :ghissue:`2374`: Issues with man pages
* :ghissue:`2316`: parallel.Client.__init__ should take cluster_id kwarg
* :ghissue:`2457`: Can a R library wrapper be created with Rmagic?
* :ghissue:`1575`: Fallback frontend for console when connecting pylab=inlnie -enabled kernel?
* :ghissue:`2097`: Do not crash if history db is corrupted
* :ghissue:`2435`: ipengines fail if clean_logs enabled
* :ghissue:`2429`: Using warnings.warn() results in TypeError
* :ghissue:`2422`: Multiprocessing in ipython notebook kernel crash
* :ghissue:`2426`: ipython crashes with the following message. I do not what went wrong. Can you help me identify the problem?
* :ghissue:`2423`: Docs typo?
* :ghissue:`2257`: pip install -e fails
* :ghissue:`2418`: rmagic can't run R's read.csv on data files with NA data
* :ghissue:`2417`: HTML notebook: Backspace sometimes deletes multiple characters
* :ghissue:`2275`: notebook: "Down_Arrow" on last line of cell should move to end of line
* :ghissue:`2414`: 0.13.1 does not work with current EPD 7.3-2
* :ghissue:`2409`: there is a redundant None
* :ghissue:`2410`: Use /usr/bin/python3 instead of /usr/bin/python
* :ghissue:`2366`: Notebook Dashboard --notebook-dir and fullpath
* :ghissue:`2406`: Inability to get docstring in debugger
* :ghissue:`2398`: Show line number for IndentationErrors
* :ghissue:`2314`: HTML lists seem to interfere with the QtConsole display
* :ghissue:`1688`: unicode exception when using %run with failing script
* :ghissue:`1884`: IPython.embed changes color on error
* :ghissue:`2381`: %time doesn't work for multiline statements
* :ghissue:`1435`: Add size keywords in Image class
* :ghissue:`2372`: interactiveshell.py misses urllib and io_open imports
* :ghissue:`2371`: iPython not working
* :ghissue:`2367`: Tab expansion moves to next cell in notebook
* :ghissue:`2359`: nbviever alters the order of print and display() output
* :ghissue:`2227`: print name for IPython Notebooks has become uninformative
* :ghissue:`2361`: client doesn't use connection file's 'location' in disambiguating 'interface'
* :ghissue:`2357`: failing traceback in terminal ipython for first exception
* :ghissue:`2343`: Installing in a python 3.3b2 or python 3.3rc1 virtual environment.
* :ghissue:`2315`: Failure in test: "Test we're not loading modules on startup that we shouldn't." 
* :ghissue:`2351`: Multiple Notebook Apps: cookies not port specific, clash with each other
* :ghissue:`2350`: running unittest from qtconsole prints output to terminal
* :ghissue:`2303`:  remote tracebacks broken since 952d0d6 (PR #2223)
* :ghissue:`2330`: qtconsole does not hightlight tab-completion suggestion with custom stylesheet
* :ghissue:`2325`: Parsing Tex formula fails in Notebook
* :ghissue:`2324`: Parsing Tex formula fails
* :ghissue:`1474`: Add argument to `run -n` for custom namespace
* :ghissue:`2318`: C-m n/p don't work in Markdown cells in the notebook
* :ghissue:`2309`: time.time() in ipython notebook producing impossible results
* :ghissue:`2307`: schedule tasks on newly arrived engines
* :ghissue:`2313`: Allow Notebook HTML/JS to send messages to Python code
* :ghissue:`2304`: ipengine throws KeyError: url
* :ghissue:`1878`: shell access using ! will not fill class or function scope vars
* :ghissue:`2253`: %paste does not retrieve clipboard contents under screen/tmux on OS X
* :ghissue:`1510`: Add-on (or Monkey-patch) infrastructure for HTML notebook
* :ghissue:`2273`: triple quote and %s at beginning of line with %paste
* :ghissue:`2243`: Regression in .embed()
* :ghissue:`2266`: SSH passwordless check with OpenSSH checks for the wrong thing
* :ghissue:`2217`: Change NewNotebook handler to use 30x redirect
* :ghissue:`2276`: config option for disabling history store
* :ghissue:`2239`: can't use parallel.Reference in view.map
* :ghissue:`2272`: Sympy piecewise messed up rendering
* :ghissue:`2252`: %paste throws an exception with empty clipboard
* :ghissue:`2259`: git-mpr is currently broken
* :ghissue:`2247`: Variable expansion in shell commands should work in substrings
* :ghissue:`2026`: Run 'fast' tests only
* :ghissue:`2241`: read a list of notebooks on server and bring into browser only notebook
* :ghissue:`2237`: please put python and text editor in the web only ipython
* :ghissue:`2053`: Improvements to the IPython.display.Image object
* :ghissue:`1456`: ERROR: Internal Python error in the inspect module.
* :ghissue:`2221`: Avoid importing from IPython.parallel in core
* :ghissue:`2213`: Can't trigger startup code in Engines
* :ghissue:`1464`: Strange behavior for backspace with lines ending with more than 4 spaces in notebook 
* :ghissue:`2187`: NaN in object_info_reply JSON causes parse error
* :ghissue:`214`: system command requiring administrative privileges  
* :ghissue:`2195`: Unknown option `no-edit` in git-mpr
* :ghissue:`2201`: Add documentation build to tools/test_pr.py
* :ghissue:`2205`: Command-line option for default Notebook output collapsing behavior
* :ghissue:`1927`: toggle between inline and floating figures
* :ghissue:`2171`: Can't start StarCluster after upgrading to IPython 0.13
* :ghissue:`2173`: oct2py v >= 0.3.1 doesn't need h5py anymore
* :ghissue:`2099`: storemagic needs to use self.shell
* :ghissue:`2166`: DirectView map_sync() with Lambdas Using Generators
* :ghissue:`2091`: Unable to use print_stats after %prun -r in notebook
* :ghissue:`2132`: Add fail-over for pastebin
* :ghissue:`2156`: Make it possible to install ipython without nasty gui dependencies
* :ghissue:`2154`: Scrolled long output should be off in print view by default
* :ghissue:`2162`: Tab completion does not work with IPython.embed_kernel()
* :ghissue:`2157`: iPython 0.13 / github-master cannot create logfile from scratch
* :ghissue:`2151`: missing newline when a magic is called from the qtconsole menu
* :ghissue:`2139`: 00_notebook_tour Image example broken on master
* :ghissue:`2143`: Add a %%cython_annotate magic
* :ghissue:`2135`: Running IPython from terminal
* :ghissue:`2093`: Makefile for building Sphinx documentation on Windows 
* :ghissue:`2122`: Bug in pretty printing
* :ghissue:`2120`: Notebook "Make a Copy..." keeps opening duplicates in the same tab
* :ghissue:`1997`: password cannot be used with url prefix
* :ghissue:`2129`: help/doc displayed multiple times if requested in loop
* :ghissue:`2121`: ipdb does not support input history in qtconsole
* :ghissue:`2114`: %logstart doesn't log
* :ghissue:`2085`: %ed magic fails in qtconsole
* :ghissue:`2119`: iPython fails to run on MacOS Lion 
* :ghissue:`2052`: %pylab inline magic does not work on windows
* :ghissue:`2111`: Ipython won't start on W7
* :ghissue:`2112`: Strange internal traceback
* :ghissue:`2108`: Backslash (\) at the end of the line behavior different from default Python
* :ghissue:`1425`: Ampersands can't be typed sometimes in notebook cells
* :ghissue:`1513`: Add expand/collapse support for long output elements like stdout and tracebacks
* :ghissue:`2087`: error when starting ipython
* :ghissue:`2103`: Ability to run notebook file from commandline
* :ghissue:`2082`: Qt Console output spacing
* :ghissue:`2083`: Test failures with Python 3.2 and PYTHONWARNINGS="d"
* :ghissue:`2094`: about inline
* :ghissue:`2077`: Starting IPython3 on the terminal
* :ghissue:`1760`: easy_install ipython fails on py3.2-win32
* :ghissue:`2075`: Local Mathjax install causes iptest3 error under python3
* :ghissue:`2057`: setup fails for python3 with LANG=C
* :ghissue:`2070`: shebang on Windows
* :ghissue:`2054`: sys_info missing git hash in sdists
* :ghissue:`2059`: duplicate and modified files in documentation
* :ghissue:`2056`: except-shadows-builtin osm.py:687
* :ghissue:`2058`: hyphen-used-as-minus-sign in manpages

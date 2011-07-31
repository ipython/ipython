.. _issues_list_011:

Issues closed in the 0.11 development cycle
===========================================

In this cycle, we closed a total of 511 issues, 226 pull requests and 285
regular issues; this is the full list (generated with the script
`tools/github_stats.py`). We should note that a few of these were made on the
0.10.x series, but we have no automatic way of filtering the issues by branch,
so this reflects all of our development over the last two years, including work
already released in 0.10.2:

Pull requests (226):

* `620 <https://github.com/ipython/ipython/issues/620>`_: Release notes and updates to GUI support docs for 0.11
* `642 <https://github.com/ipython/ipython/issues/642>`_: fix typo in docs/examples/vim/README.rst
* `631 <https://github.com/ipython/ipython/issues/631>`_: two-way vim-ipython integration
* `637 <https://github.com/ipython/ipython/issues/637>`_: print is a function, this allows to properly exit ipython
* `635 <https://github.com/ipython/ipython/issues/635>`_: support html representations in the notebook frontend
* `639 <https://github.com/ipython/ipython/issues/639>`_: Updating the credits file
* `628 <https://github.com/ipython/ipython/issues/628>`_: import pexpect from IPython.external in irunner
* `596 <https://github.com/ipython/ipython/issues/596>`_: Irunner
* `598 <https://github.com/ipython/ipython/issues/598>`_: Fix templates for CrashHandler
* `590 <https://github.com/ipython/ipython/issues/590>`_: Desktop
* `600 <https://github.com/ipython/ipython/issues/600>`_: Fix bug with non-ascii reprs inside pretty-printed lists.
* `618 <https://github.com/ipython/ipython/issues/618>`_: I617
* `599 <https://github.com/ipython/ipython/issues/599>`_: Gui Qt example and docs
* `619 <https://github.com/ipython/ipython/issues/619>`_: manpage update
* `582 <https://github.com/ipython/ipython/issues/582>`_: Updating sympy profile to match the exec_lines of isympy.
* `578 <https://github.com/ipython/ipython/issues/578>`_: Check to see if correct source for decorated functions can be displayed
* `589 <https://github.com/ipython/ipython/issues/589>`_: issue 588
* `591 <https://github.com/ipython/ipython/issues/591>`_: simulate shell expansion on %run arguments, at least tilde expansion
* `576 <https://github.com/ipython/ipython/issues/576>`_: Show message about %paste magic on an IndentationError
* `574 <https://github.com/ipython/ipython/issues/574>`_: Getcwdu
* `565 <https://github.com/ipython/ipython/issues/565>`_: don't move old config files, keep nagging the user
* `575 <https://github.com/ipython/ipython/issues/575>`_: Added more docstrings to IPython.zmq.session.
* `567 <https://github.com/ipython/ipython/issues/567>`_: fix trailing whitespace from reseting indentation
* `564 <https://github.com/ipython/ipython/issues/564>`_: Command line args in docs
* `560 <https://github.com/ipython/ipython/issues/560>`_: reorder qt support in kernel
* `561 <https://github.com/ipython/ipython/issues/561>`_: command-line suggestions
* `556 <https://github.com/ipython/ipython/issues/556>`_: qt_for_kernel: use matplotlib rcParams to decide between PyQt4 and PySide
* `557 <https://github.com/ipython/ipython/issues/557>`_: Update usage.py to newapp
* `555 <https://github.com/ipython/ipython/issues/555>`_: Rm default old config
* `552 <https://github.com/ipython/ipython/issues/552>`_: update parallel code for py3k
* `504 <https://github.com/ipython/ipython/issues/504>`_: Updating string formatting
* `551 <https://github.com/ipython/ipython/issues/551>`_: Make pylab import all configurable
* `496 <https://github.com/ipython/ipython/issues/496>`_: Qt editing keybindings
* `550 <https://github.com/ipython/ipython/issues/550>`_: Support v2 PyQt4 APIs and PySide in kernel's GUI support
* `546 <https://github.com/ipython/ipython/issues/546>`_: doc update
* `548 <https://github.com/ipython/ipython/issues/548>`_: Fix sympy profile to work with sympy 0.7.
* `542 <https://github.com/ipython/ipython/issues/542>`_: issue 440
* `533 <https://github.com/ipython/ipython/issues/533>`_: Remove unused configobj and validate libraries from externals.
* `538 <https://github.com/ipython/ipython/issues/538>`_: fix various tests on Windows
* `540 <https://github.com/ipython/ipython/issues/540>`_: support `-pylab` flag with deprecation warning
* `537 <https://github.com/ipython/ipython/issues/537>`_: Docs update
* `536 <https://github.com/ipython/ipython/issues/536>`_: `setup.py install` depends on setuptools on Windows
* `480 <https://github.com/ipython/ipython/issues/480>`_: Get help mid-command
* `462 <https://github.com/ipython/ipython/issues/462>`_: Str and Bytes traitlets
* `534 <https://github.com/ipython/ipython/issues/534>`_: Handle unicode properly in IPython.zmq.iostream
* `527 <https://github.com/ipython/ipython/issues/527>`_: ZMQ displayhook
* `526 <https://github.com/ipython/ipython/issues/526>`_: Handle asynchronous output in Qt console
* `528 <https://github.com/ipython/ipython/issues/528>`_: Do not import deprecated functions from external decorators library.
* `454 <https://github.com/ipython/ipython/issues/454>`_: New BaseIPythonApplication
* `532 <https://github.com/ipython/ipython/issues/532>`_: Zmq unicode
* `531 <https://github.com/ipython/ipython/issues/531>`_: Fix Parallel test
* `525 <https://github.com/ipython/ipython/issues/525>`_: fallback on lsof if otool not found in libedit detection
* `517 <https://github.com/ipython/ipython/issues/517>`_: Merge IPython.parallel.streamsession into IPython.zmq.session
* `521 <https://github.com/ipython/ipython/issues/521>`_: use dict.get(key) instead of dict[key] for safety from KeyErrors
* `492 <https://github.com/ipython/ipython/issues/492>`_: add QtConsoleApp using newapplication
* `485 <https://github.com/ipython/ipython/issues/485>`_: terminal IPython with newapp
* `486 <https://github.com/ipython/ipython/issues/486>`_: Use newapp in parallel code
* `511 <https://github.com/ipython/ipython/issues/511>`_: Add a new line before displaying multiline strings in the Qt console.
* `509 <https://github.com/ipython/ipython/issues/509>`_: i508
* `501 <https://github.com/ipython/ipython/issues/501>`_: ignore EINTR in channel loops
* `495 <https://github.com/ipython/ipython/issues/495>`_: Better selection of Qt bindings when QT_API is not specified
* `498 <https://github.com/ipython/ipython/issues/498>`_: Check for .pyd as extension for binary files.
* `494 <https://github.com/ipython/ipython/issues/494>`_: QtConsole zoom adjustments
* `490 <https://github.com/ipython/ipython/issues/490>`_: fix UnicodeEncodeError writing SVG string to .svg file, fixes #489
* `491 <https://github.com/ipython/ipython/issues/491>`_: add QtConsoleApp using newapplication
* `479 <https://github.com/ipython/ipython/issues/479>`_: embed() doesn't load default config
* `483 <https://github.com/ipython/ipython/issues/483>`_: Links launchpad -> github
* `419 <https://github.com/ipython/ipython/issues/419>`_: %xdel magic
* `477 <https://github.com/ipython/ipython/issues/477>`_: Add \n to lines in the log
* `459 <https://github.com/ipython/ipython/issues/459>`_: use os.system for shell.system in Terminal frontend
* `475 <https://github.com/ipython/ipython/issues/475>`_: i473
* `471 <https://github.com/ipython/ipython/issues/471>`_: Add test decorator onlyif_unicode_paths.
* `474 <https://github.com/ipython/ipython/issues/474>`_: Fix support for raw GTK and WX matplotlib backends.
* `472 <https://github.com/ipython/ipython/issues/472>`_: Kernel event loop is robust against random SIGINT.
* `460 <https://github.com/ipython/ipython/issues/460>`_: Share code for magic_edit
* `469 <https://github.com/ipython/ipython/issues/469>`_: Add exit code when running all tests with iptest.
* `464 <https://github.com/ipython/ipython/issues/464>`_: Add home directory expansion to IPYTHON_DIR environment variables.
* `455 <https://github.com/ipython/ipython/issues/455>`_: Bugfix with logger
* `448 <https://github.com/ipython/ipython/issues/448>`_: Separate out skip_doctest decorator
* `453 <https://github.com/ipython/ipython/issues/453>`_: Draft of new main BaseIPythonApplication.
* `452 <https://github.com/ipython/ipython/issues/452>`_: Use list/tuple/dict/set subclass's overridden __repr__ instead of the pretty
* `398 <https://github.com/ipython/ipython/issues/398>`_: allow toggle of svg/png inline figure format
* `381 <https://github.com/ipython/ipython/issues/381>`_: Support inline PNGs of matplotlib plots
* `413 <https://github.com/ipython/ipython/issues/413>`_: Retries and Resubmit (#411 and #412)
* `370 <https://github.com/ipython/ipython/issues/370>`_: Fixes to the display system
* `449 <https://github.com/ipython/ipython/issues/449>`_: Fix issue 447 - inspecting old-style classes.
* `423 <https://github.com/ipython/ipython/issues/423>`_: Allow type checking on elements of List,Tuple,Set traits
* `400 <https://github.com/ipython/ipython/issues/400>`_: Config5
* `421 <https://github.com/ipython/ipython/issues/421>`_: Generalise mechanism to put text at the next prompt in the Qt console.
* `443 <https://github.com/ipython/ipython/issues/443>`_: pinfo code duplication
* `429 <https://github.com/ipython/ipython/issues/429>`_: add check_pid, and handle stale PID info in ipcluster.
* `431 <https://github.com/ipython/ipython/issues/431>`_: Fix error message in test_irunner
* `427 <https://github.com/ipython/ipython/issues/427>`_: handle different SyntaxError messages in test_irunner
* `424 <https://github.com/ipython/ipython/issues/424>`_: Irunner test failure
* `430 <https://github.com/ipython/ipython/issues/430>`_: Small parallel doc typo
* `422 <https://github.com/ipython/ipython/issues/422>`_: Make ipython-qtconsole a GUI script
* `420 <https://github.com/ipython/ipython/issues/420>`_: Permit kernel std* to be redirected
* `408 <https://github.com/ipython/ipython/issues/408>`_: History request
* `388 <https://github.com/ipython/ipython/issues/388>`_: Add Emacs-style kill ring to Qt console
* `414 <https://github.com/ipython/ipython/issues/414>`_: Warn on old config files
* `415 <https://github.com/ipython/ipython/issues/415>`_: Prevent prefilter from crashing IPython
* `418 <https://github.com/ipython/ipython/issues/418>`_: Minor configuration doc fixes
* `407 <https://github.com/ipython/ipython/issues/407>`_: Update What's new documentation
* `410 <https://github.com/ipython/ipython/issues/410>`_: Install notebook frontend
* `406 <https://github.com/ipython/ipython/issues/406>`_: install IPython.zmq.gui
* `393 <https://github.com/ipython/ipython/issues/393>`_: ipdir unicode
* `397 <https://github.com/ipython/ipython/issues/397>`_: utils.io.Term.cin/out/err -> utils.io.stdin/out/err
* `389 <https://github.com/ipython/ipython/issues/389>`_: DB fixes and Scheduler HWM
* `374 <https://github.com/ipython/ipython/issues/374>`_: Various Windows-related fixes to IPython.parallel
* `362 <https://github.com/ipython/ipython/issues/362>`_: fallback on defaultencoding if filesystemencoding is None
* `382 <https://github.com/ipython/ipython/issues/382>`_: Shell's reset method clears namespace from last %run command.
* `385 <https://github.com/ipython/ipython/issues/385>`_: Update iptest exclusions (fix #375)
* `383 <https://github.com/ipython/ipython/issues/383>`_: Catch errors in querying readline which occur with pyreadline.
* `373 <https://github.com/ipython/ipython/issues/373>`_: Remove runlines etc.
* `364 <https://github.com/ipython/ipython/issues/364>`_: Single output
* `372 <https://github.com/ipython/ipython/issues/372>`_: Multiline input push
* `363 <https://github.com/ipython/ipython/issues/363>`_: Issue 125
* `361 <https://github.com/ipython/ipython/issues/361>`_: don't rely on setuptools for readline dependency check
* `349 <https://github.com/ipython/ipython/issues/349>`_: Fix %autopx magic
* `355 <https://github.com/ipython/ipython/issues/355>`_: History save thread
* `356 <https://github.com/ipython/ipython/issues/356>`_: Usability improvements to history in Qt console
* `357 <https://github.com/ipython/ipython/issues/357>`_: Exit autocall
* `353 <https://github.com/ipython/ipython/issues/353>`_: Rewrite quit()/exit()/Quit()/Exit() calls as magic
* `354 <https://github.com/ipython/ipython/issues/354>`_: Cell tweaks
* `345 <https://github.com/ipython/ipython/issues/345>`_: Attempt to address (partly) issue ipython/#342 by rewriting quit(), exit(), etc.
* `352 <https://github.com/ipython/ipython/issues/352>`_: #342: Try to recover as intelligently as possible if user calls magic().
* `346 <https://github.com/ipython/ipython/issues/346>`_: Dedent prefix bugfix + tests: #142
* `348 <https://github.com/ipython/ipython/issues/348>`_: %reset doesn't reset prompt number.
* `347 <https://github.com/ipython/ipython/issues/347>`_: Make ip.reset() work the same in interactive or non-interactive code.
* `343 <https://github.com/ipython/ipython/issues/343>`_: make readline a dependency on OSX
* `344 <https://github.com/ipython/ipython/issues/344>`_: restore auto debug behavior
* `339 <https://github.com/ipython/ipython/issues/339>`_: fix for issue 337: incorrect/phantom tooltips for magics
* `254 <https://github.com/ipython/ipython/issues/254>`_: newparallel branch (add zmq.parallel submodule)
* `334 <https://github.com/ipython/ipython/issues/334>`_: Hard reset
* `316 <https://github.com/ipython/ipython/issues/316>`_: Unicode win process
* `332 <https://github.com/ipython/ipython/issues/332>`_: AST splitter
* `325 <https://github.com/ipython/ipython/issues/325>`_: Removetwisted
* `330 <https://github.com/ipython/ipython/issues/330>`_: Magic pastebin
* `309 <https://github.com/ipython/ipython/issues/309>`_: Bug tests for GH Issues 238, 284, 306, 307. Skip module machinery if not installed. Known failures reported as 'K'
* `331 <https://github.com/ipython/ipython/issues/331>`_: Tweak config loader for PyPy compatibility.
* `319 <https://github.com/ipython/ipython/issues/319>`_: Rewrite code to restore readline history after an action
* `329 <https://github.com/ipython/ipython/issues/329>`_: Do not store file contents in history when running a .ipy file.
* `179 <https://github.com/ipython/ipython/issues/179>`_: Html notebook
* `323 <https://github.com/ipython/ipython/issues/323>`_: Add missing external.pexpect to packages
* `295 <https://github.com/ipython/ipython/issues/295>`_: Magic local scope
* `315 <https://github.com/ipython/ipython/issues/315>`_: Unicode magic args
* `310 <https://github.com/ipython/ipython/issues/310>`_: allow Unicode Command-Line options
* `313 <https://github.com/ipython/ipython/issues/313>`_: Readline shortcuts
* `311 <https://github.com/ipython/ipython/issues/311>`_: Qtconsole exit
* `312 <https://github.com/ipython/ipython/issues/312>`_: History memory
* `294 <https://github.com/ipython/ipython/issues/294>`_: Issue 290
* `292 <https://github.com/ipython/ipython/issues/292>`_: Issue 31
* `252 <https://github.com/ipython/ipython/issues/252>`_: Unicode issues
* `235 <https://github.com/ipython/ipython/issues/235>`_: Fix history magic command's bugs wrt to full history and add -O option to display full history
* `236 <https://github.com/ipython/ipython/issues/236>`_: History minus p flag
* `261 <https://github.com/ipython/ipython/issues/261>`_: Adapt magic commands to new history system.
* `282 <https://github.com/ipython/ipython/issues/282>`_: SQLite history
* `191 <https://github.com/ipython/ipython/issues/191>`_: Unbundle external libraries
* `199 <https://github.com/ipython/ipython/issues/199>`_: Magic arguments
* `204 <https://github.com/ipython/ipython/issues/204>`_: Emacs completion bugfix
* `293 <https://github.com/ipython/ipython/issues/293>`_: Issue 133
* `249 <https://github.com/ipython/ipython/issues/249>`_: Writing unicode characters to a log file. (IPython 0.10.2.git)
* `283 <https://github.com/ipython/ipython/issues/283>`_: Support for 256-color escape sequences in Qt console
* `281 <https://github.com/ipython/ipython/issues/281>`_: Refactored and improved Qt console's HTML export facility
* `237 <https://github.com/ipython/ipython/issues/237>`_: Fix185 (take two)
* `251 <https://github.com/ipython/ipython/issues/251>`_: Issue 129
* `278 <https://github.com/ipython/ipython/issues/278>`_: add basic XDG_CONFIG_HOME support
* `275 <https://github.com/ipython/ipython/issues/275>`_: inline pylab cuts off labels on log plots
* `280 <https://github.com/ipython/ipython/issues/280>`_: Add %precision magic
* `259 <https://github.com/ipython/ipython/issues/259>`_: Pyside support
* `193 <https://github.com/ipython/ipython/issues/193>`_: Make ipython cProfile-able
* `272 <https://github.com/ipython/ipython/issues/272>`_: Magic examples
* `219 <https://github.com/ipython/ipython/issues/219>`_: Doc magic pycat
* `221 <https://github.com/ipython/ipython/issues/221>`_: Doc magic alias
* `230 <https://github.com/ipython/ipython/issues/230>`_: Doc magic edit
* `224 <https://github.com/ipython/ipython/issues/224>`_: Doc magic cpaste
* `229 <https://github.com/ipython/ipython/issues/229>`_: Doc magic pdef
* `273 <https://github.com/ipython/ipython/issues/273>`_: Docs build
* `228 <https://github.com/ipython/ipython/issues/228>`_: Doc magic who
* `233 <https://github.com/ipython/ipython/issues/233>`_: Doc magic cd
* `226 <https://github.com/ipython/ipython/issues/226>`_: Doc magic pwd
* `218 <https://github.com/ipython/ipython/issues/218>`_: Doc magic history
* `231 <https://github.com/ipython/ipython/issues/231>`_: Doc magic reset
* `225 <https://github.com/ipython/ipython/issues/225>`_: Doc magic save
* `222 <https://github.com/ipython/ipython/issues/222>`_: Doc magic timeit
* `223 <https://github.com/ipython/ipython/issues/223>`_: Doc magic colors
* `203 <https://github.com/ipython/ipython/issues/203>`_: Small typos in zmq/blockingkernelmanager.py
* `227 <https://github.com/ipython/ipython/issues/227>`_: Doc magic logon
* `232 <https://github.com/ipython/ipython/issues/232>`_: Doc magic profile
* `264 <https://github.com/ipython/ipython/issues/264>`_: Kernel logging
* `220 <https://github.com/ipython/ipython/issues/220>`_: Doc magic edit
* `268 <https://github.com/ipython/ipython/issues/268>`_: PyZMQ >= 2.0.10
* `267 <https://github.com/ipython/ipython/issues/267>`_: GitHub Pages (again)
* `266 <https://github.com/ipython/ipython/issues/266>`_: OSX-specific fixes to the Qt console
* `255 <https://github.com/ipython/ipython/issues/255>`_: Gitwash typo
* `265 <https://github.com/ipython/ipython/issues/265>`_: Fix string input2
* `260 <https://github.com/ipython/ipython/issues/260>`_: Kernel crash with empty history
* `243 <https://github.com/ipython/ipython/issues/243>`_: New display system
* `242 <https://github.com/ipython/ipython/issues/242>`_: Fix terminal exit
* `250 <https://github.com/ipython/ipython/issues/250>`_: always use Session.send
* `239 <https://github.com/ipython/ipython/issues/239>`_: Makefile command & script for GitHub Pages
* `244 <https://github.com/ipython/ipython/issues/244>`_: My exit
* `234 <https://github.com/ipython/ipython/issues/234>`_: Timed history save
* `217 <https://github.com/ipython/ipython/issues/217>`_: Doc magic lsmagic
* `215 <https://github.com/ipython/ipython/issues/215>`_: History fix
* `195 <https://github.com/ipython/ipython/issues/195>`_: Formatters
* `192 <https://github.com/ipython/ipython/issues/192>`_: Ready colorize bug
* `198 <https://github.com/ipython/ipython/issues/198>`_: Windows workdir
* `174 <https://github.com/ipython/ipython/issues/174>`_: Whitespace cleanup
* `188 <https://github.com/ipython/ipython/issues/188>`_: Version info: update our version management system to use git.
* `158 <https://github.com/ipython/ipython/issues/158>`_: Ready for merge
* `187 <https://github.com/ipython/ipython/issues/187>`_: Resolved Print shortcut collision with ctrl-P emacs binding
* `183 <https://github.com/ipython/ipython/issues/183>`_: cleanup of exit/quit commands for qt console
* `184 <https://github.com/ipython/ipython/issues/184>`_: Logo added to sphinx docs
* `180 <https://github.com/ipython/ipython/issues/180>`_: Cleanup old code
* `171 <https://github.com/ipython/ipython/issues/171>`_: Expose Pygments styles as options
* `170 <https://github.com/ipython/ipython/issues/170>`_: HTML Fixes
* `172 <https://github.com/ipython/ipython/issues/172>`_: Fix del method exit test
* `164 <https://github.com/ipython/ipython/issues/164>`_: Qt frontend shutdown behavior fixes and enhancements
* `167 <https://github.com/ipython/ipython/issues/167>`_: Added HTML export
* `163 <https://github.com/ipython/ipython/issues/163>`_: Execution refactor
* `159 <https://github.com/ipython/ipython/issues/159>`_: Ipy3 preparation
* `155 <https://github.com/ipython/ipython/issues/155>`_: Ready startup fix
* `152 <https://github.com/ipython/ipython/issues/152>`_: 0.10.1 sge
* `151 <https://github.com/ipython/ipython/issues/151>`_: mk_object_info -> object_info
* `149 <https://github.com/ipython/ipython/issues/149>`_: Simple bug-fix

Regular issues (285):

* `630 <https://github.com/ipython/ipython/issues/630>`_: new.py in pwd prevents ipython from starting
* `623 <https://github.com/ipython/ipython/issues/623>`_: Execute DirectView commands while running LoadBalancedView tasks
* `437 <https://github.com/ipython/ipython/issues/437>`_: Users should have autocompletion in the notebook
* `583 <https://github.com/ipython/ipython/issues/583>`_: update manpages
* `594 <https://github.com/ipython/ipython/issues/594>`_: irunner command line options defer to file extensions
* `603 <https://github.com/ipython/ipython/issues/603>`_: Users should see colored text in tracebacks and the pager
* `597 <https://github.com/ipython/ipython/issues/597>`_: UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2
* `608 <https://github.com/ipython/ipython/issues/608>`_: Organize and layout buttons in the notebook panel sections
* `609 <https://github.com/ipython/ipython/issues/609>`_: Implement controls in the Kernel panel section
* `611 <https://github.com/ipython/ipython/issues/611>`_: Add kernel status widget back to notebook
* `610 <https://github.com/ipython/ipython/issues/610>`_: Implement controls in the Cell section panel
* `612 <https://github.com/ipython/ipython/issues/612>`_: Implement Help panel section
* `621 <https://github.com/ipython/ipython/issues/621>`_: [qtconsole] on windows xp, cannot  PageUp more than once
* `616 <https://github.com/ipython/ipython/issues/616>`_: Store exit status of last command
* `605 <https://github.com/ipython/ipython/issues/605>`_: Users should be able to open different notebooks in the cwd
* `302 <https://github.com/ipython/ipython/issues/302>`_: Users should see a consistent behavior in the Out prompt in the html  notebook
* `435 <https://github.com/ipython/ipython/issues/435>`_: Notebook should not import anything by default
* `595 <https://github.com/ipython/ipython/issues/595>`_: qtconsole command issue
* `588 <https://github.com/ipython/ipython/issues/588>`_: ipython-qtconsole uses 100% CPU
* `586 <https://github.com/ipython/ipython/issues/586>`_: ? + plot() Command B0rks QTConsole Strangely
* `585 <https://github.com/ipython/ipython/issues/585>`_: %pdoc throws Errors for classes without __init__ or docstring
* `584 <https://github.com/ipython/ipython/issues/584>`_:  %pdoc throws TypeError
* `580 <https://github.com/ipython/ipython/issues/580>`_: Client instantiation AssertionError
* `569 <https://github.com/ipython/ipython/issues/569>`_: UnicodeDecodeError during startup
* `572 <https://github.com/ipython/ipython/issues/572>`_: Indented command hits error
* `573 <https://github.com/ipython/ipython/issues/573>`_: -wthread breaks indented top-level statements
* `570 <https://github.com/ipython/ipython/issues/570>`_: "--pylab inline" vs. "--pylab=inline"
* `566 <https://github.com/ipython/ipython/issues/566>`_: Can't use exec_file in config file
* `562 <https://github.com/ipython/ipython/issues/562>`_: update docs to reflect '--args=values'
* `558 <https://github.com/ipython/ipython/issues/558>`_: triple quote and %s at beginning of line
* `554 <https://github.com/ipython/ipython/issues/554>`_: Update 0.11 docs to explain Qt console and how to do a clean install
* `553 <https://github.com/ipython/ipython/issues/553>`_: embed() fails if config files not installed
* `8 <https://github.com/ipython/ipython/issues/8>`_: Ensure %gui qt works with new Mayavi and pylab
* `269 <https://github.com/ipython/ipython/issues/269>`_: Provide compatibility api for IPython.Shell().start().mainloop()
* `66 <https://github.com/ipython/ipython/issues/66>`_: Update the main What's New document to reflect work on 0.11
* `549 <https://github.com/ipython/ipython/issues/549>`_: Don't check for 'linux2' value in sys.platform
* `505 <https://github.com/ipython/ipython/issues/505>`_: Qt windows created within imported functions won't show()
* `545 <https://github.com/ipython/ipython/issues/545>`_: qtconsole ignores exec_lines
* `371 <https://github.com/ipython/ipython/issues/371>`_: segfault in qtconsole when kernel quits
* `377 <https://github.com/ipython/ipython/issues/377>`_: Failure: error (nothing to repeat)
* `544 <https://github.com/ipython/ipython/issues/544>`_: Ipython qtconsole pylab config issue.
* `543 <https://github.com/ipython/ipython/issues/543>`_: RuntimeError in completer 
* `440 <https://github.com/ipython/ipython/issues/440>`_: %run filename autocompletion "The kernel heartbeat has been inactive ... " error
* `541 <https://github.com/ipython/ipython/issues/541>`_: log_level is broken in the  ipython Application
* `369 <https://github.com/ipython/ipython/issues/369>`_: windows source install doesn't create scripts correctly
* `351 <https://github.com/ipython/ipython/issues/351>`_: Make sure that the Windows installer handles the top-level IPython scripts.
* `512 <https://github.com/ipython/ipython/issues/512>`_: Two displayhooks in zmq
* `340 <https://github.com/ipython/ipython/issues/340>`_: Make sure that the Windows HPC scheduler support is working for 0.11
* `98 <https://github.com/ipython/ipython/issues/98>`_: Should be able to get help on an object mid-command
* `529 <https://github.com/ipython/ipython/issues/529>`_: unicode problem in qtconsole for windows
* `476 <https://github.com/ipython/ipython/issues/476>`_: Separate input area in Qt Console
* `175 <https://github.com/ipython/ipython/issues/175>`_: Qt console needs configuration support
* `156 <https://github.com/ipython/ipython/issues/156>`_: Key history lost when debugging program crash
* `470 <https://github.com/ipython/ipython/issues/470>`_: decorator: uses deprecated features
* `30 <https://github.com/ipython/ipython/issues/30>`_: readline in OS X does not have correct key bindings
* `503 <https://github.com/ipython/ipython/issues/503>`_: merge IPython.parallel.streamsession and IPython.zmq.session
* `456 <https://github.com/ipython/ipython/issues/456>`_: pathname in document punctuated by dots not slashes
* `451 <https://github.com/ipython/ipython/issues/451>`_: Allow switching the default image format for inline mpl backend
* `79 <https://github.com/ipython/ipython/issues/79>`_: Implement more robust handling of config stages in Application
* `522 <https://github.com/ipython/ipython/issues/522>`_: Encoding problems
* `524 <https://github.com/ipython/ipython/issues/524>`_: otool should not be unconditionally called on osx
* `523 <https://github.com/ipython/ipython/issues/523>`_: Get profile and config file inheritance working
* `519 <https://github.com/ipython/ipython/issues/519>`_: qtconsole --pure: "TypeError: string indices must be integers, not str"
* `516 <https://github.com/ipython/ipython/issues/516>`_: qtconsole --pure: "KeyError: 'ismagic'"
* `520 <https://github.com/ipython/ipython/issues/520>`_: qtconsole --pure: "TypeError: string indices must be integers, not str"
* `450 <https://github.com/ipython/ipython/issues/450>`_: resubmitted tasks sometimes stuck as pending
* `518 <https://github.com/ipython/ipython/issues/518>`_: JSON serialization problems with ObjectId type (MongoDB)
* `178 <https://github.com/ipython/ipython/issues/178>`_: Channels should be named for their function, not their socket type
* `515 <https://github.com/ipython/ipython/issues/515>`_: [ipcluster] termination on os x
* `510 <https://github.com/ipython/ipython/issues/510>`_: qtconsole: indentation problem printing numpy arrays
* `508 <https://github.com/ipython/ipython/issues/508>`_: "AssertionError: Missing message part." in ipython-qtconsole --pure
* `499 <https://github.com/ipython/ipython/issues/499>`_: "ZMQError: Interrupted system call" when saving inline figure
* `426 <https://github.com/ipython/ipython/issues/426>`_: %edit magic fails in qtconsole
* `497 <https://github.com/ipython/ipython/issues/497>`_: Don't show info from .pyd files
* `493 <https://github.com/ipython/ipython/issues/493>`_: QFont::setPointSize: Point size <= 0 (0), must be greater than 0
* `489 <https://github.com/ipython/ipython/issues/489>`_: UnicodeEncodeError in qt.svg.save_svg
* `458 <https://github.com/ipython/ipython/issues/458>`_: embed() doesn't load default config
* `488 <https://github.com/ipython/ipython/issues/488>`_: Using IPython with RubyPython leads to problems with IPython.parallel.client.client.Client.__init()
* `401 <https://github.com/ipython/ipython/issues/401>`_: Race condition when running lbview.apply() fast multiple times in loop
* `168 <https://github.com/ipython/ipython/issues/168>`_: Scrub Launchpad links from code, docs
* `141 <https://github.com/ipython/ipython/issues/141>`_: garbage collection problem (revisited)
* `59 <https://github.com/ipython/ipython/issues/59>`_: test_magic.test_obj_del fails on win32
* `457 <https://github.com/ipython/ipython/issues/457>`_: Backgrounded Tasks not Allowed?  (but easy to slip by . . .)
* `297 <https://github.com/ipython/ipython/issues/297>`_: Shouldn't use pexpect for subprocesses in in-process terminal frontend
* `110 <https://github.com/ipython/ipython/issues/110>`_: magic to return exit status
* `473 <https://github.com/ipython/ipython/issues/473>`_: OSX readline detection fails in the debugger
* `466 <https://github.com/ipython/ipython/issues/466>`_: tests fail without unicode filename support
* `468 <https://github.com/ipython/ipython/issues/468>`_: iptest script has 0 exit code even when tests fail
* `465 <https://github.com/ipython/ipython/issues/465>`_: client.db_query() behaves different with SQLite and MongoDB
* `467 <https://github.com/ipython/ipython/issues/467>`_: magic_install_default_config test fails when there is no .ipython directory
* `463 <https://github.com/ipython/ipython/issues/463>`_: IPYTHON_DIR (and IPYTHONDIR) don't expand tilde to '~' directory
* `446 <https://github.com/ipython/ipython/issues/446>`_: Test machinery is imported at normal runtime
* `438 <https://github.com/ipython/ipython/issues/438>`_: Users should be able to use Up/Down for cell navigation
* `439 <https://github.com/ipython/ipython/issues/439>`_: Users should be able to copy notebook input and output
* `291 <https://github.com/ipython/ipython/issues/291>`_: Rename special display methods and put them lower in priority than display functions
* `447 <https://github.com/ipython/ipython/issues/447>`_: Instantiating classes without __init__ function causes kernel to crash
* `444 <https://github.com/ipython/ipython/issues/444>`_: Ctrl + t in WxIPython Causes Unexpected Behavior
* `445 <https://github.com/ipython/ipython/issues/445>`_: qt and console Based Startup Errors
* `428 <https://github.com/ipython/ipython/issues/428>`_: ipcluster doesn't handle stale pid info well
* `434 <https://github.com/ipython/ipython/issues/434>`_: 10.0.2 seg fault with rpy2
* `441 <https://github.com/ipython/ipython/issues/441>`_: Allow running a block of code in a file
* `432 <https://github.com/ipython/ipython/issues/432>`_: Silent request fails
* `409 <https://github.com/ipython/ipython/issues/409>`_: Test failure in IPython.lib
* `402 <https://github.com/ipython/ipython/issues/402>`_: History section of messaging spec is incorrect
* `88 <https://github.com/ipython/ipython/issues/88>`_: Error when inputting UTF8 CJK characters
* `366 <https://github.com/ipython/ipython/issues/366>`_: Ctrl-K should kill line and store it, so that Ctrl-y can yank it back
* `425 <https://github.com/ipython/ipython/issues/425>`_: typo in %gui magic help
* `304 <https://github.com/ipython/ipython/issues/304>`_: Persistent warnings if old configuration files exist
* `216 <https://github.com/ipython/ipython/issues/216>`_: crash of ipython when alias is used with %s and echo
* `412 <https://github.com/ipython/ipython/issues/412>`_: add support to automatic retry of tasks
* `411 <https://github.com/ipython/ipython/issues/411>`_: add support to continue tasks
* `417 <https://github.com/ipython/ipython/issues/417>`_: IPython should display things unsorted if it can't sort them
* `416 <https://github.com/ipython/ipython/issues/416>`_: wrong encode when printing unicode string
* `376 <https://github.com/ipython/ipython/issues/376>`_: Failing InputsplitterTest
* `405 <https://github.com/ipython/ipython/issues/405>`_: TraitError in traitlets.py(332) on any input
* `392 <https://github.com/ipython/ipython/issues/392>`_: UnicodeEncodeError on start
* `137 <https://github.com/ipython/ipython/issues/137>`_: sys.getfilesystemencoding return value not checked
* `300 <https://github.com/ipython/ipython/issues/300>`_: Users should be able to manage kernels and kernel sessions from the notebook UI
* `301 <https://github.com/ipython/ipython/issues/301>`_: Users should have access to working Kernel, Tabs, Edit, Help menus in the notebook
* `396 <https://github.com/ipython/ipython/issues/396>`_: cursor move triggers a lot of IO access
* `379 <https://github.com/ipython/ipython/issues/379>`_: Minor doc nit: --paging argument
* `399 <https://github.com/ipython/ipython/issues/399>`_: Add task queue limit in engine when load-balancing
* `78 <https://github.com/ipython/ipython/issues/78>`_: StringTask won't take unicode code strings
* `391 <https://github.com/ipython/ipython/issues/391>`_: MongoDB.add_record() does not work in 0.11dev
* `365 <https://github.com/ipython/ipython/issues/365>`_: newparallel on Windows
* `386 <https://github.com/ipython/ipython/issues/386>`_: FAIL: test that pushed functions have access to globals
* `387 <https://github.com/ipython/ipython/issues/387>`_: Interactively defined functions can't access user namespace
* `118 <https://github.com/ipython/ipython/issues/118>`_: Snow Leopard ipy_vimserver POLL error
* `394 <https://github.com/ipython/ipython/issues/394>`_: System escape interpreted in multi-line string
* `26 <https://github.com/ipython/ipython/issues/26>`_: find_job_cmd is too hasty to fail on Windows
* `368 <https://github.com/ipython/ipython/issues/368>`_: Installation instructions in dev docs are completely wrong
* `380 <https://github.com/ipython/ipython/issues/380>`_: qtconsole pager RST - HTML not happening consistently
* `367 <https://github.com/ipython/ipython/issues/367>`_: Qt console doesn't support ibus input method
* `375 <https://github.com/ipython/ipython/issues/375>`_: Missing libraries cause ImportError in tests
* `71 <https://github.com/ipython/ipython/issues/71>`_: temp file errors in iptest IPython.core
* `350 <https://github.com/ipython/ipython/issues/350>`_: Decide how to handle displayhook being triggered multiple times
* `360 <https://github.com/ipython/ipython/issues/360>`_: Remove `runlines` method
* `125 <https://github.com/ipython/ipython/issues/125>`_: Exec lines in config should not contribute to line numbering or history
* `20 <https://github.com/ipython/ipython/issues/20>`_: Robust readline support on OS X's builtin Python
* `147 <https://github.com/ipython/ipython/issues/147>`_: On Windows, %page is being too restrictive to split line by \r\n only
* `326 <https://github.com/ipython/ipython/issues/326>`_: Update docs and examples for parallel stuff to reflect movement away from Twisted
* `341 <https://github.com/ipython/ipython/issues/341>`_: FIx Parallel Magics for newparallel
* `338 <https://github.com/ipython/ipython/issues/338>`_: Usability improvements to Qt console
* `142 <https://github.com/ipython/ipython/issues/142>`_: unexpected auto-indenting when varibles names that start with 'pass' 
* `296 <https://github.com/ipython/ipython/issues/296>`_: Automatic PDB via %pdb doesn't work
* `337 <https://github.com/ipython/ipython/issues/337>`_: exit( and quit( in Qt console produces phantom signature/docstring popup, even though quit() or exit() raises NameError
* `318 <https://github.com/ipython/ipython/issues/318>`_: %debug broken in master: invokes missing save_history() method
* `307 <https://github.com/ipython/ipython/issues/307>`_: lines ending with semicolon should not go to cache
* `104 <https://github.com/ipython/ipython/issues/104>`_: have ipengine run start-up scripts before registering with the controller
* `33 <https://github.com/ipython/ipython/issues/33>`_: The skip_doctest decorator is failing to work on Shell.MatplotlibShellBase.magic_run
* `336 <https://github.com/ipython/ipython/issues/336>`_: Missing figure development/figs/iopubfade.png for docs
* `49 <https://github.com/ipython/ipython/issues/49>`_: %clear should also delete _NN references and Out[NN] ones
* `335 <https://github.com/ipython/ipython/issues/335>`_: using setuptools installs every script twice
* `306 <https://github.com/ipython/ipython/issues/306>`_: multiline strings at end of input cause noop
* `327 <https://github.com/ipython/ipython/issues/327>`_: PyPy compatibility
* `328 <https://github.com/ipython/ipython/issues/328>`_: %run script.ipy raises "ERROR! Session/line number was not unique in database."
* `7 <https://github.com/ipython/ipython/issues/7>`_: Update the changes doc to reflect the kernel config work
* `303 <https://github.com/ipython/ipython/issues/303>`_: Users should be able to scroll a notebook w/o moving the menu/buttons
* `322 <https://github.com/ipython/ipython/issues/322>`_: Embedding an interactive IPython shell 
* `321 <https://github.com/ipython/ipython/issues/321>`_: %debug broken in master
* `287 <https://github.com/ipython/ipython/issues/287>`_: Crash when using %macros in sqlite-history branch
* `55 <https://github.com/ipython/ipython/issues/55>`_: Can't edit files whose names begin with numbers
* `284 <https://github.com/ipython/ipython/issues/284>`_: In variable no longer works in 0.11
* `92 <https://github.com/ipython/ipython/issues/92>`_: Using multiprocessing module crashes parallel iPython
* `262 <https://github.com/ipython/ipython/issues/262>`_: Fail to recover history after force-kill.
* `320 <https://github.com/ipython/ipython/issues/320>`_: Tab completing re.search objects crashes IPython
* `317 <https://github.com/ipython/ipython/issues/317>`_: IPython.kernel: parallel map issues
* `197 <https://github.com/ipython/ipython/issues/197>`_: ipython-qtconsole unicode problem in magic ls
* `305 <https://github.com/ipython/ipython/issues/305>`_: more readline shortcuts in qtconsole
* `314 <https://github.com/ipython/ipython/issues/314>`_: Multi-line, multi-block cells can't be executed.
* `308 <https://github.com/ipython/ipython/issues/308>`_: Test suite should set sqlite history to work in :memory:
* `202 <https://github.com/ipython/ipython/issues/202>`_: Matplotlib native 'MacOSX' backend broken in '-pylab' mode
* `196 <https://github.com/ipython/ipython/issues/196>`_: IPython can't deal with unicode file name.
* `25 <https://github.com/ipython/ipython/issues/25>`_: unicode bug - encoding input
* `290 <https://github.com/ipython/ipython/issues/290>`_: try/except/else clauses can't be typed, code input stops too early.
* `43 <https://github.com/ipython/ipython/issues/43>`_: Implement SSH support in ipcluster
* `6 <https://github.com/ipython/ipython/issues/6>`_: Update the Sphinx docs for the new ipcluster
* `9 <https://github.com/ipython/ipython/issues/9>`_: Getting "DeadReferenceError: Calling Stale Broker" after ipcontroller restart
* `132 <https://github.com/ipython/ipython/issues/132>`_: Ipython prevent south from working
* `27 <https://github.com/ipython/ipython/issues/27>`_: generics.complete_object broken
* `60 <https://github.com/ipython/ipython/issues/60>`_: Improve absolute import management for iptest.py
* `31 <https://github.com/ipython/ipython/issues/31>`_: Issues in magic_whos code
* `52 <https://github.com/ipython/ipython/issues/52>`_: Document testing process better
* `44 <https://github.com/ipython/ipython/issues/44>`_: Merge history from multiple sessions
* `182 <https://github.com/ipython/ipython/issues/182>`_: ipython q4thread in version 10.1 not starting properly
* `143 <https://github.com/ipython/ipython/issues/143>`_: Ipython.gui.wx.ipython_view.IPShellWidget: ignores user*_ns arguments
* `127 <https://github.com/ipython/ipython/issues/127>`_: %edit does not work on filenames consisted of pure numbers
* `126 <https://github.com/ipython/ipython/issues/126>`_: Can't transfer command line argument to script
* `28 <https://github.com/ipython/ipython/issues/28>`_: Offer finer control for initialization of input streams
* `58 <https://github.com/ipython/ipython/issues/58>`_: ipython change char '0xe9' to 4 spaces
* `68 <https://github.com/ipython/ipython/issues/68>`_: Problems with Control-C stopping ipcluster on Windows/Python2.6
* `24 <https://github.com/ipython/ipython/issues/24>`_: ipcluster does not start all the engines
* `240 <https://github.com/ipython/ipython/issues/240>`_: Incorrect method displayed in %psource
* `120 <https://github.com/ipython/ipython/issues/120>`_: inspect.getsource fails for functions defined on command line
* `212 <https://github.com/ipython/ipython/issues/212>`_: IPython ignores exceptions in the first evaulation of class attrs
* `108 <https://github.com/ipython/ipython/issues/108>`_: ipython disables python logger
* `100 <https://github.com/ipython/ipython/issues/100>`_: Overzealous introspection
* `18 <https://github.com/ipython/ipython/issues/18>`_: %cpaste freeze sync frontend
* `200 <https://github.com/ipython/ipython/issues/200>`_: Unicode error when starting ipython in a folder with non-ascii path
* `130 <https://github.com/ipython/ipython/issues/130>`_: Deadlock when importing a module that creates an IPython client
* `134 <https://github.com/ipython/ipython/issues/134>`_: multline block scrolling
* `46 <https://github.com/ipython/ipython/issues/46>`_: Input to %timeit is not preparsed
* `285 <https://github.com/ipython/ipython/issues/285>`_: ipcluster local -n 4 fails
* `205 <https://github.com/ipython/ipython/issues/205>`_: In the Qt console, Tab should insert 4 spaces when not completing
* `145 <https://github.com/ipython/ipython/issues/145>`_: Bug on MSW sytems: idle can not be set as default IPython editor. Fix Suggested.
* `77 <https://github.com/ipython/ipython/issues/77>`_: ipython oops in cygwin
* `121 <https://github.com/ipython/ipython/issues/121>`_: If plot windows are closed via window controls, no more plotting is possible.
* `111 <https://github.com/ipython/ipython/issues/111>`_: Iterator version of TaskClient.map() that returns results as they become available
* `109 <https://github.com/ipython/ipython/issues/109>`_: WinHPCLauncher is a hard dependency that causes errors in the test suite
* `86 <https://github.com/ipython/ipython/issues/86>`_: Make IPython work with multiprocessing
* `15 <https://github.com/ipython/ipython/issues/15>`_: Implement SGE support in ipcluster
* `3 <https://github.com/ipython/ipython/issues/3>`_: Implement PBS support in ipcluster
* `53 <https://github.com/ipython/ipython/issues/53>`_: Internal Python error in the inspect module
* `74 <https://github.com/ipython/ipython/issues/74>`_: Manager() [from multiprocessing module] hangs ipythonx but not ipython
* `51 <https://github.com/ipython/ipython/issues/51>`_: Out not working with ipythonx
* `201 <https://github.com/ipython/ipython/issues/201>`_: use session.send throughout zmq code
* `115 <https://github.com/ipython/ipython/issues/115>`_: multiline specials not defined in 0.11 branch
* `93 <https://github.com/ipython/ipython/issues/93>`_: when looping, cursor appears at leftmost point in newline
* `133 <https://github.com/ipython/ipython/issues/133>`_: whitespace after Source introspection
* `50 <https://github.com/ipython/ipython/issues/50>`_: Ctrl-C with -gthread on Windows, causes uncaught IOError
* `65 <https://github.com/ipython/ipython/issues/65>`_: Do not use .message attributes in exceptions, deprecated in 2.6
* `76 <https://github.com/ipython/ipython/issues/76>`_: syntax error when raise is inside except process
* `107 <https://github.com/ipython/ipython/issues/107>`_: bdist_rpm causes traceback looking for a non-existant file
* `113 <https://github.com/ipython/ipython/issues/113>`_: initial magic ? (question mark) fails before wildcard
* `128 <https://github.com/ipython/ipython/issues/128>`_: Pdb instance has no attribute 'curframe'
* `139 <https://github.com/ipython/ipython/issues/139>`_: running with -pylab pollutes namespace
* `140 <https://github.com/ipython/ipython/issues/140>`_: malloc error during tab completion of numpy array member functions starting with 'c'
* `153 <https://github.com/ipython/ipython/issues/153>`_: ipy_vimserver traceback on Windows
* `154 <https://github.com/ipython/ipython/issues/154>`_: using ipython in Slicer3 show how os.environ['HOME'] is not defined
* `185 <https://github.com/ipython/ipython/issues/185>`_: show() blocks in pylab mode with ipython 0.10.1 
* `189 <https://github.com/ipython/ipython/issues/189>`_: Crash on tab completion
* `274 <https://github.com/ipython/ipython/issues/274>`_: bashism in sshx.sh
* `276 <https://github.com/ipython/ipython/issues/276>`_: Calling `sip.setapi` does not work if app has already imported from PyQt4
* `277 <https://github.com/ipython/ipython/issues/277>`_: matplotlib.image imgshow from 10.1 segfault
* `288 <https://github.com/ipython/ipython/issues/288>`_: Incorrect docstring in zmq/kernelmanager.py
* `286 <https://github.com/ipython/ipython/issues/286>`_: Fix IPython.Shell compatibility layer
* `99 <https://github.com/ipython/ipython/issues/99>`_: blank lines in history
* `129 <https://github.com/ipython/ipython/issues/129>`_: psearch: TypeError: expected string or buffer
* `190 <https://github.com/ipython/ipython/issues/190>`_: Add option to format float point output
* `246 <https://github.com/ipython/ipython/issues/246>`_: Application not conforms XDG Base Directory Specification
* `48 <https://github.com/ipython/ipython/issues/48>`_: IPython should follow the XDG Base Directory spec for configuration
* `176 <https://github.com/ipython/ipython/issues/176>`_: Make client-side history persistence readline-independent
* `279 <https://github.com/ipython/ipython/issues/279>`_: Backtraces when using ipdb do not respect -colour LightBG setting
* `119 <https://github.com/ipython/ipython/issues/119>`_: Broken type filter in magic_who_ls
* `271 <https://github.com/ipython/ipython/issues/271>`_: Intermittent problem with print output in Qt console.
* `270 <https://github.com/ipython/ipython/issues/270>`_: Small typo in IPython developer’s guide
* `166 <https://github.com/ipython/ipython/issues/166>`_: Add keyboard accelerators to Qt close dialog
* `173 <https://github.com/ipython/ipython/issues/173>`_: asymmetrical ctrl-A/ctrl-E behavior in multiline
* `45 <https://github.com/ipython/ipython/issues/45>`_: Autosave history for robustness
* `162 <https://github.com/ipython/ipython/issues/162>`_: make command history persist in ipythonqt
* `161 <https://github.com/ipython/ipython/issues/161>`_: make ipythonqt exit without dialog when exit() is called
* `263 <https://github.com/ipython/ipython/issues/263>`_: [ipython + numpy] Some test errors 
* `256 <https://github.com/ipython/ipython/issues/256>`_: reset docstring ipython 0.10 
* `258 <https://github.com/ipython/ipython/issues/258>`_: allow caching to avoid matplotlib object referrences
* `248 <https://github.com/ipython/ipython/issues/248>`_: Can't open and read files after upgrade from 0.10 to 0.10.0
* `247 <https://github.com/ipython/ipython/issues/247>`_: ipython + Stackless
* `245 <https://github.com/ipython/ipython/issues/245>`_: Magic save and macro missing newlines, line ranges don't match prompt numbers.
* `241 <https://github.com/ipython/ipython/issues/241>`_: "exit" hangs on terminal version of IPython
* `213 <https://github.com/ipython/ipython/issues/213>`_: ipython -pylab no longer plots interactively on 0.10.1
* `4 <https://github.com/ipython/ipython/issues/4>`_: wx frontend don't display well commands output
* `5 <https://github.com/ipython/ipython/issues/5>`_: ls command not supported in ipythonx wx frontend
* `1 <https://github.com/ipython/ipython/issues/1>`_: Document winhpcjob.py and launcher.py
* `83 <https://github.com/ipython/ipython/issues/83>`_: Usage of testing.util.DeferredTestCase should be replace with twisted.trial.unittest.TestCase
* `117 <https://github.com/ipython/ipython/issues/117>`_: Redesign how Component instances are tracked and queried
* `47 <https://github.com/ipython/ipython/issues/47>`_: IPython.kernel.client cannot be imported inside an engine
* `105 <https://github.com/ipython/ipython/issues/105>`_: Refactor the task dependencies system
* `210 <https://github.com/ipython/ipython/issues/210>`_: 0.10.1 doc mistake - New IPython Sphinx directive error
* `209 <https://github.com/ipython/ipython/issues/209>`_: can't activate IPython parallel magics
* `206 <https://github.com/ipython/ipython/issues/206>`_: Buggy linewrap in Mac OSX Terminal
* `194 <https://github.com/ipython/ipython/issues/194>`_: !sudo <command> displays password in plain text
* `186 <https://github.com/ipython/ipython/issues/186>`_: %edit issue under OS X 10.5 - IPython 0.10.1
* `11 <https://github.com/ipython/ipython/issues/11>`_: Create a daily build PPA for ipython
* `144 <https://github.com/ipython/ipython/issues/144>`_: logo missing from sphinx docs
* `181 <https://github.com/ipython/ipython/issues/181>`_: cls command does not work on windows
* `169 <https://github.com/ipython/ipython/issues/169>`_: Kernel can only be bound to localhost
* `36 <https://github.com/ipython/ipython/issues/36>`_: tab completion does not escape ()
* `177 <https://github.com/ipython/ipython/issues/177>`_: Report tracebacks of interactively entered input
* `148 <https://github.com/ipython/ipython/issues/148>`_: dictionary having multiple keys having frozenset fails to print on iPython
* `160 <https://github.com/ipython/ipython/issues/160>`_: magic_gui throws TypeError when gui magic is used
* `150 <https://github.com/ipython/ipython/issues/150>`_: History entries ending with parentheses corrupt command line on OS X 10.6.4
* `146 <https://github.com/ipython/ipython/issues/146>`_: -ipythondir - using an alternative .ipython dir for rc type stuff
* `114 <https://github.com/ipython/ipython/issues/114>`_: Interactive strings get mangled with "_ip.magic"
* `135 <https://github.com/ipython/ipython/issues/135>`_: crash on  invalid print
* `69 <https://github.com/ipython/ipython/issues/69>`_: Usage of "mycluster" profile in docs and examples
* `37 <https://github.com/ipython/ipython/issues/37>`_: Fix colors in output of ResultList on Windows

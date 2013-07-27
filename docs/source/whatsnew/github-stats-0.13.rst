.. _issues_list_013:

Issues closed in the 0.13 development cycle
===========================================

Issues closed in 0.13
---------------------

GitHub stats since IPython 0.12 (2011/12/19 - 2012/06/30)

These lists are automatically generated, and may be incomplete or contain
duplicates.

The following 62 authors contributed 1760 commits.

* Aaron Culich
* Aaron Meurer
* Alex Kramer
* Andrew Giessel
* Andrew Straw
* André Matos
* Aron Ahmadia
* Ben Edwards
* Benjamin Ragan-Kelley
* Bradley M. Froehle
* Brandon Parsons
* Brian E. Granger
* Carlos Cordoba
* David Hirschfeld
* David Zderic
* Ernie French
* Fernando Perez
* Ian Murray
* Jason Grout
* Jens H Nielsen
* Jez Ng
* Jonathan March
* Jonathan Taylor
* Julian Taylor
* Jörgen Stenarson
* Kent Inverarity
* Marc Abramowitz
* Mark Wiebe
* Matthew Brett
* Matthias BUSSONNIER
* Michael Droettboom
* Mike Hansen
* Nathan Rice
* Pankaj Pandey
* Paul
* Paul Ivanov
* Piotr Zolnierczuk
* Piti Ongmongkolkul
* Puneeth Chaganti
* Robert Kern
* Ross Jones
* Roy Hyunjin Han
* Scott Tsai
* Skipper Seabold
* Stefan van der Walt
* Steven Johnson
* Takafumi Arakaki
* Ted Wright
* Thomas Hisch
* Thomas Kluyver
* Thomas Spura
* Thomi Richards
* Tim Couper
* Timo Paulssen
* Toby Gilham
* Tony S Yu
* W. Trevor King
* Walter Doerwald
* anatoly techtonik
* fawce
* mcelrath
* wilsaj


We closed a total of 1115 issues, 373 pull requests and 742 regular issues;
this is the full list (generated with the script 
:file:`tools/github_stats.py`):

Pull Requests (373):

* :ghpull:`1943`: add screenshot and link into releasenotes
* :ghpull:`1954`: update some example notebooks
* :ghpull:`2048`: move _encode_binary to jsonutil.encode_images
* :ghpull:`2050`: only add quotes around xunit-file on Windows
* :ghpull:`2047`: disable auto-scroll on mozilla
* :ghpull:`2015`: Fixes for %paste with special transformations
* :ghpull:`2046`: Iptest unicode
* :ghpull:`1939`: Namespaces
* :ghpull:`2042`: increase auto-scroll threshold to 100 lines
* :ghpull:`2043`: move RemoteError import to top-level
* :ghpull:`2036`: %alias_magic
* :ghpull:`1968`: Proposal of icons for .ipynb files
* :ghpull:`2037`: remove `ipython-qtconsole` gui-script
* :ghpull:`2038`: add extra clear warning to shell doc
* :ghpull:`2029`: Ship unminified js
* :ghpull:`2007`: Add custom_control and custom_page_control variables to override the Qt widgets used by qtconsole
* :ghpull:`2034`: fix&test push/pull recarrays
* :ghpull:`2028`: Reduce unhelpful information shown by pinfo
* :ghpull:`2030`: check wxPython version in inputhook
* :ghpull:`2024`: Make interactive_usage a bit more rst friendly
* :ghpull:`2031`: disable ^C^C confirmation on Windows
* :ghpull:`2027`: match stdin encoding in frontend readline test
* :ghpull:`2025`: Fix parallel test on WinXP - wait for resource cleanup.
* :ghpull:`2016`: BUG: test runner fails in Windows if filenames contain spaces.
* :ghpull:`2020`: Fix home path expansion test in Windows.
* :ghpull:`2021`: Fix Windows pathname issue in 'odd encoding' test.
* :ghpull:`2022`: don't check writability in test for get_home_dir when HOME is undefined
* :ghpull:`1996`: frontend test tweaks
* :ghpull:`2014`: relax profile regex in notebook
* :ghpull:`2012`: Mono cursor offset
* :ghpull:`2004`: Clarify generic message spec vs. Python message API in docs
* :ghpull:`2010`: notebook: Print a warning (but do not abort) if no webbrowser can be found.
* :ghpull:`2002`: Refactor %magic into a lsmagic_docs API function.
* :ghpull:`1999`: `%magic` help: display line and cell magics in alphabetical order.
* :ghpull:`1981`: Clean BG processes created by %%script on kernel exit
* :ghpull:`1994`: Fix RST misformatting.
* :ghpull:`1951`: minor notebook startup/notebook-dir adjustments
* :ghpull:`1974`: Allow path completion on notebook.
* :ghpull:`1964`: allow multiple instances of a Magic
* :ghpull:`1991`: fix _ofind attr in %page
* :ghpull:`1988`: check for active frontend in update_restart_checkbox
* :ghpull:`1979`: Add support for tox (http://tox.testrun.org/) and Travis CI (http://travis-ci.org/)
* :ghpull:`1970`: dblclick to restore size of images
* :ghpull:`1978`: Notebook names truncating at the first period
* :ghpull:`1825`: second attempt at scrolled long output
* :ghpull:`1934`: Cell/Worksheet metadata
* :ghpull:`1746`: Confirm restart (configuration option, and checkbox UI)
* :ghpull:`1944`: [qtconsole] take %,%% prefix into account for completion
* :ghpull:`1973`: fix another FreeBSD $HOME symlink issue
* :ghpull:`1967`: Fix psums example description in docs
* :ghpull:`1965`: fix for #1678, undo no longer clears cells
* :ghpull:`1952`: avoid duplicate "Websockets closed" dialog on ws close
* :ghpull:`1962`: Support unicode prompts
* :ghpull:`1955`: update to latest version of vim-ipython
* :ghpull:`1945`: Add --proc option to %%script
* :ghpull:`1956`: move import RemoteError after get_exc_info
* :ghpull:`1950`: Fix for copy action (Ctrl+C) when there is no pager defined in qtconsole
* :ghpull:`1948`: Fix help string for InteractiveShell.ast_node_interactivity
* :ghpull:`1942`: swallow stderr of which in utils.process.find_cmd
* :ghpull:`1940`: fix completer css on some Chrome versions
* :ghpull:`1938`: remove remaining references to deprecated XREP/XREQ names
* :ghpull:`1925`: Fix styling of superscripts and subscripts. Closes #1924.
* :ghpull:`1936`: increase duration of save messages
* :ghpull:`1937`: add %save -f
* :ghpull:`1935`: add version checking to pyreadline import test
* :ghpull:`1849`: Octave magics
* :ghpull:`1759`: github, merge PR(s) just by number(s) 
* :ghpull:`1931`: Win py3fixes
* :ghpull:`1933`: oinspect.find_file: Additional safety if file cannot be found.
* :ghpull:`1932`: Fix adding functions to CommandChainDispatcher with equal priority on Py 3
* :ghpull:`1928`: Select NoDB by default
* :ghpull:`1923`: Add IPython syntax support to the %timeit magic, in line and cell mode
* :ghpull:`1926`: Make completer recognize escaped quotes in strings.
* :ghpull:`1893`: Update Parallel Magics and Exception Display
* :ghpull:`1921`: magic_arguments: dedent but otherwise preserve indentation.
* :ghpull:`1919`: Use oinspect in CodeMagics._find_edit_target
* :ghpull:`1918`: don't warn in iptest if deathrow/quarantine are missing
* :ghpull:`1917`: Fix for %pdef on Python 3
* :ghpull:`1913`: Fix for #1428
* :ghpull:`1911`: temporarily skip autoreload tests
* :ghpull:`1909`: Fix for #1908, use os.path.normcase for safe filename comparisons
* :ghpull:`1907`: py3compat fixes for %%script and tests
* :ghpull:`1906`: ofind finds non-unique cell magics
* :ghpull:`1845`: Fixes to inspection machinery for magics
* :ghpull:`1902`: Workaround fix for gh-1632; minimal revert of gh-1424
* :ghpull:`1900`: Cython libs
* :ghpull:`1899`: add ScriptMagics to class list for generated config
* :ghpull:`1898`: minimize manpages
* :ghpull:`1897`: use glob for bad exclusion warning
* :ghpull:`1855`: %%script and %%file magics
* :ghpull:`1870`: add %%capture for capturing stdout/err
* :ghpull:`1861`: Use dvipng to format sympy.Matrix
* :ghpull:`1867`: Fix 1px margin bouncing of selected menu item.
* :ghpull:`1889`: Reconnect when the websocket connection closes unexpectedly
* :ghpull:`1886`: Fix a bug in renaming notebook
* :ghpull:`1895`: Fix error in test suite with ip.system()
* :ghpull:`1762`: add `locate` entry points
* :ghpull:`1883`: Fix vertical offset due to bold/italics, and bad browser fonts.
* :ghpull:`1875`: re-write columnize, with intermediate step.
* :ghpull:`1851`: new completer for qtconsole.
* :ghpull:`1892`: Remove suspicious quotes in interactiveshell.py
* :ghpull:`1864`: Rmagic exceptions
* :ghpull:`1829`: [notebook] don't care about leading prct in completion
* :ghpull:`1832`: Make svg, jpeg and png images resizable in notebook.
* :ghpull:`1674`: HTML Notebook carriage-return handling, take 2
* :ghpull:`1882`: Remove importlib dependency which not available in Python 2.6.
* :ghpull:`1879`: Correct stack depth for variable expansion in !system commands
* :ghpull:`1841`: [notebook] deduplicate completion results
* :ghpull:`1850`: Remove args/kwargs handling in TryNext, fix %paste error messages.
* :ghpull:`1663`: Keep line-endings in ipynb
* :ghpull:`1815`: Make : invalid in filenames in the Notebook JS code.
* :ghpull:`1819`: doc: cleanup the parallel psums example a little
* :ghpull:`1839`: External cleanup
* :ghpull:`1782`: fix Magic menu in qtconsole, split in groups
* :ghpull:`1862`: Minor bind_kernel improvements
* :ghpull:`1857`: Prevent jumping of window to input when output is clicked.
* :ghpull:`1856`: Fix 1px jumping of cells and menus in Notebook.
* :ghpull:`1852`: fix chained resubmissions
* :ghpull:`1780`: Rmagic extension
* :ghpull:`1847`: add InlineBackend to ConsoleApp class list
* :ghpull:`1836`: preserve header for resubmitted tasks
* :ghpull:`1828`: change default extension to .ipy for %save -r
* :ghpull:`1800`: Reintroduce recall
* :ghpull:`1830`: lsmagic lists magics in alphabetical order
* :ghpull:`1773`: Update SymPy profile: SymPy's latex() can now print set and frozenset
* :ghpull:`1761`: Edited documentation to use IPYTHONDIR in place of ~/.ipython
* :ghpull:`1822`: aesthetics pass on AsyncResult.display_outputs
* :ghpull:`1821`: ENTER submits the rename notebook dialog.
* :ghpull:`1820`: NotebookApp: Make the number of ports to retry user configurable.
* :ghpull:`1816`: Always use filename as the notebook name.
* :ghpull:`1813`: Add assert_in method to nose for Python 2.6
* :ghpull:`1711`: New Tooltip, New Completer and JS Refactor
* :ghpull:`1798`: a few simple fixes for docs/parallel
* :ghpull:`1812`: Ensure AsyncResult.display_outputs doesn't display empty streams
* :ghpull:`1811`: warn on nonexistent exclusions in iptest
* :ghpull:`1810`: fix for #1809, failing tests in IPython.zmq
* :ghpull:`1808`: Reposition alternate upload for firefox [need cross browser/OS/language test]
* :ghpull:`1742`: Check for custom_exceptions only once
* :ghpull:`1807`: add missing cython exclusion in iptest
* :ghpull:`1805`: Fixed a vcvarsall.bat error on win32/Py2.7 when trying to compile with m...
* :ghpull:`1739`: Dashboard improvement (necessary merge of #1658 and #1676 + fix #1492)
* :ghpull:`1770`: Cython related magic functions
* :ghpull:`1707`: Accept --gui=<...> switch in IPython qtconsole.
* :ghpull:`1797`: Fix comment which breaks Emacs syntax highlighting.
* :ghpull:`1795`: fix %gui magic
* :ghpull:`1793`: Raise repr limit for strings to 80 characters (from 30).
* :ghpull:`1794`: don't use XDG path on OS X
* :ghpull:`1792`: Unicode-aware logger
* :ghpull:`1791`: update zmqshell magics
* :ghpull:`1787`: DOC: Remove regression from qt-console docs.
* :ghpull:`1758`: test_pr, fallback on http if git protocol fail, and SSL errors...
* :ghpull:`1748`: Fix some tests for Python 3.3
* :ghpull:`1755`: test for pygments before running qt tests
* :ghpull:`1771`: Make default value of interactivity passed to run_ast_nodes configurable
* :ghpull:`1784`: restore loadpy to load
* :ghpull:`1768`: Update parallel magics
* :ghpull:`1779`: Tidy up error raising in magic decorators.
* :ghpull:`1769`: Allow cell mode timeit without setup code.
* :ghpull:`1716`: Fix for fake filenames in verbose traceback
* :ghpull:`1763`: [qtconsole] fix append_plain_html -> append_html
* :ghpull:`1732`: Refactoring of the magics system and implementation of cell magics
* :ghpull:`1630`: Merge divergent Kernel implementations
* :ghpull:`1705`: [notebook] Make pager resizable, and remember size...
* :ghpull:`1606`: Share code for %pycat and %loadpy, make %pycat aware of URLs
* :ghpull:`1757`: Open IPython notebook hyperlinks in a new window using target=_blank
* :ghpull:`1754`: Fix typo enconters->encounters
* :ghpull:`1753`: Clear window title when kernel is restarted
* :ghpull:`1449`: Fix for bug #735 : Images missing from XML/SVG export
* :ghpull:`1743`: Tooltip completer js refactor
* :ghpull:`1681`: add qt config option to clear_on_kernel_restart
* :ghpull:`1733`: Tooltip completer js refactor
* :ghpull:`1727`: terminate kernel after embed_kernel tests
* :ghpull:`1737`: add HistoryManager to ipapp class list
* :ghpull:`1686`: ENH: Open a notebook from the command line
* :ghpull:`1709`: fixes #1708, failing test in arg_split on windows
* :ghpull:`1718`: Use CRegExp trait for regular expressions.
* :ghpull:`1729`: Catch failure in repr() for %whos
* :ghpull:`1726`: use eval for command-line args instead of exec
* :ghpull:`1724`: fix scatter/gather with targets='all'
* :ghpull:`1725`: add --no-ff to git pull in test_pr
* :ghpull:`1721`: Tooltip completer js refactor
* :ghpull:`1657`: Add `wait` optional argument to `hooks.editor`
* :ghpull:`1717`: Define generic sys.ps{1,2,3}, for use by scripts.
* :ghpull:`1691`: Finish PR #1446
* :ghpull:`1710`: update MathJax CDN url for https
* :ghpull:`1713`: Make autocall regexp's configurable.
* :ghpull:`1703`: Allow TryNext to have an error message without it affecting the command chain
* :ghpull:`1714`: minor adjustments to test_pr
* :ghpull:`1704`: ensure all needed qt parts can be imported before settling for one
* :ghpull:`1706`: Mark test_push_numpy_nocopy as a known failure for Python 3
* :ghpull:`1698`: fix tooltip on token with number
* :ghpull:`1245`: pythonw py3k fixes for issue #1226
* :ghpull:`1685`: Add script to test pull request
* :ghpull:`1693`: deprecate IPYTHON_DIR in favor of IPYTHONDIR
* :ghpull:`1695`: Avoid deprecated warnings from ipython-qtconsole.desktop.
* :ghpull:`1694`: Add quote to notebook to allow it to load
* :ghpull:`1689`: Fix sys.path missing '' as first entry in `ipython kernel`.
* :ghpull:`1687`: import Binary from bson instead of pymongo
* :ghpull:`1616`: Make IPython.core.display.Image less notebook-centric
* :ghpull:`1684`: CLN: Remove redundant function definition.
* :ghpull:`1670`: Point %pastebin to gist
* :ghpull:`1669`: handle pyout messages in test_message_spec
* :ghpull:`1295`: add binary-tree engine interconnect example
* :ghpull:`1642`: Cherry-picked commits from 0.12.1 release
* :ghpull:`1659`: Handle carriage return characters ("\r") in HTML notebook output.
* :ghpull:`1656`: ensure kernels are cleaned up in embed_kernel tests
* :ghpull:`1664`: InteractiveShell.run_code: Update docstring.
* :ghpull:`1662`: Delay flushing softspace until after cell finishes
* :ghpull:`1643`: handle jpg/jpeg in the qtconsole
* :ghpull:`1652`: add patch_pyzmq() for backporting a few changes from newer pyzmq
* :ghpull:`1650`: DOC: moving files with SSH launchers
* :ghpull:`1357`: add IPython.embed_kernel() 
* :ghpull:`1640`: Finish up embed_kernel
* :ghpull:`1651`: Remove bundled Itpl module
* :ghpull:`1634`: incremental improvements to SSH launchers
* :ghpull:`1649`: move examples/test_embed into examples/tests/embed
* :ghpull:`1633`: Fix installing extension from local file on Windows
* :ghpull:`1645`: Exclude UserDict when deep reloading NumPy.
* :ghpull:`1637`: Removed a ':' which shouldn't have been there
* :ghpull:`1631`: TST: QApplication doesn't quit early enough with PySide.
* :ghpull:`1629`: evaluate a few dangling validate_message generators
* :ghpull:`1621`: clear In[] prompt numbers on "Clear All Output"
* :ghpull:`1627`: Test the Message Spec
* :ghpull:`1624`: Fixes for byte-compilation on Python 3
* :ghpull:`1615`: Add show() method to figure objects.
* :ghpull:`1625`: Fix deepreload on Python 3
* :ghpull:`1620`: pyin message now have execution_count
* :ghpull:`1457`: Update deepreload to use a rewritten knee.py. Fixes dreload(numpy).
* :ghpull:`1613`: allow map / parallel function for single-engine views
* :ghpull:`1609`: exit notebook cleanly on SIGINT, SIGTERM
* :ghpull:`1607`: cleanup sqlitedb temporary db file after tests
* :ghpull:`1608`: don't rely on timedelta.total_seconds in AsyncResult
* :ghpull:`1599`: Fix for %run -d on Python 3
* :ghpull:`1602`: Fix %env magic on Python 3.
* :ghpull:`1603`: Remove python3 profile
* :ghpull:`1604`: Exclude IPython.quarantine from installation
* :ghpull:`1600`: Specify encoding for io.open in notebook_reformat tests
* :ghpull:`1605`: Small fixes for Animation and Progress notebook
* :ghpull:`1529`: __all__ feature, improvement to dir2, and tests for both
* :ghpull:`1548`: add sugar methods/properties to AsyncResult
* :ghpull:`1535`: Fix pretty printing dispatch
* :ghpull:`1399`: Use LaTeX to print various built-in types with the SymPy printing extension
* :ghpull:`1597`: re-enter kernel.eventloop after catching SIGINT
* :ghpull:`1490`: rename plaintext cell -> raw cell
* :ghpull:`1480`: Fix %notebook magic, etc. nbformat unicode tests and fixes
* :ghpull:`1588`: Gtk3 integration with ipython works.
* :ghpull:`1595`: Examples syntax (avoid errors installing on Python 3)
* :ghpull:`1526`: Find encoding for Python files
* :ghpull:`1594`: Fix writing git commit ID to a file on build with Python 3
* :ghpull:`1556`: shallow-copy DictDB query results
* :ghpull:`1502`: small changes in response to pyflakes pass
* :ghpull:`1445`: Don't build sphinx docs for sdists
* :ghpull:`1538`: store git commit hash in utils._sysinfo instead of hidden data file
* :ghpull:`1546`: attempt to suppress exceptions in channel threads at shutdown
* :ghpull:`1559`: update tools/github_stats.py to use GitHub API v3
* :ghpull:`1563`: clear_output improvements
* :ghpull:`1560`: remove obsolete discussion of Twisted/trial from testing docs
* :ghpull:`1569`: BUG: qtconsole -- non-standard handling of \a and \b. [Fixes #1561]
* :ghpull:`1573`: BUG: Ctrl+C crashes wx pylab kernel in qtconsole.
* :ghpull:`1568`: fix PR #1567
* :ghpull:`1567`: Fix: openssh_tunnel did not parse port in `server`
* :ghpull:`1565`: fix AsyncResult.abort
* :ghpull:`1552`: use os.getcwdu in NotebookManager
* :ghpull:`1541`: display_pub flushes stdout/err
* :ghpull:`1544`: make MultiKernelManager.kernel_manager_class configurable
* :ghpull:`1517`: Fix indentation bug in IPython/lib/pretty.py
* :ghpull:`1519`: BUG: Include the name of the exception type in its pretty format.
* :ghpull:`1489`: Fix zero-copy push
* :ghpull:`1477`: fix dangling `buffer` in IPython.parallel.util
* :ghpull:`1514`: DOC: Fix references to IPython.lib.pretty instead of the old location
* :ghpull:`1481`: BUG: Improve placement of CallTipWidget
* :ghpull:`1496`: BUG: LBYL when clearing the output history on shutdown.
* :ghpull:`1508`: fix sorting profiles in clustermanager
* :ghpull:`1495`: BUG: Fix pretty-printing for overzealous objects
* :ghpull:`1472`: more general fix for #662
* :ghpull:`1483`: updated magic_history docstring
* :ghpull:`1383`: First version of cluster web service.
* :ghpull:`1398`: fix %tb after SyntaxError
* :ghpull:`1440`: Fix for failing testsuite when using --with-xml-coverage on windows.
* :ghpull:`1419`: Add %install_ext magic function.
* :ghpull:`1424`: Win32 shell interactivity
* :ghpull:`1468`: Simplify structure of a Job in the TaskScheduler
* :ghpull:`1447`: 1107 - Tab autocompletion can suggest invalid syntax
* :ghpull:`1469`: Fix typo in comment (insert space)
* :ghpull:`1463`: Fix completion when importing modules in the cwd.
* :ghpull:`1466`: Fix for issue #1437, unfriendly windows qtconsole error handling
* :ghpull:`1432`: Fix ipython directive
* :ghpull:`1465`: allow `ipython help subcommand` syntax
* :ghpull:`1416`: Conditional import of ctypes in inputhook
* :ghpull:`1462`: expedite parallel tests
* :ghpull:`1410`: Add javascript library and css stylesheet loading to JS class.
* :ghpull:`1448`: Fix for #875 Never build unicode error messages
* :ghpull:`1458`: use eval to uncan References
* :ghpull:`1450`: load mathjax from CDN via https
* :ghpull:`1451`: include heading level in JSON
* :ghpull:`1444`: Fix pyhton -> python typos
* :ghpull:`1414`: ignore errors in shell.var_expand
* :ghpull:`1430`: Fix for tornado check for tornado < 1.1.0
* :ghpull:`1413`: get_home_dir expands symlinks, adjust test accordingly
* :ghpull:`1385`: updated and prettified magic doc strings
* :ghpull:`1406`: Browser selection
* :ghpull:`1377`: Saving non-ascii history
* :ghpull:`1402`: fix symlinked /home issue for FreeBSD
* :ghpull:`1405`: Only monkeypatch xunit when the tests are run using it.
* :ghpull:`1395`: Xunit & KnownFailure
* :ghpull:`1396`: Fix for %tb magic.
* :ghpull:`1386`: Jsd3
* :ghpull:`1388`: Add simple support for running inside a virtualenv
* :ghpull:`1391`: Improve Hub/Scheduler when no engines are registered
* :ghpull:`1369`: load header with engine id when engine dies in TaskScheduler
* :ghpull:`1353`: Save notebook as script using unicode file handle.
* :ghpull:`1352`: Add '-m mod : run library module as a script' option.
* :ghpull:`1363`: Fix some minor color/style config issues in the qtconsole
* :ghpull:`1371`: Adds a quiet keyword to sync_imports
* :ghpull:`1387`: Fixing Cell menu to update cell type select box.
* :ghpull:`1296`: Wx gui example: fixes the broken example for `%gui wx`.
* :ghpull:`1372`: ipcontroller cleans up connection files unless reuse=True
* :ghpull:`1374`: remove calls to meaningless ZMQStream.on_err
* :ghpull:`1370`: allow draft76 websockets (Safari)
* :ghpull:`1368`: Ensure handler patterns are str, not unicode
* :ghpull:`1361`: Notebook bug fix branch
* :ghpull:`1364`: avoid jsonlib returning Decimal
* :ghpull:`1362`: Don't log complete contents of history replies, even in debug
* :ghpull:`1347`: fix weird magic completion in notebook
* :ghpull:`1346`: fixups for alternate URL prefix stuff
* :ghpull:`1336`: crack at making notebook.html use the layout.html template
* :ghpull:`1331`: RST and heading cells
* :ghpull:`1247`: fixes a bug causing extra newlines after comments.
* :ghpull:`1332`: notebook - allow prefixes in URL path.
* :ghpull:`1341`: Don't attempt to tokenize binary files for tracebacks
* :ghpull:`1334`: added key handler for control-s to notebook, seems to work pretty well
* :ghpull:`1338`: Fix see also in docstrings so API docs build
* :ghpull:`1335`: Notebook toolbar UI
* :ghpull:`1299`: made notebook.html extend layout.html
* :ghpull:`1318`: make Ctrl-D in qtconsole act same as in terminal (ready to merge)
* :ghpull:`1328`: Coverage
* :ghpull:`1206`: don't preserve fixConsole output in json
* :ghpull:`1330`: Add linewrapping to text cells (new feature in CodeMirror).
* :ghpull:`1309`: Inoculate clearcmd extension into %reset functionality
* :ghpull:`1327`: Updatecm2
* :ghpull:`1326`: Removing Ace edit capability.
* :ghpull:`1325`: forgotten selected_cell -> get_selected_cell
* :ghpull:`1316`: Pass subprocess test runners a suitable location for xunit output
* :ghpull:`1303`: Updatecm
* :ghpull:`1312`: minor heartbeat tweaks
* :ghpull:`1306`: Fix %prun input parsing for escaped characters (closes #1302)
* :ghpull:`1301`: New "Fix for issue #1202" based on current master.
* :ghpull:`1289`: Make autoreload extension work on Python 3.
* :ghpull:`1288`: Don't ask for confirmation when stdin isn't available
* :ghpull:`1294`: TaskScheduler.hwm default to 1 instead of 0
* :ghpull:`1283`: HeartMonitor.period should be an Integer
* :ghpull:`1264`: Aceify
* :ghpull:`1284`: a fix for GH 1269
* :ghpull:`1213`: BUG: Minor typo in history_console_widget.py
* :ghpull:`1267`: add NoDB for non-recording Hub
* :ghpull:`1222`: allow Reference as callable in map/apply
* :ghpull:`1257`: use self.kernel_manager_class in qtconsoleapp
* :ghpull:`1253`: set auto_create flag for notebook apps
* :ghpull:`1262`: Heartbeat no longer shares the app's Context
* :ghpull:`1229`: Fix display of SyntaxError in Python 3
* :ghpull:`1256`: Dewijmoize
* :ghpull:`1246`: Skip tests that require X, when importing pylab results in RuntimeError.
* :ghpull:`1211`: serve local files in notebook-dir
* :ghpull:`1224`: edit text cells on double-click instead of single-click
* :ghpull:`1187`: misc notebook: connection file cleanup, first heartbeat, startup flush
* :ghpull:`1207`: fix loadpy duplicating newlines
* :ghpull:`1129`: Unified setup.py
* :ghpull:`1199`: Reduce IPython.external.*
* :ghpull:`1218`: Added -q option to %prun for suppression of the output, along with editing the dochelp string.
* :ghpull:`1217`: Added -q option to %prun for suppression of the output, along with editing the dochelp string
* :ghpull:`1175`: core.completer: Clean up excessive and unused code.
* :ghpull:`1196`: docs: looks like a file path might have been accidentally pasted in the middle of a word
* :ghpull:`1190`: Fix link to Chris Fonnesbeck blog post about 0.11 highlights.

Issues (742):

* :ghissue:`1943`: add screenshot and link into releasenotes
* :ghissue:`1570`: [notebook] remove 'left panel' references from example.
* :ghissue:`1954`: update some example notebooks
* :ghissue:`2048`: move _encode_binary to jsonutil.encode_images
* :ghissue:`2050`: only add quotes around xunit-file on Windows
* :ghissue:`2047`: disable auto-scroll on mozilla
* :ghissue:`1258`: Magic %paste error
* :ghissue:`2015`: Fixes for %paste with special transformations
* :ghissue:`760`: Windows: test runner fails if repo path contains spaces
* :ghissue:`2046`: Iptest unicode
* :ghissue:`1939`: Namespaces
* :ghissue:`2042`: increase auto-scroll threshold to 100 lines
* :ghissue:`2043`: move RemoteError import to top-level
* :ghissue:`641`: In %magic help, remove duplicate aliases
* :ghissue:`2036`: %alias_magic
* :ghissue:`1968`: Proposal of icons for .ipynb files
* :ghissue:`825`: keyboardinterrupt crashes gtk gui when gtk.set_interactive is not available
* :ghissue:`1971`: Remove duplicate magics docs
* :ghissue:`2040`: Namespaces for cleaner public APIs
* :ghissue:`2039`: ipython parallel import exception
* :ghissue:`2035`: Getdefaultencoding test error with sympy 0.7.1_git
* :ghissue:`2037`: remove `ipython-qtconsole` gui-script
* :ghissue:`1516`: ipython-qtconsole script isn't installed for Python 2.x
* :ghissue:`1297`: "ipython -p sh" is in documentation but doesn't work
* :ghissue:`2038`: add extra clear warning to shell doc
* :ghissue:`1265`: please ship unminified js and css sources
* :ghissue:`2029`: Ship unminified js
* :ghissue:`1920`: Provide an easy way to override the Qt widget used by qtconsole
* :ghissue:`2007`: Add custom_control and custom_page_control variables to override the Qt widgets used by qtconsole
* :ghissue:`2009`: In %magic help, remove duplicate aliases
* :ghissue:`2033`: ipython parallel pushing and pulling recarrays
* :ghissue:`2034`: fix&test push/pull recarrays
* :ghissue:`2028`: Reduce unhelpful information shown by pinfo
* :ghissue:`1992`: Tab completion fails with many spaces in filename 
* :ghissue:`1885`: handle too old wx
* :ghissue:`2030`: check wxPython version in inputhook
* :ghissue:`2024`: Make interactive_usage a bit more rst friendly
* :ghissue:`2031`: disable ^C^C confirmation on Windows
* :ghissue:`2023`: Unicode test failure on OS X
* :ghissue:`2027`: match stdin encoding in frontend readline test
* :ghissue:`1901`: Windows: parallel test fails assert, leaves 14 python processes alive
* :ghissue:`2025`: Fix parallel test on WinXP - wait for resource cleanup.
* :ghissue:`1986`: Line magic function `%R` not found. (Rmagic)
* :ghissue:`1712`: test failure in ubuntu package daily build
* :ghissue:`1183`: 0.12 testsuite failures
* :ghissue:`2016`: BUG: test runner fails in Windows if filenames contain spaces.
* :ghissue:`1806`: Alternate upload methods in firefox
* :ghissue:`2019`: Windows: home directory expansion test fails
* :ghissue:`2020`: Fix home path expansion test in Windows.
* :ghissue:`2017`: Windows core test error - filename quoting
* :ghissue:`2021`: Fix Windows pathname issue in 'odd encoding' test.
* :ghissue:`1998`: call to nt.assert_true(path._writable_dir(home)) returns false in test_path.py
* :ghissue:`2022`: don't check writability in test for get_home_dir when HOME is undefined
* :ghissue:`1589`: Test failures and docs don't build on Mac OS X Lion
* :ghissue:`1996`: frontend test tweaks
* :ghissue:`2011`: Notebook server can't start cluster with hyphen-containing profile name
* :ghissue:`2014`: relax profile regex in notebook
* :ghissue:`2013`: brew install pyqt
* :ghissue:`2005`: Strange output artifacts in footer of notebook
* :ghissue:`2012`: Mono cursor offset
* :ghissue:`2004`: Clarify generic message spec vs. Python message API in docs
* :ghissue:`2006`: Don't crash when starting notebook server if runnable browser not found
* :ghissue:`2010`: notebook: Print a warning (but do not abort) if no webbrowser can be found.
* :ghissue:`2008`: pip install virtualenv
* :ghissue:`2003`: Wrong case of rmagic in docs
* :ghissue:`2002`: Refactor %magic into a lsmagic_docs API function.
* :ghissue:`2000`: kernel.js consistency with generic IPython message format.
* :ghissue:`1999`: `%magic` help: display line and cell magics in alphabetical order.
* :ghissue:`1635`: test_prun_quotes fails on Windows
* :ghissue:`1984`: Cannot restart Notebook when using `%%script --bg`
* :ghissue:`1981`: Clean BG processes created by %%script on kernel exit
* :ghissue:`1994`: Fix RST misformatting.
* :ghissue:`1949`: Introduce Notebook Magics
* :ghissue:`1985`: Kernels should start in notebook dir when manually specified
* :ghissue:`1980`: Notebook should check that --notebook-dir exists
* :ghissue:`1951`: minor notebook startup/notebook-dir adjustments
* :ghissue:`1969`: tab completion in notebook for paths not triggered
* :ghissue:`1974`: Allow path completion on notebook.
* :ghissue:`1964`: allow multiple instances of a Magic
* :ghissue:`1960`: %page not working
* :ghissue:`1991`: fix _ofind attr in %page
* :ghissue:`1982`: Shutdown qtconsole problem?
* :ghissue:`1988`: check for active frontend in update_restart_checkbox
* :ghissue:`1979`: Add support for tox (http://tox.testrun.org/) and Travis CI (http://travis-ci.org/)
* :ghissue:`1989`: Parallel: output of %px and %px${suffix} is inconsistent
* :ghissue:`1966`: ValueError: packer could not serialize a simple message
* :ghissue:`1987`: Notebook: MathJax offline install not recognized
* :ghissue:`1970`: dblclick to restore size of images
* :ghissue:`1983`: Notebook does not save heading level
* :ghissue:`1978`: Notebook names truncating at the first period
* :ghissue:`1553`: Limited size of output cells and provide scroll bars for such output cells
* :ghissue:`1825`: second attempt at scrolled long output
* :ghissue:`1915`: add cell-level metadata
* :ghissue:`1934`: Cell/Worksheet metadata
* :ghissue:`1746`: Confirm restart (configuration option, and checkbox UI)
* :ghissue:`1790`: Commenting function.
* :ghissue:`1767`: Tab completion problems with cell magics
* :ghissue:`1944`: [qtconsole] take %,%% prefix into account for completion
* :ghissue:`1973`: fix another FreeBSD $HOME symlink issue
* :ghissue:`1972`: Fix completion of '%tim' in the Qt console
* :ghissue:`1887`: Make it easy to resize jpeg/png images back to original size.
* :ghissue:`1967`: Fix psums example description in docs
* :ghissue:`1678`: ctrl-z clears cell output in notebook when pressed enough times
* :ghissue:`1965`: fix for #1678, undo no longer clears cells
* :ghissue:`1952`: avoid duplicate "Websockets closed" dialog on ws close
* :ghissue:`1961`: UnicodeDecodeError on directory with unicode chars in prompt
* :ghissue:`1963`: styling prompt, {color.Normal} excepts
* :ghissue:`1962`: Support unicode prompts
* :ghissue:`1959`: %page not working on qtconsole for Windows XP 32-bit
* :ghissue:`1955`: update to latest version of vim-ipython
* :ghissue:`1945`: Add --proc option to %%script
* :ghissue:`1957`: fix indentation in kernel.js
* :ghissue:`1956`: move import RemoteError after get_exc_info
* :ghissue:`1950`: Fix for copy action (Ctrl+C) when there is no pager defined in qtconsole
* :ghissue:`1948`: Fix help string for InteractiveShell.ast_node_interactivity
* :ghissue:`1941`: script magics cause terminal spam
* :ghissue:`1942`: swallow stderr of which in utils.process.find_cmd
* :ghissue:`1833`: completer draws slightly too small on Chrome
* :ghissue:`1940`: fix completer css on some Chrome versions
* :ghissue:`1938`: remove remaining references to deprecated XREP/XREQ names
* :ghissue:`1924`: HTML superscripts not shown raised in the notebook
* :ghissue:`1925`: Fix styling of superscripts and subscripts. Closes #1924.
* :ghissue:`1461`: User notification if notebook saving fails
* :ghissue:`1936`: increase duration of save messages
* :ghissue:`1542`: %save magic fails in clients without stdin if file already exists
* :ghissue:`1937`: add %save -f
* :ghissue:`1572`: pyreadline version dependency not correctly checked
* :ghissue:`1935`: add version checking to pyreadline import test
* :ghissue:`1849`: Octave magics
* :ghissue:`1759`: github, merge PR(s) just by number(s) 
* :ghissue:`1931`: Win py3fixes
* :ghissue:`1646`: Meaning of restart parameter in client.shutdown() unclear
* :ghissue:`1933`: oinspect.find_file: Additional safety if file cannot be found.
* :ghissue:`1916`: %paste doesn't work on py3
* :ghissue:`1932`: Fix adding functions to CommandChainDispatcher with equal priority on Py 3
* :ghissue:`1928`: Select NoDB by default
* :ghissue:`1923`: Add IPython syntax support to the %timeit magic, in line and cell mode
* :ghissue:`1926`: Make completer recognize escaped quotes in strings.
* :ghissue:`1929`: Ipython-qtconsole (0.12.1) hangs with Python 2.7.3, Windows 7 64 bit
* :ghissue:`1409`: [qtconsole] forward delete bring completion into current line
* :ghissue:`1922`: py3k compatibility for setupegg.py
* :ghissue:`1598`: document that sync_imports() can't handle "import foo as bar"
* :ghissue:`1893`: Update Parallel Magics and Exception Display
* :ghissue:`1890`: Docstrings for magics that use @magic_arguments are rendered wrong
* :ghissue:`1921`: magic_arguments: dedent but otherwise preserve indentation.
* :ghissue:`1919`: Use oinspect in CodeMagics._find_edit_target
* :ghissue:`1918`: don't warn in iptest if deathrow/quarantine are missing
* :ghissue:`1914`: %pdef failing on python3
* :ghissue:`1917`: Fix for %pdef on Python 3
* :ghissue:`1428`: Failing test that prun does not clobber string escapes
* :ghissue:`1913`: Fix for #1428
* :ghissue:`1911`: temporarily skip autoreload tests
* :ghissue:`1549`: autoreload extension crashes ipython
* :ghissue:`1908`: find_file errors on windows
* :ghissue:`1909`: Fix for #1908, use os.path.normcase for safe filename comparisons
* :ghissue:`1907`: py3compat fixes for %%script and tests
* :ghissue:`1904`: %%px? doesn't work, shows info for %px, general cell magic problem
* :ghissue:`1906`: ofind finds non-unique cell magics
* :ghissue:`1894`: Win64 binary install fails
* :ghissue:`1799`: Source file not found for magics
* :ghissue:`1845`: Fixes to inspection machinery for magics
* :ghissue:`1774`: Some magics seems broken
* :ghissue:`1586`: Clean up tight coupling between Notebook, CodeCell and Kernel Javascript objects
* :ghissue:`1632`: Win32 shell interactivity apparently broke qtconsole "cd" magic
* :ghissue:`1902`: Workaround fix for gh-1632; minimal revert of gh-1424
* :ghissue:`1900`: Cython libs
* :ghissue:`1503`: Cursor is offset in notebook in Chrome 17 on Linux
* :ghissue:`1426`: Qt console doesn't handle the `--gui` flag correctly.
* :ghissue:`1180`: Can't start IPython kernel in Spyder
* :ghissue:`581`: test IPython.zmq
* :ghissue:`1593`: Name embedded in notebook overrides filename
* :ghissue:`1899`: add ScriptMagics to class list for generated config
* :ghissue:`1618`: generate or minimize manpages
* :ghissue:`1898`: minimize manpages
* :ghissue:`1896`: Windows: apparently spurious warning 'Excluding nonexistent file' ... test_exampleip
* :ghissue:`1897`: use glob for bad exclusion warning
* :ghissue:`1215`: updated %quickref to show short-hand for %sc and %sx
* :ghissue:`1855`: %%script and %%file magics
* :ghissue:`1863`: Ability to silence a cell in the notebook
* :ghissue:`1870`: add %%capture for capturing stdout/err
* :ghissue:`1861`: Use dvipng to format sympy.Matrix
* :ghissue:`1867`: Fix 1px margin bouncing of selected menu item.
* :ghissue:`1889`: Reconnect when the websocket connection closes unexpectedly
* :ghissue:`1577`: If a notebook loses its network connection WebSockets won't reconnect
* :ghissue:`1886`: Fix a bug in renaming notebook
* :ghissue:`1895`: Fix error in test suite with ip.system()
* :ghissue:`1762`: add `locate` entry points
* :ghissue:`1883`: Fix vertical offset due to bold/italics, and bad browser fonts.
* :ghissue:`1875`: re-write columnize, with intermediate step.
* :ghissue:`1860`: IPython.utils.columnize sometime wrong...
* :ghissue:`1851`: new completer for qtconsole.
* :ghissue:`1892`: Remove suspicious quotes in interactiveshell.py
* :ghissue:`1854`: Class `%hierarchy` and graphiz `%%dot` magics
* :ghissue:`1827`: Sending tracebacks over ZMQ should protect against unicode failure
* :ghissue:`1864`: Rmagic exceptions
* :ghissue:`1829`: [notebook] don't care about leading prct in completion
* :ghissue:`1832`: Make svg, jpeg and png images resizable in notebook.
* :ghissue:`1674`: HTML Notebook carriage-return handling, take 2
* :ghissue:`1874`: cython_magic uses importlib, which doesn't ship with py2.6
* :ghissue:`1882`: Remove importlib dependency which not available in Python 2.6.
* :ghissue:`1878`: shell access using ! will not fill class or function scope vars
* :ghissue:`1879`: Correct stack depth for variable expansion in !system commands
* :ghissue:`1840`: New JS completer should merge completions before display
* :ghissue:`1841`: [notebook] deduplicate completion results
* :ghissue:`1736`: no good error message on missing tkinter and %paste
* :ghissue:`1741`: Display message from TryNext error in magic_paste
* :ghissue:`1850`: Remove args/kwargs handling in TryNext, fix %paste error messages.
* :ghissue:`1663`: Keep line-endings in ipynb
* :ghissue:`1872`: Matplotlib window freezes using intreractive plot in qtconsole
* :ghissue:`1869`: Improve CodeMagics._find_edit_target
* :ghissue:`1781`: Colons in notebook name causes notebook deletion without warning
* :ghissue:`1815`: Make : invalid in filenames in the Notebook JS code.
* :ghissue:`1819`: doc: cleanup the parallel psums example a little
* :ghissue:`1838`: externals cleanup
* :ghissue:`1839`: External cleanup
* :ghissue:`1782`: fix Magic menu in qtconsole, split in groups
* :ghissue:`1862`: Minor bind_kernel improvements
* :ghissue:`1859`: kernmagic during console startup
* :ghissue:`1857`: Prevent jumping of window to input when output is clicked.
* :ghissue:`1856`: Fix 1px jumping of cells and menus in Notebook.
* :ghissue:`1848`: task fails with "AssertionError: not enough buffers!" after second resubmit
* :ghissue:`1852`: fix chained resubmissions
* :ghissue:`1780`: Rmagic extension
* :ghissue:`1853`: Fix jumpy notebook behavior
* :ghissue:`1842`: task with UnmetDependency error still owned by engine
* :ghissue:`1847`: add InlineBackend to ConsoleApp class list
* :ghissue:`1846`: Exceptions within multiprocessing crash Ipython notebook kernel
* :ghissue:`1843`: Notebook does not exist and permalinks
* :ghissue:`1837`: edit magic broken in head
* :ghissue:`1834`: resubmitted tasks doesn't have same session name
* :ghissue:`1836`: preserve header for resubmitted tasks
* :ghissue:`1776`: fix magic menu in qtconsole
* :ghissue:`1828`: change default extension to .ipy for %save -r
* :ghissue:`1800`: Reintroduce recall
* :ghissue:`1671`: __future__ environments
* :ghissue:`1830`: lsmagic lists magics in alphabetical order
* :ghissue:`1835`: Use Python import in ipython profile config
* :ghissue:`1773`: Update SymPy profile: SymPy's latex() can now print set and frozenset
* :ghissue:`1761`: Edited documentation to use IPYTHONDIR in place of ~/.ipython
* :ghissue:`1772`: notebook autocomplete fail when typing number
* :ghissue:`1822`: aesthetics pass on AsyncResult.display_outputs
* :ghissue:`1460`: Redirect http to https for notebook
* :ghissue:`1287`: Refactor the notebook tab completion/tooltip
* :ghissue:`1596`: In rename dialog, <return> should submit
* :ghissue:`1821`: ENTER submits the rename notebook dialog.
* :ghissue:`1750`: Let the user disable random port selection
* :ghissue:`1820`: NotebookApp: Make the number of ports to retry user configurable.
* :ghissue:`1816`: Always use filename as the notebook name.
* :ghissue:`1775`: assert_in not present on Python 2.6
* :ghissue:`1813`: Add assert_in method to nose for Python 2.6
* :ghissue:`1498`: Add tooltip keyboard shortcuts
* :ghissue:`1711`: New Tooltip, New Completer and JS Refactor
* :ghissue:`1798`: a few simple fixes for docs/parallel
* :ghissue:`1818`: possible bug with latex / markdown
* :ghissue:`1647`: Aborted parallel tasks can't be resubmitted
* :ghissue:`1817`: Change behavior of ipython notebook --port=...
* :ghissue:`1738`: IPython.embed_kernel issues
* :ghissue:`1610`: Basic bold and italic in HTML output cells
* :ghissue:`1576`: Start and stop kernels from the notebook dashboard
* :ghissue:`1515`: impossible to shutdown notebook kernels
* :ghissue:`1812`: Ensure AsyncResult.display_outputs doesn't display empty streams
* :ghissue:`1811`: warn on nonexistent exclusions in iptest
* :ghissue:`1809`: test suite error in IPython.zmq on windows
* :ghissue:`1810`: fix for #1809, failing tests in IPython.zmq
* :ghissue:`1808`: Reposition alternate upload for firefox [need cross browser/OS/language test]
* :ghissue:`1742`: Check for custom_exceptions only once
* :ghissue:`1802`: cythonmagic tests should be skipped if Cython not available
* :ghissue:`1062`: warning message in IPython.extensions test
* :ghissue:`1807`: add missing cython exclusion in iptest
* :ghissue:`1805`: Fixed a vcvarsall.bat error on win32/Py2.7 when trying to compile with m...
* :ghissue:`1803`: MPI parallel %px bug 
* :ghissue:`1804`: Fixed a vcvarsall.bat error on win32/Py2.7 when trying to compile with mingw.
* :ghissue:`1492`: Drag target very small if IPython Dashboard has no notebooks
* :ghissue:`1562`: Offer a method other than drag-n-drop to upload notebooks
* :ghissue:`1739`: Dashboard improvement (necessary merge of #1658 and #1676 + fix #1492)
* :ghissue:`1770`: Cython related magic functions
* :ghissue:`1532`: qtconsole does not accept --gui switch
* :ghissue:`1707`: Accept --gui=<...> switch in IPython qtconsole.
* :ghissue:`1797`: Fix comment which breaks Emacs syntax highlighting.
* :ghissue:`1796`: %gui magic broken
* :ghissue:`1795`: fix %gui magic
* :ghissue:`1788`: extreme truncating of return values
* :ghissue:`1793`: Raise repr limit for strings to 80 characters (from 30).
* :ghissue:`1794`: don't use XDG path on OS X
* :ghissue:`1777`: ipython crash on wrong encoding
* :ghissue:`1792`: Unicode-aware logger
* :ghissue:`1791`: update zmqshell magics
* :ghissue:`1787`: DOC: Remove regression from qt-console docs.
* :ghissue:`1785`: IPython.utils.tests.test_process.SubProcessTestCase
* :ghissue:`1758`: test_pr, fallback on http if git protocol fail, and SSL errors...
* :ghissue:`1786`: Make notebook save failures more salient
* :ghissue:`1748`: Fix some tests for Python 3.3
* :ghissue:`1755`: test for pygments before running qt tests
* :ghissue:`1771`: Make default value of interactivity passed to run_ast_nodes configurable
* :ghissue:`1783`: part of PR #1606 (loadpy -> load) erased by magic refactoring.
* :ghissue:`1784`: restore loadpy to load
* :ghissue:`1768`: Update parallel magics
* :ghissue:`1778`: string exception in IPython/core/magic.py:232
* :ghissue:`1779`: Tidy up error raising in magic decorators.
* :ghissue:`1769`: Allow cell mode timeit without setup code.
* :ghissue:`1716`: Fix for fake filenames in verbose traceback
* :ghissue:`1763`: [qtconsole] fix append_plain_html -> append_html
* :ghissue:`1766`: Test failure in IPython.parallel
* :ghissue:`1611`: IPEP1: Cell magics and general cleanup of the Magic system
* :ghissue:`1732`: Refactoring of the magics system and implementation of cell magics
* :ghissue:`1765`: test_pr should clearn PYTHONPATH for the subprocesses
* :ghissue:`1630`: Merge divergent Kernel implementations
* :ghissue:`1705`: [notebook] Make pager resizable, and remember size...
* :ghissue:`1606`: Share code for %pycat and %loadpy, make %pycat aware of URLs
* :ghissue:`1720`: Adding interactive inline plotting to notebooks with flot
* :ghissue:`1701`: [notebook] Open HTML links in a new window by default
* :ghissue:`1757`: Open IPython notebook hyperlinks in a new window using target=_blank
* :ghissue:`1735`: Open IPython notebook hyperlinks in a new window using target=_blank
* :ghissue:`1754`: Fix typo enconters->encounters
* :ghissue:`1753`: Clear window title when kernel is restarted
* :ghissue:`735`: Images missing from XML/SVG export (for me)
* :ghissue:`1449`: Fix for bug #735 : Images missing from XML/SVG export
* :ghissue:`1752`: Reconnect Websocket when it closes unexpectedly
* :ghissue:`1751`: Reconnect Websocket when it closes unexpectedly
* :ghissue:`1749`: Load MathJax.js using HTTPS when IPython notebook server is HTTPS
* :ghissue:`1743`: Tooltip completer js refactor
* :ghissue:`1700`: A module for sending custom user messages from the kernel.
* :ghissue:`1745`: htmlnotebook: Cursor is off
* :ghissue:`1728`: ipython crash with matplotlib during picking
* :ghissue:`1681`: add qt config option to clear_on_kernel_restart
* :ghissue:`1733`: Tooltip completer js refactor
* :ghissue:`1676`: Kernel status/shutdown from dashboard
* :ghissue:`1658`: Alternate notebook upload methods
* :ghissue:`1727`: terminate kernel after embed_kernel tests
* :ghissue:`1737`: add HistoryManager to ipapp class list
* :ghissue:`945`: Open a notebook from the command line
* :ghissue:`1686`: ENH: Open a notebook from the command line
* :ghissue:`1709`: fixes #1708, failing test in arg_split on windows
* :ghissue:`1718`: Use CRegExp trait for regular expressions.
* :ghissue:`1729`: Catch failure in repr() for %whos
* :ghissue:`1726`: use eval for command-line args instead of exec
* :ghissue:`1723`: scatter/gather fail with targets='all'
* :ghissue:`1724`: fix scatter/gather with targets='all'
* :ghissue:`1725`: add --no-ff to git pull in test_pr
* :ghissue:`1722`: unicode exception when evaluating expression with non-ascii characters
* :ghissue:`1721`: Tooltip completer js refactor
* :ghissue:`1657`: Add `wait` optional argument to `hooks.editor`
* :ghissue:`123`: Define sys.ps{1,2}
* :ghissue:`1717`: Define generic sys.ps{1,2,3}, for use by scripts.
* :ghissue:`1442`: cache-size issue in qtconsole
* :ghissue:`1691`: Finish PR #1446
* :ghissue:`1446`: Fixing Issue #1442
* :ghissue:`1710`: update MathJax CDN url for https
* :ghissue:`81`: Autocall fails if first function argument begins with "-" or "+
* :ghissue:`1713`: Make autocall regexp's configurable.
* :ghissue:`211`: paste command not working
* :ghissue:`1703`: Allow TryNext to have an error message without it affecting the command chain
* :ghissue:`1714`: minor adjustments to test_pr
* :ghissue:`1509`: New tooltip for notebook
* :ghissue:`1697`: Major refactoring of the Notebook, Kernel and CodeCell JavaScript.
* :ghissue:`788`: Progress indicator in the notebook (and perhaps the Qt console)
* :ghissue:`1034`: Single process Qt console
* :ghissue:`1557`: magic function conflict while using --pylab
* :ghissue:`1476`: Pylab figure objects not properly updating
* :ghissue:`1704`: ensure all needed qt parts can be imported before settling for one
* :ghissue:`1708`: test failure in arg_split on windows
* :ghissue:`1706`: Mark test_push_numpy_nocopy as a known failure for Python 3
* :ghissue:`1696`: notebook tooltip fail on function with number
* :ghissue:`1698`: fix tooltip on token with number
* :ghissue:`1226`: Windows GUI only (pythonw) bug for IPython on Python 3.x
* :ghissue:`1245`: pythonw py3k fixes for issue #1226
* :ghissue:`1417`: Notebook Completer Class
* :ghissue:`1690`: [Bogus] Deliberately make a test fail
* :ghissue:`1685`: Add script to test pull request
* :ghissue:`1167`: Settle on a choice for $IPYTHONDIR
* :ghissue:`1693`: deprecate IPYTHON_DIR in favor of IPYTHONDIR
* :ghissue:`1672`: ipython-qtconsole.desktop is using a deprecated format
* :ghissue:`1695`: Avoid deprecated warnings from ipython-qtconsole.desktop.
* :ghissue:`1694`: Add quote to notebook to allow it to load
* :ghissue:`1240`: sys.path missing `''` as first entry when kernel launched without interface
* :ghissue:`1689`: Fix sys.path missing '' as first entry in `ipython kernel`.
* :ghissue:`1683`: Parallel controller failing with Pymongo 2.2
* :ghissue:`1687`: import Binary from bson instead of pymongo
* :ghissue:`1614`: Display Image in Qtconsole
* :ghissue:`1616`: Make IPython.core.display.Image less notebook-centric
* :ghissue:`1684`: CLN: Remove redundant function definition.
* :ghissue:`1655`: Add %open magic command to open editor in non-blocking manner
* :ghissue:`1677`: middle-click paste broken in notebook
* :ghissue:`1670`: Point %pastebin to gist
* :ghissue:`1667`: Test failure in test_message_spec
* :ghissue:`1668`: Test failure in IPython.zmq.tests.test_message_spec.test_complete "'pyout' != 'status'"
* :ghissue:`1669`: handle pyout messages in test_message_spec
* :ghissue:`1295`: add binary-tree engine interconnect example
* :ghissue:`1642`: Cherry-picked commits from 0.12.1 release
* :ghissue:`1659`: Handle carriage return characters ("\r") in HTML notebook output.
* :ghissue:`1313`: Figure out MathJax 2 support
* :ghissue:`1653`: Test failure in IPython.zmq
* :ghissue:`1656`: ensure kernels are cleaned up in embed_kernel tests
* :ghissue:`1666`: pip install ipython==dev installs version 0.8 from an old svn repo
* :ghissue:`1664`: InteractiveShell.run_code: Update docstring.
* :ghissue:`1512`: `print stuff,` should avoid newline
* :ghissue:`1662`: Delay flushing softspace until after cell finishes
* :ghissue:`1643`: handle jpg/jpeg in the qtconsole
* :ghissue:`966`: dreload fails on Windows XP with iPython 0.11 "Unexpected Error"
* :ghissue:`1500`: dreload doesn't seem to exclude numpy
* :ghissue:`1520`: kernel crash when showing tooltip (?)
* :ghissue:`1652`: add patch_pyzmq() for backporting a few changes from newer pyzmq
* :ghissue:`1650`: DOC: moving files with SSH launchers
* :ghissue:`1357`: add IPython.embed_kernel() 
* :ghissue:`1640`: Finish up embed_kernel
* :ghissue:`1651`: Remove bundled Itpl module
* :ghissue:`1634`: incremental improvements to SSH launchers
* :ghissue:`1649`: move examples/test_embed into examples/tests/embed
* :ghissue:`1171`: Recognise virtualenvs
* :ghissue:`1479`: test_extension failing in Windows
* :ghissue:`1633`: Fix installing extension from local file on Windows
* :ghissue:`1644`: Update copyright date to 2012
* :ghissue:`1636`: Test_deepreload breaks pylab irunner tests
* :ghissue:`1645`: Exclude UserDict when deep reloading NumPy.
* :ghissue:`1454`: make it possible to start engine in 'disabled' mode and 'enable' later
* :ghissue:`1641`: Escape code for the current time in PromptManager
* :ghissue:`1638`: ipython console clobbers custom sys.path
* :ghissue:`1637`: Removed a ':' which shouldn't have been there
* :ghissue:`1536`: ipython 0.12 embed shell won't run startup scripts
* :ghissue:`1628`: error: QApplication already exists in TestKillRing
* :ghissue:`1631`: TST: QApplication doesn't quit early enough with PySide.
* :ghissue:`1629`: evaluate a few dangling validate_message generators
* :ghissue:`1621`: clear In[] prompt numbers on "Clear All Output"
* :ghissue:`1627`: Test the Message Spec
* :ghissue:`1470`: SyntaxError on setup.py install with Python 3
* :ghissue:`1624`: Fixes for byte-compilation on Python 3
* :ghissue:`1612`: pylab=inline fig.show() non-existent in notebook
* :ghissue:`1615`: Add show() method to figure objects.
* :ghissue:`1622`: deepreload fails on Python 3
* :ghissue:`1625`: Fix deepreload on Python 3
* :ghissue:`1626`: Failure in new `dreload` tests under Python 3.2
* :ghissue:`1623`: iPython / matplotlib Memory error with imshow
* :ghissue:`1619`: pyin messages should have execution_count
* :ghissue:`1620`: pyin message now have execution_count
* :ghissue:`32`: dreload produces spurious traceback when numpy is involved
* :ghissue:`1457`: Update deepreload to use a rewritten knee.py. Fixes dreload(numpy).
* :ghissue:`1613`: allow map / parallel function for single-engine views
* :ghissue:`1609`: exit notebook cleanly on SIGINT, SIGTERM
* :ghissue:`1531`: Function keyword completion fails if cursor is in the middle of the complete parentheses
* :ghissue:`1607`: cleanup sqlitedb temporary db file after tests
* :ghissue:`1608`: don't rely on timedelta.total_seconds in AsyncResult
* :ghissue:`1421`: ipython32 %run -d breaks with NameError name 'execfile' is not defined
* :ghissue:`1599`: Fix for %run -d on Python 3
* :ghissue:`1201`: %env magic fails with Python 3.2
* :ghissue:`1602`: Fix %env magic on Python 3.
* :ghissue:`1603`: Remove python3 profile
* :ghissue:`1604`: Exclude IPython.quarantine from installation
* :ghissue:`1601`: Security file is not removed after shutdown by Ctrl+C or kill -INT
* :ghissue:`1600`: Specify encoding for io.open in notebook_reformat tests
* :ghissue:`1605`: Small fixes for Animation and Progress notebook
* :ghissue:`1452`: Bug fix for approval
* :ghissue:`13`: Improve robustness and debuggability of test suite
* :ghissue:`70`: IPython should prioritize __all__ during tab completion
* :ghissue:`1529`: __all__ feature, improvement to dir2, and tests for both
* :ghissue:`1475`: Custom namespace for %run
* :ghissue:`1564`: calling .abort on AsyncMapResult  results in traceback
* :ghissue:`1548`: add sugar methods/properties to AsyncResult
* :ghissue:`1535`: Fix pretty printing dispatch
* :ghissue:`1522`: Discussion: some potential Qt console refactoring
* :ghissue:`1399`: Use LaTeX to print various built-in types with the SymPy printing extension
* :ghissue:`1597`: re-enter kernel.eventloop after catching SIGINT
* :ghissue:`1490`: rename plaintext cell -> raw cell
* :ghissue:`1487`: %notebook fails in qtconsole
* :ghissue:`1545`: trailing newline not preserved in splitline ipynb
* :ghissue:`1480`: Fix %notebook magic, etc. nbformat unicode tests and fixes
* :ghissue:`1588`: Gtk3 integration with ipython works.
* :ghissue:`1595`: Examples syntax (avoid errors installing on Python 3)
* :ghissue:`1526`: Find encoding for Python files
* :ghissue:`1594`: Fix writing git commit ID to a file on build with Python 3
* :ghissue:`1556`: shallow-copy DictDB query results
* :ghissue:`1499`: various pyflakes issues
* :ghissue:`1502`: small changes in response to pyflakes pass
* :ghissue:`1445`: Don't build sphinx docs for sdists
* :ghissue:`1484`: unhide .git_commit_info.ini
* :ghissue:`1538`: store git commit hash in utils._sysinfo instead of hidden data file
* :ghissue:`1546`: attempt to suppress exceptions in channel threads at shutdown
* :ghissue:`1524`: unhide git_commit_info.ini
* :ghissue:`1559`: update tools/github_stats.py to use GitHub API v3
* :ghissue:`1563`: clear_output improvements
* :ghissue:`1558`: Ipython testing documentation still mentions twisted and trial
* :ghissue:`1560`: remove obsolete discussion of Twisted/trial from testing docs
* :ghissue:`1561`: Qtconsole - nonstandard \a and \b
* :ghissue:`1569`: BUG: qtconsole -- non-standard handling of \a and \b. [Fixes #1561]
* :ghissue:`1574`: BUG: Ctrl+C crashes wx pylab kernel in qtconsole
* :ghissue:`1573`: BUG: Ctrl+C crashes wx pylab kernel in qtconsole.
* :ghissue:`1590`: 'iPython3 qtconsole' doesn't work in Windows 7
* :ghissue:`602`: User test the html notebook
* :ghissue:`613`: Implement Namespace panel section
* :ghissue:`879`: How to handle Javascript output in the notebook
* :ghissue:`1255`: figure.show() raises an error with the inline backend
* :ghissue:`1467`: Document or bundle a git-integrated facility for stripping VCS-unfriendly binary data
* :ghissue:`1237`: Kernel status and logout button overlap
* :ghissue:`1319`: Running a cell with ctrl+Enter selects text in cell
* :ghissue:`1571`: module member autocomplete should respect __all__
* :ghissue:`1566`: ipython3 doesn't run in Win7 with Python 3.2 
* :ghissue:`1568`: fix PR #1567
* :ghissue:`1567`: Fix: openssh_tunnel did not parse port in `server`
* :ghissue:`1565`: fix AsyncResult.abort
* :ghissue:`1550`: Crash when starting notebook in a non-ascii path
* :ghissue:`1552`: use os.getcwdu in NotebookManager
* :ghissue:`1554`: wrong behavior of the all function on iterators
* :ghissue:`1541`: display_pub flushes stdout/err
* :ghissue:`1539`: Asynchrous issue when using clear_display and print x,y,z
* :ghissue:`1544`: make MultiKernelManager.kernel_manager_class configurable
* :ghissue:`1494`: Untrusted Secure Websocket broken on latest chrome dev
* :ghissue:`1521`: only install ipython-qtconsole gui script on Windows
* :ghissue:`1528`: Tab completion optionally respects __all__ (+ dir2() cleanup)
* :ghissue:`1527`: Making a progress bar work in IPython Notebook
* :ghissue:`1497`: __all__ functionality added to dir2(obj)
* :ghissue:`1518`: Pretty printing exceptions is broken
* :ghissue:`811`: Fixes for ipython unhandeled OSError exception on failure of os.getcwdu()
* :ghissue:`1517`: Fix indentation bug in IPython/lib/pretty.py
* :ghissue:`1519`: BUG: Include the name of the exception type in its pretty format.
* :ghissue:`1525`: A hack for auto-complete numpy recarray
* :ghissue:`1489`: Fix zero-copy push
* :ghissue:`1401`: numpy arrays cannot be used with View.apply() in Python 3
* :ghissue:`1477`: fix dangling `buffer` in IPython.parallel.util
* :ghissue:`1514`: DOC: Fix references to IPython.lib.pretty instead of the old location
* :ghissue:`1511`: Version comparison error ( '2.1.11' < '2.1.4' ==> True)
* :ghissue:`1506`: "Fixing" the Notebook scroll to help in visually comparing outputs
* :ghissue:`1481`: BUG: Improve placement of CallTipWidget
* :ghissue:`1241`: When our debugger class is used standalone `_oh` key errors are thrown
* :ghissue:`676`: IPython.embed() from ipython crashes twice on exit
* :ghissue:`1496`: BUG: LBYL when clearing the output history on shutdown.
* :ghissue:`1507`: python3 notebook: TypeError: unorderable types
* :ghissue:`1508`: fix sorting profiles in clustermanager
* :ghissue:`1495`: BUG: Fix pretty-printing for overzealous objects
* :ghissue:`1505`: SQLite objects created in a thread can only be used in that same thread
* :ghissue:`1482`: %history documentation out of date?
* :ghissue:`1501`: dreload doesn't seem to exclude numpy
* :ghissue:`1472`: more general fix for #662
* :ghissue:`1486`: save state of qtconsole
* :ghissue:`1485`: add history search to qtconsole
* :ghissue:`1483`: updated magic_history docstring
* :ghissue:`1383`: First version of cluster web service.
* :ghissue:`482`: test_run.test_tclass fails on Windows
* :ghissue:`1398`: fix %tb after SyntaxError
* :ghissue:`1478`: key function or lambda in sorted function doesn't find global variables
* :ghissue:`1415`: handle exit/quit/exit()/quit() variants in zmqconsole
* :ghissue:`1440`: Fix for failing testsuite when using --with-xml-coverage on windows.
* :ghissue:`1419`: Add %install_ext magic function.
* :ghissue:`1424`: Win32 shell interactivity
* :ghissue:`1434`: Controller should schedule tasks of multiple clients at the same time
* :ghissue:`1268`: notebook %reset magic fails with StdinNotImplementedError
* :ghissue:`1438`: from cherrypy import expose fails when running script form parent directory
* :ghissue:`1468`: Simplify structure of a Job in the TaskScheduler
* :ghissue:`875`: never build unicode error messages
* :ghissue:`1107`: Tab autocompletion can suggest invalid syntax
* :ghissue:`1447`: 1107 - Tab autocompletion can suggest invalid syntax
* :ghissue:`1469`: Fix typo in comment (insert space)
* :ghissue:`1463`: Fix completion when importing modules in the cwd.
* :ghissue:`1437`: unfriendly error handling with pythonw and ipython-qtconsole
* :ghissue:`1466`: Fix for issue #1437, unfriendly windows qtconsole error handling
* :ghissue:`1432`: Fix ipython directive
* :ghissue:`1465`: allow `ipython help subcommand` syntax
* :ghissue:`1394`: Wishlist: Remove hard dependency on ctypes
* :ghissue:`1416`: Conditional import of ctypes in inputhook
* :ghissue:`1462`: expedite parallel tests
* :ghissue:`1418`: Strict mode in javascript
* :ghissue:`1410`: Add javascript library and css stylesheet loading to JS class.
* :ghissue:`1427`: #922 again
* :ghissue:`1448`: Fix for #875 Never build unicode error messages
* :ghissue:`1458`: use eval to uncan References
* :ghissue:`1455`: Python3 install fails
* :ghissue:`1450`: load mathjax from CDN via https
* :ghissue:`1182`: Qtconsole, multiwindow
* :ghissue:`1439`: Notebook not storing heading celltype information
* :ghissue:`1451`: include heading level in JSON
* :ghissue:`1444`: Fix pyhton -> python typos
* :ghissue:`1412`: Input parsing issue with %prun
* :ghissue:`1414`: ignore errors in shell.var_expand
* :ghissue:`1441`: (1) Enable IPython.notebook.kernel.execute to publish display_* even it is not called with a code cell and (2) remove empty html element when execute "display_*"
* :ghissue:`1431`: Beginner Error: ipython qtconsole
* :ghissue:`1436`: "ipython-qtconsole --gui qt" hangs on 64-bit win7
* :ghissue:`1433`: websocket connection fails on Chrome
* :ghissue:`1430`: Fix for tornado check for tornado < 1.1.0
* :ghissue:`1408`: test_get_home_dir_3 failed on Mac OS X
* :ghissue:`1413`: get_home_dir expands symlinks, adjust test accordingly
* :ghissue:`1420`: fixes #922
* :ghissue:`823`: KnownFailure tests appearing as errors
* :ghissue:`1385`: updated and prettified magic doc strings
* :ghissue:`1406`: Browser selection
* :ghissue:`1411`: ipcluster starts 8 engines "successfully" but Client only finds two
* :ghissue:`1375`: %history -g -f file encoding issue
* :ghissue:`1377`: Saving non-ascii history
* :ghissue:`797`: Source introspection needs to be smarter in python 3.2
* :ghissue:`846`: Autoreload extension doesn't work with Python 3.2
* :ghissue:`1360`: IPython notebook not starting on winXP
* :ghissue:`1407`: Qtconsole segfaults on OSX when displaying some pop-up function tooltips
* :ghissue:`1402`: fix symlinked /home issue for FreeBSD
* :ghissue:`1403`: pyreadline cyclic dependency with pdb++/pdbpp module
* :ghissue:`1405`: Only monkeypatch xunit when the tests are run using it.
* :ghissue:`1404`: Feature Request: List/Dictionary tab completion
* :ghissue:`1395`: Xunit & KnownFailure
* :ghissue:`1396`: Fix for %tb magic.
* :ghissue:`1397`: Stay or leave message not working, Safari session lost.
* :ghissue:`1389`: pylab=inline inoperant through ssh tunnelling?
* :ghissue:`1386`: Jsd3
* :ghissue:`1388`: Add simple support for running inside a virtualenv
* :ghissue:`826`: Add support for creation of parallel task when no engine is running
* :ghissue:`1391`: Improve Hub/Scheduler when no engines are registered
* :ghissue:`1369`: load header with engine id when engine dies in TaskScheduler
* :ghissue:`1345`: notebook can't save unicode as script
* :ghissue:`1353`: Save notebook as script using unicode file handle.
* :ghissue:`1352`: Add '-m mod : run library module as a script' option.
* :ghissue:`1363`: Fix some minor color/style config issues in the qtconsole
* :ghissue:`1371`: Adds a quiet keyword to sync_imports
* :ghissue:`1390`: Blank screen for notebooks on Safari
* :ghissue:`1387`: Fixing Cell menu to update cell type select box.
* :ghissue:`645`: Standalone WX GUI support is broken
* :ghissue:`1296`: Wx gui example: fixes the broken example for `%gui wx`.
* :ghissue:`1254`: typo in notebooklist.js breaks links
* :ghissue:`781`: Users should be able to clone a notebook
* :ghissue:`1372`: ipcontroller cleans up connection files unless reuse=True
* :ghissue:`1374`: remove calls to meaningless ZMQStream.on_err
* :ghissue:`1382`: Update RO for Notebook
* :ghissue:`1370`: allow draft76 websockets (Safari)
* :ghissue:`1368`: Ensure handler patterns are str, not unicode
* :ghissue:`1379`: Sage link on website homepage broken
* :ghissue:`1376`: FWIW does not work with Chrome 16.0.912.77 Ubuntu 10.10
* :ghissue:`1358`: Cannot install ipython on Windows 7 64-bit
* :ghissue:`1367`: Ctrl - m  t does not toggle output in chrome
* :ghissue:`1359`: [sympyprinting] MathJax can't render \root{m}{n}
* :ghissue:`1337`: Tab in the notebook after `(` should not indent, only give a tooltip
* :ghissue:`1339`: Notebook printing broken
* :ghissue:`1344`: Ctrl + M + L does not toggle line numbering in htmlnotebook
* :ghissue:`1348`: Ctrl + M + M does not switch to markdown cell
* :ghissue:`1361`: Notebook bug fix branch
* :ghissue:`1364`: avoid jsonlib returning Decimal
* :ghissue:`1362`: Don't log complete contents of history replies, even in debug
* :ghissue:`888`: ReST support in notebooks
* :ghissue:`1205`: notebook stores HTML escaped text in the file
* :ghissue:`1351`: add IPython.embed_kernel() 
* :ghissue:`1243`: magic commands without % are not completed properly in htmlnotebook
* :ghissue:`1347`: fix weird magic completion in notebook
* :ghissue:`1355`: notebook.html extends layout.html now
* :ghissue:`1354`: min and max in the notebook
* :ghissue:`1346`: fixups for alternate URL prefix stuff
* :ghissue:`1336`: crack at making notebook.html use the layout.html template
* :ghissue:`1331`: RST and heading cells
* :ghissue:`1350`: Add '-m mod : run library module as a script' option
* :ghissue:`1247`: fixes a bug causing extra newlines after comments.
* :ghissue:`1329`: add base_url to notebook configuration options
* :ghissue:`1332`: notebook - allow prefixes in URL path.
* :ghissue:`1317`: Very slow traceback construction from Cython extension
* :ghissue:`1341`: Don't attempt to tokenize binary files for tracebacks
* :ghissue:`1300`: Cell Input collapse
* :ghissue:`1334`: added key handler for control-s to notebook, seems to work pretty well
* :ghissue:`1338`: Fix see also in docstrings so API docs build
* :ghissue:`1335`: Notebook toolbar UI
* :ghissue:`1299`: made notebook.html extend layout.html
* :ghissue:`1318`: make Ctrl-D in qtconsole act same as in terminal (ready to merge)
* :ghissue:`873`: ReST support in notebook frontend
* :ghissue:`1139`: Notebook webkit notification
* :ghissue:`1314`: Insertcell
* :ghissue:`1328`: Coverage
* :ghissue:`1206`: don't preserve fixConsole output in json
* :ghissue:`1330`: Add linewrapping to text cells (new feature in CodeMirror).
* :ghissue:`1309`: Inoculate clearcmd extension into %reset functionality
* :ghissue:`1327`: Updatecm2
* :ghissue:`1326`: Removing Ace edit capability.
* :ghissue:`1325`: forgotten selected_cell -> get_selected_cell
* :ghissue:`1316`: Pass subprocess test runners a suitable location for xunit output
* :ghissue:`1315`: Collect results from subprocess runners and spit out Xunit XML output.
* :ghissue:`1233`: Update CodeMirror to the latest version
* :ghissue:`1234`: Refactor how the notebook focuses cells
* :ghissue:`1235`: After upgrading CodeMirror check the status of some bugs
* :ghissue:`1236`: Review how select is called when notebook cells are inserted
* :ghissue:`1303`: Updatecm
* :ghissue:`1311`: Fixing CM related indentation problems.
* :ghissue:`1304`: controller/server load can disrupt heartbeat
* :ghissue:`1312`: minor heartbeat tweaks
* :ghissue:`1302`: Input parsing with %prun clobbers escapes
* :ghissue:`1306`: Fix %prun input parsing for escaped characters (closes #1302)
* :ghissue:`1251`: IPython-0.12 can't import map module on Python 3.1
* :ghissue:`1202`: Pyreadline install exclusion for 64 bit windows no longer required,  version dependency not correctly specified.
* :ghissue:`1301`: New "Fix for issue #1202" based on current master.
* :ghissue:`1242`: changed key map name to match changes to python mode
* :ghissue:`1203`: Fix for issue #1202
* :ghissue:`1289`: Make autoreload extension work on Python 3.
* :ghissue:`1263`: Different 'C-x' for shortcut, 'C-m c' not toCodeCell anymore
* :ghissue:`1259`: Replace "from (.|..) import" with absolute imports.
* :ghissue:`1278`: took a crack at making notebook.html extend layout.html
* :ghissue:`1210`: Add 'quiet' option to suppress screen output during %prun calls, edited dochelp
* :ghissue:`1288`: Don't ask for confirmation when stdin isn't available
* :ghissue:`1290`: Cell-level cut & paste overwrites multiple cells
* :ghissue:`1291`: Minor, but important fixes to cut/copy/paste.
* :ghissue:`1293`: TaskScheduler.hwm default value
* :ghissue:`1294`: TaskScheduler.hwm default to 1 instead of 0
* :ghissue:`1281`: in Hub: registration_timeout must be an integer, but heartmonitor.period is CFloat
* :ghissue:`1283`: HeartMonitor.period should be an Integer
* :ghissue:`1162`: Allow merge/split adjacent cells in notebook
* :ghissue:`1264`: Aceify
* :ghissue:`1261`: Mergesplit
* :ghissue:`1269`: Another strange input handling error
* :ghissue:`1284`: a fix for GH 1269
* :ghissue:`1232`: Dead kernel loop
* :ghissue:`1279`: ImportError: cannot import name S1 (from logging)
* :ghissue:`1276`: notebook menu item to send a KeyboardInterrupt to the kernel
* :ghissue:`1213`: BUG: Minor typo in history_console_widget.py
* :ghissue:`1248`: IPython notebook doesn't work with lastest version of tornado
* :ghissue:`1267`: add NoDB for non-recording Hub
* :ghissue:`1222`: allow Reference as callable in map/apply
* :ghissue:`1257`: use self.kernel_manager_class in qtconsoleapp
* :ghissue:`1220`: Open a new notebook while connecting to an existing kernel (opened by qtconsole or terminal or standalone)
* :ghissue:`1253`: set auto_create flag for notebook apps
* :ghissue:`1260`: heartbeat failure on long gil-holding operation
* :ghissue:`1262`: Heartbeat no longer shares the app's Context
* :ghissue:`1225`: SyntaxError display broken in Python 3
* :ghissue:`1229`: Fix display of SyntaxError in Python 3
* :ghissue:`1256`: Dewijmoize
* :ghissue:`1246`: Skip tests that require X, when importing pylab results in RuntimeError.
* :ghissue:`1250`: Wijmoize
* :ghissue:`1244`: can not imput chinese word "造" , exit right now
* :ghissue:`1194`: Adding Opera 11 as a compatible browser for ipython notebook
* :ghissue:`1198`: Kernel Has Died error in Notebook
* :ghissue:`1211`: serve local files in notebook-dir
* :ghissue:`1224`: edit text cells on double-click instead of single-click
* :ghissue:`1187`: misc notebook: connection file cleanup, first heartbeat, startup flush
* :ghissue:`1207`: fix loadpy duplicating newlines
* :ghissue:`1060`: Always save the .py file to disk next to the .ipynb
* :ghissue:`1066`: execute cell in place should preserve the current insertion-point in the notebook
* :ghissue:`1141`: "In" numbers are not invalidated when restarting kernel
* :ghissue:`1231`: pip on OSX tries to install files in /System directory.
* :ghissue:`1129`: Unified setup.py
* :ghissue:`1199`: Reduce IPython.external.*
* :ghissue:`1219`: Make all the static files path absolute.
* :ghissue:`1218`: Added -q option to %prun for suppression of the output, along with editing the dochelp string.
* :ghissue:`1217`: Added -q option to %prun for suppression of the output, along with editing the dochelp string
* :ghissue:`1216`: Pdb tab completion does not work in QtConsole
* :ghissue:`1197`: Interactive shell trying to: from ... import history
* :ghissue:`1175`: core.completer: Clean up excessive and unused code.
* :ghissue:`1208`: should dv.sync_import print failed imports ?
* :ghissue:`1186`: payloadpage.py not used by qtconsole
* :ghissue:`1204`: double newline from %loadpy in python notebook (at least on mac)
* :ghissue:`1192`: Invalid JSON data
* :ghissue:`1196`: docs: looks like a file path might have been accidentally pasted in the middle of a word
* :ghissue:`1189`: Right justify of 'in' prompt in variable prompt size configurations
* :ghissue:`1185`: ipython console not work proper with stdout...
* :ghissue:`1191`: profile/startup files not executed with "notebook"
* :ghissue:`1190`: Fix link to Chris Fonnesbeck blog post about 0.11 highlights.
* :ghissue:`1174`: Remove %install_default_config and %install_profiles

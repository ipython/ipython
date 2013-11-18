.. _issues_list_012:

Issues closed in the 0.12 development cycle
===========================================

Issues closed in 0.12.1
-----------------------

GitHub stats for bugfix release 0.12.1 (12/28/2011-04/16/2012), backporting
pull requests from 0.13.

We closed a total of 71 issues: 44 pull requests and 27 issues; this is the
full list (generated with the script `tools/github_stats.py`).

This list is automatically generated, and may be incomplete:

Pull Requests (44):

* :ghpull:`1175`: core.completer: Clean up excessive and unused code.
* :ghpull:`1187`: misc notebook: connection file cleanup, first heartbeat, startup flush
* :ghpull:`1190`: Fix link to Chris Fonnesbeck blog post about 0.11 highlights.
* :ghpull:`1196`: docs: looks like a file path might have been accidentally pasted in the middle of a word
* :ghpull:`1206`: don't preserve fixConsole output in json
* :ghpull:`1207`: fix loadpy duplicating newlines
* :ghpull:`1213`: BUG: Minor typo in history_console_widget.py
* :ghpull:`1218`: Added -q option to %prun for suppression of the output, along with editing the dochelp string.
* :ghpull:`1222`: allow Reference as callable in map/apply
* :ghpull:`1229`: Fix display of SyntaxError in Python 3
* :ghpull:`1246`: Skip tests that require X, when importing pylab results in RuntimeError.
* :ghpull:`1253`: set auto_create flag for notebook apps
* :ghpull:`1257`: use self.kernel_manager_class in qtconsoleapp
* :ghpull:`1262`: Heartbeat no longer shares the app's Context
* :ghpull:`1283`: HeartMonitor.period should be an Integer
* :ghpull:`1284`: a fix for GH 1269
* :ghpull:`1289`: Make autoreload extension work on Python 3.
* :ghpull:`1306`: Fix %prun input parsing for escaped characters (closes #1302)
* :ghpull:`1312`: minor heartbeat tweaks
* :ghpull:`1318`: make Ctrl-D in qtconsole act same as in terminal (ready to merge)
* :ghpull:`1341`: Don't attempt to tokenize binary files for tracebacks
* :ghpull:`1353`: Save notebook as script using unicode file handle.
* :ghpull:`1363`: Fix some minor color/style config issues in the qtconsole
* :ghpull:`1364`: avoid jsonlib returning Decimal
* :ghpull:`1369`: load header with engine id when engine dies in TaskScheduler
* :ghpull:`1370`: allow draft76 websockets (Safari)
* :ghpull:`1374`: remove calls to meaningless ZMQStream.on_err
* :ghpull:`1377`: Saving non-ascii history
* :ghpull:`1396`: Fix for %tb magic.
* :ghpull:`1402`: fix symlinked /home issue for FreeBSD
* :ghpull:`1413`: get_home_dir expands symlinks, adjust test accordingly
* :ghpull:`1414`: ignore errors in shell.var_expand
* :ghpull:`1430`: Fix for tornado check for tornado < 1.1.0
* :ghpull:`1445`: Don't build sphinx docs for sdists
* :ghpull:`1463`: Fix completion when importing modules in the cwd.
* :ghpull:`1477`: fix dangling `buffer` in IPython.parallel.util
* :ghpull:`1495`: BUG: Fix pretty-printing for overzealous objects
* :ghpull:`1496`: BUG: LBYL when clearing the output history on shutdown.
* :ghpull:`1514`: DOC: Fix references to IPython.lib.pretty instead of the old location
* :ghpull:`1517`: Fix indentation bug in IPython/lib/pretty.py
* :ghpull:`1538`: store git commit hash in utils._sysinfo instead of hidden data file
* :ghpull:`1599`: Fix for %run -d in Python 3
* :ghpull:`1602`: Fix %env for Python 3
* :ghpull:`1607`: cleanup sqlitedb temporary db file after tests

Issues (27):

* :ghissue:`676`: IPython.embed() from ipython crashes twice on exit
* :ghissue:`846`: Autoreload extension doesn't work with Python 3.2
* :ghissue:`1187`: misc notebook: connection file cleanup, first heartbeat, startup flush
* :ghissue:`1191`: profile/startup files not executed with "notebook"
* :ghissue:`1197`: Interactive shell trying to: from ... import history
* :ghissue:`1198`: Kernel Has Died error in Notebook
* :ghissue:`1201`: %env magic fails with Python 3.2
* :ghissue:`1204`: double newline from %loadpy in python notebook (at least on mac)
* :ghissue:`1208`: should dv.sync_import print failed imports ?
* :ghissue:`1225`: SyntaxError display broken in Python 3
* :ghissue:`1232`: Dead kernel loop
* :ghissue:`1241`: When our debugger class is used standalone `_oh` key errors are thrown
* :ghissue:`1254`: typo in notebooklist.js breaks links
* :ghissue:`1260`: heartbeat failure on long gil-holding operation
* :ghissue:`1268`: notebook %reset magic fails with StdinNotImplementedError
* :ghissue:`1269`: Another strange input handling error
* :ghissue:`1281`: in Hub: registration_timeout must be an integer, but heartmonitor.period is CFloat
* :ghissue:`1302`: Input parsing with %prun clobbers escapes
* :ghissue:`1304`: controller/server load can disrupt heartbeat
* :ghissue:`1317`: Very slow traceback construction from Cython extension
* :ghissue:`1345`: notebook can't save unicode as script
* :ghissue:`1375`: %history -g -f file encoding issue
* :ghissue:`1401`: numpy arrays cannot be used with View.apply() in Python 3
* :ghissue:`1408`: test_get_home_dir_3 failed on Mac OS X
* :ghissue:`1412`: Input parsing issue with %prun
* :ghissue:`1421`: ipython32 %run -d breaks with NameError name 'execfile' is not defined
* :ghissue:`1484`: unhide .git_commit_info.ini


Issues closed in 0.12
---------------------

In this cycle, from August 1 to December 28 2011, we closed a total of 515
issues, 257 pull requests and 258 regular issues; this is the full list
(generated with the script `tools/github_stats.py`).

Pull requests (257):

* `1174 <https://github.com/ipython/ipython/issues/1174>`_: Remove %install_default_config and %install_profiles
* `1178 <https://github.com/ipython/ipython/issues/1178>`_: Correct string type casting in pinfo.
* `1096 <https://github.com/ipython/ipython/issues/1096>`_: Show class init and call tooltips in notebook
* `1176 <https://github.com/ipython/ipython/issues/1176>`_: Modifications to profile list
* `1173 <https://github.com/ipython/ipython/issues/1173>`_: don't load gui/pylab in console frontend
* `1168 <https://github.com/ipython/ipython/issues/1168>`_: Add --script flag as shorthand for notebook save_script option.
* `1165 <https://github.com/ipython/ipython/issues/1165>`_: encode image_tag as utf8 in [x]html export
* `1161 <https://github.com/ipython/ipython/issues/1161>`_: Allow %loadpy to load remote URLs that don't end in .py
* `1158 <https://github.com/ipython/ipython/issues/1158>`_: Add coding header when notebook exported to .py file.
* `1160 <https://github.com/ipython/ipython/issues/1160>`_: don't ignore ctrl-C during `%gui qt`
* `1159 <https://github.com/ipython/ipython/issues/1159>`_: Add encoding header to Python files downloaded from notebooks.
* `1155 <https://github.com/ipython/ipython/issues/1155>`_: minor post-execute fixes (#1154)
* `1153 <https://github.com/ipython/ipython/issues/1153>`_: Pager tearing bug
* `1152 <https://github.com/ipython/ipython/issues/1152>`_: Add support for displaying maptlotlib axes directly.
* `1079 <https://github.com/ipython/ipython/issues/1079>`_: Login/out button cleanups
* `1151 <https://github.com/ipython/ipython/issues/1151>`_: allow access to user_ns in prompt_manager
* `1120 <https://github.com/ipython/ipython/issues/1120>`_: updated vim-ipython (pending)
* `1150 <https://github.com/ipython/ipython/issues/1150>`_: BUG: Scrolling pager in vsplit on Mac OSX tears.
* `1149 <https://github.com/ipython/ipython/issues/1149>`_: #1148 (win32 arg_split)
* `1147 <https://github.com/ipython/ipython/issues/1147>`_: Put qtconsole forground when launching
* `1146 <https://github.com/ipython/ipython/issues/1146>`_: allow saving notebook.py next to notebook.ipynb
* `1128 <https://github.com/ipython/ipython/issues/1128>`_: fix pylab StartMenu item
* `1140 <https://github.com/ipython/ipython/issues/1140>`_: Namespaces for embedding
* `1132 <https://github.com/ipython/ipython/issues/1132>`_: [notebook] read-only: disable name field
* `1125 <https://github.com/ipython/ipython/issues/1125>`_: notebook : update logo
* `1135 <https://github.com/ipython/ipython/issues/1135>`_: allow customized template and static file paths for the notebook web app
* `1122 <https://github.com/ipython/ipython/issues/1122>`_: BUG: Issue #755 qt IPythonWidget.execute_file fails if filename contains...
* `1137 <https://github.com/ipython/ipython/issues/1137>`_: rename MPIExecLaunchers to MPILaunchers
* `1130 <https://github.com/ipython/ipython/issues/1130>`_: optionally ignore  shlex's ValueError in arg_split
* `1116 <https://github.com/ipython/ipython/issues/1116>`_: Shlex unicode
* `1073 <https://github.com/ipython/ipython/issues/1073>`_: Storemagic plugin
* `1143 <https://github.com/ipython/ipython/issues/1143>`_: Add post_install script to create start menu entries in Python 3
* `1138 <https://github.com/ipython/ipython/issues/1138>`_: Fix tests to work when ~/.config/ipython contains a symlink.
* `1121 <https://github.com/ipython/ipython/issues/1121>`_: Don't transform function calls on IPyAutocall objects
* `1118 <https://github.com/ipython/ipython/issues/1118>`_: protect CRLF from carriage-return action
* `1105 <https://github.com/ipython/ipython/issues/1105>`_: Fix for prompts containing newlines.
* `1126 <https://github.com/ipython/ipython/issues/1126>`_: Totally remove pager when read only (notebook)
* `1091 <https://github.com/ipython/ipython/issues/1091>`_: qtconsole : allow copy with shortcut in pager
* `1114 <https://github.com/ipython/ipython/issues/1114>`_: fix magics history in two-process ipython console
* `1113 <https://github.com/ipython/ipython/issues/1113>`_: Fixing #1112 removing failing asserts for test_carriage_return and test_beep
* `1089 <https://github.com/ipython/ipython/issues/1089>`_: Support carriage return ('\r') and beep ('\b') characters in the qtconsole
* `1108 <https://github.com/ipython/ipython/issues/1108>`_: Completer usability 2 (rebased of  pr #1082)
* `864 <https://github.com/ipython/ipython/issues/864>`_: Two-process terminal frontend (ipython core branch)
* `1082 <https://github.com/ipython/ipython/issues/1082>`_: usability and cross browser compat for completer
* `1053 <https://github.com/ipython/ipython/issues/1053>`_: minor improvements to text placement in qtconsole
* `1106 <https://github.com/ipython/ipython/issues/1106>`_: Fix display of errors in compiled code on Python 3
* `1077 <https://github.com/ipython/ipython/issues/1077>`_: allow the notebook to run without MathJax
* `1072 <https://github.com/ipython/ipython/issues/1072>`_: If object has a getdoc() method, override its normal docstring.
* `1059 <https://github.com/ipython/ipython/issues/1059>`_: Switch to simple `__IPYTHON__` global
* `1070 <https://github.com/ipython/ipython/issues/1070>`_: Execution count after SyntaxError
* `1098 <https://github.com/ipython/ipython/issues/1098>`_: notebook: config section UI
* `1101 <https://github.com/ipython/ipython/issues/1101>`_: workaround spawnb missing from pexpect.__all__
* `1097 <https://github.com/ipython/ipython/issues/1097>`_: typo, should fix #1095
* `1099 <https://github.com/ipython/ipython/issues/1099>`_: qtconsole export xhtml/utf8
* `1083 <https://github.com/ipython/ipython/issues/1083>`_: Prompts
* `1081 <https://github.com/ipython/ipython/issues/1081>`_: Fix wildcard search for updated namespaces
* `1084 <https://github.com/ipython/ipython/issues/1084>`_: write busy in notebook window title...
* `1078 <https://github.com/ipython/ipython/issues/1078>`_: PromptManager fixes
* `1064 <https://github.com/ipython/ipython/issues/1064>`_: Win32 shlex
* `1069 <https://github.com/ipython/ipython/issues/1069>`_: As you type completer, fix on Firefox
* `1039 <https://github.com/ipython/ipython/issues/1039>`_: Base of an as you type completer.
* `1065 <https://github.com/ipython/ipython/issues/1065>`_: Qtconsole fix racecondition
* `507 <https://github.com/ipython/ipython/issues/507>`_: Prompt manager
* `1056 <https://github.com/ipython/ipython/issues/1056>`_: Warning in code. qtconsole ssh -X
* `1036 <https://github.com/ipython/ipython/issues/1036>`_: Clean up javascript based on js2-mode feedback.
* `1052 <https://github.com/ipython/ipython/issues/1052>`_: Pylab fix
* `648 <https://github.com/ipython/ipython/issues/648>`_: Usermod
* `969 <https://github.com/ipython/ipython/issues/969>`_: Pexpect-u
* `1007 <https://github.com/ipython/ipython/issues/1007>`_: Fix paste/cpaste bug and refactor/cleanup that code a lot.
* `506 <https://github.com/ipython/ipython/issues/506>`_: make ENTER on a previous input field replace current input buffer
* `1040 <https://github.com/ipython/ipython/issues/1040>`_: json/jsonapi cleanup
* `1042 <https://github.com/ipython/ipython/issues/1042>`_: fix firefox (windows) break line on empty prompt number
* `1015 <https://github.com/ipython/ipython/issues/1015>`_: emacs freezes when tab is hit in ipython with latest python-mode
* `1023 <https://github.com/ipython/ipython/issues/1023>`_: flush stdout/stderr at the end of kernel init
* `956 <https://github.com/ipython/ipython/issues/956>`_: Generate "All magics..." menu live
* `1038 <https://github.com/ipython/ipython/issues/1038>`_: Notebook: don't change cell when selecting code using shift+up/down.
* `987 <https://github.com/ipython/ipython/issues/987>`_: Add Tooltip to notebook.
* `1028 <https://github.com/ipython/ipython/issues/1028>`_: Cleaner minimum version comparison 
* `998 <https://github.com/ipython/ipython/issues/998>`_: defer to stdlib for path.get_home_dir()
* `1033 <https://github.com/ipython/ipython/issues/1033>`_: update copyright to 2011/20xx-2011
* `1032 <https://github.com/ipython/ipython/issues/1032>`_: Intercept <esc> avoid closing websocket on Firefox
* `1030 <https://github.com/ipython/ipython/issues/1030>`_: use pyzmq tools where appropriate
* `1029 <https://github.com/ipython/ipython/issues/1029>`_: Restore pspersistence, including %store magic, as an extension.
* `1025 <https://github.com/ipython/ipython/issues/1025>`_: Dollar escape
* `999 <https://github.com/ipython/ipython/issues/999>`_: Fix issue #880 - more useful message to user when %paste fails
* `938 <https://github.com/ipython/ipython/issues/938>`_: changes to get ipython.el to work with the latest python-mode.el
* `1012 <https://github.com/ipython/ipython/issues/1012>`_: Add logout button.
* `1020 <https://github.com/ipython/ipython/issues/1020>`_: Dollar formatter for ! shell calls
* `1019 <https://github.com/ipython/ipython/issues/1019>`_: Use repr() to make quoted strings
* `1008 <https://github.com/ipython/ipython/issues/1008>`_: don't use crash_handler by default
* `1003 <https://github.com/ipython/ipython/issues/1003>`_: Drop consecutive duplicates when refilling readline history
* `997 <https://github.com/ipython/ipython/issues/997>`_: don't unregister interrupted post-exec functions
* `996 <https://github.com/ipython/ipython/issues/996>`_: add Integer traitlet
* `1016 <https://github.com/ipython/ipython/issues/1016>`_: Fix password hashing for Python 3
* `1014 <https://github.com/ipython/ipython/issues/1014>`_: escape minus signs in manpages
* `1013 <https://github.com/ipython/ipython/issues/1013>`_: [NumPyExampleDocstring] link was pointing to raw file
* `1011 <https://github.com/ipython/ipython/issues/1011>`_: Add hashed password support.
* `1005 <https://github.com/ipython/ipython/issues/1005>`_: Quick fix for os.system requiring str parameter
* `994 <https://github.com/ipython/ipython/issues/994>`_: Allow latex formulas in HTML output
* `955 <https://github.com/ipython/ipython/issues/955>`_: Websocket Adjustments
* `979 <https://github.com/ipython/ipython/issues/979>`_: use system_raw in terminal, even on Windows
* `989 <https://github.com/ipython/ipython/issues/989>`_: fix arguments for commands in _process_posix
* `991 <https://github.com/ipython/ipython/issues/991>`_: Show traceback, continuing to start kernel if pylab init fails
* `981 <https://github.com/ipython/ipython/issues/981>`_: Split likely multiline text when writing JSON notebooks
* `957 <https://github.com/ipython/ipython/issues/957>`_: allow change of png DPI in inline backend
* `968 <https://github.com/ipython/ipython/issues/968>`_: add wantDirectory to ipdoctest, so that directories will be checked for e
* `984 <https://github.com/ipython/ipython/issues/984>`_: Do not expose variables defined at startup to %who etc.
* `985 <https://github.com/ipython/ipython/issues/985>`_: Fixes for parallel code on Python 3
* `963 <https://github.com/ipython/ipython/issues/963>`_: disable calltips in PySide < 1.0.7 to prevent segfault
* `976 <https://github.com/ipython/ipython/issues/976>`_: Getting started on what's new
* `929 <https://github.com/ipython/ipython/issues/929>`_: Multiline history
* `964 <https://github.com/ipython/ipython/issues/964>`_: Default profile
* `961 <https://github.com/ipython/ipython/issues/961>`_: Disable the pager for the test suite
* `953 <https://github.com/ipython/ipython/issues/953>`_: Physics extension
* `950 <https://github.com/ipython/ipython/issues/950>`_: Add directory for startup files
* `940 <https://github.com/ipython/ipython/issues/940>`_: allow setting HistoryManager.hist_file with config
* `948 <https://github.com/ipython/ipython/issues/948>`_: Monkeypatch Tornado 2.1.1 so it works with Google Chrome 16.
* `916 <https://github.com/ipython/ipython/issues/916>`_: Run p ( https://github.com/ipython/ipython/pull/901 )
* `923 <https://github.com/ipython/ipython/issues/923>`_: %config magic
* `920 <https://github.com/ipython/ipython/issues/920>`_: unordered iteration of AsyncMapResults (+ a couple fixes)
* `941 <https://github.com/ipython/ipython/issues/941>`_: Follow-up to 387dcd6a, `_rl.__doc__` is `None` with pyreadline
* `931 <https://github.com/ipython/ipython/issues/931>`_: read-only notebook mode
* `921 <https://github.com/ipython/ipython/issues/921>`_: Show invalid config message on TraitErrors during init
* `815 <https://github.com/ipython/ipython/issues/815>`_: Fix #481 using custom qt4 input hook
* `936 <https://github.com/ipython/ipython/issues/936>`_: Start webbrowser in a thread.  Prevents lockup with Chrome.
* `937 <https://github.com/ipython/ipython/issues/937>`_: add dirty trick for readline import on OSX
* `913 <https://github.com/ipython/ipython/issues/913>`_: Py3 tests2
* `933 <https://github.com/ipython/ipython/issues/933>`_: Cancel in qt console closeevent should trigger event.ignore()
* `930 <https://github.com/ipython/ipython/issues/930>`_: read-only notebook mode
* `910 <https://github.com/ipython/ipython/issues/910>`_: Make import checks more explicit in %whos
* `926 <https://github.com/ipython/ipython/issues/926>`_: reincarnate -V cmdline option
* `928 <https://github.com/ipython/ipython/issues/928>`_: BUG: Set context for font size change shortcuts in ConsoleWidget
* `901 <https://github.com/ipython/ipython/issues/901>`_:   - There is a bug when running the profiler in the magic command (prun) with python3
* `912 <https://github.com/ipython/ipython/issues/912>`_: Add magic for cls on windows. Fix for #181.
* `905 <https://github.com/ipython/ipython/issues/905>`_: enable %gui/%pylab magics in the Kernel
* `909 <https://github.com/ipython/ipython/issues/909>`_: Allow IPython to run without sqlite3
* `887 <https://github.com/ipython/ipython/issues/887>`_: Qtconsole menu
* `895 <https://github.com/ipython/ipython/issues/895>`_: notebook download implies save
* `896 <https://github.com/ipython/ipython/issues/896>`_: Execfile
* `899 <https://github.com/ipython/ipython/issues/899>`_: Brian's Notebook work
* `892 <https://github.com/ipython/ipython/issues/892>`_: don't close figures every cycle with inline matplotlib backend
* `893 <https://github.com/ipython/ipython/issues/893>`_: Adding clear_output to kernel and HTML notebook
* `789 <https://github.com/ipython/ipython/issues/789>`_: Adding clear_output to kernel and HTML notebook.
* `898 <https://github.com/ipython/ipython/issues/898>`_: Don't pass unicode sys.argv with %run or `ipython script.py`
* `897 <https://github.com/ipython/ipython/issues/897>`_: Add tooltips to the notebook via 'title' attr.
* `877 <https://github.com/ipython/ipython/issues/877>`_: partial fix for issue #678
* `838 <https://github.com/ipython/ipython/issues/838>`_: reenable multiline history for terminals
* `872 <https://github.com/ipython/ipython/issues/872>`_: The constructor of Client() checks for AssertionError in validate_url to open a file instead of connection to a URL if it fails.
* `884 <https://github.com/ipython/ipython/issues/884>`_: Notebook usability fixes
* `883 <https://github.com/ipython/ipython/issues/883>`_: User notification if notebook saving fails
* `889 <https://github.com/ipython/ipython/issues/889>`_: Add drop_by_id method to shell, to remove variables added by extensions.
* `891 <https://github.com/ipython/ipython/issues/891>`_: Ability to open the notebook in a browser when it starts
* `813 <https://github.com/ipython/ipython/issues/813>`_: Create menu bar for qtconsole
* `876 <https://github.com/ipython/ipython/issues/876>`_: protect IPython from bad custom exception handlers
* `856 <https://github.com/ipython/ipython/issues/856>`_: Backgroundjobs
* `868 <https://github.com/ipython/ipython/issues/868>`_: Warn user if MathJax can't be fetched from notebook closes #744
* `878 <https://github.com/ipython/ipython/issues/878>`_: store_history=False default for run_cell
* `824 <https://github.com/ipython/ipython/issues/824>`_: History access
* `850 <https://github.com/ipython/ipython/issues/850>`_: Update codemirror to 2.15 and make the code internally more version-agnostic
* `861 <https://github.com/ipython/ipython/issues/861>`_: Fix for issue #56
* `819 <https://github.com/ipython/ipython/issues/819>`_: Adding -m option to %run, similar to -m for python interpreter.
* `855 <https://github.com/ipython/ipython/issues/855>`_: promote aliases and flags, to ensure they have priority over config files
* `862 <https://github.com/ipython/ipython/issues/862>`_: BUG: Completion widget position and pager focus.
* `847 <https://github.com/ipython/ipython/issues/847>`_: Allow connection to kernels by files
* `708 <https://github.com/ipython/ipython/issues/708>`_: Two-process terminal frontend
* `857 <https://github.com/ipython/ipython/issues/857>`_: make sdist flags work again (e.g. --manifest-only)
* `835 <https://github.com/ipython/ipython/issues/835>`_: Add Tab key to list of keys that scroll down the paging widget.
* `859 <https://github.com/ipython/ipython/issues/859>`_: Fix for issue #800
* `848 <https://github.com/ipython/ipython/issues/848>`_: Python3 setup.py install failiure
* `845 <https://github.com/ipython/ipython/issues/845>`_: Tests on Python 3
* `802 <https://github.com/ipython/ipython/issues/802>`_: DOC: extensions: add documentation for the bundled extensions
* `830 <https://github.com/ipython/ipython/issues/830>`_: contiguous stdout/stderr in notebook
* `761 <https://github.com/ipython/ipython/issues/761>`_: Windows: test runner fails if repo path (e.g. home dir) contains spaces
* `801 <https://github.com/ipython/ipython/issues/801>`_: Py3 notebook
* `809 <https://github.com/ipython/ipython/issues/809>`_: use CFRunLoop directly in `ipython kernel --pylab osx`
* `841 <https://github.com/ipython/ipython/issues/841>`_: updated old scipy.org links, other minor doc fixes
* `837 <https://github.com/ipython/ipython/issues/837>`_: remove all trailling spaces
* `834 <https://github.com/ipython/ipython/issues/834>`_: Issue https://github.com/ipython/ipython/issues/832 resolution
* `746 <https://github.com/ipython/ipython/issues/746>`_: ENH: extensions: port autoreload to current API
* `828 <https://github.com/ipython/ipython/issues/828>`_: fixed permissions (sub-modules should not be executable) + added shebang  for run_ipy_in_profiler.py
* `798 <https://github.com/ipython/ipython/issues/798>`_: pexpect & Python 3
* `804 <https://github.com/ipython/ipython/issues/804>`_: Magic 'range' crash if greater than len(input_hist)
* `821 <https://github.com/ipython/ipython/issues/821>`_: update tornado dependency to 2.1
* `807 <https://github.com/ipython/ipython/issues/807>`_: Faciliate ssh tunnel sharing by announcing ports
* `795 <https://github.com/ipython/ipython/issues/795>`_: Add cluster-id for multiple cluster instances per profile
* `742 <https://github.com/ipython/ipython/issues/742>`_: Glut
* `668 <https://github.com/ipython/ipython/issues/668>`_: Greedy completer
* `776 <https://github.com/ipython/ipython/issues/776>`_: Reworking qtconsole shortcut, add fullscreen
* `790 <https://github.com/ipython/ipython/issues/790>`_: TST: add future unicode_literals test (#786)
* `775 <https://github.com/ipython/ipython/issues/775>`_: redirect_in/redirect_out should be constrained to windows only
* `793 <https://github.com/ipython/ipython/issues/793>`_: Don't use readline in the ZMQShell
* `743 <https://github.com/ipython/ipython/issues/743>`_: Pyglet
* `774 <https://github.com/ipython/ipython/issues/774>`_: basic/initial .mailmap for nice shortlog summaries
* `770 <https://github.com/ipython/ipython/issues/770>`_: #769 (reopened)
* `784 <https://github.com/ipython/ipython/issues/784>`_: Parse user code to AST using compiler flags.
* `783 <https://github.com/ipython/ipython/issues/783>`_: always use StringIO, never cStringIO
* `782 <https://github.com/ipython/ipython/issues/782>`_: flush stdout/stderr on displayhook call
* `622 <https://github.com/ipython/ipython/issues/622>`_: Make pylab import all configurable 
* `745 <https://github.com/ipython/ipython/issues/745>`_: Don't assume history requests succeed in qtconsole
* `725 <https://github.com/ipython/ipython/issues/725>`_: don't assume cursor.selectedText() is a string
* `778 <https://github.com/ipython/ipython/issues/778>`_: don't override execfile on Python 2
* `663 <https://github.com/ipython/ipython/issues/663>`_: Python 3 compatilibility work
* `762 <https://github.com/ipython/ipython/issues/762>`_: qtconsole ipython widget's execute_file fails if filename contains spaces or quotes
* `763 <https://github.com/ipython/ipython/issues/763>`_: Set context for shortcuts in ConsoleWidget
* `722 <https://github.com/ipython/ipython/issues/722>`_: PyPy compatibility
* `757 <https://github.com/ipython/ipython/issues/757>`_: ipython.el is broken in 0.11
* `764 <https://github.com/ipython/ipython/issues/764>`_: fix "--colors=<color>" option in py-python-command-args.
* `758 <https://github.com/ipython/ipython/issues/758>`_: use ROUTER/DEALER socket names instead of XREP/XREQ
* `736 <https://github.com/ipython/ipython/issues/736>`_: enh: added authentication ability for webapp
* `748 <https://github.com/ipython/ipython/issues/748>`_: Check for tornado before running frontend.html tests.
* `754 <https://github.com/ipython/ipython/issues/754>`_: restore msg_id/msg_type aliases in top level of msg dict
* `769 <https://github.com/ipython/ipython/issues/769>`_: Don't treat bytes objects as json-safe
* `753 <https://github.com/ipython/ipython/issues/753>`_: DOC: msg['msg_type'] removed
* `766 <https://github.com/ipython/ipython/issues/766>`_: fix "--colors=<color>" option in py-python-command-args.
* `765 <https://github.com/ipython/ipython/issues/765>`_: fix "--colors=<color>" option in py-python-command-args.
* `741 <https://github.com/ipython/ipython/issues/741>`_: Run PyOs_InputHook in pager to keep plot windows interactive.
* `664 <https://github.com/ipython/ipython/issues/664>`_: Remove ipythonrc references from documentation
* `750 <https://github.com/ipython/ipython/issues/750>`_: Tiny doc fixes
* `433 <https://github.com/ipython/ipython/issues/433>`_: ZMQ terminal frontend
* `734 <https://github.com/ipython/ipython/issues/734>`_: Allow %magic argument filenames with spaces to be specified with quotes under win32
* `731 <https://github.com/ipython/ipython/issues/731>`_: respect encoding of display data from urls
* `730 <https://github.com/ipython/ipython/issues/730>`_: doc improvements for running notebook via secure protocol
* `729 <https://github.com/ipython/ipython/issues/729>`_: use null char to start markdown cell placeholder
* `727 <https://github.com/ipython/ipython/issues/727>`_: Minor fixes to the htmlnotebook
* `726 <https://github.com/ipython/ipython/issues/726>`_: use bundled argparse if system argparse is < 1.1
* `705 <https://github.com/ipython/ipython/issues/705>`_: Htmlnotebook
* `723 <https://github.com/ipython/ipython/issues/723>`_: Add 'import time' to IPython/parallel/apps/launcher.py as time.sleep is called without time being imported
* `714 <https://github.com/ipython/ipython/issues/714>`_: Install mathjax for offline use
* `718 <https://github.com/ipython/ipython/issues/718>`_: Underline keyboard shortcut characters on appropriate buttons
* `717 <https://github.com/ipython/ipython/issues/717>`_: Add source highlighting to markdown snippets
* `716 <https://github.com/ipython/ipython/issues/716>`_: update EvalFormatter to allow arbitrary expressions
* `712 <https://github.com/ipython/ipython/issues/712>`_: Reset execution counter after cache is cleared
* `713 <https://github.com/ipython/ipython/issues/713>`_: Align colons in html notebook help dialog
* `709 <https://github.com/ipython/ipython/issues/709>`_: Allow usage of '.' in notebook names
* `706 <https://github.com/ipython/ipython/issues/706>`_: Implement static publishing of HTML notebook
* `674 <https://github.com/ipython/ipython/issues/674>`_: use argparse to parse aliases & flags
* `679 <https://github.com/ipython/ipython/issues/679>`_: HistoryManager.get_session_info()
* `696 <https://github.com/ipython/ipython/issues/696>`_: Fix columnize bug, where tab completion with very long filenames would crash Qt console
* `686 <https://github.com/ipython/ipython/issues/686>`_: add ssh tunnel support to qtconsole
* `685 <https://github.com/ipython/ipython/issues/685>`_: Add SSH tunneling to engines
* `384 <https://github.com/ipython/ipython/issues/384>`_: Allow pickling objects defined interactively.
* `647 <https://github.com/ipython/ipython/issues/647>`_: My fix rpmlint
* `587 <https://github.com/ipython/ipython/issues/587>`_: don't special case for py3k+numpy
* `703 <https://github.com/ipython/ipython/issues/703>`_: make config-loading debug messages more explicit
* `699 <https://github.com/ipython/ipython/issues/699>`_: make calltips configurable in qtconsole
* `666 <https://github.com/ipython/ipython/issues/666>`_: parallel tests & extra readline escapes
* `683 <https://github.com/ipython/ipython/issues/683>`_: BF - allow nose with-doctest setting in environment
* `689 <https://github.com/ipython/ipython/issues/689>`_: Protect ipkernel from bad messages
* `702 <https://github.com/ipython/ipython/issues/702>`_: Prevent ipython.py launcher from being imported.
* `701 <https://github.com/ipython/ipython/issues/701>`_: Prevent ipython.py from being imported by accident
* `670 <https://github.com/ipython/ipython/issues/670>`_: check for writable dirs, not just existence, in utils.path
* `579 <https://github.com/ipython/ipython/issues/579>`_: Sessionwork
* `687 <https://github.com/ipython/ipython/issues/687>`_: add `ipython kernel` for starting just a kernel
* `627 <https://github.com/ipython/ipython/issues/627>`_: Qt Console history search
* `646 <https://github.com/ipython/ipython/issues/646>`_: Generate package list automatically in find_packages
* `660 <https://github.com/ipython/ipython/issues/660>`_: i658
* `659 <https://github.com/ipython/ipython/issues/659>`_: don't crash on bad config files

Regular issues (258):

* `1177 <https://github.com/ipython/ipython/issues/1177>`_: UnicodeDecodeError in py3compat from "xlrd??"
* `1094 <https://github.com/ipython/ipython/issues/1094>`_: Tooltip doesn't show constructor docstrings
* `1170 <https://github.com/ipython/ipython/issues/1170>`_: double pylab greeting with c.InteractiveShellApp.pylab = "tk" in zmqconsole
* `1166 <https://github.com/ipython/ipython/issues/1166>`_: E-mail cpaste broken
* `1164 <https://github.com/ipython/ipython/issues/1164>`_: IPython qtconsole (0.12) can't export to html with external png
* `1103 <https://github.com/ipython/ipython/issues/1103>`_: %loadpy should cut out encoding declaration
* `1156 <https://github.com/ipython/ipython/issues/1156>`_: Notebooks downloaded as Python files require a header stating the encoding
* `1157 <https://github.com/ipython/ipython/issues/1157>`_: Ctrl-C not working when GUI/pylab integration is active
* `1154 <https://github.com/ipython/ipython/issues/1154>`_: We should be less aggressive in de-registering post-execution functions
* `1134 <https://github.com/ipython/ipython/issues/1134>`_: "select-all, kill" leaves qtconsole in unusable state
* `1148 <https://github.com/ipython/ipython/issues/1148>`_: A lot of testerrors
* `803 <https://github.com/ipython/ipython/issues/803>`_: Make doctests work with Python 3
* `1119 <https://github.com/ipython/ipython/issues/1119>`_: Start menu shortcuts not created in Python 3
* `1136 <https://github.com/ipython/ipython/issues/1136>`_: The embedding machinery ignores user_ns
* `607 <https://github.com/ipython/ipython/issues/607>`_: Use the new IPython logo/font in the notebook header
* `755 <https://github.com/ipython/ipython/issues/755>`_: qtconsole ipython widget's execute_file fails if filename contains spaces or quotes
* `1115 <https://github.com/ipython/ipython/issues/1115>`_: shlex_split should return unicode
* `1109 <https://github.com/ipython/ipython/issues/1109>`_: timeit with string ending in space gives "ValueError: No closing quotation"
* `1142 <https://github.com/ipython/ipython/issues/1142>`_: Install problems
* `700 <https://github.com/ipython/ipython/issues/700>`_: Some SVG images render incorrectly in htmlnotebook
* `1117 <https://github.com/ipython/ipython/issues/1117>`_: quit() doesn't work in terminal
* `1111 <https://github.com/ipython/ipython/issues/1111>`_: ls broken after merge of #1089
* `1104 <https://github.com/ipython/ipython/issues/1104>`_: Prompt spacing weird
* `1124 <https://github.com/ipython/ipython/issues/1124>`_: Seg Fault 11 when calling PySide using "run" command
* `1088 <https://github.com/ipython/ipython/issues/1088>`_: QtConsole : can't copy from pager
* `568 <https://github.com/ipython/ipython/issues/568>`_: Test error and failure in IPython.core on windows
* `1112 <https://github.com/ipython/ipython/issues/1112>`_: testfailure in IPython.frontend on windows
* `1102 <https://github.com/ipython/ipython/issues/1102>`_: magic in IPythonDemo fails when not located at top of demo file
* `629 <https://github.com/ipython/ipython/issues/629>`_: \r and \b in qtconsole don't behave as expected
* `1080 <https://github.com/ipython/ipython/issues/1080>`_: Notebook: tab completion should close on "("
* `973 <https://github.com/ipython/ipython/issues/973>`_: Qt Console close dialog and on-top Qt Console
* `1087 <https://github.com/ipython/ipython/issues/1087>`_: QtConsole xhtml/Svg export broken ?
* `1067 <https://github.com/ipython/ipython/issues/1067>`_: Parallel test suite hangs on Python 3
* `1018 <https://github.com/ipython/ipython/issues/1018>`_: Local mathjax breaks install
* `993 <https://github.com/ipython/ipython/issues/993>`_: `raw_input` redirection to foreign kernels is extremely brittle
* `1100 <https://github.com/ipython/ipython/issues/1100>`_: ipython3 traceback unicode issue from extensions
* `1071 <https://github.com/ipython/ipython/issues/1071>`_: Large html-notebooks hang on load on a slow machine
* `89 <https://github.com/ipython/ipython/issues/89>`_: %pdoc np.ma.compress shows docstring twice
* `22 <https://github.com/ipython/ipython/issues/22>`_: Include improvements from anythingipython.el
* `633 <https://github.com/ipython/ipython/issues/633>`_: Execution count & SyntaxError
* `1095 <https://github.com/ipython/ipython/issues/1095>`_: Uncaught TypeError: Object has no method 'remove_and_cancell_tooltip'
* `1075 <https://github.com/ipython/ipython/issues/1075>`_: We're ignoring prompt customizations
* `1086 <https://github.com/ipython/ipython/issues/1086>`_: Can't open qtconsole from outside source tree
* `1076 <https://github.com/ipython/ipython/issues/1076>`_: namespace changes broke `foo.*bar*?` syntax
* `1074 <https://github.com/ipython/ipython/issues/1074>`_: pprinting old-style class objects fails (TypeError: 'tuple' object is not callable)
* `1063 <https://github.com/ipython/ipython/issues/1063>`_: IPython.utils test error due to missing unicodedata module
* `592 <https://github.com/ipython/ipython/issues/592>`_: Bug in argument parsing for %run
* `378 <https://github.com/ipython/ipython/issues/378>`_: Windows path escape issues
* `1068 <https://github.com/ipython/ipython/issues/1068>`_: Notebook tab completion broken in Firefox
* `75 <https://github.com/ipython/ipython/issues/75>`_: No tab completion after "/
* `103 <https://github.com/ipython/ipython/issues/103>`_: customizable cpaste
* `324 <https://github.com/ipython/ipython/issues/324>`_: Remove code in IPython.testing that is not being used
* `131 <https://github.com/ipython/ipython/issues/131>`_: Global variables not seen by cprofile.run()
* `851 <https://github.com/ipython/ipython/issues/851>`_: IPython shell swallows exceptions in certain circumstances
* `882 <https://github.com/ipython/ipython/issues/882>`_: ipython freezes at start if IPYTHONDIR is on an NFS mount
* `1057 <https://github.com/ipython/ipython/issues/1057>`_: Blocker: Qt console broken after "all magics" menu became dynamic
* `1027 <https://github.com/ipython/ipython/issues/1027>`_: ipython does not like white space at end of file
* `1058 <https://github.com/ipython/ipython/issues/1058>`_: New bug: Notebook asks for confirmation to leave even saved pages.
* `1061 <https://github.com/ipython/ipython/issues/1061>`_: rep (magic recall) under pypy
* `1047 <https://github.com/ipython/ipython/issues/1047>`_: Document the notebook format
* `102 <https://github.com/ipython/ipython/issues/102>`_: Properties accessed twice for classes defined interactively
* `16 <https://github.com/ipython/ipython/issues/16>`_: %store raises exception when storing compiled regex
* `67 <https://github.com/ipython/ipython/issues/67>`_: tab expansion should only take one directory level at the time
* `62 <https://github.com/ipython/ipython/issues/62>`_: Global variables undefined in interactive use of embedded ipython shell
* `57 <https://github.com/ipython/ipython/issues/57>`_: debugging with ipython does not work well outside ipython
* `38 <https://github.com/ipython/ipython/issues/38>`_: Line entry edge case error
* `980 <https://github.com/ipython/ipython/issues/980>`_: Update parallel docs for new parallel architecture
* `1017 <https://github.com/ipython/ipython/issues/1017>`_: Add small example about ipcluster/ssh startup
* `1041 <https://github.com/ipython/ipython/issues/1041>`_: Proxy Issues
* `967 <https://github.com/ipython/ipython/issues/967>`_: KernelManagers don't use zmq eventloop properly
* `1055 <https://github.com/ipython/ipython/issues/1055>`_: "All Magics" display on Ubuntu 
* `1054 <https://github.com/ipython/ipython/issues/1054>`_: ipython explodes on syntax error
* `1051 <https://github.com/ipython/ipython/issues/1051>`_: ipython3 set_next_input() failure
* `693 <https://github.com/ipython/ipython/issues/693>`_: "run -i" no longer works after %reset in terminal
* `29 <https://github.com/ipython/ipython/issues/29>`_: cPickle works in standard interpreter, but not in IPython
* `1050 <https://github.com/ipython/ipython/issues/1050>`_: ipython3 broken by commit 8bb887c8c2c447bf7
* `1048 <https://github.com/ipython/ipython/issues/1048>`_: Update docs on notebook password
* `1046 <https://github.com/ipython/ipython/issues/1046>`_: Searies of questions/issues?
* `1045 <https://github.com/ipython/ipython/issues/1045>`_: crash when exiting - previously launched embedded sub-shell
* `1043 <https://github.com/ipython/ipython/issues/1043>`_: pylab doesn't work in qtconsole
* `1044 <https://github.com/ipython/ipython/issues/1044>`_: run -p doesn't work in python 3
* `1010 <https://github.com/ipython/ipython/issues/1010>`_: emacs freezes when ipython-complete is called
* `82 <https://github.com/ipython/ipython/issues/82>`_: Update devel docs with discussion about good changelogs
* `116 <https://github.com/ipython/ipython/issues/116>`_: Update release management scipts and release.revision for git
* `1022 <https://github.com/ipython/ipython/issues/1022>`_: Pylab banner shows up with first cell to execute
* `787 <https://github.com/ipython/ipython/issues/787>`_: Keyboard selection of multiple lines in the notebook behaves inconsistently
* `1037 <https://github.com/ipython/ipython/issues/1037>`_: notepad + jsonlib: TypeError: Only whitespace may be used for indentation.
* `970 <https://github.com/ipython/ipython/issues/970>`_: Default home not writable, %HOME% does not help (windows)
* `747 <https://github.com/ipython/ipython/issues/747>`_: HOMESHARE not a good choice for "writable homedir" on Windows
* `810 <https://github.com/ipython/ipython/issues/810>`_: cleanup utils.path.get_home_dir
* `2 <https://github.com/ipython/ipython/issues/2>`_: Fix the copyright statement in source code files to be accurate
* `1031 <https://github.com/ipython/ipython/issues/1031>`_: <esc> on Firefox crash websocket
* `684 <https://github.com/ipython/ipython/issues/684>`_: %Store eliminated in configuration and magic commands in 0.11
* `1026 <https://github.com/ipython/ipython/issues/1026>`_: BUG: wrong default parameter in ask_yes_no
* `880 <https://github.com/ipython/ipython/issues/880>`_: Better error message if %paste fails
* `1024 <https://github.com/ipython/ipython/issues/1024>`_: autopx magic broken 
* `822 <https://github.com/ipython/ipython/issues/822>`_: Unicode bug in Itpl when expanding shell variables in syscalls with !
* `1009 <https://github.com/ipython/ipython/issues/1009>`_: Windows: regression in cd magic handling of paths
* `833 <https://github.com/ipython/ipython/issues/833>`_: Crash python with matplotlib and unequal length arrays
* `695 <https://github.com/ipython/ipython/issues/695>`_: Crash handler initialization is too aggressive
* `1000 <https://github.com/ipython/ipython/issues/1000>`_: Remove duplicates when refilling readline history
* `992 <https://github.com/ipython/ipython/issues/992>`_: Interrupting certain matplotlib operations leaves the inline backend 'wedged'
* `942 <https://github.com/ipython/ipython/issues/942>`_: number traits should cast if value doesn't change
* `1006 <https://github.com/ipython/ipython/issues/1006>`_: ls crashes when run on a UNC path or with non-ascii args
* `944 <https://github.com/ipython/ipython/issues/944>`_: Decide the default image format for inline figures: SVG or PNG?
* `842 <https://github.com/ipython/ipython/issues/842>`_: Python 3 on Windows (pyreadline) - expected an object with the buffer interface
* `1002 <https://github.com/ipython/ipython/issues/1002>`_: ImportError due to incorrect version checking
* `1001 <https://github.com/ipython/ipython/issues/1001>`_: Ipython "source" command?
* `954 <https://github.com/ipython/ipython/issues/954>`_: IPython embed doesn't respect namespaces
* `681 <https://github.com/ipython/ipython/issues/681>`_: pdb freezes inside qtconsole
* `698 <https://github.com/ipython/ipython/issues/698>`_: crash report "TypeError: can only concatenate list (not "unicode") to list"
* `978 <https://github.com/ipython/ipython/issues/978>`_: ipython 0.11 buffers external command output till the cmd is done
* `952 <https://github.com/ipython/ipython/issues/952>`_: Need user-facing warning in the browser if websocket connection fails
* `988 <https://github.com/ipython/ipython/issues/988>`_: Error using idlsave
* `990 <https://github.com/ipython/ipython/issues/990>`_: ipython notebook - kernel dies if matplotlib is not installed
* `752 <https://github.com/ipython/ipython/issues/752>`_: Matplotlib figures showed only once in notebook
* `54 <https://github.com/ipython/ipython/issues/54>`_: Exception hook should be optional for embedding IPython in GUIs
* `918 <https://github.com/ipython/ipython/issues/918>`_: IPython.frontend tests fail without tornado
* `986 <https://github.com/ipython/ipython/issues/986>`_: Views created with c.direct_view() fail
* `697 <https://github.com/ipython/ipython/issues/697>`_: Filter out from %who names loaded at initialization time
* `932 <https://github.com/ipython/ipython/issues/932>`_: IPython 0.11 quickref card has superfluous "%recall and"
* `982 <https://github.com/ipython/ipython/issues/982>`_: png files with executable permissions
* `914 <https://github.com/ipython/ipython/issues/914>`_: Simpler system for running code after InteractiveShell is initialised
* `911 <https://github.com/ipython/ipython/issues/911>`_: ipython crashes on startup if readline is missing
* `971 <https://github.com/ipython/ipython/issues/971>`_: bookmarks created in 0.11 are corrupt in 0.12
* `974 <https://github.com/ipython/ipython/issues/974>`_: object feature tab-completion crash
* `939 <https://github.com/ipython/ipython/issues/939>`_: ZMQShell always uses default profile
* `946 <https://github.com/ipython/ipython/issues/946>`_: Multi-tab Close action should offer option to leave all kernels alone
* `949 <https://github.com/ipython/ipython/issues/949>`_: Test suite must not require any manual interaction
* `643 <https://github.com/ipython/ipython/issues/643>`_: enable gui eventloop integration in ipkernel
* `965 <https://github.com/ipython/ipython/issues/965>`_: ipython is crashed without launch.(python3.2)
* `958 <https://github.com/ipython/ipython/issues/958>`_: Can't use os X clipboard on with qtconsole
* `962 <https://github.com/ipython/ipython/issues/962>`_: Don't require tornado in the tests
* `960 <https://github.com/ipython/ipython/issues/960>`_: crash on syntax error on Windows XP
* `934 <https://github.com/ipython/ipython/issues/934>`_: The latest ipython branch doesn't work in Chrome
* `870 <https://github.com/ipython/ipython/issues/870>`_: zmq version detection
* `943 <https://github.com/ipython/ipython/issues/943>`_: HISTIGNORE for IPython
* `947 <https://github.com/ipython/ipython/issues/947>`_: qtconsole segfaults at startup
* `903 <https://github.com/ipython/ipython/issues/903>`_: Expose a magic to control config of the inline pylab backend
* `908 <https://github.com/ipython/ipython/issues/908>`_: bad user config shouldn't crash IPython
* `935 <https://github.com/ipython/ipython/issues/935>`_: Typing `break` causes IPython to crash.
* `869 <https://github.com/ipython/ipython/issues/869>`_: Tab completion of `~/` shows no output post 0.10.x
* `904 <https://github.com/ipython/ipython/issues/904>`_: whos under pypy1.6
* `773 <https://github.com/ipython/ipython/issues/773>`_: check_security_dir() and check_pid_dir() fail on network filesystem
* `915 <https://github.com/ipython/ipython/issues/915>`_: OS X Lion Terminal.app line wrap problem
* `886 <https://github.com/ipython/ipython/issues/886>`_: Notebook kernel crash when specifying --notebook-dir on commandline
* `636 <https://github.com/ipython/ipython/issues/636>`_: debugger.py: pydb broken
* `808 <https://github.com/ipython/ipython/issues/808>`_: Ctrl+C during %reset confirm message crash Qtconsole
* `927 <https://github.com/ipython/ipython/issues/927>`_: Using return outside a function crashes ipython
* `919 <https://github.com/ipython/ipython/issues/919>`_: Pop-up segfault when moving cursor out of qtconsole window
* `181 <https://github.com/ipython/ipython/issues/181>`_: cls command does not work on windows
* `917 <https://github.com/ipython/ipython/issues/917>`_: documentation typos
* `818 <https://github.com/ipython/ipython/issues/818>`_: %run does not work with non-ascii characeters in path
* `907 <https://github.com/ipython/ipython/issues/907>`_: Errors in custom completer functions can crash IPython
* `867 <https://github.com/ipython/ipython/issues/867>`_: doc: notebook password authentication howto
* `211 <https://github.com/ipython/ipython/issues/211>`_: paste command not working
* `900 <https://github.com/ipython/ipython/issues/900>`_: Tab key should insert 4 spaces in qt console
* `513 <https://github.com/ipython/ipython/issues/513>`_: [Qt console] cannot insert new lines into console functions using tab
* `906 <https://github.com/ipython/ipython/issues/906>`_: qtconsoleapp 'parse_command_line' doen't like --existing anymore
* `638 <https://github.com/ipython/ipython/issues/638>`_: Qt console --pylab=inline and getfigs(), etc.
* `710 <https://github.com/ipython/ipython/issues/710>`_: unwanted unicode passed to args
* `436 <https://github.com/ipython/ipython/issues/436>`_: Users should see tooltips for all buttons in the notebook UI
* `207 <https://github.com/ipython/ipython/issues/207>`_: ipython crashes if atexit handler raises exception
* `692 <https://github.com/ipython/ipython/issues/692>`_: use of Tracer() when debugging works but gives error messages
* `690 <https://github.com/ipython/ipython/issues/690>`_: debugger does not print error message by default in 0.11
* `571 <https://github.com/ipython/ipython/issues/571>`_: history of multiline entries
* `749 <https://github.com/ipython/ipython/issues/749>`_: IPython.parallel test failure under Windows 7 and XP
* `890 <https://github.com/ipython/ipython/issues/890>`_: ipclusterapp.py - helep
* `885 <https://github.com/ipython/ipython/issues/885>`_: `ws-hostname` alias not recognized by notebook
* `881 <https://github.com/ipython/ipython/issues/881>`_: Missing manual.pdf?
* `744 <https://github.com/ipython/ipython/issues/744>`_: cannot create notebook in offline mode if mathjax not installed
* `865 <https://github.com/ipython/ipython/issues/865>`_: Make tracebacks from %paste show the code
* `535 <https://github.com/ipython/ipython/issues/535>`_: exception unicode handling in %run is faulty in qtconsole
* `817 <https://github.com/ipython/ipython/issues/817>`_: iPython crashed
* `799 <https://github.com/ipython/ipython/issues/799>`_: %edit magic not working on windows xp in qtconsole
* `732 <https://github.com/ipython/ipython/issues/732>`_: QTConsole wrongly promotes the index of the input line on which user presses Enter
* `662 <https://github.com/ipython/ipython/issues/662>`_: ipython test failures on Mac OS X Lion
* `650 <https://github.com/ipython/ipython/issues/650>`_: Handle bad config files better
* `829 <https://github.com/ipython/ipython/issues/829>`_: We should not insert new lines after all print statements in the notebook
* `874 <https://github.com/ipython/ipython/issues/874>`_: ipython-qtconsole: pyzmq Version Comparison
* `640 <https://github.com/ipython/ipython/issues/640>`_: matplotlib macosx windows don't respond in qtconsole
* `624 <https://github.com/ipython/ipython/issues/624>`_: ipython intermittently segfaults when figure is closed (Mac OS X)
* `871 <https://github.com/ipython/ipython/issues/871>`_: Notebook crashes if a profile is used
* `56 <https://github.com/ipython/ipython/issues/56>`_: Have %cpaste accept also Ctrl-D as a termination marker
* `849 <https://github.com/ipython/ipython/issues/849>`_: Command line options to not override profile options
* `806 <https://github.com/ipython/ipython/issues/806>`_: Provide single-port connection to kernels
* `691 <https://github.com/ipython/ipython/issues/691>`_: [wishlist] Automatically find existing kernel
* `688 <https://github.com/ipython/ipython/issues/688>`_: local security vulnerability: all ports visible to any local user.
* `866 <https://github.com/ipython/ipython/issues/866>`_: DistributionNotFound on running ipython 0.11 on Windows XP x86
* `673 <https://github.com/ipython/ipython/issues/673>`_: raw_input appears to be round-robin for qtconsole
* `863 <https://github.com/ipython/ipython/issues/863>`_: Graceful degradation when home directory not writable
* `800 <https://github.com/ipython/ipython/issues/800>`_: Timing scripts with run -t -N <N> fails on report output
* `858 <https://github.com/ipython/ipython/issues/858>`_: Typing 'continue' makes ipython0.11 crash
* `840 <https://github.com/ipython/ipython/issues/840>`_: all processes run on one CPU core
* `843 <https://github.com/ipython/ipython/issues/843>`_: "import braces" crashes ipython
* `836 <https://github.com/ipython/ipython/issues/836>`_: Strange Output after IPython Install
* `839 <https://github.com/ipython/ipython/issues/839>`_: Qtconsole segfaults when mouse exits window with active tooltip
* `827 <https://github.com/ipython/ipython/issues/827>`_: Add support for checking several limits before running task on engine
* `826 <https://github.com/ipython/ipython/issues/826>`_: Add support for creation of parallel task when no engine is running
* `832 <https://github.com/ipython/ipython/issues/832>`_: Improve error message for %logstop
* `831 <https://github.com/ipython/ipython/issues/831>`_: %logstart in read-only directory forbid any further command
* `814 <https://github.com/ipython/ipython/issues/814>`_: ipython does not start -- DistributionNotFound
* `794 <https://github.com/ipython/ipython/issues/794>`_: Allow >1 controller per profile
* `820 <https://github.com/ipython/ipython/issues/820>`_: Tab Completion feature
* `812 <https://github.com/ipython/ipython/issues/812>`_: Qt console crashes on Ubuntu 11.10
* `816 <https://github.com/ipython/ipython/issues/816>`_: Import error using Python 2.7 and dateutil2.0 No module named _thread
* `756 <https://github.com/ipython/ipython/issues/756>`_: qtconsole Windows fails to print error message for '%run nonexistent_file'
* `651 <https://github.com/ipython/ipython/issues/651>`_: Completion doesn't work on element of a list
* `617 <https://github.com/ipython/ipython/issues/617>`_: [qtconsole] %hist doesn't show anything in qtconsole
* `786 <https://github.com/ipython/ipython/issues/786>`_: from __future__ import unicode_literals does not work
* `779 <https://github.com/ipython/ipython/issues/779>`_: Using irunner from virtual evn uses systemwide ipython
* `768 <https://github.com/ipython/ipython/issues/768>`_: codepage handling of output from scripts and shellcommands are not handled properly by qtconsole
* `785 <https://github.com/ipython/ipython/issues/785>`_: Don't strip leading whitespace in repr() in notebook
* `737 <https://github.com/ipython/ipython/issues/737>`_: in pickleshare.py line52 should be "if not os.path.isdir(self.root):"?
* `738 <https://github.com/ipython/ipython/issues/738>`_: in ipthon_win_post_install.py line 38
* `777 <https://github.com/ipython/ipython/issues/777>`_: print(…, sep=…) raises SyntaxError
* `728 <https://github.com/ipython/ipython/issues/728>`_: ipcontroller crash with MPI
* `780 <https://github.com/ipython/ipython/issues/780>`_: qtconsole Out value prints before the print statements that precede it
* `632 <https://github.com/ipython/ipython/issues/632>`_: IPython Crash Report (0.10.2)
* `253 <https://github.com/ipython/ipython/issues/253>`_: Unable to install ipython on windows
* `80 <https://github.com/ipython/ipython/issues/80>`_: Split IPClusterApp into multiple Application subclasses for each subcommand
* `34 <https://github.com/ipython/ipython/issues/34>`_: non-blocking pendingResult partial results
* `739 <https://github.com/ipython/ipython/issues/739>`_: Tests fail if tornado not installed
* `719 <https://github.com/ipython/ipython/issues/719>`_: Better support Pypy
* `667 <https://github.com/ipython/ipython/issues/667>`_: qtconsole problem with default pylab profile
* `661 <https://github.com/ipython/ipython/issues/661>`_: ipythonrc referenced in magic command in 0.11
* `665 <https://github.com/ipython/ipython/issues/665>`_: Source introspection with ?? is broken
* `724 <https://github.com/ipython/ipython/issues/724>`_: crash - ipython qtconsole, %quickref
* `655 <https://github.com/ipython/ipython/issues/655>`_: ipython with qtconsole crashes
* `593 <https://github.com/ipython/ipython/issues/593>`_: HTML Notebook Prompt can be deleted . . .
* `563 <https://github.com/ipython/ipython/issues/563>`_: use argparse instead of kvloader for flags&aliases
* `751 <https://github.com/ipython/ipython/issues/751>`_: Tornado version greater than 2.0 needed for firefox 6
* `720 <https://github.com/ipython/ipython/issues/720>`_: Crash report when importing easter egg
* `740 <https://github.com/ipython/ipython/issues/740>`_: Ctrl-Enter clears line in notebook
* `772 <https://github.com/ipython/ipython/issues/772>`_: ipengine fails on Windows with "XXX lineno: 355, opcode: 0"
* `771 <https://github.com/ipython/ipython/issues/771>`_: Add python 3 tag to setup.py
* `767 <https://github.com/ipython/ipython/issues/767>`_: non-ascii in __doc__ string crashes qtconsole kernel when showing tooltip
* `733 <https://github.com/ipython/ipython/issues/733>`_: In Windows, %run fails to strip quotes from filename
* `721 <https://github.com/ipython/ipython/issues/721>`_: no completion in emacs by ipython(ipython.el)
* `669 <https://github.com/ipython/ipython/issues/669>`_: Do not accept an ipython_dir that's not writeable
* `711 <https://github.com/ipython/ipython/issues/711>`_: segfault on mac os x
* `500 <https://github.com/ipython/ipython/issues/500>`_: "RuntimeError: Cannot change input buffer during execution" in console_widget.py
* `707 <https://github.com/ipython/ipython/issues/707>`_: Copy and paste keyboard shortcuts do not work in Qt Console on OS X
* `478 <https://github.com/ipython/ipython/issues/478>`_: PyZMQ's use of memoryviews breaks reconstruction of numpy arrays
* `694 <https://github.com/ipython/ipython/issues/694>`_: Turning off callout tips in qtconsole
* `704 <https://github.com/ipython/ipython/issues/704>`_: return kills IPython
* `442 <https://github.com/ipython/ipython/issues/442>`_: Users should have intelligent autoindenting in the notebook
* `615 <https://github.com/ipython/ipython/issues/615>`_: Wireframe and implement a project dashboard page
* `614 <https://github.com/ipython/ipython/issues/614>`_: Wireframe and implement a notebook dashboard page
* `606 <https://github.com/ipython/ipython/issues/606>`_: Users should be able to use the notebook to import/export a notebook to .py or .rst
* `604 <https://github.com/ipython/ipython/issues/604>`_: A user should be able to leave a kernel running in the notebook and reconnect
* `298 <https://github.com/ipython/ipython/issues/298>`_: Users should be able to save a notebook and then later reload it
* `649 <https://github.com/ipython/ipython/issues/649>`_: ipython qtconsole (v0.11): setting "c.IPythonWidget.in_prompt = '>>> ' crashes
* `672 <https://github.com/ipython/ipython/issues/672>`_: What happened to Exit?
* `658 <https://github.com/ipython/ipython/issues/658>`_: Put the InteractiveShellApp section first in the auto-generated config files
* `656 <https://github.com/ipython/ipython/issues/656>`_: [suggestion] dependency checking for pyqt for  Windows installer
* `654 <https://github.com/ipython/ipython/issues/654>`_: broken documentation link on download page
* `653 <https://github.com/ipython/ipython/issues/653>`_: Test failures in IPython.parallel

# Get the config being loaded so we can set attributes on it
c = get_config()

#-----------------------------------------------------------------------------
# Global options
#-----------------------------------------------------------------------------

# c.Global.display_banner = True

# c.Global.classic = False

# c.Global.nosep = True

# Set this to determine the detail of what is logged at startup.
# The default is 30 and possible values are 0,10,20,30,40,50.
# c.Global.log_level = 20

# This should be a list of importable Python modules that have an
# load_ipython_extension(ip) method.  This method gets called when the extension
# is loaded.  You can put your extensions anywhere they can be imported
# but we add the extensions subdir of the ipython directory to sys.path
# during extension loading, so you can put them there as well.
# c.Global.extensions = [
#     'myextension'
# ]

# These lines are run in IPython in the user's namespace after extensions 
# are loaded.  They can contain full IPython syntax with magics etc.
# c.Global.exec_lines = [
#     'import numpy',
#     'a = 10; b = 20',
#     '1/0'
# ]

# These files are run in IPython in the user's namespace.  Files with a .py
# extension need to be pure Python.  Files with a .ipy extension can have
# custom IPython syntax (like magics, etc.).  
# These files need to be in the cwd, the ipython_dir or be absolute paths.
# c.Global.exec_files = [
#     'mycode.py',
#     'fancy.ipy'
# ]

#-----------------------------------------------------------------------------
# InteractiveShell options
#-----------------------------------------------------------------------------

# c.InteractiveShell.autocall = 1

# c.TerminalInteractiveShell.autoedit_syntax = False

# c.InteractiveShell.autoindent = True

# c.InteractiveShell.automagic = False

# c.TerminalTerminalInteractiveShell.banner1 = 'This if for overriding the default IPython banner'
 
# c.TerminalTerminalInteractiveShell.banner2 = "This is for extra banner text"

# c.InteractiveShell.cache_size = 1000

# c.InteractiveShell.colors = 'LightBG'

# c.InteractiveShell.color_info = True

# c.TerminalInteractiveShell.confirm_exit = True

# c.InteractiveShell.deep_reload = False

# c.TerminalInteractiveShell.editor = 'nano'

# c.InteractiveShell.logstart = True

# c.InteractiveShell.logfile = u'ipython_log.py'

# c.InteractiveShell.logappend = u'mylog.py'

# c.InteractiveShell.object_info_string_level = 0

# c.TerminalInteractiveShell.pager = 'less'

# c.InteractiveShell.pdb = False

# c.InteractiveShell.prompt_in1 = 'In [\#]: '
# c.InteractiveShell.prompt_in2 = '   .\D.: '
# c.InteractiveShell.prompt_out = 'Out[\#]: '
# c.InteractiveShell.prompts_pad_left = True

# c.InteractiveShell.quiet = False

# c.InteractiveShell.history_length = 10000

# Readline 
# c.InteractiveShell.readline_use = True

# c.InteractiveShell.readline_parse_and_bind = [
#     'tab: complete',
#     '"\C-l": possible-completions',
#     'set show-all-if-ambiguous on',
#     '"\C-o": tab-insert',
#     '"\M-i": "    "',
#     '"\M-o": "\d\d\d\d"',
#     '"\M-I": "\d\d\d\d"',
#     '"\C-r": reverse-search-history',
#     '"\C-s": forward-search-history',
#     '"\C-p": history-search-backward',
#     '"\C-n": history-search-forward',
#     '"\e[A": history-search-backward',
#     '"\e[B": history-search-forward',
#     '"\C-k": kill-line',
#     '"\C-u": unix-line-discard',
# ]
# c.InteractiveShell.readline_remove_delims = '-/~'
# c.InteractiveShell.readline_merge_completions = True
# c.InteractiveShell.readline_omit__names = 0

# c.TerminalInteractiveShell.screen_length = 0

# c.InteractiveShell.separate_in = '\n'
# c.InteractiveShell.separate_out = ''
# c.InteractiveShell.separate_out2 = ''

# c.TerminalInteractiveShell.term_title = False

# c.InteractiveShell.wildcards_case_sensitive = True

# c.InteractiveShell.xmode = 'Context'

#-----------------------------------------------------------------------------
# Formatter and display options
#-----------------------------------------------------------------------------

# c.PlainTextFormatter.pprint = True

#-----------------------------------------------------------------------------
# PrefilterManager options
#-----------------------------------------------------------------------------

# c.PrefilterManager.multi_line_specials = True

#-----------------------------------------------------------------------------
# AliasManager options
#-----------------------------------------------------------------------------

# Do this to disable all defaults
# c.AliasManager.default_aliases = []

# c.AliasManager.user_aliases = [
#     ('foo', 'echo Hi')
# ]

#-----------------------------------------------------------------------------
# HistoryManager options
#-----------------------------------------------------------------------------

# Enable logging output as well as input to the database.
# c.HistoryManager.db_log_output = False

# Only write to the database every n commands - this can save disk
# access (and hence power) over the default of writing on every command.
# c.HistoryManager.db_cache_size = 0

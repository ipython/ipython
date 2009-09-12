#-----------------------------------------------------------------------------
# Global options
#-----------------------------------------------------------------------------

Global.classic = False
Global.nosep = False

#-----------------------------------------------------------------------------
# InteractiveShell options
#-----------------------------------------------------------------------------


InteractiveShell.autocall = 1

InteractiveShell.autoedit_syntax = False

InteractiveShell.autoindent = True

InteractiveShell.automagic = False

InteractiveShell.banner1 = 'This if for overriding the default IPython banner'
 
InteractiveShell.banner2 = "This is for extra banner text"

InteractiveShell.cache_size = 1000

InteractiveShell.colors = 'LightBG'

InteractiveShell.color_info = True

InteractiveShell.confirm_exit = True

InteractiveShell.deep_reload = False

InteractiveShell.display_banner = True

InteractiveShell.editor = 'nano'

InteractiveShell.logstart = True

InteractiveShell.logfile = 'ipython_log.py'

InteractiveShell.logplay = 'mylog.py'

InteractiveShell.object_info_string_level = 0

InteractiveShell.pager = 'less'

InteractiveShell.pdb = False

InteractiveShell.pprint = True

InteractiveShell.prompt_in1 = 'In [\#]: '
InteractiveShell.prompt_in2 = '   .\D.: '
InteractiveShell.prompt_out = 'Out[\#]: '
InteractiveShell.prompts_pad_left = True

InteractiveShell.quiet = False

# Readline 
InteractiveShell.readline_use = False

InteractiveShell.readline_parse_and_bind = [
    'tab: complete',
    '"\C-l": possible-completions',
    'set show-all-if-ambiguous on',
    '"\C-o": tab-insert',
    '"\M-i": "    "',
    '"\M-o": "\d\d\d\d"',
    '"\M-I": "\d\d\d\d"',
    '"\C-r": reverse-search-history',
    '"\C-s": forward-search-history',
    '"\C-p": history-search-backward',
    '"\C-n": history-search-forward',
    '"\e[A": history-search-backward',
    '"\e[B": history-search-forward',
    '"\C-k": kill-line',
    '"\C-u": unix-line-discard',
]
InteractiveShell.readline_remove_delims = '-/~'
InteractiveShell.readline_merge_completions = True
InteractiveShell.readline_omit_names = 0

InteractiveShell.screen_length = 0

InteractiveShell.separate_in = '\n'
InteractiveShell.separate_out = ''
InteractiveShell.separate_out2 = ''

InteractiveShell.system_header = "IPython system call: "

InteractiveShell.system_verbose = True

InteractiveShell.term_title = False

InteractiveShell.wildcards_case_sensitive = True

InteractiveShell.xmode = 'Context'

#-----------------------------------------------------------------------------
# PrefilterManager options
#-----------------------------------------------------------------------------

PrefilterManager.multi_line_specials = True

#-----------------------------------------------------------------------------
# AliasManager options
#-----------------------------------------------------------------------------

# Do this to enable all defaults
# AliasManager.default_aliases = []

AliasManger.user_aliases = [
    ('foo', 'echo Hi')
]
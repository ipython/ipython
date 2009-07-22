#-----------------------------------------------------------------------------
# IPython Shell Configuration Defaults
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Startup
#-----------------------------------------------------------------------------

AUTOCALL = True

AUTOEDIT_SYNTAX = False

AUTOINDENT = True

AUTOMAGIC = True

CACHE_SIZE = 1000

CLASSIC = False

COLORS = 'Linux'

COLOR_INFO = True

CONFIRM_EXIT = True

DEEP_RELOAD = False

EDITOR = 0

LOG = True

LOGFILE = ''

BANNER = True

MESSAGES = True

PDB = False

PPRINT = True

PROMPT_IN1 = 'In [\#]: '

PROMPT_IN2 = '   .\D.: '

PROMPT_OUT = 'Out[\#]: '

PROMPTS_PAD_LEFT = True

QUICK = False

SCREEN_LENGTH = 0

SEPARATE_IN = '\n'
SEPARATE_OUT = ''
SEPARATE_OUT2 = ''
NOSEP = False

WILDCARDS_CASE_SENSITIVE = True

OBJECT_INFO_STRING_LEVEL = 0

XMODE = 'Context'

MULTI_LINE_SPECIALS = True

SYSTEM_HEADER = "IPython system call: "

SYSTEM_VERBOSE = True

#-----------------------------------------------------------------------------
# Readline
#-----------------------------------------------------------------------------

READLINE = True

READLINE_PARSE_AND_BIND = [
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

READLINE_REMOVE_DELIMS = '-/~'

READLINE_MERGE_COMPLETIONS = True

READLINE_OMIT_NAMES = 0

#-----------------------------------------------------------------------------
# Code to execute
#-----------------------------------------------------------------------------

EXECUTE = [
    'import numpy as np',
    'import sympy',
    'a = 10'
]

EXECFILE = []

#-----------------------------------------------------------------------------
# Alias
#-----------------------------------------------------------------------------

ALIAS = [
    ('myls', 'ls -la')
]
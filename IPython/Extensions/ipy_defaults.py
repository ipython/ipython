""" Set default options for IPython. 

Just import this module to get reasonable defaults for everything.

These configurations used to be performed in ipythonrc (or ipythonrc.ini). 
Therefore importing this in your config files makes ipython basically
ignore your ipythonrc. This is *not* imported by default, you need to import 
this manually in one of your config files.

You can further override these defaults in e.g. your ipy_user_config.py,
ipy_profile_PROFILENAME etc.

"""

import IPython.rlineimpl as readline
import IPython.ipapi
ip = IPython.ipapi.get()

o = ip.options

o.colors = "Linux"
o.color_info=1
o.confirm_exit=1
o.pprint=1
o.multi_line_specials=1
o.xmode="Context"


o.prompt_in1='In [\#]: '
o.prompt_in2 ='   .\D.: '
o.prompt_out = 'Out[\#]: '
o.prompts_pad_left=1

o.autoindent = 1

o.readline_remove_delims="-/~"
o.readline_merge_completions=1

o.readline = 1

rlopts = """\
tab: complete
"\C-l": possible-completions
set show-all-if-ambiguous on
"\C-o": tab-insert
"\M-i": "    "
"\M-o": "\d\d\d\d"
"\M-I": "\d\d\d\d"
"\C-r": reverse-search-history
"\C-s": forward-search-history
"\C-p": history-search-backward
"\C-n": history-search-forward
"\e[A": history-search-backward
"\e[B": history-search-forward
"\C-k": kill-line
"\C-u": unix-line-discard"""

if readline.have_readline:
    for cmd in rlopts.split('\n'):
        readline.parse_and_bind(cmd)
    
    

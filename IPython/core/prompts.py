# -*- coding: utf-8 -*-
"""Classes for handling input/output prompts.

Authors:

* Fernando Perez
* Brian Granger
* Thomas Kluyver
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2011 The IPython Development Team
#       Copyright (C) 2001-2007 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import socket
import sys
import time

from string import Formatter

from IPython.config.configurable import Configurable
from IPython.core import release
from IPython.utils import coloransi
from IPython.utils.traitlets import (Unicode, Instance, Dict, Bool, Int)

#-----------------------------------------------------------------------------
# Color schemes for prompts
#-----------------------------------------------------------------------------

InputColors = coloransi.InputTermColors  # just a shorthand
Colors = coloransi.TermColors  # just a shorthand

color_lists = dict(normal=Colors(), inp=InputColors(), nocolor=coloransi.NoColors())

PColNoColors = coloransi.ColorScheme(
    'NoColor',
    in_prompt  = InputColors.NoColor,  # Input prompt
    in_number  = InputColors.NoColor,  # Input prompt number
    in_prompt2 = InputColors.NoColor, # Continuation prompt
    in_normal  = InputColors.NoColor,  # color off (usu. Colors.Normal)

    out_prompt = Colors.NoColor, # Output prompt
    out_number = Colors.NoColor, # Output prompt number

    normal = Colors.NoColor  # color off (usu. Colors.Normal)
    )

# make some schemes as instances so we can copy them for modification easily:
PColLinux =  coloransi.ColorScheme(
    'Linux',
    in_prompt  = InputColors.Green,
    in_number  = InputColors.LightGreen,
    in_prompt2 = InputColors.Green,
    in_normal  = InputColors.Normal,  # color off (usu. Colors.Normal)

    out_prompt = Colors.Red,
    out_number = Colors.LightRed,

    normal = Colors.Normal
    )

# Slightly modified Linux for light backgrounds
PColLightBG  = PColLinux.copy('LightBG')

PColLightBG.colors.update(
    in_prompt  = InputColors.Blue,
    in_number  = InputColors.LightBlue,
    in_prompt2 = InputColors.Blue
)

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

class LazyEvaluate(object):
    """This is used for formatting strings with values that need to be updated
    at that time, such as the current time or working directory."""
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def __call__(self, **kwargs):
        self.kwargs.update(kwargs)
        return self.func(*self.args, **self.kwargs)
    
    def __str__(self):
        return str(self())

def multiple_replace(dict, text):
    """ Replace in 'text' all occurences of any key in the given
    dictionary by its corresponding value.  Returns the new string."""

    # Function by Xavier Defrang, originally found at:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/81330

    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))
    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)

#-----------------------------------------------------------------------------
# Special characters that can be used in prompt templates, mainly bash-like
#-----------------------------------------------------------------------------

# If $HOME isn't defined (Windows), make it an absurd string so that it can
# never be expanded out into '~'.  Basically anything which can never be a
# reasonable directory name will do, we just want the $HOME -> '~' operation
# to become a no-op.  We pre-compute $HOME here so it's not done on every
# prompt call.

# FIXME:

# - This should be turned into a class which does proper namespace management,
# since the prompt specials need to be evaluated in a certain namespace.
# Currently it's just globals, which need to be managed manually by code
# below.

# - I also need to split up the color schemes from the prompt specials
# somehow.  I don't have a clean design for that quite yet.

HOME = os.environ.get("HOME","//////:::::ZZZZZ,,,~~~")

# We precompute a few more strings here for the prompt_specials, which are
# fixed once ipython starts.  This reduces the runtime overhead of computing
# prompt strings.
USER           = os.environ.get("USER")
HOSTNAME       = socket.gethostname()
HOSTNAME_SHORT = HOSTNAME.split(".")[0]
ROOT_SYMBOL    = "#" if (os.name=='nt' or os.getuid()==0) else "$"

prompt_abbreviations = {
    # Prompt/history count
    '%n' : '{color.number}' '{count}' '{color.prompt}',
    r'\#': '{color.number}' '{count}' '{color.prompt}',
    # Just the prompt counter number, WITHOUT any coloring wrappers, so users
    # can get numbers displayed in whatever color they want.
    r'\N': '{count}',

    # Prompt/history count, with the actual digits replaced by dots.  Used
    # mainly in continuation prompts (prompt_in2)
    r'\D': '{dots}',

    # Current time
    r'\T' : '{time}',
    # Current working directory
    r'\w': '{cwd}',
    # Basename of current working directory.
    # (use os.sep to make this portable across OSes)
    r'\W' : '{cwd_last}',
    # These X<N> are an extension to the normal bash prompts.  They return
    # N terms of the path, after replacing $HOME with '~'
    r'\X0': '{cwd_x[0]}',
    r'\X1': '{cwd_x[1]}',
    r'\X2': '{cwd_x[2]}',
    r'\X3': '{cwd_x[3]}',
    r'\X4': '{cwd_x[4]}',
    r'\X5': '{cwd_x[5]}',
    # Y<N> are similar to X<N>, but they show '~' if it's the directory
    # N+1 in the list.  Somewhat like %cN in tcsh.
    r'\Y0': '{cwd_y[0]}',
    r'\Y1': '{cwd_y[1]}',
    r'\Y2': '{cwd_y[2]}',
    r'\Y3': '{cwd_y[3]}',
    r'\Y4': '{cwd_y[4]}',
    r'\Y5': '{cwd_y[5]}',
    # Hostname up to first .
    r'\h': HOSTNAME_SHORT,
    # Full hostname
    r'\H': HOSTNAME,
    # Username of current user
    r'\u': USER,
    # Escaped '\'
    '\\\\': '\\',
    # Newline
    r'\n': '\n',
    # Carriage return
    r'\r': '\r',
    # Release version
    r'\v': release.version,
    # Root symbol ($ or #)
    r'\$': ROOT_SYMBOL,
    }

#-----------------------------------------------------------------------------
# More utilities
#-----------------------------------------------------------------------------

def cwd_filt(depth):
    """Return the last depth elements of the current working directory.

    $HOME is always replaced with '~'.
    If depth==0, the full path is returned."""

    cwd = os.getcwd().replace(HOME,"~")
    out = os.sep.join(cwd.split(os.sep)[-depth:])
    return out or os.sep

def cwd_filt2(depth):
    """Return the last depth elements of the current working directory.

    $HOME is always replaced with '~'.
    If depth==0, the full path is returned."""

    full_cwd = os.getcwd()
    cwd = full_cwd.replace(HOME,"~").split(os.sep)
    if '~' in cwd and len(cwd) == depth+1:
        depth += 1
    drivepart = ''
    if sys.platform == 'win32' and len(cwd) > depth:
        drivepart = os.path.splitdrive(full_cwd)[0]
    out = drivepart + '/'.join(cwd[-depth:])

    return out or os.sep

#-----------------------------------------------------------------------------
# Prompt classes
#-----------------------------------------------------------------------------

lazily_evaluate = {'time': LazyEvaluate(time.strftime, "%H:%M:%S"),
                   'cwd': LazyEvaluate(os.getcwd),
                   'cwd_last': LazyEvaluate(lambda: os.getcwd().split(os.sep)[-1]),
                   'cwd_x': [LazyEvaluate(lambda: os.getcwd().replace("%s","~"))] +\
                            [LazyEvaluate(cwd_filt, x) for x in range(1,6)],
                   'cwd_y': [LazyEvaluate(cwd_filt2, x) for x in range(6)]
                   }

def _lenlastline(s):
    """Get the length of the last line. More intelligent than
    len(s.splitlines()[-1]).
    """
    if not s or s.endswith(('\n', '\r')):
        return 0
    return len(s.splitlines()[-1])


class UserNSFormatter(Formatter):
    """A Formatter that falls back on a shell's user_ns and __builtins__ for name resolution"""
    def __init__(self, shell):
        self.shell = shell

    def get_value(self, key, args, kwargs):
        # try regular formatting first:
        try:
            return Formatter.get_value(self, key, args, kwargs)
        except Exception:
            pass
        # next, look in user_ns and builtins:
        for container in (self.shell.user_ns, __builtins__):
            if key in container:
                return container[key]
        # nothing found, put error message in its place
        return "<ERROR: '%s' not found>" % key


class PromptManager(Configurable):
    """This is the primary interface for producing IPython's prompts."""
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    
    color_scheme_table = Instance(coloransi.ColorSchemeTable)
    color_scheme = Unicode('Linux', config=True)
    def _color_scheme_changed(self, name, new_value):
        self.color_scheme_table.set_active_scheme(new_value)
        for pname in ['in', 'in2', 'out', 'rewrite']:
            # We need to recalculate the number of invisible characters
            self.update_prompt(pname)
    
    lazy_evaluate_fields = Dict(help="""
        This maps field names used in the prompt templates to functions which
        will be called when the prompt is rendered. This allows us to include
        things like the current time in the prompts. Functions are only called
        if they are used in the prompt.
        """)
    def _lazy_evaluate_fields_default(self): return lazily_evaluate.copy()
    
    in_template = Unicode('In [\\#]: ', config=True,
        help="Input prompt.  '\\#' will be transformed to the prompt number")
    in2_template = Unicode('   .\\D.: ', config=True,
        help="Continuation prompt.")
    out_template = Unicode('Out[\\#]: ', config=True,
        help="Output prompt. '\\#' will be transformed to the prompt number")
    
    justify = Bool(True, config=True, help="""
        If True (default), each prompt will be right-aligned with the
        preceding one.
        """)
    
    # We actually store the expanded templates here:
    templates = Dict()
    
    # The number of characters in the last prompt rendered, not including
    # colour characters.
    width = Int()
    txtwidth = Int()   # Not including right-justification
    
    # The number of characters in each prompt which don't contribute to width
    invisible_chars = Dict()
    def _invisible_chars_default(self):
        return {'in': 0, 'in2': 0, 'out': 0, 'rewrite':0}
    
    def __init__(self, shell, config=None):
        super(PromptManager, self).__init__(shell=shell, config=config)
        
        # Prepare colour scheme table
        self.color_scheme_table = coloransi.ColorSchemeTable([PColNoColors,
                                    PColLinux, PColLightBG], self.color_scheme)
        
        self._formatter = UserNSFormatter(shell)
        # Prepare templates & numbers of invisible characters
        self.update_prompt('in', self.in_template)
        self.update_prompt('in2', self.in2_template)
        self.update_prompt('out', self.out_template)
        self.update_prompt('rewrite')
        self.on_trait_change(self._update_prompt_trait, ['in_template',
                            'in2_template', 'out_template'])
    
    def update_prompt(self, name, new_template=None):
        """This is called when a prompt template is updated. It processes
        abbreviations used in the prompt template (like \#) and calculates how
        many invisible characters (ANSI colour escapes) the resulting prompt
        contains.
        
        It is also called for each prompt on changing the colour scheme. In both
        cases, traitlets should take care of calling this automatically.
        """
        if new_template is not None:
            self.templates[name] = multiple_replace(prompt_abbreviations, new_template)
        # We count invisible characters (colour escapes) on the last line of the
        # prompt, to calculate the width for lining up subsequent prompts.
        invis_chars = _lenlastline(self._render(name, color=True)) - \
                        _lenlastline(self._render(name, color=False))
        self.invisible_chars[name] = invis_chars
    
    def _update_prompt_trait(self, traitname, new_template):
        name = traitname[:-9]   # Cut off '_template'
        self.update_prompt(name, new_template)
    
    def _render(self, name, color=True, **kwargs):
        """Render but don't justify, or update the width or txtwidth attributes.
        """
        if name == 'rewrite':
            return self._render_rewrite(color=color)
        
        if color:
            scheme = self.color_scheme_table.active_colors
            if name=='out':
                colors = color_lists['normal']
                colors.number, colors.prompt, colors.normal = \
                        scheme.out_number, scheme.out_prompt, scheme.normal
            else:
                colors = color_lists['inp']
                colors.number, colors.prompt, colors.normal = \
                        scheme.in_number, scheme.in_prompt, scheme.in_normal
                if name=='in2':
                    colors.prompt = scheme.in_prompt2
        else:
            # No color
            colors = color_lists['nocolor']
            colors.number, colors.prompt, colors.normal = '', '', ''
        
        count = self.shell.execution_count    # Shorthand
        # Build the dictionary to be passed to string formatting
        fmtargs = dict(color=colors, count=count,
                        dots="."*len(str(count)),
                        width=self.width, txtwidth=self.txtwidth )
        fmtargs.update(self.lazy_evaluate_fields)
        fmtargs.update(kwargs)
        
        # Prepare the prompt
        prompt = colors.prompt + self.templates[name] + colors.normal
        
        # Fill in required fields
        return self._formatter.format(prompt, **fmtargs)
    
    def _render_rewrite(self, color=True):
        """Render the ---> rewrite prompt."""
        if color:
            scheme = self.color_scheme_table.active_colors
            # We need a non-input version of these escapes
            color_prompt = scheme.in_prompt.replace("\001","").replace("\002","")
            color_normal = scheme.normal
        else:
            color_prompt, color_normal = '', ''

        return color_prompt + "-> ".rjust(self.txtwidth, "-") + color_normal
    
    def render(self, name, color=True, just=None, **kwargs):
        """
        Render the selected prompt.
        
        Parameters
        ----------
        name : str
          Which prompt to render. One of 'in', 'in2', 'out', 'rewrite'
        color : bool
          If True (default), include ANSI escape sequences for a coloured prompt.
        just : bool
          If True, justify the prompt to the width of the last prompt. The
          default is stored in self.justify.
        **kwargs :
          Additional arguments will be passed to the string formatting operation,
          so they can override the values that would otherwise fill in the
          template.
        
        Returns
        -------
        A string containing the rendered prompt.
        """
        res = self._render(name, color=color, **kwargs)
        
        # Handle justification of prompt
        invis_chars = self.invisible_chars[name] if color else 0
        self.txtwidth = _lenlastline(res) - invis_chars
        just = self.justify if (just is None) else just
        # If the prompt spans more than one line, don't try to justify it:
        if just and ('\n' not in res) and ('\r' not in res):
            res = res.rjust(self.width + invis_chars)
        self.width = _lenlastline(res) - invis_chars
        return res

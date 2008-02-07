# -*- coding: utf-8 -*-
"""
Classes for handling input/output prompts.

$Id: Prompts.py 3026 2008-02-07 16:03:16Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license
__version__ = Release.version

#****************************************************************************
# Required modules
import __builtin__
import os
import socket
import sys
import time

# IPython's own
from IPython import ColorANSI
from IPython.Itpl import ItplNS
from IPython.ipstruct import Struct
from IPython.macro import Macro
from IPython.genutils import *
from IPython.ipapi import TryNext

#****************************************************************************
#Color schemes for Prompts.

PromptColors = ColorANSI.ColorSchemeTable()
InputColors = ColorANSI.InputTermColors  # just a shorthand
Colors = ColorANSI.TermColors  # just a shorthand

PromptColors.add_scheme(ColorANSI.ColorScheme(
    'NoColor',
    in_prompt  = InputColors.NoColor,  # Input prompt
    in_number  = InputColors.NoColor,  # Input prompt number
    in_prompt2 = InputColors.NoColor, # Continuation prompt
    in_normal  = InputColors.NoColor,  # color off (usu. Colors.Normal)
    
    out_prompt = Colors.NoColor, # Output prompt
    out_number = Colors.NoColor, # Output prompt number

    normal = Colors.NoColor  # color off (usu. Colors.Normal)
    ))

# make some schemes as instances so we can copy them for modification easily:
__PColLinux =  ColorANSI.ColorScheme(
    'Linux',
    in_prompt  = InputColors.Green,
    in_number  = InputColors.LightGreen,
    in_prompt2 = InputColors.Green,
    in_normal  = InputColors.Normal,  # color off (usu. Colors.Normal)

    out_prompt = Colors.Red,
    out_number = Colors.LightRed,

    normal = Colors.Normal
    )
# Don't forget to enter it into the table!
PromptColors.add_scheme(__PColLinux)

# Slightly modified Linux for light backgrounds
__PColLightBG  = __PColLinux.copy('LightBG')

__PColLightBG.colors.update(
    in_prompt  = InputColors.Blue,
    in_number  = InputColors.LightBlue,
    in_prompt2 = InputColors.Blue
)
PromptColors.add_scheme(__PColLightBG)

del Colors,InputColors

#-----------------------------------------------------------------------------
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
ROOT_SYMBOL    = "$#"[os.name=='nt' or os.getuid()==0]

prompt_specials_color = {
    # Prompt/history count
    '%n' : '${self.col_num}' '${self.cache.prompt_count}' '${self.col_p}',
    r'\#': '${self.col_num}' '${self.cache.prompt_count}' '${self.col_p}',
    # Just the prompt counter number, WITHOUT any coloring wrappers, so users
    # can get numbers displayed in whatever color they want.
    r'\N': '${self.cache.prompt_count}',
    # Prompt/history count, with the actual digits replaced by dots.  Used
    # mainly in continuation prompts (prompt_in2)
    r'\D': '${"."*len(str(self.cache.prompt_count))}',
    # Current working directory
    r'\w': '${os.getcwd()}',
    # Current time
    r'\t' : '${time.strftime("%H:%M:%S")}',
    # Basename of current working directory.
    # (use os.sep to make this portable across OSes)
    r'\W' : '${os.getcwd().split("%s")[-1]}' % os.sep,
    # These X<N> are an extension to the normal bash prompts.  They return
    # N terms of the path, after replacing $HOME with '~'
    r'\X0': '${os.getcwd().replace("%s","~")}' % HOME,
    r'\X1': '${self.cwd_filt(1)}',
    r'\X2': '${self.cwd_filt(2)}',
    r'\X3': '${self.cwd_filt(3)}',
    r'\X4': '${self.cwd_filt(4)}',
    r'\X5': '${self.cwd_filt(5)}',
    # Y<N> are similar to X<N>, but they show '~' if it's the directory
    # N+1 in the list.  Somewhat like %cN in tcsh.
    r'\Y0': '${self.cwd_filt2(0)}',
    r'\Y1': '${self.cwd_filt2(1)}',
    r'\Y2': '${self.cwd_filt2(2)}',
    r'\Y3': '${self.cwd_filt2(3)}',
    r'\Y4': '${self.cwd_filt2(4)}',
    r'\Y5': '${self.cwd_filt2(5)}',
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
    r'\v': __version__,
    # Root symbol ($ or #)
    r'\$': ROOT_SYMBOL,
    }

# A copy of the prompt_specials dictionary but with all color escapes removed,
# so we can correctly compute the prompt length for the auto_rewrite method.
prompt_specials_nocolor = prompt_specials_color.copy()
prompt_specials_nocolor['%n'] = '${self.cache.prompt_count}'
prompt_specials_nocolor[r'\#'] = '${self.cache.prompt_count}'

# Add in all the InputTermColors color escapes as valid prompt characters.
# They all get added as \\C_COLORNAME, so that we don't have any conflicts
# with a color name which may begin with a letter used by any other of the
# allowed specials.  This of course means that \\C will never be allowed for
# anything else.
input_colors = ColorANSI.InputTermColors
for _color in dir(input_colors):
    if _color[0] != '_':
        c_name = r'\C_'+_color
        prompt_specials_color[c_name] = getattr(input_colors,_color)
        prompt_specials_nocolor[c_name] = ''

# we default to no color for safety.  Note that prompt_specials is a global
# variable used by all prompt objects.
prompt_specials = prompt_specials_nocolor

#-----------------------------------------------------------------------------
def str_safe(arg):
    """Convert to a string, without ever raising an exception.

    If str(arg) fails, <ERROR: ... > is returned, where ... is the exception
    error message."""

    try:
        out = str(arg)
    except UnicodeError:
        try:
            out = arg.encode('utf_8','replace')
        except Exception,msg:
            # let's keep this little duplication here, so that the most common
            # case doesn't suffer from a double try wrapping.
            out = '<ERROR: %s>' % msg
    except Exception,msg:
        out = '<ERROR: %s>' % msg
    return out

class BasePrompt(object):
    """Interactive prompt similar to Mathematica's."""

    def _get_p_template(self):
        return self._p_template

    def _set_p_template(self,val):
        self._p_template = val
        self.set_p_str()

    p_template = property(_get_p_template,_set_p_template,
                          doc='Template for prompt string creation')

    def __init__(self,cache,sep,prompt,pad_left=False):

        # Hack: we access information about the primary prompt through the
        # cache argument.  We need this, because we want the secondary prompt
        # to be aligned with the primary one.  Color table info is also shared
        # by all prompt classes through the cache.  Nice OO spaghetti code!
        self.cache = cache
        self.sep = sep
        
        # regexp to count the number of spaces at the end of a prompt
        # expression, useful for prompt auto-rewriting
        self.rspace = re.compile(r'(\s*)$')
        # Flag to left-pad prompt strings to match the length of the primary
        # prompt
        self.pad_left = pad_left

        # Set template to create each actual prompt (where numbers change).
        # Use a property
        self.p_template = prompt
        self.set_p_str()

    def set_p_str(self):
        """ Set the interpolating prompt strings.

        This must be called every time the color settings change, because the
        prompt_specials global may have changed."""

        import os,time  # needed in locals for prompt string handling
        loc = locals()
        try:
            self.p_str = ItplNS('%s%s%s' %
                                ('${self.sep}${self.col_p}',
                                 multiple_replace(prompt_specials, self.p_template),
                                 '${self.col_norm}'),self.cache.user_ns,loc)
    
            self.p_str_nocolor = ItplNS(multiple_replace(prompt_specials_nocolor,
                                                         self.p_template),
                                        self.cache.user_ns,loc)
        except:
            print "Illegal prompt template (check $ usage!):",self.p_template
            self.p_str = self.p_template
            self.p_str_nocolor = self.p_template

    def write(self,msg):  # dbg
        sys.stdout.write(msg)
        return ''

    def __str__(self):
        """Return a string form of the prompt.

        This for is useful for continuation and output prompts, since it is
        left-padded to match lengths with the primary one (if the
        self.pad_left attribute is set)."""

        out_str = str_safe(self.p_str)
        if self.pad_left:
            # We must find the amount of padding required to match lengths,
            # taking the color escapes (which are invisible on-screen) into
            # account.
            esc_pad = len(out_str) - len(str_safe(self.p_str_nocolor))
            format = '%%%ss' % (len(str(self.cache.last_prompt))+esc_pad)
            return format % out_str
        else:
            return out_str

    # these path filters are put in as methods so that we can control the
    # namespace where the prompt strings get evaluated
    def cwd_filt(self,depth):
        """Return the last depth elements of the current working directory.

        $HOME is always replaced with '~'.
        If depth==0, the full path is returned."""

        cwd = os.getcwd().replace(HOME,"~")
        out = os.sep.join(cwd.split(os.sep)[-depth:])
        if out:
            return out
        else:
            return os.sep

    def cwd_filt2(self,depth):
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

        if out:
            return out
        else:
            return os.sep

    def __nonzero__(self):
        """Implement boolean behavior.

        Checks whether the p_str attribute is non-empty"""

        return bool(self.p_template)

class Prompt1(BasePrompt):
    """Input interactive prompt similar to Mathematica's."""

    def __init__(self,cache,sep='\n',prompt='In [\\#]: ',pad_left=True):
        BasePrompt.__init__(self,cache,sep,prompt,pad_left)

    def set_colors(self):
        self.set_p_str()
        Colors = self.cache.color_table.active_colors # shorthand
        self.col_p = Colors.in_prompt
        self.col_num = Colors.in_number
        self.col_norm = Colors.in_normal
        # We need a non-input version of these escapes for the '--->'
        # auto-call prompts used in the auto_rewrite() method.
        self.col_p_ni = self.col_p.replace('\001','').replace('\002','') 
        self.col_norm_ni = Colors.normal        
        
    def __str__(self):
        self.cache.prompt_count += 1
        self.cache.last_prompt = str_safe(self.p_str_nocolor).split('\n')[-1]
        return str_safe(self.p_str)

    def auto_rewrite(self):
        """Print a string of the form '--->' which lines up with the previous
        input string. Useful for systems which re-write the user input when
        handling automatically special syntaxes."""

        curr = str(self.cache.last_prompt)
        nrspaces = len(self.rspace.search(curr).group())
        return '%s%s>%s%s' % (self.col_p_ni,'-'*(len(curr)-nrspaces-1),
                              ' '*nrspaces,self.col_norm_ni)

class PromptOut(BasePrompt):
    """Output interactive prompt similar to Mathematica's."""

    def __init__(self,cache,sep='',prompt='Out[\\#]: ',pad_left=True):
        BasePrompt.__init__(self,cache,sep,prompt,pad_left)
        if not self.p_template:
            self.__str__ = lambda: ''

    def set_colors(self):
        self.set_p_str()
        Colors = self.cache.color_table.active_colors # shorthand
        self.col_p = Colors.out_prompt
        self.col_num = Colors.out_number
        self.col_norm = Colors.normal

class Prompt2(BasePrompt):
    """Interactive continuation prompt."""
    
    def __init__(self,cache,prompt='   .\\D.: ',pad_left=True):
        self.cache = cache
        self.p_template = prompt
        self.pad_left = pad_left
        self.set_p_str()

    def set_p_str(self):
        import os,time  # needed in locals for prompt string handling
        loc = locals()
        self.p_str = ItplNS('%s%s%s' %
                            ('${self.col_p2}',
                             multiple_replace(prompt_specials, self.p_template),
                             '$self.col_norm'),
                            self.cache.user_ns,loc)
        self.p_str_nocolor = ItplNS(multiple_replace(prompt_specials_nocolor,
                                                     self.p_template),
                                    self.cache.user_ns,loc)

    def set_colors(self):
        self.set_p_str()
        Colors = self.cache.color_table.active_colors
        self.col_p2 = Colors.in_prompt2
        self.col_norm = Colors.in_normal
        # FIXME (2004-06-16) HACK: prevent crashes for users who haven't
        # updated their prompt_in2 definitions.  Remove eventually.
        self.col_p = Colors.out_prompt
        self.col_num = Colors.out_number


#-----------------------------------------------------------------------------
class CachedOutput:
    """Class for printing output from calculations while keeping a cache of
    reults. It dynamically creates global variables prefixed with _ which
    contain these results.

    Meant to be used as a sys.displayhook replacement, providing numbered
    prompts and cache services.

    Initialize with initial and final values for cache counter (this defines
    the maximum size of the cache."""

    def __init__(self,shell,cache_size,Pprint,
                 colors='NoColor',input_sep='\n',
                 output_sep='\n',output_sep2='',
                 ps1 = None, ps2 = None,ps_out = None,pad_left=True):

        cache_size_min = 3
        if cache_size <= 0:
            self.do_full_cache = 0
            cache_size = 0
        elif cache_size < cache_size_min:
            self.do_full_cache = 0
            cache_size = 0
            warn('caching was disabled (min value for cache size is %s).' %
                 cache_size_min,level=3)
        else:
            self.do_full_cache = 1

        self.cache_size = cache_size
        self.input_sep = input_sep

        # we need a reference to the user-level namespace
        self.shell = shell
        self.user_ns = shell.user_ns
        # and to the user's input
        self.input_hist = shell.input_hist
        # and to the user's logger, for logging output
        self.logger = shell.logger

        # Set input prompt strings and colors
        if cache_size == 0:
            if ps1.find('%n') > -1 or ps1.find(r'\#') > -1 \
                   or ps1.find(r'\N') > -1:
                ps1 = '>>> '
            if ps2.find('%n') > -1 or ps2.find(r'\#') > -1 \
                   or ps2.find(r'\N') > -1:
                ps2 = '... '
        self.ps1_str = self._set_prompt_str(ps1,'In [\\#]: ','>>> ')
        self.ps2_str = self._set_prompt_str(ps2,'   .\\D.: ','... ')
        self.ps_out_str = self._set_prompt_str(ps_out,'Out[\\#]: ','')

        self.color_table = PromptColors
        self.prompt1 = Prompt1(self,sep=input_sep,prompt=self.ps1_str,
                               pad_left=pad_left)
        self.prompt2 = Prompt2(self,prompt=self.ps2_str,pad_left=pad_left)
        self.prompt_out = PromptOut(self,sep='',prompt=self.ps_out_str,
                                    pad_left=pad_left)
        self.set_colors(colors)

        # other more normal stuff
        # b/c each call to the In[] prompt raises it by 1, even the first.
        self.prompt_count = 0
        # Store the last prompt string each time, we need it for aligning
        # continuation and auto-rewrite prompts
        self.last_prompt = ''
        self.Pprint = Pprint
        self.output_sep = output_sep
        self.output_sep2 = output_sep2
        self._,self.__,self.___ = '','',''
        self.pprint_types = map(type,[(),[],{}])
        
        # these are deliberately global:
        to_user_ns = {'_':self._,'__':self.__,'___':self.___}
        self.user_ns.update(to_user_ns)

    def _set_prompt_str(self,p_str,cache_def,no_cache_def):
        if p_str is None:
            if self.do_full_cache:
                return cache_def
            else:
                return no_cache_def
        else:
            return p_str
                
    def set_colors(self,colors):
        """Set the active color scheme and configure colors for the three
        prompt subsystems."""

        # FIXME: the prompt_specials global should be gobbled inside this
        # class instead.  Do it when cleaning up the whole 3-prompt system.
        global prompt_specials
        if colors.lower()=='nocolor':
            prompt_specials = prompt_specials_nocolor
        else:
            prompt_specials = prompt_specials_color
        
        self.color_table.set_active_scheme(colors)
        self.prompt1.set_colors()
        self.prompt2.set_colors()
        self.prompt_out.set_colors()

    def __call__(self,arg=None):
        """Printing with history cache management.
        
        This is invoked everytime the interpreter needs to print, and is
        activated by setting the variable sys.displayhook to it."""

        # If something injected a '_' variable in __builtin__, delete
        # ipython's automatic one so we don't clobber that.  gettext() in
        # particular uses _, so we need to stay away from it.
        if '_' in __builtin__.__dict__:
            try:
                del self.user_ns['_']
            except KeyError:
                pass
        if arg is not None:
            cout_write = Term.cout.write # fast lookup
            # first handle the cache and counters

            # do not print output if input ends in ';'
            try:
                if self.input_hist[self.prompt_count].endswith(';\n'):
                    return
            except IndexError:
                # some uses of ipshellembed may fail here
                pass
            # don't use print, puts an extra space
            cout_write(self.output_sep)
            outprompt = self.shell.hooks.generate_output_prompt()
            if self.do_full_cache:
                cout_write(outprompt)

            # and now call a possibly user-defined print mechanism
            manipulated_val = self.display(arg)
            
            # user display hooks can change the variable to be stored in
            # output history
            
            if manipulated_val is not None:
                arg = manipulated_val
                
            # avoid recursive reference when displaying _oh/Out
            if arg is not self.user_ns['_oh']:
                self.update(arg)

            if self.logger.log_output:
                self.logger.log_write(repr(arg),'output')
            cout_write(self.output_sep2)
            Term.cout.flush()

    def _display(self,arg):
        """Default printer method, uses pprint.

        Do ip.set_hook("result_display", my_displayhook) for custom result
        display, e.g. when your own objects need special formatting.
        """
        try:
            return IPython.generics.result_display(arg)
        except TryNext:            
            return self.shell.hooks.result_display(arg)

    # Assign the default display method:
    display = _display

    def update(self,arg):
        #print '***cache_count', self.cache_count # dbg
        if len(self.user_ns['_oh']) >= self.cache_size and self.do_full_cache:
            warn('Output cache limit (currently '+
                  `self.cache_size`+' entries) hit.\n'
                 'Flushing cache and resetting history counter...\n'
                 'The only history variables available will be _,__,___ and _1\n'
                 'with the current result.')

            self.flush()
        # Don't overwrite '_' and friends if '_' is in __builtin__ (otherwise
        # we cause buggy behavior for things like gettext).
        if '_' not in __builtin__.__dict__:
            self.___ = self.__
            self.__ = self._
            self._ = arg
            self.user_ns.update({'_':self._,'__':self.__,'___':self.___})
            
        # hackish access to top-level  namespace to create _1,_2... dynamically
        to_main = {}
        if self.do_full_cache:
            new_result = '_'+`self.prompt_count`
            to_main[new_result] = arg
            self.user_ns.update(to_main)
            self.user_ns['_oh'][self.prompt_count] = arg

    def flush(self):
        if not self.do_full_cache:
            raise ValueError,"You shouldn't have reached the cache flush "\
                  "if full caching is not enabled!"
        # delete auto-generated vars from global namespace
        
        for n in range(1,self.prompt_count + 1):
            key = '_'+`n`
            try:
                del self.user_ns[key]
            except: pass
        self.user_ns['_oh'].clear()
        
        if '_' not in __builtin__.__dict__:
            self.user_ns.update({'_':None,'__':None, '___':None})
        import gc
        gc.collect() # xxx needed?


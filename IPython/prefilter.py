# -*- coding: utf-8 -*-
"""
Classes and functions for prefiltering (transforming) a line of user input.
This module is responsible, primarily, for breaking the line up into useful
pieces and triggering the appropriate handlers in iplib to do the actual
transforming work.
"""
__docformat__ = "restructuredtext en"

import re
import IPython.ipapi

class LineInfo(object):
    """A single line of input and associated info.

    Includes the following as properties: 

    line
      The original, raw line
    
    continue_prompt
      Is this line a continuation in a sequence of multiline input?
    
    pre
      The initial esc character or whitespace.
    
    preChar
      The escape character(s) in pre or the empty string if there isn't one.
      Note that '!!' is a possible value for preChar.  Otherwise it will
      always be a single character.
    
    preWhitespace
      The leading whitespace from pre if it exists.  If there is a preChar,
      this is just ''.
    
    iFun
      The 'function part', which is basically the maximal initial sequence
      of valid python identifiers and the '.' character.  This is what is
      checked for alias and magic transformations, used for auto-calling,
      etc.
    
    theRest
      Everything else on the line.
    """
    def __init__(self, line, continue_prompt):
        self.line            = line
        self.continue_prompt = continue_prompt
        self.pre, self.iFun, self.theRest = splitUserInput(line)

        self.preChar       = self.pre.strip()
        if self.preChar:
            self.preWhitespace = '' # No whitespace allowd before esc chars
        else: 
            self.preWhitespace = self.pre

        self._oinfo = None

    def ofind(self, ip):
        """Do a full, attribute-walking lookup of the iFun in the various
        namespaces for the given IPython InteractiveShell instance.

        Return a dict with keys: found,obj,ospace,ismagic

        Note: can cause state changes because of calling getattr, but should
        only be run if autocall is on and if the line hasn't matched any
        other, less dangerous handlers.

        Does cache the results of the call, so can be called multiple times
        without worrying about *further* damaging state.
        """
        if not self._oinfo:
            self._oinfo = ip._ofind(self.iFun)
        return self._oinfo
    def __str__(self):                                                         
        return "Lineinfo [%s|%s|%s]" %(self.pre,self.iFun,self.theRest)        

def splitUserInput(line, pattern=None):
    """Split user input into pre-char/whitespace, function part and rest.

    Mostly internal to this module, but also used by iplib.expand_aliases,
    which passes in a shell pattern.
    """
    # It seems to me that the shell splitting should be a separate method.
    
    if not pattern:
        pattern = line_split
    match = pattern.match(line)
    if not match:
        #print "match failed for line '%s'" % line
        try:
            iFun,theRest = line.split(None,1)
        except ValueError:
            #print "split failed for line '%s'" % line
            iFun,theRest = line,''
        pre = re.match('^(\s*)(.*)',line).groups()[0]
    else:
        pre,iFun,theRest = match.groups()

    # iFun has to be a valid python identifier, so it better be only pure
    # ascii, no unicode:
    try:
        iFun = iFun.encode('ascii')
    except UnicodeEncodeError:
        theRest = iFun + u' ' + theRest
        iFun = u''

    #print 'line:<%s>' % line # dbg
    #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun.strip(),theRest) # dbg
    return pre,iFun.strip(),theRest.lstrip()


# RegExp for splitting line contents into pre-char//first word-method//rest.
# For clarity, each group in on one line.

# WARNING: update the regexp if the escapes in iplib are changed, as they
# are hardwired in.

# Although it's not solely driven by the regex, note that:
# ,;/% only trigger if they are the first character on the line
# ! and !! trigger if they are first char(s) *or* follow an indent 
# ? triggers as first or last char.

# The three parts of the regex are:
#  1) pre:     pre_char *or* initial whitespace 
#  2) iFun:    first word/method (mix of \w and '.')
#  3) theRest: rest of line (separated from iFun by space if non-empty)
line_split = re.compile(r'^([,;/%?]|!!?|\s*)'
                        r'\s*([\w\.]+)'
                        r'(\s+.*$|$)')

shell_line_split = re.compile(r'^(\s*)(\S*\s*)(.*$)')

def prefilter(line_info, ip):
    """Call one of the passed-in InteractiveShell's handler preprocessors,
    depending on the form of the line.  Return the results, which must be a
    value, even if it's a blank ('')."""
    # Note: the order of these checks does matter. 
    for check in [ checkEmacs,
                   checkShellEscape,
                   checkIPyAutocall,
                   checkMultiLineMagic,
                   checkEscChars,
                   checkAssignment,
                   checkAutomagic,
                   checkAlias,
                   checkPythonOps,
                   checkAutocall,
                   ]:
        handler = check(line_info, ip)
        if handler:
            return handler(line_info)

    return ip.handle_normal(line_info)

# Handler checks
#
# All have the same interface: they take a LineInfo object and a ref to the
# iplib.InteractiveShell object.  They check the line to see if a particular
# handler should be called, and return either a handler or None.  The
# handlers which they return are *bound* methods of the InteractiveShell
# object. 
#
# In general, these checks should only take responsibility for their 'own'
# handler.  If it doesn't get triggered, they should just return None and
# let the rest of the check sequence run.

def checkShellEscape(l_info,ip):
    if l_info.line.lstrip().startswith(ip.ESC_SHELL):
        return ip.handle_shell_escape

def checkEmacs(l_info,ip):
    "Emacs ipython-mode tags certain input lines."
    if l_info.line.endswith('# PYTHON-MODE'):
        return ip.handle_emacs
    else:
        return None

def checkIPyAutocall(l_info,ip):
    "Instances of IPyAutocall in user_ns get autocalled immediately"
    obj = ip.user_ns.get(l_info.iFun, None)
    if isinstance(obj, IPython.ipapi.IPyAutocall):
        obj.set_ip(ip.api)
        return ip.handle_auto
    else:
        return None
    
    
def checkMultiLineMagic(l_info,ip):
    "Allow ! and !! in multi-line statements if multi_line_specials is on"
    # Note that this one of the only places we check the first character of
    # iFun and *not* the preChar.  Also note that the below test matches
    # both ! and !!.    
    if l_info.continue_prompt \
        and ip.rc.multi_line_specials:
            if l_info.iFun.startswith(ip.ESC_MAGIC):
                return ip.handle_magic
    else:
        return None

def checkEscChars(l_info,ip):
    """Check for escape character and return either a handler to handle it,
    or None if there is no escape char."""
    if l_info.line[-1] == ip.ESC_HELP \
           and l_info.preChar != ip.ESC_SHELL \
           and l_info.preChar != ip.ESC_SH_CAP:
        # the ? can be at the end, but *not* for either kind of shell escape,
        # because a ? can be a vaild final char in a shell cmd
        return ip.handle_help
    elif l_info.preChar in ip.esc_handlers:
        return ip.esc_handlers[l_info.preChar]
    else:
        return None


def checkAssignment(l_info,ip):
    """Check to see if user is assigning to a var for the first time, in
    which case we want to avoid any sort of automagic / autocall games.
    
    This allows users to assign to either alias or magic names true python
    variables (the magic/alias systems always take second seat to true
    python code).  E.g. ls='hi', or ls,that=1,2"""
    if l_info.theRest and l_info.theRest[0] in '=,':
        return ip.handle_normal
    else:
        return None


def checkAutomagic(l_info,ip):
    """If the iFun is magic, and automagic is on, run it.  Note: normal,
    non-auto magic would already have been triggered via '%' in
    check_esc_chars. This just checks for automagic.  Also, before
    triggering the magic handler, make sure that there is nothing in the
    user namespace which could shadow it."""
    if not ip.rc.automagic or not hasattr(ip,'magic_'+l_info.iFun):
        return None

    # We have a likely magic method.  Make sure we should actually call it.
    if l_info.continue_prompt and not ip.rc.multi_line_specials:
        return None

    head = l_info.iFun.split('.',1)[0]
    if isShadowed(head,ip):
        return None

    return ip.handle_magic

        
def checkAlias(l_info,ip):
    "Check if the initital identifier on the line is an alias."
    # Note: aliases can not contain '.'
    head = l_info.iFun.split('.',1)[0]
    
    if l_info.iFun not in ip.alias_table \
           or head not in ip.alias_table \
           or isShadowed(head,ip): 
        return None

    return ip.handle_alias


def checkPythonOps(l_info,ip):
    """If the 'rest' of the line begins with a function call or pretty much
    any python operator, we should simply execute the line (regardless of
    whether or not there's a possible autocall expansion).  This avoids
    spurious (and very confusing) geattr() accesses."""
    if l_info.theRest and l_info.theRest[0] in '!=()<>,+*/%^&|':
        return ip.handle_normal
    else:
        return None


def checkAutocall(l_info,ip):
    "Check if the initial word/function is callable and autocall is on."
    if not ip.rc.autocall:
        return None

    oinfo = l_info.ofind(ip) # This can mutate state via getattr
    if not oinfo['found']:
        return None
        
    if callable(oinfo['obj']) \
           and (not re_exclude_auto.match(l_info.theRest)) \
           and re_fun_name.match(l_info.iFun):
        #print 'going auto'  # dbg
        return ip.handle_auto
    else:
        #print 'was callable?', callable(l_info.oinfo['obj'])  # dbg
        return None
    
# RegExp to identify potential function names
re_fun_name = re.compile(r'[a-zA-Z_]([a-zA-Z0-9_.]*) *$')

# RegExp to exclude strings with this start from autocalling.  In
# particular, all binary operators should be excluded, so that if foo is
# callable, foo OP bar doesn't become foo(OP bar), which is invalid.  The
# characters '!=()' don't need to be checked for, as the checkPythonChars
# routine explicitely does so, to catch direct calls and rebindings of
# existing names.

# Warning: the '-' HAS TO BE AT THE END of the first group, otherwise
# it affects the rest of the group in square brackets.
re_exclude_auto = re.compile(r'^[,&^\|\*/\+-]'
                             r'|^is |^not |^in |^and |^or ')

# try to catch also methods for stuff in lists/tuples/dicts: off
# (experimental). For this to work, the line_split regexp would need
# to be modified so it wouldn't break things at '['. That line is
# nasty enough that I shouldn't change it until I can test it _well_.
#self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')

# Handler Check Utilities
def isShadowed(identifier,ip):
    """Is the given identifier defined in one of the namespaces which shadow
    the alias and magic namespaces?  Note that an identifier is different
    than iFun, because it can not contain a '.' character."""
    # This is much safer than calling ofind, which can change state
    return (identifier in ip.user_ns \
            or identifier in ip.internal_ns \
            or identifier in ip.ns_table['builtin'])


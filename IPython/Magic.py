# -*- coding: utf-8 -*-
"""Magic functions for InteractiveShell.

$Id: Magic.py 2996 2008-01-30 06:31:39Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

#****************************************************************************
# Modules and globals

from IPython import Release
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license

# Python standard modules
import __builtin__
import bdb
import inspect
import os
import pdb
import pydoc
import sys
import re
import tempfile
import time
import cPickle as pickle
import textwrap
from cStringIO import StringIO
from getopt import getopt,GetoptError
from pprint import pprint, pformat
from sets import Set

# cProfile was added in Python2.5
try:
    import cProfile as profile
    import pstats
except ImportError:
    # profile isn't bundled by default in Debian for license reasons
    try:
        import profile,pstats
    except ImportError:
        profile = pstats = None

# Homebrewed
import IPython
from IPython import Debugger, OInspect, wildcard
from IPython.FakeModule import FakeModule
from IPython.Itpl import Itpl, itpl, printpl,itplns
from IPython.PyColorize import Parser
from IPython.ipstruct import Struct
from IPython.macro import Macro
from IPython.genutils import *
from IPython import platutils
import IPython.generics
import IPython.ipapi
from IPython.ipapi import UsageError
from IPython.testing import decorators as testdec

#***************************************************************************
# Utility functions
def on_off(tag):
    """Return an ON/OFF string for a 1/0 input. Simple utility function."""
    return ['OFF','ON'][tag]

class Bunch: pass

def compress_dhist(dh):
    head, tail = dh[:-10], dh[-10:]

    newhead = []
    done = Set()
    for h in head:
        if h in done:
            continue
        newhead.append(h)
        done.add(h)

    return newhead + tail        
        

#***************************************************************************
# Main class implementing Magic functionality
class Magic:
    """Magic functions for InteractiveShell.

    Shell functions which can be reached as %function_name. All magic
    functions should accept a string, which they can parse for their own
    needs. This can make some functions easier to type, eg `%cd ../`
    vs. `%cd("../")`

    ALL definitions MUST begin with the prefix magic_. The user won't need it
    at the command line, but it is is needed in the definition. """

    # class globals
    auto_status = ['Automagic is OFF, % prefix IS needed for magic functions.',
                   'Automagic is ON, % prefix NOT needed for magic functions.']

    #......................................................................
    # some utility functions

    def __init__(self,shell):
        
        self.options_table = {}
        if profile is None:
            self.magic_prun = self.profile_missing_notice
        self.shell = shell

        # namespace for holding state we may need
        self._magic_state = Bunch()

    def profile_missing_notice(self, *args, **kwargs):
        error("""\
The profile module could not be found. It has been removed from the standard
python packages because of its non-free license. To use profiling, install the
python-profiler package from non-free.""")

    def default_option(self,fn,optstr):
        """Make an entry in the options_table for fn, with value optstr"""

        if fn not in self.lsmagic():
            error("%s is not a magic function" % fn)
        self.options_table[fn] = optstr

    def lsmagic(self):
        """Return a list of currently available magic functions.

        Gives a list of the bare names after mangling (['ls','cd', ...], not
        ['magic_ls','magic_cd',...]"""

        # FIXME. This needs a cleanup, in the way the magics list is built.
        
        # magics in class definition
        class_magic = lambda fn: fn.startswith('magic_') and \
                      callable(Magic.__dict__[fn])
        # in instance namespace (run-time user additions)
        inst_magic =  lambda fn: fn.startswith('magic_') and \
                     callable(self.__dict__[fn])
        # and bound magics by user (so they can access self):
        inst_bound_magic =  lambda fn: fn.startswith('magic_') and \
                           callable(self.__class__.__dict__[fn])
        magics = filter(class_magic,Magic.__dict__.keys()) + \
                 filter(inst_magic,self.__dict__.keys()) + \
                 filter(inst_bound_magic,self.__class__.__dict__.keys())
        out = []
        for fn in Set(magics):
            out.append(fn.replace('magic_','',1))
        out.sort()
        return out
    
    def extract_input_slices(self,slices,raw=False):
        """Return as a string a set of input history slices.

        Inputs:

          - slices: the set of slices is given as a list of strings (like
          ['1','4:8','9'], since this function is for use by magic functions
          which get their arguments as strings.

        Optional inputs:

          - raw(False): by default, the processed input is used.  If this is
          true, the raw input history is used instead.

        Note that slices can be called with two notations:

        N:M -> standard python form, means including items N...(M-1).

        N-M -> include items N..M (closed endpoint)."""

        if raw:
            hist = self.shell.input_hist_raw
        else:
            hist = self.shell.input_hist

        cmds = []
        for chunk in slices:
            if ':' in chunk:
                ini,fin = map(int,chunk.split(':'))
            elif '-' in chunk:
                ini,fin = map(int,chunk.split('-'))
                fin += 1
            else:
                ini = int(chunk)
                fin = ini+1
            cmds.append(hist[ini:fin])
        return cmds
        
    def _ofind(self, oname, namespaces=None):
        """Find an object in the available namespaces.

        self._ofind(oname) -> dict with keys: found,obj,ospace,ismagic

        Has special code to detect magic functions.
        """
        
        oname = oname.strip()

        alias_ns = None
        if namespaces is None:
            # Namespaces to search in:
            # Put them in a list. The order is important so that we
            # find things in the same order that Python finds them.
            namespaces = [ ('Interactive', self.shell.user_ns),
                           ('IPython internal', self.shell.internal_ns),
                           ('Python builtin', __builtin__.__dict__),
                           ('Alias', self.shell.alias_table),
                           ]
            alias_ns = self.shell.alias_table

        # initialize results to 'null'
        found = 0; obj = None;  ospace = None;  ds = None;
        ismagic = 0; isalias = 0; parent = None

        # Look for the given name by splitting it in parts.  If the head is
        # found, then we look for all the remaining parts as members, and only
        # declare success if we can find them all.
        oname_parts = oname.split('.')
        oname_head, oname_rest = oname_parts[0],oname_parts[1:]
        for nsname,ns in namespaces:
            try:
                obj = ns[oname_head]
            except KeyError:
                continue
            else:
                #print 'oname_rest:', oname_rest  # dbg
                for part in oname_rest:
                    try:
                        parent = obj
                        obj = getattr(obj,part)
                    except:
                        # Blanket except b/c some badly implemented objects
                        # allow __getattr__ to raise exceptions other than
                        # AttributeError, which then crashes IPython.
                        break
                else:
                    # If we finish the for loop (no break), we got all members
                    found = 1
                    ospace = nsname
                    if ns == alias_ns:
                        isalias = 1
                    break  # namespace loop

        # Try to see if it's magic
        if not found:
            if oname.startswith(self.shell.ESC_MAGIC):
                oname = oname[1:]
            obj = getattr(self,'magic_'+oname,None)
            if obj is not None:
                found = 1
                ospace = 'IPython internal'
                ismagic = 1

        # Last try: special-case some literals like '', [], {}, etc:
        if not found and oname_head in ["''",'""','[]','{}','()']:
            obj = eval(oname_head)
            found = 1
            ospace = 'Interactive'
            
        return {'found':found, 'obj':obj, 'namespace':ospace,
                'ismagic':ismagic, 'isalias':isalias, 'parent':parent}
    
    def arg_err(self,func):
        """Print docstring if incorrect arguments were passed"""
        print 'Error in arguments:'
        print OInspect.getdoc(func)

    def format_latex(self,strng):
        """Format a string for latex inclusion."""

        # Characters that need to be escaped for latex:
        escape_re = re.compile(r'(%|_|\$|#|&)',re.MULTILINE)
        # Magic command names as headers:
        cmd_name_re = re.compile(r'^(%s.*?):' % self.shell.ESC_MAGIC,
                                 re.MULTILINE)
        # Magic commands 
        cmd_re = re.compile(r'(?P<cmd>%s.+?\b)(?!\}\}:)' % self.shell.ESC_MAGIC,
                            re.MULTILINE)
        # Paragraph continue
        par_re = re.compile(r'\\$',re.MULTILINE)

        # The "\n" symbol
        newline_re = re.compile(r'\\n')

        # Now build the string for output:
        #strng = cmd_name_re.sub(r'\n\\texttt{\\textsl{\\large \1}}:',strng)
        strng = cmd_name_re.sub(r'\n\\bigskip\n\\texttt{\\textbf{ \1}}:',
                                strng)
        strng = cmd_re.sub(r'\\texttt{\g<cmd>}',strng)
        strng = par_re.sub(r'\\\\',strng)
        strng = escape_re.sub(r'\\\1',strng)
        strng = newline_re.sub(r'\\textbackslash{}n',strng)
        return strng

    def format_screen(self,strng):
        """Format a string for screen printing.

        This removes some latex-type format codes."""
        # Paragraph continue
        par_re = re.compile(r'\\$',re.MULTILINE)
        strng = par_re.sub('',strng)
        return strng

    def parse_options(self,arg_str,opt_str,*long_opts,**kw):
        """Parse options passed to an argument string.

        The interface is similar to that of getopt(), but it returns back a
        Struct with the options as keys and the stripped argument string still
        as a string.

        arg_str is quoted as a true sys.argv vector by using shlex.split.
        This allows us to easily expand variables, glob files, quote
        arguments, etc.

        Options:
          -mode: default 'string'. If given as 'list', the argument string is
          returned as a list (split on whitespace) instead of a string.

          -list_all: put all option values in lists. Normally only options
          appearing more than once are put in a list.

          -posix (True): whether to split the input line in POSIX mode or not,
          as per the conventions outlined in the shlex module from the
          standard library."""
 
        # inject default options at the beginning of the input line
        caller = sys._getframe(1).f_code.co_name.replace('magic_','')
        arg_str = '%s %s' % (self.options_table.get(caller,''),arg_str)
        
        mode = kw.get('mode','string')
        if mode not in ['string','list']:
            raise ValueError,'incorrect mode given: %s' % mode
        # Get options
        list_all = kw.get('list_all',0)
        posix = kw.get('posix',True)

        # Check if we have more than one argument to warrant extra processing:
        odict = {}  # Dictionary with options
        args = arg_str.split()
        if len(args) >= 1:
            # If the list of inputs only has 0 or 1 thing in it, there's no
            # need to look for options
            argv = arg_split(arg_str,posix)
            # Do regular option processing
            try:
                opts,args = getopt(argv,opt_str,*long_opts)
            except GetoptError,e:
                raise UsageError('%s ( allowed: "%s" %s)' % (e.msg,opt_str, 
                                        " ".join(long_opts)))
            for o,a in opts:
                if o.startswith('--'):
                    o = o[2:]
                else:
                    o = o[1:]
                try:
                    odict[o].append(a)
                except AttributeError:
                    odict[o] = [odict[o],a]
                except KeyError:
                    if list_all:
                        odict[o] = [a]
                    else:
                        odict[o] = a

        # Prepare opts,args for return
        opts = Struct(odict)
        if mode == 'string':
            args = ' '.join(args)

        return opts,args
    
    #......................................................................
    # And now the actual magic functions

    # Functions for IPython shell work (vars,funcs, config, etc)
    def magic_lsmagic(self, parameter_s = ''):
        """List currently available magic functions."""
        mesc = self.shell.ESC_MAGIC
        print 'Available magic functions:\n'+mesc+\
              ('  '+mesc).join(self.lsmagic())
        print '\n' + Magic.auto_status[self.shell.rc.automagic]
        return None
        
    def magic_magic(self, parameter_s = ''):
        """Print information about the magic function system.
        
        Supported formats: -latex, -brief, -rest        
        """

        mode = ''
        try:
            if parameter_s.split()[0] == '-latex':
                mode = 'latex'
            if parameter_s.split()[0] == '-brief':
                mode = 'brief'
            if parameter_s.split()[0] == '-rest':
                mode = 'rest'
                rest_docs = []
        except:
            pass

        magic_docs = []
        for fname in self.lsmagic():
            mname = 'magic_' + fname
            for space in (Magic,self,self.__class__):
                try:
                    fn = space.__dict__[mname]
                except KeyError:
                    pass
                else:
                    break
            if mode == 'brief':
                # only first line
                if fn.__doc__:                    
                    fndoc = fn.__doc__.split('\n',1)[0]
                else:
                    fndoc = 'No documentation'
            else:
                fndoc = fn.__doc__.rstrip()
                
            if mode == 'rest':
                rest_docs.append('**%s%s**::\n\n\t%s\n\n' %(self.shell.ESC_MAGIC,
                                                    fname,fndoc))
                
            else:
                magic_docs.append('%s%s:\n\t%s\n' %(self.shell.ESC_MAGIC,
                                                    fname,fndoc))
                
        magic_docs = ''.join(magic_docs)

        if mode == 'rest':
            return "".join(rest_docs)
        
        if mode == 'latex':
            print self.format_latex(magic_docs)
            return
        else:
            magic_docs = self.format_screen(magic_docs)
        if mode == 'brief':
            return magic_docs
        
        outmsg = """
IPython's 'magic' functions
===========================

The magic function system provides a series of functions which allow you to
control the behavior of IPython itself, plus a lot of system-type
features. All these functions are prefixed with a % character, but parameters
are given without parentheses or quotes.

NOTE: If you have 'automagic' enabled (via the command line option or with the
%automagic function), you don't need to type in the % explicitly.  By default,
IPython ships with automagic on, so you should only rarely need the % escape.

Example: typing '%cd mydir' (without the quotes) changes you working directory
to 'mydir', if it exists.

You can define your own magic functions to extend the system. See the supplied
ipythonrc and example-magic.py files for details (in your ipython
configuration directory, typically $HOME/.ipython/).

You can also define your own aliased names for magic functions. In your
ipythonrc file, placing a line like:

  execute __IPYTHON__.magic_pf = __IPYTHON__.magic_profile

will define %pf as a new name for %profile.

You can also call magics in code using the ipmagic() function, which IPython
automatically adds to the builtin namespace.  Type 'ipmagic?' for details.

For a list of the available magic functions, use %lsmagic. For a description
of any of them, type %magic_name?, e.g. '%cd?'.

Currently the magic system has the following functions:\n"""

        mesc = self.shell.ESC_MAGIC
        outmsg = ("%s\n%s\n\nSummary of magic functions (from %slsmagic):"
                  "\n\n%s%s\n\n%s" % (outmsg,
                                     magic_docs,mesc,mesc,
                                     ('  '+mesc).join(self.lsmagic()),
                                     Magic.auto_status[self.shell.rc.automagic] ) )

        page(outmsg,screen_lines=self.shell.rc.screen_length)
  

    def magic_autoindent(self, parameter_s = ''):
        """Toggle autoindent on/off (if available)."""

        self.shell.set_autoindent()
        print "Automatic indentation is:",['OFF','ON'][self.shell.autoindent]


    def magic_automagic(self, parameter_s = ''):
        """Make magic functions callable without having to type the initial %.

        Without argumentsl toggles on/off (when off, you must call it as
        %automagic, of course).  With arguments it sets the value, and you can
        use any of (case insensitive):

         - on,1,True: to activate

         - off,0,False: to deactivate.

        Note that magic functions have lowest priority, so if there's a
        variable whose name collides with that of a magic fn, automagic won't
        work for that function (you get the variable instead). However, if you
        delete the variable (del var), the previously shadowed magic function
        becomes visible to automagic again."""

        rc = self.shell.rc
        arg = parameter_s.lower()
        if parameter_s in ('on','1','true'):
            rc.automagic = True
        elif parameter_s in ('off','0','false'):
            rc.automagic = False
        else:
            rc.automagic = not rc.automagic
        print '\n' + Magic.auto_status[rc.automagic]

    @testdec.skip_doctest
    def magic_autocall(self, parameter_s = ''):
        """Make functions callable without having to type parentheses.

        Usage:

           %autocall [mode]

        The mode can be one of: 0->Off, 1->Smart, 2->Full.  If not given, the
        value is toggled on and off (remembering the previous state).

        In more detail, these values mean:

        0 -> fully disabled

        1 -> active, but do not apply if there are no arguments on the line.

        In this mode, you get:

        In [1]: callable
        Out[1]: <built-in function callable>

        In [2]: callable 'hello'
        ------> callable('hello')
        Out[2]: False

        2 -> Active always.  Even if no arguments are present, the callable
        object is called:

        In [2]: float
        ------> float()
        Out[2]: 0.0

        Note that even with autocall off, you can still use '/' at the start of
        a line to treat the first argument on the command line as a function
        and add parentheses to it:

        In [8]: /str 43
        ------> str(43)
        Out[8]: '43'

        # all-random (note for auto-testing)
        """

        rc = self.shell.rc

        if parameter_s:
            arg = int(parameter_s)
        else:
            arg = 'toggle'

        if not arg in (0,1,2,'toggle'):
            error('Valid modes: (0->Off, 1->Smart, 2->Full')
            return

        if arg in (0,1,2):
            rc.autocall = arg
        else: # toggle
            if rc.autocall:
                self._magic_state.autocall_save = rc.autocall
                rc.autocall = 0
            else:
                try:
                    rc.autocall = self._magic_state.autocall_save
                except AttributeError:
                    rc.autocall = self._magic_state.autocall_save = 1

        print "Automatic calling is:",['OFF','Smart','Full'][rc.autocall]

    def magic_system_verbose(self, parameter_s = ''):
        """Set verbose printing of system calls.

        If called without an argument, act as a toggle"""

        if parameter_s:
            val = bool(eval(parameter_s))
        else:
            val = None
            
        self.shell.rc_set_toggle('system_verbose',val)
        print "System verbose printing is:",\
              ['OFF','ON'][self.shell.rc.system_verbose]


    def magic_page(self, parameter_s=''):
        """Pretty print the object and display it through a pager.
        
        %page [options] OBJECT

        If no object is given, use _ (last output).
        
        Options:

          -r: page str(object), don't pretty-print it."""

        # After a function contributed by Olivier Aubert, slightly modified.

        # Process options/args
        opts,args = self.parse_options(parameter_s,'r')
        raw = 'r' in opts

        oname = args and args or '_'
        info = self._ofind(oname)
        if info['found']:
            txt = (raw and str or pformat)( info['obj'] )
            page(txt)
        else:
            print 'Object `%s` not found' % oname

    def magic_profile(self, parameter_s=''):
        """Print your currently active IPyhton profile."""
        if self.shell.rc.profile:
            printpl('Current IPython profile: $self.shell.rc.profile.')
        else:
            print 'No profile active.'

    def magic_pinfo(self, parameter_s='', namespaces=None):
        """Provide detailed information about an object.
    
        '%pinfo object' is just a synonym for object? or ?object."""
    
        #print 'pinfo par: <%s>' % parameter_s  # dbg
    
        
        # detail_level: 0 -> obj? , 1 -> obj??
        detail_level = 0
        # We need to detect if we got called as 'pinfo pinfo foo', which can
        # happen if the user types 'pinfo foo?' at the cmd line.
        pinfo,qmark1,oname,qmark2 = \
               re.match('(pinfo )?(\?*)(.*?)(\??$)',parameter_s).groups()
        if pinfo or qmark1 or qmark2:
            detail_level = 1
        if "*" in oname:
            self.magic_psearch(oname)
        else:
            self._inspect('pinfo', oname, detail_level=detail_level,
                          namespaces=namespaces)

    def magic_pdef(self, parameter_s='', namespaces=None):
        """Print the definition header for any callable object.

        If the object is a class, print the constructor information."""
        self._inspect('pdef',parameter_s, namespaces)

    def magic_pdoc(self, parameter_s='', namespaces=None):
        """Print the docstring for an object.

        If the given object is a class, it will print both the class and the
        constructor docstrings."""
        self._inspect('pdoc',parameter_s, namespaces)

    def magic_psource(self, parameter_s='', namespaces=None):
        """Print (or run through pager) the source code for an object."""
        self._inspect('psource',parameter_s, namespaces)

    def magic_pfile(self, parameter_s=''):
        """Print (or run through pager) the file where an object is defined.

        The file opens at the line where the object definition begins. IPython
        will honor the environment variable PAGER if set, and otherwise will
        do its best to print the file in a convenient form.

        If the given argument is not an object currently defined, IPython will
        try to interpret it as a filename (automatically adding a .py extension
        if needed). You can thus use %pfile as a syntax highlighting code
        viewer."""

        # first interpret argument as an object name
        out = self._inspect('pfile',parameter_s)
        # if not, try the input as a filename
        if out == 'not found':
            try:
                filename = get_py_filename(parameter_s)
            except IOError,msg:
                print msg
                return
            page(self.shell.inspector.format(file(filename).read()))

    def _inspect(self,meth,oname,namespaces=None,**kw):
        """Generic interface to the inspector system.

        This function is meant to be called by pdef, pdoc & friends."""

        #oname = oname.strip()
        #print '1- oname: <%r>' % oname  # dbg
        try:
            oname = oname.strip().encode('ascii')
            #print '2- oname: <%r>' % oname  # dbg
        except UnicodeEncodeError:
            print 'Python identifiers can only contain ascii characters.'
            return 'not found'
            
        info = Struct(self._ofind(oname, namespaces))
        
        if info.found:
            try:
                IPython.generics.inspect_object(info.obj)
                return
            except IPython.ipapi.TryNext:
                pass
            # Get the docstring of the class property if it exists.
            path = oname.split('.')
            root = '.'.join(path[:-1])
            if info.parent is not None:
                try:
                    target = getattr(info.parent, '__class__') 
                    # The object belongs to a class instance. 
                    try: 
                        target = getattr(target, path[-1])
                        # The class defines the object. 
                        if isinstance(target, property):
                            oname = root + '.__class__.' + path[-1]
                            info = Struct(self._ofind(oname))
                    except AttributeError: pass
                except AttributeError: pass
                        
            pmethod = getattr(self.shell.inspector,meth)
            formatter = info.ismagic and self.format_screen or None
            if meth == 'pdoc':
                pmethod(info.obj,oname,formatter)
            elif meth == 'pinfo':
                pmethod(info.obj,oname,formatter,info,**kw)
            else:
                pmethod(info.obj,oname)
        else:
            print 'Object `%s` not found.' % oname
            return 'not found'  # so callers can take other action
        
    def magic_psearch(self, parameter_s=''):
        """Search for object in namespaces by wildcard.

        %psearch [options] PATTERN [OBJECT TYPE]

        Note: ? can be used as a synonym for %psearch, at the beginning or at
        the end: both a*? and ?a* are equivalent to '%psearch a*'.  Still, the
        rest of the command line must be unchanged (options come first), so
        for example the following forms are equivalent

        %psearch -i a* function
        -i a* function?
        ?-i a* function

        Arguments:
        
          PATTERN

          where PATTERN is a string containing * as a wildcard similar to its
          use in a shell.  The pattern is matched in all namespaces on the
          search path. By default objects starting with a single _ are not
          matched, many IPython generated objects have a single
          underscore. The default is case insensitive matching. Matching is
          also done on the attributes of objects and not only on the objects
          in a module.

          [OBJECT TYPE]

          Is the name of a python type from the types module. The name is
          given in lowercase without the ending type, ex. StringType is
          written string. By adding a type here only objects matching the
          given type are matched. Using all here makes the pattern match all
          types (this is the default).

        Options:

          -a: makes the pattern match even objects whose names start with a
          single underscore.  These names are normally ommitted from the
          search.

          -i/-c: make the pattern case insensitive/sensitive.  If neither of
          these options is given, the default is read from your ipythonrc
          file.  The option name which sets this value is
          'wildcards_case_sensitive'.  If this option is not specified in your
          ipythonrc file, IPython's internal default is to do a case sensitive
          search.

          -e/-s NAMESPACE: exclude/search a given namespace.  The pattern you
          specifiy can be searched in any of the following namespaces:
          'builtin', 'user', 'user_global','internal', 'alias', where
          'builtin' and 'user' are the search defaults.  Note that you should
          not use quotes when specifying namespaces.

          'Builtin' contains the python module builtin, 'user' contains all
          user data, 'alias' only contain the shell aliases and no python
          objects, 'internal' contains objects used by IPython.  The
          'user_global' namespace is only used by embedded IPython instances,
          and it contains module-level globals.  You can add namespaces to the
          search with -s or exclude them with -e (these options can be given
          more than once).
    
        Examples:
       
        %psearch a*            -> objects beginning with an a
        %psearch -e builtin a* -> objects NOT in the builtin space starting in a
        %psearch a* function   -> all functions beginning with an a
        %psearch re.e*         -> objects beginning with an e in module re
        %psearch r*.e*         -> objects that start with e in modules starting in r
        %psearch r*.* string   -> all strings in modules beginning with r

        Case sensitve search:
       
        %psearch -c a*         list all object beginning with lower case a

        Show objects beginning with a single _:
       
        %psearch -a _*         list objects beginning with a single underscore"""
        try:
            parameter_s = parameter_s.encode('ascii')
        except UnicodeEncodeError:
            print 'Python identifiers can only contain ascii characters.'
            return

        # default namespaces to be searched
        def_search = ['user','builtin']

        # Process options/args
        opts,args = self.parse_options(parameter_s,'cias:e:',list_all=True)
        opt = opts.get
        shell = self.shell
        psearch = shell.inspector.psearch

        # select case options
        if opts.has_key('i'):
            ignore_case = True
        elif opts.has_key('c'):
            ignore_case = False
        else:
            ignore_case = not shell.rc.wildcards_case_sensitive

        # Build list of namespaces to search from user options
        def_search.extend(opt('s',[]))
        ns_exclude = ns_exclude=opt('e',[])
        ns_search = [nm for nm in def_search if nm not in ns_exclude]
        
        # Call the actual search
        try:
            psearch(args,shell.ns_table,ns_search,
                    show_all=opt('a'),ignore_case=ignore_case)
        except:
            shell.showtraceback()

    def magic_who_ls(self, parameter_s=''):
        """Return a sorted list of all interactive variables.

        If arguments are given, only variables of types matching these
        arguments are returned."""

        user_ns = self.shell.user_ns
        internal_ns = self.shell.internal_ns
        user_config_ns = self.shell.user_config_ns
        out = []
        typelist = parameter_s.split()

        for i in user_ns:
            if not (i.startswith('_') or i.startswith('_i')) \
                   and not (i in internal_ns or i in user_config_ns):
                if typelist:
                    if type(user_ns[i]).__name__ in typelist:
                        out.append(i)
                else:
                    out.append(i)
        out.sort()
        return out
        
    def magic_who(self, parameter_s=''):
        """Print all interactive variables, with some minimal formatting.

        If any arguments are given, only variables whose type matches one of
        these are printed.  For example:

          %who function str

        will only list functions and strings, excluding all other types of
        variables.  To find the proper type names, simply use type(var) at a
        command line to see how python prints type names.  For example:

          In [1]: type('hello')\\
          Out[1]: <type 'str'>

        indicates that the type name for strings is 'str'.

        %who always excludes executed names loaded through your configuration
        file and things which are internal to IPython.

        This is deliberate, as typically you may load many modules and the
        purpose of %who is to show you only what you've manually defined."""

        varlist = self.magic_who_ls(parameter_s)
        if not varlist:
            if parameter_s:
                print 'No variables match your requested type.'
            else:
                print 'Interactive namespace is empty.'
            return

        # if we have variables, move on...
        count = 0
        for i in varlist:
            print i+'\t',
            count += 1
            if count > 8:
                count = 0
                print
        print

    def magic_whos(self, parameter_s=''):
        """Like %who, but gives some extra information about each variable.

        The same type filtering of %who can be applied here.

        For all variables, the type is printed. Additionally it prints:
        
          - For {},[],(): their length.

          - For numpy and Numeric arrays, a summary with shape, number of
          elements, typecode and size in memory.

          - Everything else: a string representation, snipping their middle if
          too long."""
        
        varnames = self.magic_who_ls(parameter_s)
        if not varnames:
            if parameter_s:
                print 'No variables match your requested type.'
            else:
                print 'Interactive namespace is empty.'
            return

        # if we have variables, move on...

        # for these types, show len() instead of data:
        seq_types = [types.DictType,types.ListType,types.TupleType]

        # for numpy/Numeric arrays, display summary info
        try:
            import numpy
        except ImportError:
            ndarray_type = None
        else:
            ndarray_type = numpy.ndarray.__name__
        try:
            import Numeric
        except ImportError:
            array_type = None
        else:
            array_type = Numeric.ArrayType.__name__

        # Find all variable names and types so we can figure out column sizes
        def get_vars(i):
            return self.shell.user_ns[i]
        
        # some types are well known and can be shorter
        abbrevs = {'IPython.macro.Macro' : 'Macro'}
        def type_name(v):
            tn = type(v).__name__
            return abbrevs.get(tn,tn)
            
        varlist = map(get_vars,varnames)

        typelist = []
        for vv in varlist:
            tt = type_name(vv)

            if tt=='instance':
                typelist.append( abbrevs.get(str(vv.__class__),
                                             str(vv.__class__)))
            else:
                typelist.append(tt)

        # column labels and # of spaces as separator
        varlabel = 'Variable'
        typelabel = 'Type'
        datalabel = 'Data/Info'
        colsep = 3
        # variable format strings
        vformat    = "$vname.ljust(varwidth)$vtype.ljust(typewidth)"
        vfmt_short = '$vstr[:25]<...>$vstr[-25:]'
        aformat    = "%s: %s elems, type `%s`, %s bytes"
        # find the size of the columns to format the output nicely
        varwidth = max(max(map(len,varnames)), len(varlabel)) + colsep
        typewidth = max(max(map(len,typelist)), len(typelabel)) + colsep
        # table header
        print varlabel.ljust(varwidth) + typelabel.ljust(typewidth) + \
              ' '+datalabel+'\n' + '-'*(varwidth+typewidth+len(datalabel)+1)
        # and the table itself
        kb = 1024
        Mb = 1048576  # kb**2
        for vname,var,vtype in zip(varnames,varlist,typelist):
            print itpl(vformat),
            if vtype in seq_types:
                print len(var)
            elif vtype in [array_type,ndarray_type]:
                vshape = str(var.shape).replace(',','').replace(' ','x')[1:-1]
                if vtype==ndarray_type:
                    # numpy
                    vsize  = var.size
                    vbytes = vsize*var.itemsize
                    vdtype = var.dtype
                else:
                    # Numeric
                    vsize  = Numeric.size(var)
                    vbytes = vsize*var.itemsize()
                    vdtype = var.typecode()
                    
                if vbytes < 100000:
                    print aformat % (vshape,vsize,vdtype,vbytes)
                else:
                    print aformat % (vshape,vsize,vdtype,vbytes),
                    if vbytes < Mb:
                        print '(%s kb)' % (vbytes/kb,)
                    else:
                        print '(%s Mb)' % (vbytes/Mb,)
            else:
                try:
                    vstr = str(var)
                except UnicodeEncodeError:
                    vstr = unicode(var).encode(sys.getdefaultencoding(),
                                               'backslashreplace')
                vstr = vstr.replace('\n','\\n')
                if len(vstr) < 50:
                    print vstr
                else:
                    printpl(vfmt_short)
                
    def magic_reset(self, parameter_s=''):
        """Resets the namespace by removing all names defined by the user.

        Input/Output history are left around in case you need them."""

        ans = self.shell.ask_yes_no(
          "Once deleted, variables cannot be recovered. Proceed (y/[n])? ")
        if not ans:
            print 'Nothing done.'
            return
        user_ns = self.shell.user_ns
        for i in self.magic_who_ls():
            del(user_ns[i])
            
        # Also flush the private list of module references kept for script
        # execution protection
        self.shell._user_main_modules[:] = []

    def magic_logstart(self,parameter_s=''):
        """Start logging anywhere in a session.

        %logstart [-o|-r|-t] [log_name [log_mode]]

        If no name is given, it defaults to a file named 'ipython_log.py' in your
        current directory, in 'rotate' mode (see below).

        '%logstart name' saves to file 'name' in 'backup' mode.  It saves your
        history up to that point and then continues logging.

        %logstart takes a second optional parameter: logging mode. This can be one
        of (note that the modes are given unquoted):\\
          append: well, that says it.\\
          backup: rename (if exists) to name~ and start name.\\
          global: single logfile in your home dir, appended to.\\
          over  : overwrite existing log.\\
          rotate: create rotating logs name.1~, name.2~, etc.

        Options:

          -o: log also IPython's output.  In this mode, all commands which
          generate an Out[NN] prompt are recorded to the logfile, right after
          their corresponding input line.  The output lines are always
          prepended with a '#[Out]# ' marker, so that the log remains valid
          Python code.

          Since this marker is always the same, filtering only the output from
          a log is very easy, using for example a simple awk call:

            awk -F'#\\[Out\\]# ' '{if($2) {print $2}}' ipython_log.py

          -r: log 'raw' input.  Normally, IPython's logs contain the processed
          input, so that user lines are logged in their final form, converted
          into valid Python.  For example, %Exit is logged as
          '_ip.magic("Exit").  If the -r flag is given, all input is logged
          exactly as typed, with no transformations applied.

          -t: put timestamps before each input line logged (these are put in
          comments)."""
        
        opts,par = self.parse_options(parameter_s,'ort')
        log_output = 'o' in opts
        log_raw_input = 'r' in opts
        timestamp = 't' in opts

        rc = self.shell.rc
        logger = self.shell.logger

        # if no args are given, the defaults set in the logger constructor by
        # ipytohn remain valid
        if par:
            try:
                logfname,logmode = par.split()
            except:
                logfname = par
                logmode = 'backup'
        else:
            logfname = logger.logfname
            logmode = logger.logmode
        # put logfname into rc struct as if it had been called on the command
        # line, so it ends up saved in the log header Save it in case we need
        # to restore it...
        old_logfile = rc.opts.get('logfile','')  
        if logfname:
            logfname = os.path.expanduser(logfname)
        rc.opts.logfile = logfname
        loghead = self.shell.loghead_tpl % (rc.opts,rc.args)
        try:
            started  = logger.logstart(logfname,loghead,logmode,
                                       log_output,timestamp,log_raw_input)
        except:
            rc.opts.logfile = old_logfile
            warn("Couldn't start log: %s" % sys.exc_info()[1])
        else:
            # log input history up to this point, optionally interleaving
            # output if requested

            if timestamp:
                # disable timestamping for the previous history, since we've
                # lost those already (no time machine here).
                logger.timestamp = False

            if log_raw_input:
                input_hist = self.shell.input_hist_raw
            else:
                input_hist = self.shell.input_hist
                
            if log_output:
                log_write = logger.log_write
                output_hist = self.shell.output_hist
                for n in range(1,len(input_hist)-1):
                    log_write(input_hist[n].rstrip())
                    if n in output_hist:
                        log_write(repr(output_hist[n]),'output')
            else:
                logger.log_write(input_hist[1:])
            if timestamp:
                # re-enable timestamping
                logger.timestamp = True
                
            print ('Activating auto-logging. '
                   'Current session state plus future input saved.')
            logger.logstate()

    def magic_logstop(self,parameter_s=''):
        """Fully stop logging and close log file.

        In order to start logging again, a new %logstart call needs to be made,
        possibly (though not necessarily) with a new filename, mode and other
        options."""
        self.logger.logstop()

    def magic_logoff(self,parameter_s=''):
        """Temporarily stop logging.

        You must have previously started logging."""
        self.shell.logger.switch_log(0)
        
    def magic_logon(self,parameter_s=''):
        """Restart logging.

        This function is for restarting logging which you've temporarily
        stopped with %logoff. For starting logging for the first time, you
        must use the %logstart function, which allows you to specify an
        optional log filename."""
        
        self.shell.logger.switch_log(1)
    
    def magic_logstate(self,parameter_s=''):
        """Print the status of the logging system."""

        self.shell.logger.logstate()
        
    def magic_pdb(self, parameter_s=''):
        """Control the automatic calling of the pdb interactive debugger.

        Call as '%pdb on', '%pdb 1', '%pdb off' or '%pdb 0'. If called without
        argument it works as a toggle.

        When an exception is triggered, IPython can optionally call the
        interactive pdb debugger after the traceback printout. %pdb toggles
        this feature on and off.

        The initial state of this feature is set in your ipythonrc
        configuration file (the variable is called 'pdb').

        If you want to just activate the debugger AFTER an exception has fired,
        without having to type '%pdb on' and rerunning your code, you can use
        the %debug magic."""

        par = parameter_s.strip().lower()

        if par:
            try:
                new_pdb = {'off':0,'0':0,'on':1,'1':1}[par]
            except KeyError:
                print ('Incorrect argument. Use on/1, off/0, '
                       'or nothing for a toggle.')
                return
        else:
            # toggle
            new_pdb = not self.shell.call_pdb

        # set on the shell
        self.shell.call_pdb = new_pdb
        print 'Automatic pdb calling has been turned',on_off(new_pdb)

    def magic_debug(self, parameter_s=''):
        """Activate the interactive debugger in post-mortem mode.

        If an exception has just occurred, this lets you inspect its stack
        frames interactively.  Note that this will always work only on the last
        traceback that occurred, so you must call this quickly after an
        exception that you wish to inspect has fired, because if another one
        occurs, it clobbers the previous one.

        If you want IPython to automatically do this on every exception, see
        the %pdb magic for more details.
        """
        
        self.shell.debugger(force=True)

    @testdec.skip_doctest
    def magic_prun(self, parameter_s ='',user_mode=1,
                   opts=None,arg_lst=None,prog_ns=None):

        """Run a statement through the python code profiler.

        Usage:
          %prun [options] statement

        The given statement (which doesn't require quote marks) is run via the
        python profiler in a manner similar to the profile.run() function.
        Namespaces are internally managed to work correctly; profile.run
        cannot be used in IPython because it makes certain assumptions about
        namespaces which do not hold under IPython.

        Options:

        -l <limit>: you can place restrictions on what or how much of the
        profile gets printed. The limit value can be:

          * A string: only information for function names containing this string
          is printed.

          * An integer: only these many lines are printed.

          * A float (between 0 and 1): this fraction of the report is printed
          (for example, use a limit of 0.4 to see the topmost 40% only).

        You can combine several limits with repeated use of the option. For
        example, '-l __init__ -l 5' will print only the topmost 5 lines of
        information about class constructors.

        -r: return the pstats.Stats object generated by the profiling. This
        object has all the information about the profile in it, and you can
        later use it for further analysis or in other functions.

       -s <key>: sort profile by given key. You can provide more than one key
        by using the option several times: '-s key1 -s key2 -s key3...'. The
        default sorting key is 'time'.

        The following is copied verbatim from the profile documentation
        referenced below:

        When more than one key is provided, additional keys are used as
        secondary criteria when the there is equality in all keys selected
        before them.
        
        Abbreviations can be used for any key names, as long as the
        abbreviation is unambiguous.  The following are the keys currently
        defined:

                Valid Arg       Meaning
                  "calls"      call count
                  "cumulative" cumulative time
                  "file"       file name
                  "module"     file name
                  "pcalls"     primitive call count
                  "line"       line number
                  "name"       function name
                  "nfl"        name/file/line
                  "stdname"    standard name
                  "time"       internal time

        Note that all sorts on statistics are in descending order (placing
        most time consuming items first), where as name, file, and line number
        searches are in ascending order (i.e., alphabetical). The subtle
        distinction between "nfl" and "stdname" is that the standard name is a
        sort of the name as printed, which means that the embedded line
        numbers get compared in an odd way.  For example, lines 3, 20, and 40
        would (if the file names were the same) appear in the string order
        "20" "3" and "40".  In contrast, "nfl" does a numeric compare of the
        line numbers.  In fact, sort_stats("nfl") is the same as
        sort_stats("name", "file", "line").

        -T <filename>: save profile results as shown on screen to a text
        file. The profile is still shown on screen.

        -D <filename>: save (via dump_stats) profile statistics to given
        filename. This data is in a format understod by the pstats module, and
        is generated by a call to the dump_stats() method of profile
        objects. The profile is still shown on screen.

        If you want to run complete programs under the profiler's control, use
        '%run -p [prof_opts] filename.py [args to program]' where prof_opts
        contains profiler specific options as described here.
        
        You can read the complete documentation for the profile module with::
        
          In [1]: import profile; profile.help()
        """

        opts_def = Struct(D=[''],l=[],s=['time'],T=[''])
        # protect user quote marks
        parameter_s = parameter_s.replace('"',r'\"').replace("'",r"\'")
        
        if user_mode:  # regular user call
            opts,arg_str = self.parse_options(parameter_s,'D:l:rs:T:',
                                              list_all=1)
            namespace = self.shell.user_ns
        else:  # called to run a program by %run -p
            try:
                filename = get_py_filename(arg_lst[0])
            except IOError,msg:
                error(msg)
                return

            arg_str = 'execfile(filename,prog_ns)'
            namespace = locals()

        opts.merge(opts_def)
        
        prof = profile.Profile()
        try:
            prof = prof.runctx(arg_str,namespace,namespace)
            sys_exit = ''
        except SystemExit:
            sys_exit = """*** SystemExit exception caught in code being profiled."""

        stats = pstats.Stats(prof).strip_dirs().sort_stats(*opts.s)

        lims = opts.l
        if lims:
            lims = []  # rebuild lims with ints/floats/strings
            for lim in opts.l:
                try:
                    lims.append(int(lim))
                except ValueError:
                    try:
                        lims.append(float(lim))
                    except ValueError:
                        lims.append(lim)
                    
        # Trap output.
        stdout_trap = StringIO()

        if hasattr(stats,'stream'):
            # In newer versions of python, the stats object has a 'stream'
            # attribute to write into.
            stats.stream = stdout_trap
            stats.print_stats(*lims)
        else:
            # For older versions, we manually redirect stdout during printing
            sys_stdout = sys.stdout
            try:
                sys.stdout = stdout_trap
                stats.print_stats(*lims)
            finally:
                sys.stdout = sys_stdout
                
        output = stdout_trap.getvalue()
        output = output.rstrip()

        page(output,screen_lines=self.shell.rc.screen_length)
        print sys_exit,

        dump_file = opts.D[0]
        text_file = opts.T[0]
        if dump_file:
            prof.dump_stats(dump_file)
            print '\n*** Profile stats marshalled to file',\
                  `dump_file`+'.',sys_exit
        if text_file:
            pfile = file(text_file,'w')
            pfile.write(output)
            pfile.close()
            print '\n*** Profile printout saved to text file',\
                  `text_file`+'.',sys_exit

        if opts.has_key('r'):
            return stats
        else:
            return None

    @testdec.skip_doctest
    def magic_run(self, parameter_s ='',runner=None):
        """Run the named file inside IPython as a program.

        Usage:\\
          %run [-n -i -t [-N<N>] -d [-b<N>] -p [profile options]] file [args]
        
        Parameters after the filename are passed as command-line arguments to
        the program (put in sys.argv). Then, control returns to IPython's
        prompt.

        This is similar to running at a system prompt:\\
          $ python file args\\
        but with the advantage of giving you IPython's tracebacks, and of
        loading all variables into your interactive namespace for further use
        (unless -p is used, see below).

        The file is executed in a namespace initially consisting only of
        __name__=='__main__' and sys.argv constructed as indicated. It thus
        sees its environment as if it were being run as a stand-alone program
        (except for sharing global objects such as previously imported
        modules). But after execution, the IPython interactive namespace gets
        updated with all variables defined in the program (except for __name__
        and sys.argv). This allows for very convenient loading of code for
        interactive work, while giving each program a 'clean sheet' to run in.

        Options:
        
        -n: __name__ is NOT set to '__main__', but to the running file's name
        without extension (as python does under import).  This allows running
        scripts and reloading the definitions in them without calling code
        protected by an ' if __name__ == "__main__" ' clause.

        -i: run the file in IPython's namespace instead of an empty one. This
        is useful if you are experimenting with code written in a text editor
        which depends on variables defined interactively.

        -e: ignore sys.exit() calls or SystemExit exceptions in the script
        being run.  This is particularly useful if IPython is being used to
        run unittests, which always exit with a sys.exit() call.  In such
        cases you are interested in the output of the test results, not in
        seeing a traceback of the unittest module.

        -t: print timing information at the end of the run.  IPython will give
        you an estimated CPU time consumption for your script, which under
        Unix uses the resource module to avoid the wraparound problems of
        time.clock().  Under Unix, an estimate of time spent on system tasks
        is also given (for Windows platforms this is reported as 0.0).

        If -t is given, an additional -N<N> option can be given, where <N>
        must be an integer indicating how many times you want the script to
        run.  The final timing report will include total and per run results.

        For example (testing the script uniq_stable.py):

            In [1]: run -t uniq_stable

            IPython CPU timings (estimated):\\
              User  :    0.19597 s.\\
              System:        0.0 s.\\

            In [2]: run -t -N5 uniq_stable

            IPython CPU timings (estimated):\\
            Total runs performed: 5\\
              Times :      Total       Per run\\
              User  :   0.910862 s,  0.1821724 s.\\
              System:        0.0 s,        0.0 s.

        -d: run your program under the control of pdb, the Python debugger.
        This allows you to execute your program step by step, watch variables,
        etc.  Internally, what IPython does is similar to calling:
        
          pdb.run('execfile("YOURFILENAME")')

        with a breakpoint set on line 1 of your file.  You can change the line
        number for this automatic breakpoint to be <N> by using the -bN option
        (where N must be an integer).  For example:

          %run -d -b40 myscript

        will set the first breakpoint at line 40 in myscript.py.  Note that
        the first breakpoint must be set on a line which actually does
        something (not a comment or docstring) for it to stop execution.

        When the pdb debugger starts, you will see a (Pdb) prompt.  You must
        first enter 'c' (without qoutes) to start execution up to the first
        breakpoint.

        Entering 'help' gives information about the use of the debugger.  You
        can easily see pdb's full documentation with "import pdb;pdb.help()"
        at a prompt.

        -p: run program under the control of the Python profiler module (which
        prints a detailed report of execution times, function calls, etc).

        You can pass other options after -p which affect the behavior of the
        profiler itself. See the docs for %prun for details.

        In this mode, the program's variables do NOT propagate back to the
        IPython interactive namespace (because they remain in the namespace
        where the profiler executes them).

        Internally this triggers a call to %prun, see its documentation for
        details on the options available specifically for profiling.

        There is one special usage for which the text above doesn't apply:
        if the filename ends with .ipy, the file is run as ipython script,
        just as if the commands were written on IPython prompt.
        """

        # get arguments and set sys.argv for program to be run.
        opts,arg_lst = self.parse_options(parameter_s,'nidtN:b:pD:l:rs:T:e',
                                          mode='list',list_all=1)

        try:
            filename = get_py_filename(arg_lst[0])
        except IndexError:
            warn('you must provide at least a filename.')
            print '\n%run:\n',OInspect.getdoc(self.magic_run)
            return
        except IOError,msg:
            error(msg)
            return

        if filename.lower().endswith('.ipy'):
            self.api.runlines(open(filename).read())
            return
        
        # Control the response to exit() calls made by the script being run
        exit_ignore = opts.has_key('e')
        
        # Make sure that the running script gets a proper sys.argv as if it
        # were run from a system shell.
        save_argv = sys.argv # save it for later restoring
        sys.argv = [filename]+ arg_lst[1:]  # put in the proper filename

        if opts.has_key('i'):
            # Run in user's interactive namespace
            prog_ns = self.shell.user_ns
            __name__save = self.shell.user_ns['__name__']
            prog_ns['__name__'] = '__main__'
            main_mod = FakeModule(prog_ns)
        else:
            # Run in a fresh, empty namespace
            if opts.has_key('n'):
                name = os.path.splitext(os.path.basename(filename))[0]
            else:
                name = '__main__'
            main_mod = FakeModule()
            prog_ns = main_mod.__dict__
            prog_ns['__name__'] = name
            # The shell MUST hold a reference to main_mod so after %run exits,
            # the python deletion mechanism doesn't zero it out (leaving
            # dangling references)
            self.shell._user_main_modules.append(main_mod)

        # Since '%run foo' emulates 'python foo.py' at the cmd line, we must
        # set the __file__ global in the script's namespace
        prog_ns['__file__'] = filename

        # pickle fix.  See iplib for an explanation.  But we need to make sure
        # that, if we overwrite __main__, we replace it at the end
        main_mod_name = prog_ns['__name__']

        if main_mod_name == '__main__':
            restore_main = sys.modules['__main__']
        else:
            restore_main = False

        # This needs to be undone at the end to prevent holding references to
        # every single object ever created.
        sys.modules[main_mod_name] = main_mod
        
        stats = None
        try:
            self.shell.savehist()

            if opts.has_key('p'):
                stats = self.magic_prun('',0,opts,arg_lst,prog_ns)
            else:
                if opts.has_key('d'):
                    deb = Debugger.Pdb(self.shell.rc.colors)
                    # reset Breakpoint state, which is moronically kept
                    # in a class
                    bdb.Breakpoint.next = 1
                    bdb.Breakpoint.bplist = {}
                    bdb.Breakpoint.bpbynumber = [None]
                    # Set an initial breakpoint to stop execution
                    maxtries = 10
                    bp = int(opts.get('b',[1])[0])
                    checkline = deb.checkline(filename,bp)
                    if not checkline:
                        for bp in range(bp+1,bp+maxtries+1):
                            if deb.checkline(filename,bp):
                                break
                        else:
                            msg = ("\nI failed to find a valid line to set "
                                   "a breakpoint\n"
                                   "after trying up to line: %s.\n"
                                   "Please set a valid breakpoint manually "
                                   "with the -b option." % bp)
                            error(msg)
                            return
                    # if we find a good linenumber, set the breakpoint
                    deb.do_break('%s:%s' % (filename,bp))
                    # Start file run
                    print "NOTE: Enter 'c' at the",
                    print "%s prompt to start your script." % deb.prompt
                    try:
                        deb.run('execfile("%s")' % filename,prog_ns)
                        
                    except:
                        etype, value, tb = sys.exc_info()
                        # Skip three frames in the traceback: the %run one,
                        # one inside bdb.py, and the command-line typed by the
                        # user (run by exec in pdb itself).
                        self.shell.InteractiveTB(etype,value,tb,tb_offset=3)
                else:
                    if runner is None:
                        runner = self.shell.safe_execfile
                    if opts.has_key('t'):
                        # timed execution
                        try:
                            nruns = int(opts['N'][0])
                            if nruns < 1:
                                error('Number of runs must be >=1')
                                return
                        except (KeyError):
                            nruns = 1
                        if nruns == 1:
                            t0 = clock2()
                            runner(filename,prog_ns,prog_ns,
                                   exit_ignore=exit_ignore)
                            t1 = clock2()
                            t_usr = t1[0]-t0[0]
                            t_sys = t1[1]-t1[1]
                            print "\nIPython CPU timings (estimated):"
                            print "  User  : %10s s." % t_usr
                            print "  System: %10s s." % t_sys
                        else:
                            runs = range(nruns)
                            t0 = clock2()
                            for nr in runs:
                                runner(filename,prog_ns,prog_ns,
                                       exit_ignore=exit_ignore)
                            t1 = clock2()
                            t_usr = t1[0]-t0[0]
                            t_sys = t1[1]-t1[1]
                            print "\nIPython CPU timings (estimated):"
                            print "Total runs performed:",nruns
                            print "  Times : %10s    %10s" % ('Total','Per run')
                            print "  User  : %10s s, %10s s." % (t_usr,t_usr/nruns)
                            print "  System: %10s s, %10s s." % (t_sys,t_sys/nruns)
                            
                    else:
                        # regular execution
                        runner(filename,prog_ns,prog_ns,exit_ignore=exit_ignore)
                if opts.has_key('i'):
                    self.shell.user_ns['__name__'] = __name__save
                else:
                    # update IPython interactive namespace
                    del prog_ns['__name__']
                    self.shell.user_ns.update(prog_ns)
        finally:
            # Ensure key global structures are restored
            sys.argv = save_argv
            if restore_main:
                sys.modules['__main__'] = restore_main
            else:
                # Remove from sys.modules the reference to main_mod we'd
                # added.  Otherwise it will trap references to objects
                # contained therein.
                del sys.modules[main_mod_name]
            self.shell.reloadhist()
                
        return stats

    def magic_runlog(self, parameter_s =''):
        """Run files as logs.

        Usage:\\
          %runlog file1 file2 ...

        Run the named files (treating them as log files) in sequence inside
        the interpreter, and return to the prompt.  This is much slower than
        %run because each line is executed in a try/except block, but it
        allows running files with syntax errors in them.

        Normally IPython will guess when a file is one of its own logfiles, so
        you can typically use %run even for logs. This shorthand allows you to
        force any file to be treated as a log file."""

        for f in parameter_s.split():
            self.shell.safe_execfile(f,self.shell.user_ns,
                                     self.shell.user_ns,islog=1)

    @testdec.skip_doctest
    def magic_timeit(self, parameter_s =''):
        """Time execution of a Python statement or expression

        Usage:\\
          %timeit [-n<N> -r<R> [-t|-c]] statement

        Time execution of a Python statement or expression using the timeit
        module.

        Options:
        -n<N>: execute the given statement <N> times in a loop. If this value
        is not given, a fitting value is chosen. 
        
        -r<R>: repeat the loop iteration <R> times and take the best result.
        Default: 3
        
        -t: use time.time to measure the time, which is the default on Unix.
        This function measures wall time.
        
        -c: use time.clock to measure the time, which is the default on
        Windows and measures wall time. On Unix, resource.getrusage is used
        instead and returns the CPU user time.

        -p<P>: use a precision of <P> digits to display the timing result.
        Default: 3

        
        Examples:

          In [1]: %timeit pass
          10000000 loops, best of 3: 53.3 ns per loop

          In [2]: u = None

          In [3]: %timeit u is None
          10000000 loops, best of 3: 184 ns per loop

          In [4]: %timeit -r 4 u == None
          1000000 loops, best of 4: 242 ns per loop

          In [5]: import time

          In [6]: %timeit -n1 time.sleep(2)
          1 loops, best of 3: 2 s per loop
          

        The times reported by %timeit will be slightly higher than those
        reported by the timeit.py script when variables are accessed. This is
        due to the fact that %timeit executes the statement in the namespace
        of the shell, compared with timeit.py, which uses a single setup
        statement to import function or create variables. Generally, the bias
        does not matter as long as results from timeit.py are not mixed with
        those from %timeit."""

        import timeit
        import math

        units = [u"s", u"ms", u"\xb5s", u"ns"]
        scaling = [1, 1e3, 1e6, 1e9]

        opts, stmt = self.parse_options(parameter_s,'n:r:tcp:',
                                        posix=False)
        if stmt == "":
            return
        timefunc = timeit.default_timer
        number = int(getattr(opts, "n", 0))
        repeat = int(getattr(opts, "r", timeit.default_repeat))
        precision = int(getattr(opts, "p", 3))
        if hasattr(opts, "t"):
            timefunc = time.time
        if hasattr(opts, "c"):
            timefunc = clock

        timer = timeit.Timer(timer=timefunc)
        # this code has tight coupling to the inner workings of timeit.Timer,
        # but is there a better way to achieve that the code stmt has access
        # to the shell namespace?

        src = timeit.template % {'stmt': timeit.reindent(stmt, 8),
                                 'setup': "pass"}
        # Track compilation time so it can be reported if too long
        # Minimum time above which compilation time will be reported
        tc_min = 0.1
        
        t0 = clock()
        code = compile(src, "<magic-timeit>", "exec")
        tc = clock()-t0
        
        ns = {}
        exec code in self.shell.user_ns, ns
        timer.inner = ns["inner"]
        
        if number == 0:
            # determine number so that 0.2 <= total time < 2.0
            number = 1
            for i in range(1, 10):
                number *= 10
                if timer.timeit(number) >= 0.2:
                    break
        
        best = min(timer.repeat(repeat, number)) / number

        if best > 0.0:
            order = min(-int(math.floor(math.log10(best)) // 3), 3)
        else:
            order = 3
        print u"%d loops, best of %d: %.*g %s per loop" % (number, repeat,
                                                          precision,
                                                          best * scaling[order],
                                                          units[order])
        if tc > tc_min:
            print "Compiler time: %.2f s" % tc

    @testdec.skip_doctest
    def magic_time(self,parameter_s = ''):
        """Time execution of a Python statement or expression.

        The CPU and wall clock times are printed, and the value of the
        expression (if any) is returned.  Note that under Win32, system time
        is always reported as 0, since it can not be measured.

        This function provides very basic timing functionality.  In Python
        2.3, the timeit module offers more control and sophistication, so this
        could be rewritten to use it (patches welcome).
        
        Some examples:

          In [1]: time 2**128
          CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
          Wall time: 0.00
          Out[1]: 340282366920938463463374607431768211456L

          In [2]: n = 1000000

          In [3]: time sum(range(n))
          CPU times: user 1.20 s, sys: 0.05 s, total: 1.25 s
          Wall time: 1.37
          Out[3]: 499999500000L

          In [4]: time print 'hello world'
          hello world
          CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
          Wall time: 0.00

          Note that the time needed by Python to compile the given expression
          will be reported if it is more than 0.1s.  In this example, the
          actual exponentiation is done by Python at compilation time, so while
          the expression can take a noticeable amount of time to compute, that
          time is purely due to the compilation:

          In [5]: time 3**9999;
          CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
          Wall time: 0.00 s

          In [6]: time 3**999999;
          CPU times: user 0.00 s, sys: 0.00 s, total: 0.00 s
          Wall time: 0.00 s
          Compiler : 0.78 s
          """
        
        # fail immediately if the given expression can't be compiled
        
        expr = self.shell.prefilter(parameter_s,False)

        # Minimum time above which compilation time will be reported
        tc_min = 0.1
        
        try:
            mode = 'eval'
            t0 = clock()
            code = compile(expr,'<timed eval>',mode)
            tc = clock()-t0
        except SyntaxError:
            mode = 'exec'
            t0 = clock()
            code = compile(expr,'<timed exec>',mode)
            tc = clock()-t0
        # skew measurement as little as possible
        glob = self.shell.user_ns
        clk = clock2
        wtime = time.time
        # time execution
        wall_st = wtime()
        if mode=='eval':
            st = clk()
            out = eval(code,glob)
            end = clk()
        else:
            st = clk()
            exec code in glob
            end = clk()
            out = None
        wall_end = wtime()
        # Compute actual times and report
        wall_time = wall_end-wall_st
        cpu_user = end[0]-st[0]
        cpu_sys = end[1]-st[1]
        cpu_tot = cpu_user+cpu_sys
        print "CPU times: user %.2f s, sys: %.2f s, total: %.2f s" % \
              (cpu_user,cpu_sys,cpu_tot)
        print "Wall time: %.2f s" % wall_time
        if tc > tc_min:
            print "Compiler : %.2f s" % tc
        return out

    @testdec.skip_doctest
    def magic_macro(self,parameter_s = ''):
        """Define a set of input lines as a macro for future re-execution.

        Usage:\\
          %macro [options] name n1-n2 n3-n4 ... n5 .. n6 ...

        Options:
        
          -r: use 'raw' input.  By default, the 'processed' history is used,
          so that magics are loaded in their transformed version to valid
          Python.  If this option is given, the raw input as typed as the
          command line is used instead.

        This will define a global variable called `name` which is a string
        made of joining the slices and lines you specify (n1,n2,... numbers
        above) from your input history into a single string. This variable
        acts like an automatic function which re-executes those lines as if
        you had typed them. You just type 'name' at the prompt and the code
        executes.

        The notation for indicating number ranges is: n1-n2 means 'use line
        numbers n1,...n2' (the endpoint is included).  That is, '5-7' means
        using the lines numbered 5,6 and 7.

        Note: as a 'hidden' feature, you can also use traditional python slice
        notation, where N:M means numbers N through M-1.

        For example, if your history contains (%hist prints it):
        
          44: x=1
          45: y=3
          46: z=x+y
          47: print x
          48: a=5
          49: print 'x',x,'y',y

        you can create a macro with lines 44 through 47 (included) and line 49
        called my_macro with:

          In [55]: %macro my_macro 44-47 49

        Now, typing `my_macro` (without quotes) will re-execute all this code
        in one pass.

        You don't need to give the line-numbers in order, and any given line
        number can appear multiple times. You can assemble macros with any
        lines from your input history in any order.

        The macro is a simple object which holds its value in an attribute,
        but IPython's display system checks for macros and executes them as
        code instead of printing them when you type their name.

        You can view a macro's contents by explicitly printing it with:
        
          'print macro_name'.

        For one-off cases which DON'T contain magic function calls in them you
        can obtain similar results by explicitly executing slices from your
        input history with:

          In [60]: exec In[44:48]+In[49]"""

        opts,args = self.parse_options(parameter_s,'r',mode='list')
        if not args:
            macs = [k for k,v in self.shell.user_ns.items() if isinstance(v, Macro)]
            macs.sort()
            return macs
        if len(args) == 1:
            raise UsageError(
                "%macro insufficient args; usage '%macro name n1-n2 n3-4...")
        name,ranges = args[0], args[1:]
        
        #print 'rng',ranges  # dbg
        lines = self.extract_input_slices(ranges,opts.has_key('r'))
        macro = Macro(lines)
        self.shell.user_ns.update({name:macro})
        print 'Macro `%s` created. To execute, type its name (without quotes).' % name
        print 'Macro contents:'
        print macro,

    def magic_save(self,parameter_s = ''):
        """Save a set of lines to a given filename.

        Usage:\\
          %save [options] filename n1-n2 n3-n4 ... n5 .. n6 ...

        Options:
        
          -r: use 'raw' input.  By default, the 'processed' history is used,
          so that magics are loaded in their transformed version to valid
          Python.  If this option is given, the raw input as typed as the
          command line is used instead.

        This function uses the same syntax as %macro for line extraction, but
        instead of creating a macro it saves the resulting string to the
        filename you specify.

        It adds a '.py' extension to the file if you don't do so yourself, and
        it asks for confirmation before overwriting existing files."""

        opts,args = self.parse_options(parameter_s,'r',mode='list')
        fname,ranges = args[0], args[1:]
        if not fname.endswith('.py'):
            fname += '.py'
        if os.path.isfile(fname):
            ans = raw_input('File `%s` exists. Overwrite (y/[N])? ' % fname)
            if ans.lower() not in ['y','yes']:
                print 'Operation cancelled.'
                return
        cmds = ''.join(self.extract_input_slices(ranges,opts.has_key('r')))
        f = file(fname,'w')
        f.write(cmds)
        f.close()
        print 'The following commands were written to file `%s`:' % fname
        print cmds

    def _edit_macro(self,mname,macro):
        """open an editor with the macro data in a file"""
        filename = self.shell.mktempfile(macro.value)
        self.shell.hooks.editor(filename)

        # and make a new macro object, to replace the old one
        mfile = open(filename)
        mvalue = mfile.read()
        mfile.close()
        self.shell.user_ns[mname] = Macro(mvalue)

    def magic_ed(self,parameter_s=''):
        """Alias to %edit."""
        return self.magic_edit(parameter_s)

    @testdec.skip_doctest
    def magic_edit(self,parameter_s='',last_call=['','']):
        """Bring up an editor and execute the resulting code.

        Usage:
          %edit [options] [args]

        %edit runs IPython's editor hook.  The default version of this hook is
        set to call the __IPYTHON__.rc.editor command.  This is read from your
        environment variable $EDITOR.  If this isn't found, it will default to
        vi under Linux/Unix and to notepad under Windows.  See the end of this
        docstring for how to change the editor hook.

        You can also set the value of this editor via the command line option
        '-editor' or in your ipythonrc file. This is useful if you wish to use
        specifically for IPython an editor different from your typical default
        (and for Windows users who typically don't set environment variables).

        This command allows you to conveniently edit multi-line code right in
        your IPython session.
        
        If called without arguments, %edit opens up an empty editor with a
        temporary file and will execute the contents of this file when you
        close it (don't forget to save it!).


        Options:

        -n <number>: open the editor at a specified line number.  By default,
        the IPython editor hook uses the unix syntax 'editor +N filename', but
        you can configure this by providing your own modified hook if your
        favorite editor supports line-number specifications with a different
        syntax.
        
        -p: this will call the editor with the same data as the previous time
        it was used, regardless of how long ago (in your current session) it
        was.

        -r: use 'raw' input.  This option only applies to input taken from the
        user's history.  By default, the 'processed' history is used, so that
        magics are loaded in their transformed version to valid Python.  If
        this option is given, the raw input as typed as the command line is
        used instead.  When you exit the editor, it will be executed by
        IPython's own processor.
        
        -x: do not execute the edited code immediately upon exit. This is
        mainly useful if you are editing programs which need to be called with
        command line arguments, which you can then do using %run.


        Arguments:

        If arguments are given, the following possibilites exist:

        - The arguments are numbers or pairs of colon-separated numbers (like
        1 4:8 9). These are interpreted as lines of previous input to be
        loaded into the editor. The syntax is the same of the %macro command.

        - If the argument doesn't start with a number, it is evaluated as a
        variable and its contents loaded into the editor. You can thus edit
        any string which contains python code (including the result of
        previous edits).

        - If the argument is the name of an object (other than a string),
        IPython will try to locate the file where it was defined and open the
        editor at the point where it is defined. You can use `%edit function`
        to load an editor exactly at the point where 'function' is defined,
        edit it and have the file be executed automatically.

        If the object is a macro (see %macro for details), this opens up your
        specified editor with a temporary file containing the macro's data.
        Upon exit, the macro is reloaded with the contents of the file.

        Note: opening at an exact line is only supported under Unix, and some
        editors (like kedit and gedit up to Gnome 2.8) do not understand the
        '+NUMBER' parameter necessary for this feature. Good editors like
        (X)Emacs, vi, jed, pico and joe all do.

        - If the argument is not found as a variable, IPython will look for a
        file with that name (adding .py if necessary) and load it into the
        editor. It will execute its contents with execfile() when you exit,
        loading any code in the file into your interactive namespace.

        After executing your code, %edit will return as output the code you
        typed in the editor (except when it was an existing file). This way
        you can reload the code in further invocations of %edit as a variable,
        via _<NUMBER> or Out[<NUMBER>], where <NUMBER> is the prompt number of
        the output.

        Note that %edit is also available through the alias %ed.

        This is an example of creating a simple function inside the editor and
        then modifying it. First, start up the editor:

        In [1]: ed
        Editing... done. Executing edited code...
        Out[1]: 'def foo():n    print "foo() was defined in an editing session"n'

        We can then call the function foo():
        
        In [2]: foo()
        foo() was defined in an editing session

        Now we edit foo.  IPython automatically loads the editor with the
        (temporary) file where foo() was previously defined:
        
        In [3]: ed foo
        Editing... done. Executing edited code...

        And if we call foo() again we get the modified version:
        
        In [4]: foo()
        foo() has now been changed!

        Here is an example of how to edit a code snippet successive
        times. First we call the editor:

        In [5]: ed
        Editing... done. Executing edited code...
        hello
        Out[5]: "print 'hello'n"

        Now we call it again with the previous output (stored in _):

        In [6]: ed _
        Editing... done. Executing edited code...
        hello world
        Out[6]: "print 'hello world'n"

        Now we call it with the output #8 (stored in _8, also as Out[8]):

        In [7]: ed _8
        Editing... done. Executing edited code...
        hello again
        Out[7]: "print 'hello again'n"


        Changing the default editor hook:

        If you wish to write your own editor hook, you can put it in a
        configuration file which you load at startup time.  The default hook
        is defined in the IPython.hooks module, and you can use that as a
        starting example for further modifications.  That file also has
        general instructions on how to set a new hook for use once you've
        defined it."""
        
        # FIXME: This function has become a convoluted mess.  It needs a
        # ground-up rewrite with clean, simple logic.

        def make_filename(arg):
            "Make a filename from the given args"
            try:
                filename = get_py_filename(arg)
            except IOError:
                if args.endswith('.py'):
                    filename = arg
                else:
                    filename = None
            return filename

        # custom exceptions
        class DataIsObject(Exception): pass

        opts,args = self.parse_options(parameter_s,'prxn:')
        # Set a few locals from the options for convenience:
        opts_p = opts.has_key('p')
        opts_r = opts.has_key('r')
        
        # Default line number value
        lineno = opts.get('n',None)

        if opts_p:
            args = '_%s' % last_call[0]
            if not self.shell.user_ns.has_key(args):
                args = last_call[1]
            
        # use last_call to remember the state of the previous call, but don't
        # let it be clobbered by successive '-p' calls.
        try:
            last_call[0] = self.shell.outputcache.prompt_count
            if not opts_p:
                last_call[1] = parameter_s
        except:
            pass

        # by default this is done with temp files, except when the given
        # arg is a filename
        use_temp = 1

        if re.match(r'\d',args):
            # Mode where user specifies ranges of lines, like in %macro.
            # This means that you can't edit files whose names begin with
            # numbers this way. Tough.
            ranges = args.split()
            data = ''.join(self.extract_input_slices(ranges,opts_r))
        elif args.endswith('.py'):
            filename = make_filename(args)
            data = ''
            use_temp = 0
        elif args:
            try:
                # Load the parameter given as a variable. If not a string,
                # process it as an object instead (below)

                #print '*** args',args,'type',type(args)  # dbg
                data = eval(args,self.shell.user_ns)
                if not type(data) in StringTypes:
                    raise DataIsObject

            except (NameError,SyntaxError):
                # given argument is not a variable, try as a filename
                filename = make_filename(args)
                if filename is None:
                    warn("Argument given (%s) can't be found as a variable "
                         "or as a filename." % args)
                    return

                data = ''
                use_temp = 0
            except DataIsObject:

                # macros have a special edit function
                if isinstance(data,Macro):
                    self._edit_macro(args,data)
                    return
                                
                # For objects, try to edit the file where they are defined
                try:
                    filename = inspect.getabsfile(data)
                    if 'fakemodule' in filename.lower() and inspect.isclass(data):                     
                        # class created by %edit? Try to find source
                        # by looking for method definitions instead, the
                        # __module__ in those classes is FakeModule.
                        attrs = [getattr(data, aname) for aname in dir(data)]
                        for attr in attrs:
                            if not inspect.ismethod(attr):
                                continue
                            filename = inspect.getabsfile(attr)
                            if filename and 'fakemodule' not in filename.lower():
                                # change the attribute to be the edit target instead
                                data = attr 
                                break
                    
                    datafile = 1
                except TypeError:
                    filename = make_filename(args)
                    datafile = 1
                    warn('Could not find file where `%s` is defined.\n'
                         'Opening a file named `%s`' % (args,filename))
                # Now, make sure we can actually read the source (if it was in
                # a temp file it's gone by now).
                if datafile:
                    try:
                        if lineno is None:
                            lineno = inspect.getsourcelines(data)[1]
                    except IOError:
                        filename = make_filename(args)
                        if filename is None:
                            warn('The file `%s` where `%s` was defined cannot '
                                 'be read.' % (filename,data))
                            return
                use_temp = 0
        else:
            data = ''

        if use_temp:
            filename = self.shell.mktempfile(data)
            print 'IPython will make a temporary file named:',filename

        # do actual editing here
        print 'Editing...',
        sys.stdout.flush()
        self.shell.hooks.editor(filename,lineno)
        if opts.has_key('x'):  # -x prevents actual execution
            print
        else:
            print 'done. Executing edited code...'
            if opts_r:
                self.shell.runlines(file_read(filename))
            else:
                self.shell.safe_execfile(filename,self.shell.user_ns,
                                         self.shell.user_ns)
        if use_temp:
            try:
                return open(filename).read()
            except IOError,msg:
                if msg.filename == filename:
                    warn('File not found. Did you forget to save?')
                    return
                else:
                    self.shell.showtraceback()

    def magic_xmode(self,parameter_s = ''):
        """Switch modes for the exception handlers.

        Valid modes: Plain, Context and Verbose.

        If called without arguments, acts as a toggle."""

        def xmode_switch_err(name):
            warn('Error changing %s exception modes.\n%s' %
                 (name,sys.exc_info()[1]))

        shell = self.shell
        new_mode = parameter_s.strip().capitalize()
        try:
            shell.InteractiveTB.set_mode(mode=new_mode)
            print 'Exception reporting mode:',shell.InteractiveTB.mode
        except:
            xmode_switch_err('user')

        # threaded shells use a special handler in sys.excepthook
        if shell.isthreaded:
            try:
                shell.sys_excepthook.set_mode(mode=new_mode)
            except:
                xmode_switch_err('threaded')
            
    def magic_colors(self,parameter_s = ''):
        """Switch color scheme for prompts, info system and exception handlers.

        Currently implemented schemes: NoColor, Linux, LightBG.

        Color scheme names are not case-sensitive."""

        def color_switch_err(name):
            warn('Error changing %s color schemes.\n%s' %
                 (name,sys.exc_info()[1]))
            
        
        new_scheme = parameter_s.strip()
        if not new_scheme:
            raise UsageError(
                "%colors: you must specify a color scheme. See '%colors?'")
            return
        # local shortcut
        shell = self.shell

        import IPython.rlineimpl as readline

        if not readline.have_readline and sys.platform == "win32":
            msg = """\
Proper color support under MS Windows requires the pyreadline library.
You can find it at:
http://ipython.scipy.org/moin/PyReadline/Intro
Gary's readline needs the ctypes module, from:
http://starship.python.net/crew/theller/ctypes
(Note that ctypes is already part of Python versions 2.5 and newer).

Defaulting color scheme to 'NoColor'"""
            new_scheme = 'NoColor'
            warn(msg)
        
        # readline option is 0
        if not shell.has_readline:
            new_scheme = 'NoColor'
            
        # Set prompt colors
        try:
            shell.outputcache.set_colors(new_scheme)
        except:
            color_switch_err('prompt')
        else:
            shell.rc.colors = \
                       shell.outputcache.color_table.active_scheme_name
        # Set exception colors
        try:
            shell.InteractiveTB.set_colors(scheme = new_scheme)
            shell.SyntaxTB.set_colors(scheme = new_scheme)
        except:
            color_switch_err('exception')

        # threaded shells use a verbose traceback in sys.excepthook
        if shell.isthreaded:
            try:
                shell.sys_excepthook.set_colors(scheme=new_scheme)
            except:
                color_switch_err('system exception handler')
        
        # Set info (for 'object?') colors
        if shell.rc.color_info:
            try:
                shell.inspector.set_active_scheme(new_scheme)
            except:
                color_switch_err('object inspector')
        else:
            shell.inspector.set_active_scheme('NoColor')
                
    def magic_color_info(self,parameter_s = ''):
        """Toggle color_info.

        The color_info configuration parameter controls whether colors are
        used for displaying object details (by things like %psource, %pfile or
        the '?' system). This function toggles this value with each call.

        Note that unless you have a fairly recent pager (less works better
        than more) in your system, using colored object information displays
        will not work properly. Test it and see."""
        
        self.shell.rc.color_info = 1 - self.shell.rc.color_info
        self.magic_colors(self.shell.rc.colors)
        print 'Object introspection functions have now coloring:',
        print ['OFF','ON'][self.shell.rc.color_info]

    def magic_Pprint(self, parameter_s=''):
        """Toggle pretty printing on/off."""
        
        self.shell.rc.pprint = 1 - self.shell.rc.pprint
        print 'Pretty printing has been turned', \
              ['OFF','ON'][self.shell.rc.pprint]
        
    def magic_exit(self, parameter_s=''):
        """Exit IPython, confirming if configured to do so.

        You can configure whether IPython asks for confirmation upon exit by
        setting the confirm_exit flag in the ipythonrc file."""

        self.shell.exit()

    def magic_quit(self, parameter_s=''):
        """Exit IPython, confirming if configured to do so (like %exit)"""

        self.shell.exit()
        
    def magic_Exit(self, parameter_s=''):
        """Exit IPython without confirmation."""

        self.shell.ask_exit()

    #......................................................................
    # Functions to implement unix shell-type things

    @testdec.skip_doctest
    def magic_alias(self, parameter_s = ''):
        """Define an alias for a system command.

        '%alias alias_name cmd' defines 'alias_name' as an alias for 'cmd'

        Then, typing 'alias_name params' will execute the system command 'cmd
        params' (from your underlying operating system).

        Aliases have lower precedence than magic functions and Python normal
        variables, so if 'foo' is both a Python variable and an alias, the
        alias can not be executed until 'del foo' removes the Python variable.

        You can use the %l specifier in an alias definition to represent the
        whole line when the alias is called.  For example:

          In [2]: alias all echo "Input in brackets: <%l>"
          In [3]: all hello world
          Input in brackets: <hello world>

        You can also define aliases with parameters using %s specifiers (one
        per parameter):
        
          In [1]: alias parts echo first %s second %s
          In [2]: %parts A B
          first A second B
          In [3]: %parts A
          Incorrect number of arguments: 2 expected.
          parts is an alias to: 'echo first %s second %s'

        Note that %l and %s are mutually exclusive.  You can only use one or
        the other in your aliases.

        Aliases expand Python variables just like system calls using ! or !! 
        do: all expressions prefixed with '$' get expanded.  For details of
        the semantic rules, see PEP-215:
        http://www.python.org/peps/pep-0215.html.  This is the library used by
        IPython for variable expansion.  If you want to access a true shell
        variable, an extra $ is necessary to prevent its expansion by IPython:

        In [6]: alias show echo
        In [7]: PATH='A Python string'
        In [8]: show $PATH
        A Python string
        In [9]: show $$PATH
        /usr/local/lf9560/bin:/usr/local/intel/compiler70/ia32/bin:...

        You can use the alias facility to acess all of $PATH.  See the %rehash
        and %rehashx functions, which automatically create aliases for the
        contents of your $PATH.

        If called with no parameters, %alias prints the current alias table."""

        par = parameter_s.strip()
        if not par:
            stored = self.db.get('stored_aliases', {} )
            atab = self.shell.alias_table
            aliases = atab.keys()
            aliases.sort()
            res = []
            showlast = []
            for alias in aliases:
                special = False
                try:
                    tgt = atab[alias][1]
                except (TypeError, AttributeError):
                    # unsubscriptable? probably a callable
                    tgt = atab[alias]
                    special = True
                # 'interesting' aliases
                if (alias in stored or
                    special or 
                    alias.lower() != os.path.splitext(tgt)[0].lower() or
                    ' ' in tgt):
                    showlast.append((alias, tgt))
                else:
                    res.append((alias, tgt ))                
            
            # show most interesting aliases last
            res.extend(showlast)
            print "Total number of aliases:",len(aliases)
            return res
        try:
            alias,cmd = par.split(None,1)
        except:
            print OInspect.getdoc(self.magic_alias)
        else:
            nargs = cmd.count('%s')
            if nargs>0 and cmd.find('%l')>=0:
                error('The %s and %l specifiers are mutually exclusive '
                      'in alias definitions.')
            else:  # all looks OK
                self.shell.alias_table[alias] = (nargs,cmd)
                self.shell.alias_table_validate(verbose=0)
    # end magic_alias

    def magic_unalias(self, parameter_s = ''):
        """Remove an alias"""

        aname = parameter_s.strip()
        if aname in self.shell.alias_table:
            del self.shell.alias_table[aname]
        stored = self.db.get('stored_aliases', {} )
        if aname in stored:
            print "Removing %stored alias",aname
            del stored[aname]
            self.db['stored_aliases'] = stored
            

    def magic_rehashx(self, parameter_s = ''):
        """Update the alias table with all executable files in $PATH.

        This version explicitly checks that every entry in $PATH is a file
        with execute access (os.X_OK), so it is much slower than %rehash.

        Under Windows, it checks executability as a match agains a
        '|'-separated string of extensions, stored in the IPython config
        variable win_exec_ext.  This defaults to 'exe|com|bat'.
        
        This function also resets the root module cache of module completer,
        used on slow filesystems.
        """
        
        
        ip = self.api

        # for the benefit of module completer in ipy_completers.py
        del ip.db['rootmodules']
        
        path = [os.path.abspath(os.path.expanduser(p)) for p in 
            os.environ.get('PATH','').split(os.pathsep)]
        path = filter(os.path.isdir,path)
        
        alias_table = self.shell.alias_table
        syscmdlist = []
        if os.name == 'posix':
            isexec = lambda fname:os.path.isfile(fname) and \
                     os.access(fname,os.X_OK)
        else:

            try:
                winext = os.environ['pathext'].replace(';','|').replace('.','')
            except KeyError:
                winext = 'exe|com|bat|py'
            if 'py' not in winext:
                winext += '|py'
            execre = re.compile(r'(.*)\.(%s)$' % winext,re.IGNORECASE)
            isexec = lambda fname:os.path.isfile(fname) and execre.match(fname)
        savedir = os.getcwd()
        try:
            # write the whole loop for posix/Windows so we don't have an if in
            # the innermost part
            if os.name == 'posix':
                for pdir in path:
                    os.chdir(pdir)
                    for ff in os.listdir(pdir):
                        if isexec(ff) and ff not in self.shell.no_alias:
                            # each entry in the alias table must be (N,name),
                            # where N is the number of positional arguments of the
                            # alias.
                            alias_table[ff] = (0,ff)
                            syscmdlist.append(ff)
            else:
                for pdir in path:
                    os.chdir(pdir)
                    for ff in os.listdir(pdir):
                        base, ext = os.path.splitext(ff)
                        if isexec(ff) and base.lower() not in self.shell.no_alias:
                            if ext.lower() == '.exe':
                                ff = base
                            alias_table[base.lower()] = (0,ff)
                            syscmdlist.append(ff)
            # Make sure the alias table doesn't contain keywords or builtins
            self.shell.alias_table_validate()
            # Call again init_auto_alias() so we get 'rm -i' and other
            # modified aliases since %rehashx will probably clobber them
            
            # no, we don't want them. if %rehashx clobbers them, good,
            # we'll probably get better versions
            # self.shell.init_auto_alias()
            db = ip.db
            db['syscmdlist'] = syscmdlist
        finally:
            os.chdir(savedir)
        
    def magic_pwd(self, parameter_s = ''):
        """Return the current working directory path."""
        return os.getcwd()

    def magic_cd(self, parameter_s=''):
        """Change the current working directory.

        This command automatically maintains an internal list of directories
        you visit during your IPython session, in the variable _dh. The
        command %dhist shows this history nicely formatted. You can also
        do 'cd -<tab>' to see directory history conveniently.

        Usage:

          cd 'dir': changes to directory 'dir'.

          cd -: changes to the last visited directory.

          cd -<n>: changes to the n-th directory in the directory history.

          cd --foo: change to directory that matches 'foo' in history
            
          cd -b <bookmark_name>: jump to a bookmark set by %bookmark
             (note: cd <bookmark_name> is enough if there is no
              directory <bookmark_name>, but a bookmark with the name exists.)
              'cd -b <tab>' allows you to tab-complete bookmark names. 

        Options:

        -q: quiet.  Do not print the working directory after the cd command is
        executed.  By default IPython's cd command does print this directory,
        since the default prompts do not display path information.
        
        Note that !cd doesn't work for this purpose because the shell where
        !command runs is immediately discarded after executing 'command'."""

        parameter_s = parameter_s.strip()
        #bkms = self.shell.persist.get("bookmarks",{})

        oldcwd = os.getcwd()
        numcd = re.match(r'(-)(\d+)$',parameter_s)
        # jump in directory history by number
        if numcd:
            nn = int(numcd.group(2))
            try:
                ps = self.shell.user_ns['_dh'][nn]
            except IndexError:
                print 'The requested directory does not exist in history.'
                return
            else:
                opts = {}
        elif parameter_s.startswith('--'):
            ps = None
            fallback = None
            pat = parameter_s[2:]
            dh = self.shell.user_ns['_dh']
            # first search only by basename (last component)
            for ent in reversed(dh):
                if pat in os.path.basename(ent) and os.path.isdir(ent):
                    ps = ent
                    break
            
                if fallback is None and pat in ent and os.path.isdir(ent):
                    fallback = ent
                
            # if we have no last part match, pick the first full path match
            if ps is None:
                ps = fallback
            
            if ps is None:
                print "No matching entry in directory history"
                return
            else:
                opts = {}
                
            
        else:
            #turn all non-space-escaping backslashes to slashes, 
            # for c:\windows\directory\names\
            parameter_s = re.sub(r'\\(?! )','/', parameter_s)            
            opts,ps = self.parse_options(parameter_s,'qb',mode='string')
        # jump to previous
        if ps == '-':
            try:
                ps = self.shell.user_ns['_dh'][-2]
            except IndexError:
                raise UsageError('%cd -: No previous directory to change to.')
        # jump to bookmark if needed
        else:
            if not os.path.isdir(ps) or opts.has_key('b'):
                bkms = self.db.get('bookmarks', {})
            
                if bkms.has_key(ps):
                    target = bkms[ps]
                    print '(bookmark:%s) -> %s' % (ps,target)
                    ps = target
                else:
                    if opts.has_key('b'):
                        raise UsageError("Bookmark '%s' not found.  "
                              "Use '%%bookmark -l' to see your bookmarks." % ps)
            
        # at this point ps should point to the target dir
        if ps:
            try:                
                os.chdir(os.path.expanduser(ps))
                if self.shell.rc.term_title:
                    #print 'set term title:',self.shell.rc.term_title  # dbg
                    platutils.set_term_title('IPy ' + abbrev_cwd())
            except OSError:
                print sys.exc_info()[1]
            else:
                cwd = os.getcwd()
                dhist = self.shell.user_ns['_dh']
                if oldcwd != cwd:
                    dhist.append(cwd)
                    self.db['dhist'] = compress_dhist(dhist)[-100:]
                
        else:
            os.chdir(self.shell.home_dir)
            if self.shell.rc.term_title:
                platutils.set_term_title("IPy ~")
            cwd = os.getcwd()
            dhist = self.shell.user_ns['_dh']
            
            if oldcwd != cwd:
                dhist.append(cwd)
                self.db['dhist'] = compress_dhist(dhist)[-100:]
        if not 'q' in opts and self.shell.user_ns['_dh']:
            print self.shell.user_ns['_dh'][-1]


    def magic_env(self, parameter_s=''):
        """List environment variables."""
        
        return os.environ.data

    def magic_pushd(self, parameter_s=''):
        """Place the current dir on stack and change directory.
        
        Usage:\\
          %pushd ['dirname']
        """
        
        dir_s = self.shell.dir_stack
        tgt = os.path.expanduser(parameter_s)
        cwd = os.getcwd().replace(self.home_dir,'~')
        if tgt:
            self.magic_cd(parameter_s)
        dir_s.insert(0,cwd)
        return self.magic_dirs()

    def magic_popd(self, parameter_s=''):
        """Change to directory popped off the top of the stack.
        """
        if not self.shell.dir_stack:
            raise UsageError("%popd on empty stack")
        top = self.shell.dir_stack.pop(0)
        self.magic_cd(top)
        print "popd ->",top

    def magic_dirs(self, parameter_s=''):
        """Return the current directory stack."""

        return self.shell.dir_stack

    def magic_dhist(self, parameter_s=''):
        """Print your history of visited directories.

        %dhist       -> print full history\\
        %dhist n     -> print last n entries only\\
        %dhist n1 n2 -> print entries between n1 and n2 (n1 not included)\\

        This history is automatically maintained by the %cd command, and
        always available as the global list variable _dh. You can use %cd -<n>
        to go to directory number <n>.
        
        Note that most of time, you should view directory history by entering
        cd -<TAB>.
        
        """

        dh = self.shell.user_ns['_dh']
        if parameter_s:
            try:
                args = map(int,parameter_s.split())
            except:
                self.arg_err(Magic.magic_dhist)
                return
            if len(args) == 1:
                ini,fin = max(len(dh)-(args[0]),0),len(dh)
            elif len(args) == 2:
                ini,fin = args
            else:
                self.arg_err(Magic.magic_dhist)
                return
        else:
            ini,fin = 0,len(dh)
        nlprint(dh,
                header = 'Directory history (kept in _dh)',
                start=ini,stop=fin)

    @testdec.skip_doctest
    def magic_sc(self, parameter_s=''):
        """Shell capture - execute a shell command and capture its output.

        DEPRECATED. Suboptimal, retained for backwards compatibility.
        
        You should use the form 'var = !command' instead. Example:
         
         "%sc -l myfiles = ls ~" should now be written as
            
         "myfiles = !ls ~"
         
        myfiles.s, myfiles.l and myfiles.n still apply as documented
        below.

        --
        %sc [options] varname=command

        IPython will run the given command using commands.getoutput(), and
        will then update the user's interactive namespace with a variable
        called varname, containing the value of the call.  Your command can
        contain shell wildcards, pipes, etc.

        The '=' sign in the syntax is mandatory, and the variable name you
        supply must follow Python's standard conventions for valid names.
        
        (A special format without variable name exists for internal use)

        Options:

          -l: list output.  Split the output on newlines into a list before
          assigning it to the given variable.  By default the output is stored
          as a single string.

          -v: verbose.  Print the contents of the variable.

        In most cases you should not need to split as a list, because the
        returned value is a special type of string which can automatically
        provide its contents either as a list (split on newlines) or as a
        space-separated string.  These are convenient, respectively, either
        for sequential processing or to be passed to a shell command.

        For example:

        # all-random
        
            # Capture into variable a
            In [1]: sc a=ls *py

            # a is a string with embedded newlines
            In [2]: a
            Out[2]: 'setup.py\\nwin32_manual_post_install.py'

            # which can be seen as a list:
            In [3]: a.l
            Out[3]: ['setup.py', 'win32_manual_post_install.py']

            # or as a whitespace-separated string:
            In [4]: a.s
            Out[4]: 'setup.py win32_manual_post_install.py'

            # a.s is useful to pass as a single command line:
            In [5]: !wc -l $a.s
              146 setup.py
              130 win32_manual_post_install.py
              276 total

            # while the list form is useful to loop over:
            In [6]: for f in a.l:
              ...:      !wc -l $f
              ...:
            146 setup.py
            130 win32_manual_post_install.py

        Similiarly, the lists returned by the -l option are also special, in
        the sense that you can equally invoke the .s attribute on them to
        automatically get a whitespace-separated string from their contents:

            In [7]: sc -l b=ls *py

            In [8]: b
            Out[8]: ['setup.py', 'win32_manual_post_install.py']

            In [9]: b.s
            Out[9]: 'setup.py win32_manual_post_install.py'

        In summary, both the lists and strings used for ouptut capture have
        the following special attributes:

            .l (or .list) : value as list.
            .n (or .nlstr): value as newline-separated string.
            .s (or .spstr): value as space-separated string.
        """

        opts,args = self.parse_options(parameter_s,'lv')
        # Try to get a variable name and command to run
        try:
            # the variable name must be obtained from the parse_options
            # output, which uses shlex.split to strip options out.
            var,_ = args.split('=',1)
            var = var.strip()
            # But the the command has to be extracted from the original input
            # parameter_s, not on what parse_options returns, to avoid the
            # quote stripping which shlex.split performs on it.
            _,cmd = parameter_s.split('=',1)
        except ValueError:
            var,cmd = '',''
        # If all looks ok, proceed
        out,err = self.shell.getoutputerror(cmd)
        if err:
            print >> Term.cerr,err
        if opts.has_key('l'):
            out = SList(out.split('\n'))
        else:
            out = LSString(out)
        if opts.has_key('v'):
            print '%s ==\n%s' % (var,pformat(out))
        if var:
            self.shell.user_ns.update({var:out})
        else:
            return out

    def magic_sx(self, parameter_s=''):
        """Shell execute - run a shell command and capture its output.

        %sx command

        IPython will run the given command using commands.getoutput(), and
        return the result formatted as a list (split on '\\n').  Since the
        output is _returned_, it will be stored in ipython's regular output
        cache Out[N] and in the '_N' automatic variables.

        Notes:

        1) If an input line begins with '!!', then %sx is automatically
        invoked.  That is, while:
          !ls
        causes ipython to simply issue system('ls'), typing
          !!ls
        is a shorthand equivalent to:
          %sx ls
        
        2) %sx differs from %sc in that %sx automatically splits into a list,
        like '%sc -l'.  The reason for this is to make it as easy as possible
        to process line-oriented shell output via further python commands.
        %sc is meant to provide much finer control, but requires more
        typing.

        3) Just like %sc -l, this is a list with special attributes:

          .l (or .list) : value as list.
          .n (or .nlstr): value as newline-separated string.
          .s (or .spstr): value as whitespace-separated string.

        This is very useful when trying to use such lists as arguments to
        system commands."""

        if parameter_s:
            out,err = self.shell.getoutputerror(parameter_s)
            if err:
                print >> Term.cerr,err
            return SList(out.split('\n'))

    def magic_bg(self, parameter_s=''):
        """Run a job in the background, in a separate thread.

        For example,

          %bg myfunc(x,y,z=1)

        will execute 'myfunc(x,y,z=1)' in a background thread.  As soon as the
        execution starts, a message will be printed indicating the job
        number.  If your job number is 5, you can use

          myvar = jobs.result(5)  or  myvar = jobs[5].result

        to assign this result to variable 'myvar'.

        IPython has a job manager, accessible via the 'jobs' object.  You can
        type jobs? to get more information about it, and use jobs.<TAB> to see
        its attributes.  All attributes not starting with an underscore are
        meant for public use.

        In particular, look at the jobs.new() method, which is used to create
        new jobs.  This magic %bg function is just a convenience wrapper
        around jobs.new(), for expression-based jobs.  If you want to create a
        new job with an explicit function object and arguments, you must call
        jobs.new() directly.

        The jobs.new docstring also describes in detail several important
        caveats associated with a thread-based model for background job
        execution.  Type jobs.new? for details.

        You can check the status of all jobs with jobs.status().

        The jobs variable is set by IPython into the Python builtin namespace.
        If you ever declare a variable named 'jobs', you will shadow this
        name.  You can either delete your global jobs variable to regain
        access to the job manager, or make a new name and assign it manually
        to the manager (stored in IPython's namespace).  For example, to
        assign the job manager to the Jobs name, use:

          Jobs = __builtins__.jobs"""
        
        self.shell.jobs.new(parameter_s,self.shell.user_ns)
        
    def magic_r(self, parameter_s=''):
        """Repeat previous input.

        Note: Consider using the more powerfull %rep instead!
        
        If given an argument, repeats the previous command which starts with
        the same string, otherwise it just repeats the previous input.

        Shell escaped commands (with ! as first character) are not recognized
        by this system, only pure python code and magic commands.
        """

        start = parameter_s.strip()
        esc_magic = self.shell.ESC_MAGIC
        # Identify magic commands even if automagic is on (which means
        # the in-memory version is different from that typed by the user).
        if self.shell.rc.automagic:
            start_magic = esc_magic+start
        else:
            start_magic = start
        # Look through the input history in reverse
        for n in range(len(self.shell.input_hist)-2,0,-1):
            input = self.shell.input_hist[n]
            # skip plain 'r' lines so we don't recurse to infinity
            if input != '_ip.magic("r")\n' and \
                   (input.startswith(start) or input.startswith(start_magic)):
                #print 'match',`input`  # dbg
                print 'Executing:',input,
                self.shell.runlines(input)
                return
        print 'No previous input matching `%s` found.' % start

    
    def magic_bookmark(self, parameter_s=''):
        """Manage IPython's bookmark system.

        %bookmark <name>       - set bookmark to current dir
        %bookmark <name> <dir> - set bookmark to <dir>
        %bookmark -l           - list all bookmarks
        %bookmark -d <name>    - remove bookmark
        %bookmark -r           - remove all bookmarks

        You can later on access a bookmarked folder with:
          %cd -b <name>
        or simply '%cd <name>' if there is no directory called <name> AND
        there is such a bookmark defined.

        Your bookmarks persist through IPython sessions, but they are
        associated with each profile."""

        opts,args = self.parse_options(parameter_s,'drl',mode='list')
        if len(args) > 2:
            raise UsageError("%bookmark: too many arguments")

        bkms = self.db.get('bookmarks',{})
            
        if opts.has_key('d'):
            try:
                todel = args[0]
            except IndexError:
                raise UsageError(
                    "%bookmark -d: must provide a bookmark to delete")
            else:
                try:
                    del bkms[todel]
                except KeyError:
                    raise UsageError(
                        "%%bookmark -d: Can't delete bookmark '%s'" % todel)

        elif opts.has_key('r'):
            bkms = {}
        elif opts.has_key('l'):
            bks = bkms.keys()
            bks.sort()
            if bks:
                size = max(map(len,bks))
            else:
                size = 0
            fmt = '%-'+str(size)+'s -> %s'
            print 'Current bookmarks:'
            for bk in bks:
                print fmt % (bk,bkms[bk])
        else:
            if not args:
                raise UsageError("%bookmark: You must specify the bookmark name")
            elif len(args)==1:
                bkms[args[0]] = os.getcwd()
            elif len(args)==2:
                bkms[args[0]] = args[1]
        self.db['bookmarks'] = bkms

    def magic_pycat(self, parameter_s=''):
        """Show a syntax-highlighted file through a pager.

        This magic is similar to the cat utility, but it will assume the file
        to be Python source and will show it with syntax highlighting. """
        
        try:
            filename = get_py_filename(parameter_s)
            cont = file_read(filename)
        except IOError:
            try:
                cont = eval(parameter_s,self.user_ns)
            except NameError:
                cont = None
        if cont is None:
            print "Error: no such file or variable"
            return
            
        page(self.shell.pycolorize(cont),
             screen_lines=self.shell.rc.screen_length)

    def magic_cpaste(self, parameter_s=''):
        """Allows you to paste & execute a pre-formatted code block from clipboard.
        
        You must terminate the block with '--' (two minus-signs) alone on the
        line. You can also provide your own sentinel with '%paste -s %%' ('%%' 
        is the new sentinel for this operation)
        
        The block is dedented prior to execution to enable execution of method
        definitions. '>' and '+' characters at the beginning of a line are
        ignored, to allow pasting directly from e-mails, diff files and
        doctests (the '...' continuation prompt is also stripped).  The
        executed block is also assigned to variable named 'pasted_block' for
        later editing with '%edit pasted_block'.
        
        You can also pass a variable name as an argument, e.g. '%cpaste foo'.
        This assigns the pasted block to variable 'foo' as string, without 
        dedenting or executing it (preceding >>> and + is still stripped)
        
        Do not be alarmed by garbled output on Windows (it's a readline bug). 
        Just press enter and type -- (and press enter again) and the block 
        will be what was just pasted.
        
        IPython statements (magics, shell escapes) are not supported (yet).
        """
        opts,args = self.parse_options(parameter_s,'s:',mode='string')
        par = args.strip()
        sentinel = opts.get('s','--')

        # Regular expressions that declare text we strip from the input:
        strip_re =  [r'^\s*In \[\d+\]:', # IPython input prompt
                     r'^\s*(\s?>)+', # Python input prompt
                     r'^\s*\.{3,}', # Continuation prompts
                     r'^\++',
                     ]

        strip_from_start = map(re.compile,strip_re)
        
        from IPython import iplib
        lines = []
        print "Pasting code; enter '%s' alone on the line to stop." % sentinel
        while 1:
            l = iplib.raw_input_original(':')
            if l ==sentinel:
                break
            
            for pat in strip_from_start: 
                l = pat.sub('',l)
            lines.append(l)
                         
        block = "\n".join(lines) + '\n'
        #print "block:\n",block
        if not par:
            b = textwrap.dedent(block)
            exec b in self.user_ns            
            self.user_ns['pasted_block'] = b
        else:
            self.user_ns[par] = SList(block.splitlines())
            print "Block assigned to '%s'" % par
            
    def magic_quickref(self,arg):
        """ Show a quick reference sheet """
        import IPython.usage
        qr = IPython.usage.quick_reference + self.magic_magic('-brief')
        
        page(qr)
        
    def magic_upgrade(self,arg):
        """ Upgrade your IPython installation
        
        This will copy the config files that don't yet exist in your 
        ipython dir from the system config dir. Use this after upgrading 
        IPython if you don't wish to delete your .ipython dir.

        Call with -nolegacy to get rid of ipythonrc* files (recommended for
        new users)

        """
        ip = self.getapi()
        ipinstallation = path(IPython.__file__).dirname()
        upgrade_script = '%s "%s"' % (sys.executable,ipinstallation / 'upgrade_dir.py')
        src_config = ipinstallation / 'UserConfig'
        userdir = path(ip.options.ipythondir)
        cmd = '%s "%s" "%s"' % (upgrade_script, src_config, userdir)
        print ">",cmd
        shell(cmd)
        if arg == '-nolegacy':
            legacy = userdir.files('ipythonrc*')
            print "Nuking legacy files:",legacy
            
            [p.remove() for p in legacy]
            suffix = (sys.platform == 'win32' and '.ini' or '')
            (userdir / ('ipythonrc' + suffix)).write_text('# Empty, see ipy_user_conf.py\n')


    def magic_doctest_mode(self,parameter_s=''):
        """Toggle doctest mode on and off.

        This mode allows you to toggle the prompt behavior between normal
        IPython prompts and ones that are as similar to the default IPython
        interpreter as possible.

        It also supports the pasting of code snippets that have leading '>>>'
        and '...' prompts in them.  This means that you can paste doctests from
        files or docstrings (even if they have leading whitespace), and the
        code will execute correctly.  You can then use '%history -tn' to see
        the translated history without line numbers; this will give you the
        input after removal of all the leading prompts and whitespace, which
        can be pasted back into an editor.

        With these features, you can switch into this mode easily whenever you
        need to do testing and changes to doctests, without having to leave
        your existing IPython session.
        """

        # XXX - Fix this to have cleaner activate/deactivate calls.
        from IPython.Extensions import InterpreterPasteInput as ipaste
        from IPython.ipstruct import Struct

        # Shorthands
        shell = self.shell
        oc = shell.outputcache
        rc = shell.rc
        meta = shell.meta
        # dstore is a data store kept in the instance metadata bag to track any
        # changes we make, so we can undo them later.
        dstore = meta.setdefault('doctest_mode',Struct())
        save_dstore = dstore.setdefault

        # save a few values we'll need to recover later
        mode = save_dstore('mode',False)
        save_dstore('rc_pprint',rc.pprint)
        save_dstore('xmode',shell.InteractiveTB.mode)
        save_dstore('rc_separate_out',rc.separate_out)
        save_dstore('rc_separate_out2',rc.separate_out2)
        save_dstore('rc_prompts_pad_left',rc.prompts_pad_left)
        save_dstore('rc_separate_in',rc.separate_in)

        if mode == False:
            # turn on
            ipaste.activate_prefilter()

            oc.prompt1.p_template = '>>> '
            oc.prompt2.p_template = '... '
            oc.prompt_out.p_template = ''

            # Prompt separators like plain python
            oc.input_sep = oc.prompt1.sep = ''
            oc.output_sep = ''
            oc.output_sep2 = ''

            oc.prompt1.pad_left = oc.prompt2.pad_left = \
                                  oc.prompt_out.pad_left = False

            rc.pprint = False

            shell.magic_xmode('Plain')

        else:
            # turn off
            ipaste.deactivate_prefilter()

            oc.prompt1.p_template = rc.prompt_in1
            oc.prompt2.p_template = rc.prompt_in2
            oc.prompt_out.p_template = rc.prompt_out

            oc.input_sep = oc.prompt1.sep = dstore.rc_separate_in

            oc.output_sep = dstore.rc_separate_out
            oc.output_sep2 = dstore.rc_separate_out2

            oc.prompt1.pad_left = oc.prompt2.pad_left = \
                         oc.prompt_out.pad_left = dstore.rc_prompts_pad_left

            rc.pprint = dstore.rc_pprint

            shell.magic_xmode(dstore.xmode)

        # Store new mode and inform
        dstore.mode = bool(1-int(mode))
        print 'Doctest mode is:',
        print ['OFF','ON'][dstore.mode]

# end Magic

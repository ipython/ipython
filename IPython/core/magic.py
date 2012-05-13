# encoding: utf-8
"""Magic functions for InteractiveShell.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#  Copyright (C) 2001 Fernando Perez <fperez@colorado.edu>
#  Copyright (C) 2008 The IPython Development Team

#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# Stdlib
import os
import re
import sys
from getopt import getopt, GetoptError

# Our own
from IPython.config.configurable import Configurable
from IPython.core import oinspect
from IPython.core.error import UsageError
from IPython.core.prefilter import ESC_MAGIC
from IPython.external.decorator import decorator
from IPython.utils.ipstruct import Struct
from IPython.utils.process import arg_split
from IPython.utils.traitlets import Dict, Enum, Instance
from IPython.utils.warn import error

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------
line_magics = {}
cell_magics = {}

#-----------------------------------------------------------------------------
# Utility classes and functions
#-----------------------------------------------------------------------------

class Bunch: pass


# Used for exception handling in magic_edit
class MacroToEdit(ValueError): pass


def on_off(tag):
    """Return an ON/OFF string for a 1/0 input. Simple utility function."""
    return ['OFF','ON'][tag]


def compress_dhist(dh):
    head, tail = dh[:-10], dh[-10:]

    newhead = []
    done = set()
    for h in head:
        if h in done:
            continue
        newhead.append(h)
        done.add(h)

    return newhead + tail


def needs_local_scope(func):
    """Decorator to mark magic functions which need to local scope to run."""
    func.needs_local_scope = True
    return func

#-----------------------------------------------------------------------------
# Class and method decorators for registering magics
#-----------------------------------------------------------------------------

def register_magics(cls):
    global line_magics, cell_magics

    cls.line_magics = line_magics
    cls.cell_magics = cell_magics
    cls.registered = True
    line_magics = {}
    cell_magics = {}
    return cls


def _magic_marker(magic_type):
    global line_magics, cell_magics

    if magic_type not in ('line', 'cell'):
        raise ValueError('magic_type must be one of ["line", "cell"], %s given'
                         % magic_type)
    if magic_type == 'line':
        line_magics = {}
    else:
        cell_magics = {}

    # This is a closure to capture the magic_type.  We could also use a class,
    # but it's overkill for just that one bit of state.
    def magic_deco(arg):
        global line_magics, cell_magics
        call = lambda f, *a, **k: f(*a, **k)

        if callable(arg):
            # "Naked" decorator call (just @foo, no args)
            func = arg
            name = func.func_name
            func.magic_name = name
            retval = decorator(call, func)
        elif isinstance(arg, basestring):
            # Decorator called with arguments (@foo('bar'))
            name = arg
            def mark(func, *a, **kw):
                func.magic_name = name
                return decorator(call, func)
            retval = mark
        else:
            raise ValueError("Decorator can only be called with "
                             "string or function")
        # Record the magic function in the global table that will then be
        # appended to the class via the register_magics class decorator
        if magic_type == 'line':
            line_magics[name] = retval
        else:
            cell_magics[name] = retval

        return retval

    return magic_deco


line_magic = _magic_marker('line')
cell_magic = _magic_marker('cell')

#-----------------------------------------------------------------------------
# Core Magic classes
#-----------------------------------------------------------------------------

class MagicManager(Configurable):
    """Object that handles all magic-related functionality for IPython.
    """
    # An instance of the IPython shell we are attached to
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    auto_status = Enum([
        'Automagic is OFF, % prefix IS needed for magic functions.',
        'Automagic is ON, % prefix NOT needed for magic functions.'])

    def __init__(self, shell=None, config=None, **traits):

        super(MagicManager, self).__init__(shell=shell, config=config, **traits)


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
        magics = filter(class_magic, Magic.__dict__.keys()) + \
                 filter(inst_magic, self.__dict__.keys()) + \
                 filter(inst_bound_magic, self.__class__.__dict__.keys())
        out = []
        for fn in set(magics):
            out.append(fn.replace('magic_', '', 1))
        out.sort()
        return out

# Key base class that provides the central functionality for magics.

class Magics(object):
    """Base class for implementing magic functions.

    Shell functions which can be reached as %function_name. All magic
    functions should accept a string, which they can parse for their own
    needs. This can make some functions easier to type, eg `%cd ../`
    vs. `%cd("../")`

    Classes providing magic functions need to subclass this class, and they
    MUST:

    - Use the method decorators `@line_magic` and `@cell_magic` to decorate
    individual methods as magic functions, AND

    - Use the class decorator `@register_magics` to ensure that the magic
    methods are properly registered at the instance level upon instance
    initialization.

    See :mod:`magic_functions` for examples of actual implementation classes.
    """

    options_table = Dict(config=True,
        help = """Dict holding all command-line options for each magic.
        """)

    class __metaclass__(type):
        def __new__(cls, name, bases, dct):
            cls.registered = False
            return type.__new__(cls, name, bases, dct)

    def __init__(self, shell):
        if not(self.__class__.registered):
            raise ValueError('unregistered Magics')
        self.shell = shell

    def arg_err(self,func):
        """Print docstring if incorrect arguments were passed"""
        print 'Error in arguments:'
        print oinspect.getdoc(func)

    def format_latex(self,strng):
        """Format a string for latex inclusion."""

        # Characters that need to be escaped for latex:
        escape_re = re.compile(r'(%|_|\$|#|&)',re.MULTILINE)
        # Magic command names as headers:
        cmd_name_re = re.compile(r'^(%s.*?):' % ESC_MAGIC,
                                 re.MULTILINE)
        # Magic commands
        cmd_re = re.compile(r'(?P<cmd>%s.+?\b)(?!\}\}:)' % ESC_MAGIC,
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

    def parse_options(self, arg_str, opt_str, *long_opts, **kw):
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
        posix = kw.get('posix', os.name == 'posix')
        strict = kw.get('strict', True)

        # Check if we have more than one argument to warrant extra processing:
        odict = {}  # Dictionary with options
        args = arg_str.split()
        if len(args) >= 1:
            # If the list of inputs only has 0 or 1 thing in it, there's no
            # need to look for options
            argv = arg_split(arg_str, posix, strict)
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

    def default_option(self,fn,optstr):
        """Make an entry in the options_table for fn, with value optstr"""

        if fn not in self.lsmagic():
            error("%s is not a magic function" % fn)
        self.options_table[fn] = optstr

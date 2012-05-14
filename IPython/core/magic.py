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
import types
from getopt import getopt, GetoptError

# Our own
from IPython.config.configurable import Configurable
from IPython.core import oinspect
from IPython.core.error import UsageError
from IPython.core.prefilter import ESC_MAGIC
from IPython.external.decorator import decorator
from IPython.utils.ipstruct import Struct
from IPython.utils.process import arg_split
from IPython.utils.traitlets import Bool, Dict, Instance
from IPython.utils.warn import error

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# A dict we'll use for each class that has magics, used as temporary storage to
# pass information between the @line/cell_magic method decorators and the
# @register_magics class decorator, because the method decorators have no
# access to the class when they run.  See for more details:
# http://stackoverflow.com/questions/2366713/can-a-python-decorator-of-an-instance-method-access-the-class

magics = dict(line={}, cell={})

magic_types = ('line', 'cell')

#-----------------------------------------------------------------------------
# Utility classes and functions
#-----------------------------------------------------------------------------

class Bunch: pass


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
    cls.registered = True
    cls.magics = dict(line = magics['line'],
                      cell = magics['cell'])
    magics['line'] = {}
    magics['cell'] = {}
    return cls


def validate_type(magic_type):
    if magic_type not in magic_types:
        raise ValueError('magic_type must be one of %s, %s given' %
                         magic_types, magic_type)


def _magic_marker(magic_type):
    validate_type(magic_type)

    # This is a closure to capture the magic_type.  We could also use a class,
    # but it's overkill for just that one bit of state.
    def magic_deco(arg):
        call = lambda f, *a, **k: f(*a, **k)

        if callable(arg):
            # "Naked" decorator call (just @foo, no args)
            func = arg
            name = func.func_name
            func.magic_name = name
            retval = decorator(call, func)
            magics[magic_type][name] = name
        elif isinstance(arg, basestring):
            # Decorator called with arguments (@foo('bar'))
            name = arg
            def mark(func, *a, **kw):
                func.magic_name = name
                magics[magic_type][name] = func.func_name
                return decorator(call, func)
            retval = mark
        else:
            raise ValueError("Decorator can only be called with "
                             "string or function")

        return retval

    return magic_deco


line_magic = _magic_marker('line')
cell_magic = _magic_marker('cell')

#-----------------------------------------------------------------------------
# Core Magic classes
#-----------------------------------------------------------------------------

class MagicsManager(Configurable):
    """Object that handles all magic-related functionality for IPython.
    """
    # Non-configurable class attributes
    magics = Dict

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    auto_magic = Bool

    _auto_status = [
        'Automagic is OFF, % prefix IS needed for magic functions.',
        'Automagic is ON, % prefix IS NOT needed for magic functions.']

    user_magics = Instance('IPython.core.magic_functions.UserMagics')

    def __init__(self, shell=None, config=None, user_magics=None, **traits):

        super(MagicsManager, self).__init__(shell=shell, config=config,
                                           user_magics=user_magics, **traits)
        self.magics = dict(line={}, cell={})

    def auto_status(self):
        """Return descriptive string with automagic status."""
        return self._auto_status[self.auto_magic]

    def lsmagic(self):
        """Return a dict of currently available magic functions.

        The return dict has the keys 'line' and 'cell', corresponding to the
        two types of magics we support.  Each value is a list of names.
        """
        return self.magics

    def register(self, *magic_objects):
        """Register one or more instances of Magics.
        """
        # Start by validating them to ensure they have all had their magic
        # methods registered at the instance level
        for m in magic_objects:
            if not m.registered:
                raise ValueError("Class of magics %r was constructed without "
                                 "the @register_macics class decorator")
            if type(m) is type:
                # If we're given an uninstantiated class
                m = m(self.shell)

            for mtype in magic_types:
                self.magics[mtype].update(m.magics[mtype])

    def define_magic(self, magic_name, func, magic_type='line'):
        """Expose own function as magic function for ipython

        Example::

          def foo_impl(self, parameter_s=''):
              'My very own magic!. (Use docstrings, IPython reads them).'
              print 'Magic function. Passed parameter is between < >:'
              print '<%s>' % parameter_s
              print 'The self object is:', self

          ip.define_magic('foo', foo_impl)
        """
        # Create the new method in the user_magics and register it in the
        # global table
        self.user_magics.new_magic(magic_name, func, magic_type)
        self.magics[magic_type][magic_name] = \
          self.user_magics.magics[magic_type][magic_name]

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
    # Dict holding all command-line options for each magic.
    options_table = None
    # Dict for the mapping of magic names to methods, set by class decorator
    magics = None
    # Flag to check that the class decorator was properly applied
    registered = False

    def __init__(self, shell):
        if not(self.__class__.registered):
            raise ValueError('unregistered Magics')
        self.shell = shell
        self.options_table = {}
        mtab = dict(line={}, cell={})
        for mtype in magic_types:
            tab = mtab[mtype]
            for magic_name, meth_name in self.magics[mtype].iteritems():
                if isinstance(meth_name, basestring):
                    tab[magic_name] = getattr(self, meth_name)
        self.magics.update(mtab)

    def arg_err(self,func):
        """Print docstring if incorrect arguments were passed"""
        print 'Error in arguments:'
        print oinspect.getdoc(func)

    def format_latex(self, strng):
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
        caller = sys._getframe(1).f_code.co_name
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

    def default_option(self, fn, optstr):
        """Make an entry in the options_table for fn, with value optstr"""

        if fn not in self.lsmagic():
            error("%s is not a magic function" % fn)
        self.options_table[fn] = optstr

    def new_magic(self, magic_name, func, magic_type='line'):
        """TODO
        """
        validate_type(magic_type)
        meth = types.MethodType(func, self)
        setattr(self, magic_name, meth)
        self.magics[magic_type][magic_name] = meth

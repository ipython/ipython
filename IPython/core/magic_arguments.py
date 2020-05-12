''' A decorator-based method of constructing IPython magics with `argparse`
option handling.

New magic functions can be defined like so::

    from IPython.core.magic_arguments import (argument, magic_arguments,
        parse_argstring)

    @magic_arguments()
    @argument('-o', '--option', help='An optional argument.')
    @argument('arg', type=int, help='An integer positional argument.')
    def magic_cool(self, arg):
        """ A really cool magic command.

    """
        args = parse_argstring(magic_cool, arg)
        ...

The `@magic_arguments` decorator marks the function as having argparse arguments.
The `@argument` decorator adds an argument using the same syntax as argparse's
`add_argument()` method. More sophisticated uses may also require the
`@argument_group` or `@kwds` decorator to customize the formatting and the
parsing.

Help text for the magic is automatically generated from the docstring and the
arguments::

    In[1]: %cool?
        %cool [-o OPTION] arg
        
        A really cool magic command.
        
        positional arguments:
          arg                   An integer positional argument.
        
        optional arguments:
          -o OPTION, --option OPTION
                                An optional argument.

Inheritance diagram:

.. inheritance-diagram:: IPython.core.magic_arguments
   :parts: 3

'''
#-----------------------------------------------------------------------------
# Copyright (C) 2010-2011, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------
import argparse
import re

# Our own imports
from IPython.core.error import UsageError
from IPython.utils.decorators import undoc
from IPython.utils.process import arg_split
from IPython.utils.text import dedent

NAME_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]*$")

@undoc
class MagicHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """A HelpFormatter with a couple of changes to meet our needs.
    """
    # Modified to dedent text.
    def _fill_text(self, text, width, indent):
        return argparse.RawDescriptionHelpFormatter._fill_text(self, dedent(text), width, indent)

    # Modified to wrap argument placeholders in <> where necessary.
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                # IPYTHON MODIFICATION: If args_string is not a plain name, wrap
                # it in <> so it's valid RST.
                if not NAME_RE.match(args_string):
                    args_string = "<%s>" % args_string
                for option_string in action.option_strings:
                    parts.append('%s %s' % (option_string, args_string))

            return ', '.join(parts)

    # Override the default prefix ('usage') to our % magic escape,
    # in a code block.
    def add_usage(self, usage, actions, groups, prefix="::\n\n  %"):
        super(MagicHelpFormatter, self).add_usage(usage, actions, groups, prefix)

class MagicArgumentParser(argparse.ArgumentParser):
    """ An ArgumentParser tweaked for use by IPython magics.
    """
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=None,
                 formatter_class=MagicHelpFormatter,
                 prefix_chars='-',
                 argument_default=None,
                 conflict_handler='error',
                 add_help=False):
        if parents is None:
            parents = []
        super(MagicArgumentParser, self).__init__(prog=prog, usage=usage,
            description=description, epilog=epilog,
            parents=parents, formatter_class=formatter_class,
            prefix_chars=prefix_chars, argument_default=argument_default,
            conflict_handler=conflict_handler, add_help=add_help)

    def error(self, message):
        """ Raise a catchable error instead of exiting.
        """
        raise UsageError(message)

    def parse_argstring(self, argstring):
        """ Split a string into an argument list and parse that argument list.
        """
        argv = arg_split(argstring)
        return self.parse_args(argv)


def construct_parser(magic_func):
    """ Construct an argument parser using the function decorations.
    """
    kwds = getattr(magic_func, 'argcmd_kwds', {})
    if 'description' not in kwds:
        kwds['description'] = getattr(magic_func, '__doc__', None)
    arg_name = real_name(magic_func)
    parser = MagicArgumentParser(arg_name, **kwds)
    # Reverse the list of decorators in order to apply them in the
    # order in which they appear in the source.
    group = None
    for deco in magic_func.decorators[::-1]:
        result = deco.add_to_parser(parser, group)
        if result is not None:
            group = result

    # Replace the magic function's docstring with the full help text.
    magic_func.__doc__ = parser.format_help()

    return parser


def parse_argstring(magic_func, argstring):
    """ Parse the string of arguments for the given magic function.
    """
    return magic_func.parser.parse_argstring(argstring)


def real_name(magic_func):
    """ Find the real name of the magic.
    """
    magic_name = magic_func.__name__
    if magic_name.startswith('magic_'):
        magic_name = magic_name[len('magic_'):]
    return getattr(magic_func, 'argcmd_name', magic_name)


class MagicArgumentDecoratedFunction:
    """Proxy function object returned by @magic_arguments.
    """
    # XXX: This is just for backwards compat with the tests.
    has_arguments = True

    def __init__(self, func):
        self._func = func

        self._decorators = []
        self._name = None

        # Argparse parser. This is lazily initialized on first use.
        self._argparse_parser = None
        self._parser_kwargs = {}

        self._lazy_doc = None

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __get__(self, instance, owner):
        return MagicArgumentDecoratedMethod(self, instance)

    def __getattr__(self, attr):
        return getattr(self._func, attr)

    def add_decorator(self, decorator):
        self._decorators.append(decorator)

    def set_kwds(self, kwds):
        self._parser_kwargs = kwds

    def set_name(self, name):
        self._name = name

    @property
    def __doc__(self):
        if self._lazy_doc is None:
            self._lazy_doc = self.parser.format_help()
        return self._lazy_doc

    @__doc__.setter
    def __doc__(self, value):
        self._lazy_doc = value

    @__doc__.deleter
    def __doc__(self):
        self._lazy_doc = None

    @property
    def decorators(self):
        return self._decorators

    @property
    def parser(self):
        if self._argparse_parser is None:
            self._argparse_parser = self._construct_parser()
        return self._argparse_parser

    # XXX: This is just for backwards compat with the tests
    @property
    def argcmd_name(self):
        if self._name is None:
            raise AttributeError('argcmd_name')
        return self._name

    def _construct_parser(self):
        kwargs = dict(self._parser_kwargs)
        kwargs.setdefault('description', getattr(self._func, '__doc__', None))

        # TODO: Clean this up
        if self._name is not None:
            name = self._name
        else:
            name = self._func.__name__
            if name.startswith('magic_'):
                name = name[len('magic_'):]

        parser = MagicArgumentParser(name, **kwargs)

        # Reverse the list of decorators in order to apply them in the
        # order in which they appear in the source.
        group = None
        for deco in reversed(self._decorators):
            result = deco.add_to_parser(parser, group)
            if result is not None:
                group = result

        return parser


class MagicArgumentDecoratedMethod:

    def __init__(self, func, instance):
        self._func = func
        self._instance = instance

    def __getattr__(self, attr):
        return getattr(self._func, attr)

    def __call__(self, *args, **kwargs):
        return self._func(self._instance, *args, **kwargs)


class ArgDecorator(object):
    """ Base class for decorators to add ArgumentParser information to a method.
    """

    def __call__(self, func):
        if not isinstance(func, MagicArgumentDecoratedFunction):
            func = MagicArgumentDecoratedFunction(func)

        func.add_decorator(self)

        return func

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser, if necessary.
        """
        pass


class magic_arguments(ArgDecorator):
    """ Mark the magic as having argparse arguments and possibly adjust the
    name.
    """

    def __init__(self, name=None):
        self.name = name

    def __call__(self, func):
        wrapped = super().__call__(func)
        wrapped.set_name(self.name)
        return wrapped


class ArgMethodWrapper(ArgDecorator):

    """
    Base class to define a wrapper for ArgumentParser method.

    Child class must define either `_method_name` or `add_to_parser`.

    """

    _method_name = None

    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser.
        """
        if group is not None:
            parser = group
        getattr(parser, self._method_name)(*self.args, **self.kwds)
        return None


class argument(ArgMethodWrapper):
    """ Store arguments and keywords to pass to add_argument().

    Instances also serve to decorate command methods.
    """
    _method_name = 'add_argument'


class defaults(ArgMethodWrapper):
    """ Store arguments and keywords to pass to set_defaults().

    Instances also serve to decorate command methods.
    """
    _method_name = 'set_defaults'


class argument_group(ArgMethodWrapper):
    """ Store arguments and keywords to pass to add_argument_group().

    Instances also serve to decorate command methods.
    """

    def add_to_parser(self, parser, group):
        """ Add this object's information to the parser.
        """
        return parser.add_argument_group(*self.args, **self.kwds)


class kwds(ArgDecorator):
    """ Provide other keywords to the sub-parser constructor.
    """
    def __init__(self, **kwds):
        self.kwds = kwds

    def __call__(self, func):
        func = super().__call__(func)
        func.set_kwds(self.kwds)
        return func


__all__ = ['magic_arguments', 'argument', 'argument_group', 'kwds',
    'parse_argstring']

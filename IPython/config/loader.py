# -*- coding: utf-8 -*-
# coding: utf-8
"""A simple configuration system.

Authors
-------
* Brian Granger
* Fernando Perez
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import os
import sys

from IPython.external import argparse
from IPython.utils.path import filefind

#-----------------------------------------------------------------------------
# Exceptions
#-----------------------------------------------------------------------------


class ConfigError(Exception):
    pass


class ConfigLoaderError(ConfigError):
    pass

#-----------------------------------------------------------------------------
# Argparse fix
#-----------------------------------------------------------------------------

# Unfortunately argparse by default prints help messages to stderr instead of
# stdout.  This makes it annoying to capture long help screens at the command
# line, since one must know how to pipe stderr, which many users don't know how
# to do.  So we override the print_help method with one that defaults to
# stdout and use our class instead.

class ArgumentParser(argparse.ArgumentParser):
    """Simple argparse subclass that prints help to stdout by default."""
    
    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        return super(ArgumentParser, self).print_help(file)
    
    print_help.__doc__ = argparse.ArgumentParser.print_help.__doc__
    
#-----------------------------------------------------------------------------
# Config class for holding config information
#-----------------------------------------------------------------------------


class Config(dict):
    """An attribute based dict that can do smart merges."""

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        # This sets self.__dict__ = self, but it has to be done this way
        # because we are also overriding __setattr__.
        dict.__setattr__(self, '__dict__', self)

    def _merge(self, other):
        to_update = {}
        for k, v in other.iteritems():
            if not self.has_key(k):
                to_update[k] = v
            else: # I have this key
                if isinstance(v, Config):
                    # Recursively merge common sub Configs
                    self[k]._merge(v)
                else:
                    # Plain updates for non-Configs
                    to_update[k] = v

        self.update(to_update)

    def _is_section_key(self, key):
        if key[0].upper()==key[0] and not key.startswith('_'):
            return True
        else:
            return False

    def __contains__(self, key):
        if self._is_section_key(key):
            return True
        else:
            return super(Config, self).__contains__(key)
    # .has_key is deprecated for dictionaries.
    has_key = __contains__

    def _has_section(self, key):
        if self._is_section_key(key):
            if super(Config, self).__contains__(key):
                return True
        return False

    def copy(self):
        return type(self)(dict.copy(self))

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        import copy
        return type(self)(copy.deepcopy(self.items()))

    def __getitem__(self, key):
        # Because we use this for an exec namespace, we need to delegate
        # the lookup of names in __builtin__ to itself.  This means
        # that you can't have section or attribute names that are 
        # builtins.
        try:
            return getattr(__builtin__, key)
        except AttributeError:
            pass
        if self._is_section_key(key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                c = Config()
                dict.__setitem__(self, key, c)
                return c
        else:
            return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        # Don't allow names in __builtin__ to be modified.
        if hasattr(__builtin__, key):
            raise ConfigError('Config variable names cannot have the same name '
                              'as a Python builtin: %s' % key)
        if self._is_section_key(key):
            if not isinstance(value, Config):
                raise ValueError('values whose keys begin with an uppercase '
                                 'char must be Config instances: %r, %r' % (key, value))
        else:
            dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError, e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        try:
            self.__setitem__(key, value)
        except KeyError, e:
            raise AttributeError(e)

    def __delattr__(self, key):
        try:
            dict.__delitem__(self, key)
        except KeyError, e:
            raise AttributeError(e)


#-----------------------------------------------------------------------------
# Config loading classes
#-----------------------------------------------------------------------------


class ConfigLoader(object):
    """A object for loading configurations from just about anywhere.
    
    The resulting configuration is packaged as a :class:`Struct`.
    
    Notes
    -----
    A :class:`ConfigLoader` does one thing: load a config from a source 
    (file, command line arguments) and returns the data as a :class:`Struct`.
    There are lots of things that :class:`ConfigLoader` does not do.  It does
    not implement complex logic for finding config files.  It does not handle
    default values or merge multiple configs.  These things need to be 
    handled elsewhere.
    """

    def __init__(self):
        """A base class for config loaders.
        
        Examples
        --------
        
        >>> cl = ConfigLoader()
        >>> config = cl.load_config()
        >>> config
        {}
        """
        self.clear()

    def clear(self):
        self.config = Config()

    def load_config(self):
        """Load a config from somewhere, return a :class:`Config` instance.
        
        Usually, this will cause self.config to be set and then returned.
        However, in most cases, :meth:`ConfigLoader.clear` should be called
        to erase any previous state.
        """
        self.clear()
        return self.config


class FileConfigLoader(ConfigLoader):
    """A base class for file based configurations.

    As we add more file based config loaders, the common logic should go
    here.
    """
    pass


class PyFileConfigLoader(FileConfigLoader):
    """A config loader for pure python files.
    
    This calls execfile on a plain python file and looks for attributes
    that are all caps.  These attribute are added to the config Struct.
    """

    def __init__(self, filename, path=None):
        """Build a config loader for a filename and path.

        Parameters
        ----------
        filename : str
            The file name of the config file.
        path : str, list, tuple
            The path to search for the config file on, or a sequence of
            paths to try in order.
        """
        super(PyFileConfigLoader, self).__init__()
        self.filename = filename
        self.path = path
        self.full_filename = ''
        self.data = None

    def load_config(self):
        """Load the config from a file and return it as a Struct."""
        self.clear()
        self._find_file()
        self._read_file_as_dict()
        self._convert_to_config()
        return self.config

    def _find_file(self):
        """Try to find the file by searching the paths."""
        self.full_filename = filefind(self.filename, self.path)

    def _read_file_as_dict(self):
        """Load the config file into self.config, with recursive loading."""
        # This closure is made available in the namespace that is used
        # to exec the config file.  This allows users to call
        # load_subconfig('myconfig.py') to load config files recursively.
        # It needs to be a closure because it has references to self.path
        # and self.config.  The sub-config is loaded with the same path
        # as the parent, but it uses an empty config which is then merged
        # with the parents.
        def load_subconfig(fname):
            loader = PyFileConfigLoader(fname, self.path)
            try:
                sub_config = loader.load_config()
            except IOError:
                # Pass silently if the sub config is not there. This happens
                # when a user us using a profile, but not the default config.
                pass
            else:
                self.config._merge(sub_config)

        # Again, this needs to be a closure and should be used in config
        # files to get the config being loaded.
        def get_config():
            return self.config

        namespace = dict(load_subconfig=load_subconfig, get_config=get_config)
        conf_filename = self.full_filename.encode(sys.getfilesystemencoding())
        execfile(conf_filename, namespace)

    def _convert_to_config(self):
        if self.data is None:
            ConfigLoaderError('self.data does not exist')


class CommandLineConfigLoader(ConfigLoader):
    """A config loader for command line arguments.

    As we add more command line based loaders, the common logic should go
    here.
    """


class ArgParseConfigLoader(CommandLineConfigLoader):

    def __init__(self, argv=None, *parser_args, **parser_kw):
        """Create a config loader for use with argparse.

        Parameters
        ----------

        argv : optional, list
          If given, used to read command-line arguments from, otherwise
          sys.argv[1:] is used.

        parser_args : tuple
          A tuple of positional arguments that will be passed to the
          constructor of :class:`argparse.ArgumentParser`.

        parser_kw : dict
          A tuple of keyword arguments that will be passed to the
          constructor of :class:`argparse.ArgumentParser`.
        """
        super(CommandLineConfigLoader, self).__init__()
        if argv == None:
            argv = sys.argv[1:]
        self.argv = argv
        self.parser_args = parser_args
        self.version = parser_kw.pop("version", None)
        kwargs = dict(argument_default=argparse.SUPPRESS)
        kwargs.update(parser_kw)
        self.parser_kw = kwargs

    def load_config(self, args=None):
        """Parse command line arguments and return as a Struct.

        Parameters
        ----------

        args : optional, list
          If given, a list with the structure of sys.argv[1:] to parse
          arguments from. If not given, the instance's self.argv attribute
          (given at construction time) is used."""
        self.clear()
        if args is None:
            args = self.argv
        self._create_parser()
        self._parse_args(args)
        self._convert_to_config()
        return self.config

    def get_extra_args(self):
        if hasattr(self, 'extra_args'):
            return self.extra_args
        else:
            return []

    def _create_parser(self):
        self.parser = ArgumentParser(*self.parser_args, **self.parser_kw)
        self._add_arguments()

    def _add_arguments(self):
        raise NotImplementedError("subclasses must implement _add_arguments")

    def _parse_args(self, args):
        """self.parser->self.parsed_data""" 
        self.parsed_data, self.extra_args = self.parser.parse_known_args(args)

    def _convert_to_config(self):
        """self.parsed_data->self.config"""
        for k, v in vars(self.parsed_data).iteritems():
            exec_str = 'self.config.' + k + '= v'
            exec exec_str in locals(), globals()



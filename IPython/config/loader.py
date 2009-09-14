#!/usr/bin/env python
# encoding: utf-8
"""A simple configuration system.

Authors:

* Brian Granger
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
from IPython.utils.genutils import filefind

#-----------------------------------------------------------------------------
# Exceptions
#-----------------------------------------------------------------------------


class ConfigError(Exception):
    pass


class ConfigLoaderError(ConfigError):
    pass


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
        for k, v in other.items():
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

    def has_key(self, key):
        if self._is_section_key(key):
            return True
        else:
            return dict.has_key(self, key)

    def _has_section(self, key):
        if self._is_section_key(key):
            if dict.has_key(self, key):
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
        """Load a config from somewhere, return a Struct.
        
        Usually, this will cause self.config to be set and then returned.
        """
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
        self._find_file()
        self._read_file_as_dict()
        self._convert_to_config()
        return self.config

    def _find_file(self):
        """Try to find the file by searching the paths."""
        self.full_filename = filefind(self.filename, self.path)

    def _read_file_as_dict(self):
        execfile(self.full_filename, self.config)

    def _convert_to_config(self):
        if self.data is None:
            ConfigLoaderError('self.data does not exist')
        del self.config['__builtins__']


class CommandLineConfigLoader(ConfigLoader):
    """A config loader for command line arguments.

    As we add more command line based loaders, the common logic should go
    here.
    """


class NoConfigDefault(object): pass
NoConfigDefault = NoConfigDefault()

class ArgParseConfigLoader(CommandLineConfigLoader):
    
    # arguments = [(('-f','--file'),dict(type=str,dest='file'))]
    arguments = ()

    def __init__(self, *args, **kw):
        """Create a config loader for use with argparse.

        The args and kwargs arguments here are passed onto the constructor
        of :class:`argparse.ArgumentParser`.
        """
        super(CommandLineConfigLoader, self).__init__()
        self.args = args
        self.kw = kw

    def load_config(self, args=None):
        """Parse command line arguments and return as a Struct."""
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
        self.parser = argparse.ArgumentParser(*self.args, **self.kw)
        self._add_arguments()
        self._add_other_arguments()

    def _add_other_arguments(self):
        pass

    def _add_arguments(self):
        for argument in self.arguments:
            if not argument[1].has_key('default'):
                argument[1]['default'] = NoConfigDefault
            self.parser.add_argument(*argument[0],**argument[1])

    def _parse_args(self, args=None):
        """self.parser->self.parsed_data"""
        if args is None:
            self.parsed_data, self.extra_args = self.parser.parse_known_args()
        else:
            self.parsed_data, self.extra_args = self.parser.parse_known_args(args)

    def _convert_to_config(self):
        """self.parsed_data->self.config"""
        for k, v in vars(self.parsed_data).items():
            if v is not NoConfigDefault:
                exec_str = 'self.config.' + k + '= v'
                exec exec_str in locals(), globals()


#!/usr/bin/env python
# encoding: utf-8
"""A factory for creating configuration objects.
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

import os
import sys

from IPython.external import argparse
from IPython.utils.ipstruct import Struct
from IPython.utils.genutils import filefind

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class ConfigLoaderError(Exception):
    pass


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
        self.config = Struct()

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
        self._convert_to_struct()
        return self.config

    def _find_file(self):
        """Try to find the file by searching the paths."""
        self.full_filename = filefind(self.filename, self.path)

    def _read_file_as_dict(self):
        self.data = {}
        execfile(self.full_filename, self.data)

    def _convert_to_struct(self):
        if self.data is None:
            ConfigLoaderError('self.data does not exist')
        for k, v in self.data.iteritems():
            if k == k.upper():
                self.config[k] = v


class CommandLineConfigLoader(ConfigLoader):
    """A config loader for command line arguments.

    As we add more command line based loaders, the common logic should go
    here.
    """


class NoDefault(object): pass
NoDefault = NoDefault()

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
        self._convert_to_struct()
        return self.config

    def _create_parser(self):
        self.parser = argparse.ArgumentParser(*self.args, **self.kw)
        self._add_arguments()
        self._add_other_arguments()

    def _add_other_arguments(self):
        pass

    def _add_arguments(self):
        for argument in self.arguments:
            if not argument[1].has_key('default'):
                argument[1]['default'] = NoDefault
            self.parser.add_argument(*argument[0],**argument[1])

    def _parse_args(self, args=None):
        """self.parser->self.parsed_data"""
        if args is None:
            self.parsed_data = self.parser.parse_args()
        else:
            self.parsed_data = self.parser.parse_args(args)

    def _convert_to_struct(self):
        """self.parsed_data->self.config"""
        self.config = Struct()
        for k, v in vars(self.parsed_data).items():
            if v is not NoDefault:
                setattr(self.config, k, v)

class IPythonArgParseConfigLoader(ArgParseConfigLoader):

    def _add_other_arguments(self):
        self.parser.add_argument('--ipythondir',dest='IPYTHONDIR',type=str,
            help='set to override default location of IPYTHONDIR',
            default=NoDefault)
        self.parser.add_argument('-p','--p',dest='PROFILE_NAME',type=str,
            help='the string name of the ipython profile to be used',
            default=None)
        self.parser.add_argument('--debug',dest="DEBUG",action='store_true',
            help='debug the application startup process',
            default=NoDefault)

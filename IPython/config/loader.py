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

from IPython.utils.ipstruct import Struct

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class ConfigLoaderError(Exception):
    pass


class ConfigLoader(object):
    """A object for loading configurations from just about anywhere.
    
    The resulting configuration is packaged as a :class:`Struct`.
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
    """A config loader for pure python files.
    
    This calls execfile on a plain python file and looks for attributes
    that are all caps.  These attribute are added to the config Struct.
    """

    def __init__(self, filename, path='.'):
        """Build a config loader for a filename and path.

        Parameters
        ----------
        filename : str
            The file name of the config file.
        path : str, list, tuple
            The path to search for the config file on, or a sequence of
            paths to try in order

        Examples
        --------
        
        
        """
        self.filename = filename
        self.path = path
        self.full_filename = ''
        self.data = None
        ConfigLoader.__init__(self)

    def find_file(self):
        """Implement file finding logic here."""
        self.full_filename = self.filename

    def read_file_as_dict(self):
        if not os.path.isfile(self.full_filename):
            raise IOError("config file does not exist: %r" % self.fullfilename)
        self.data = {}
        execfile(self.full_filename, self.data)

    def convert_to_struct(self):
        if self.data is None:
            ConfigLoaderError('self.data does not exist')
        for k, v in self.data.iteritems():
            if k == k.upper():
                self.config[k] = v

    def load_config(self):
        self.find_file()
        self.read_file_as_dict()
        self.convert_to_struct()
        return self.config

class PyConfigLoader(object):
    pass


class DefaultFileConfigLoader(object):

    def __init__(self, filename, install_location):
        pass

    def load_config(self):
        pass

    def install(self, force=False):
        pass


class CommandLineConfigLoader(ConfigLoader):

    def __init__(self):
        self.parser = None
        self.parsed_data = None
        self.clear()
        

    def clear(self):
        self.config = Struct()

    def load_config(self, args=None):
        self.create_parser()
        self.parse_args(args)
        self.convert_to_struct()
        return self.config

    def create_parser(self):
        """Create self.parser"""

    def parse_args(self, args=None):
        """self.parser->self.parsed_data"""
        if self.parser is None:
            raise ConfigLoaderError('self.parser does not exist')
        if args is None:
            self.parsed_data = parser.parse_args()
        else:
            self.parse_data = parser.parse_args(args)

    def convert_to_struct(self):
        """self.parsed_data->self.config"""
        if self.parsed_data is None:
            raise ConfigLoaderError('self.parsed_data does not exist')
        self.config = Struct(vars(self.parsed_data))


class ArgParseConfigLoader(CommandLineConfigLoader):

    # arguments = [(('-f','--file'),dict(type=str,dest='file'))]
    arguments = []

    def __init__(self, *args, **kw):
        """Create a config loader for use with argparse.
        
        The args and kwargs arguments here are passed onto the constructor
        of :class:`argparse.ArgumentParser`.
        """
        self.args = args
        self.kw = kw
        CommandLineConfigLoader.__init__(self)

    def create_parser(self):
        self.parser = argparse.ArgumentParser(*self.args, **self.kw)
        self.add_arguments()

    def add_arguments(self):
        for argument in self.arguments:
            self.parser.add_argument(*argument[0],**argument[1])


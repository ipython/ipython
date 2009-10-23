#!/usr/bin/env python
# encoding: utf-8
"""
The IPython cluster directory
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
import shutil

from IPython.core import release
from IPython.config.loader import PyFileConfigLoader
from IPython.core.application import Application
from IPython.core.component import Component
from IPython.config.loader import ArgParseConfigLoader, NoConfigDefault
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


class ClusterDir(Component):
    """An object to manage the cluster directory and its resources.

    The cluster directory is used by :command:`ipcontroller`, 
    :command:`ipcontroller` and :command:`ipcontroller` to manage the
    configuration, logging and security of these applications.

    This object knows how to find, create and manage these directories. This
    should be used by any code that want's to handle cluster directories.
    """

    security_dir_name = Unicode('security')
    log_dir_name = Unicode('log')
    security_dir = Unicode()
    log_dir = Unicode('')
    location = Unicode('')

    def __init__(self, location):
        super(ClusterDir, self).__init__(None)
        self.location = location

    def _location_changed(self, name, old, new):
        if not os.path.isdir(new):
            os.makedirs(new, mode=0777)
        else:
            os.chmod(new, 0777)
        self.security_dir = os.path.join(new, self.security_dir_name)
        self.log_dir = os.path.join(new, self.log_dir_name)

    def _log_dir_changed(self, name, old, new):
        if not os.path.isdir(new):
            os.mkdir(new, 0777)
        else:
            os.chmod(new, 0777)

    def _security_dir_changed(self, name, old, new):
        if not os.path.isdir(new):
            os.mkdir(new, 0700)
        else:
            os.chmod(new, 0700)

    def load_config_file(self, filename):
        """Load a config file from the top level of the cluster dir.

        Parameters
        ----------
        filename : unicode or str
            The filename only of the config file that must be located in
            the top-level of the cluster directory.
        """
        loader = PyFileConfigLoader(filename, self.location)
        return loader.load_config()

    def copy_config_file(self, config_file, path=None):
        """Copy a default config file into the active cluster directory.

        Default configuration files are kept in :mod:`IPython.config.default`.
        This function moves these from that location to the working cluster
        directory.
        """
        if path is None:
            import IPython.config.default
            path = IPython.config.default.__file__.split(os.path.sep)[:-1]
            path = os.path.sep.join(path)
        src = os.path.join(path, config_file)
        dst = os.path.join(self.location, config_file)
        shutil.copy(src, dst)

    def copy_all_config_files(self):
        """Copy all config files into the active cluster directory."""
        for f in ['ipcontroller_config.py', 'ipengine_config.py']:
            self.copy_config_file(f)

    @classmethod
    def find_cluster_dir_by_profile(cls, path, profile='default'):
        """Find/create a cluster dir by profile name and return its ClusterDir.

        This will create the cluster directory if it doesn't exist.

        Parameters
        ----------
        path : unicode or str
            The directory path to look for the cluster directory in.
        profile : unicode or str
            The name of the profile.  The name of the cluster directory
            will be "cluster_<profile>".
        """
        dirname = 'cluster_' + profile
        cluster_dir = os.path.join(os.getcwd(), dirname)
        if os.path.isdir(cluster_dir):
            return ClusterDir(cluster_dir)
        else:
            if not os.path.isdir(path):
                raise IOError("Directory doesn't exist: %s" % path)
            cluster_dir = os.path.join(path, dirname)
            return ClusterDir(cluster_dir)

    @classmethod
    def find_cluster_dir(cls, cluster_dir):
        """Find/create a cluster dir and return its ClusterDir.

        This will create the cluster directory if it doesn't exist.

        Parameters
        ----------
        cluster_dir : unicode or str
            The path of the cluster directory.  This is expanded using
            :func:`os.path.expandvars` and :func:`os.path.expanduser`.
        """
        cluster_dir = os.path.expandvars(os.path.expanduser(cluster_dir))
        return ClusterDir(cluster_dir)


class AppWithClusterDirArgParseConfigLoader(ArgParseConfigLoader):
    """Default command line options for IPython cluster applications."""

    def _add_other_arguments(self):
        self.parser.add_argument('-ipythondir', '--ipython-dir', 
            dest='Global.ipythondir',type=str,
            help='Set to override default location of Global.ipythondir.',
            default=NoConfigDefault,
            metavar='Global.ipythondir')
        self.parser.add_argument('-p','-profile', '--profile',
            dest='Global.profile',type=str,
            help='The string name of the profile to be used. This determines '
            'the name of the cluster dir as: cluster_<profile>. The default profile '
            'is named "default".  The cluster directory is resolve this way '
            'if the --cluster-dir option is not used.',
            default=NoConfigDefault,
            metavar='Global.profile')
        self.parser.add_argument('-log_level', '--log-level',
            dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
            default=NoConfigDefault)
        self.parser.add_argument('-cluster_dir', '--cluster-dir',
            dest='Global.cluster_dir',type=str,
            help='Set the cluster dir. This overrides the logic used by the '
            '--profile option.',
            default=NoConfigDefault,
            metavar='Global.cluster_dir')


class ApplicationWithClusterDir(Application):
    """An application that puts everything into a cluster directory.

    Instead of looking for things in the ipythondir, this type of application
    will use its own private directory called the "cluster directory"
    for things like config files, log files, etc.

    The cluster directory is resolved as follows:

    * If the ``--cluster-dir`` option is given, it is used.
    * If ``--cluster-dir`` is not given, the application directory is 
      resolve using the profile name as ``cluster_<profile>``. The search 
      path for this directory is then i) cwd if it is found there
      and ii) in ipythondir otherwise.

    The config file for the application is to be put in the cluster
    dir and named the value of the ``config_file_name`` class attribute.
    """

    def create_default_config(self):
        super(ApplicationWithClusterDir, self).create_default_config()
        self.default_config.Global.profile = 'default'
        self.default_config.Global.cluster_dir = ''

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return AppWithClusterDirArgParseConfigLoader(
            description=self.description, 
            version=release.version
        )

    def find_config_file_name(self):
        """Find the config file name for this application."""
        # For this type of Application it should be set as a class attribute.
        if not hasattr(self, 'config_file_name'):
            self.log.critical("No config filename found")

    def find_config_file_paths(self):
        """This resolves the cluster directory and sets ``config_file_paths``.

        This does the following:
        * Create the :class:`ClusterDir` object for the application.
        * Set the ``cluster_dir`` attribute of the application and config
          objects.
        * Set ``config_file_paths`` to point to the cluster directory.
        """

        # Create the ClusterDir object for managing everything
        try:
            cluster_dir = self.command_line_config.Global.cluster_dir
        except AttributeError:
            cluster_dir = self.default_config.Global.cluster_dir
        cluster_dir = os.path.expandvars(os.path.expanduser(cluster_dir))
        if cluster_dir:
            # Just use cluster_dir
            self.cluster_dir_obj = ClusterDir.find_cluster_dir(cluster_dir)
        else:
            # Then look for a profile
            try:
                self.profile = self.command_line_config.Global.profile
            except AttributeError:
                self.profile = self.default_config.Global.profile
            self.cluster_dir_obj = ClusterDir.find_cluster_dir_by_profile(
                self.ipythondir, self.profile)

        # Set the cluster directory
        self.cluster_dir = self.cluster_dir_obj.location
        
        # These have to be set because they could be different from the one
        # that we just computed.  Because command line has the highest
        # priority, this will always end up in the master_config.
        self.default_config.Global.cluster_dir = self.cluster_dir
        self.command_line_config.Global.cluster_dir = self.cluster_dir
        self.log.info("Cluster directory set to: %s" % self.cluster_dir)

        # Set the search path to the cluster directory
        self.config_file_paths = (self.cluster_dir,)

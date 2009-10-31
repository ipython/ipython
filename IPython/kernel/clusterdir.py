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
import sys

from twisted.python import log

from IPython.core import release
from IPython.config.loader import PyFileConfigLoader
from IPython.core.application import Application
from IPython.core.component import Component
from IPython.config.loader import ArgParseConfigLoader, NoConfigDefault
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


class ClusterDirError(Exception):
    pass


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
        self.check_dirs()

    def _log_dir_changed(self, name, old, new):
        self.check_log_dir()

    def check_log_dir(self):
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir, 0777)
        else:
            os.chmod(self.log_dir, 0777)

    def _security_dir_changed(self, name, old, new):
        self.check_security_dir()

    def check_security_dir(self):
        if not os.path.isdir(self.security_dir):
            os.mkdir(self.security_dir, 0700)
        else:
            os.chmod(self.security_dir, 0700)

    def check_dirs(self):
        self.check_security_dir()
        self.check_log_dir()

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

    def copy_config_file(self, config_file, path=None, overwrite=False):
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
        if not os.path.isfile(dst) or overwrite:
            shutil.copy(src, dst)

    def copy_all_config_files(self, path=None, overwrite=False):
        """Copy all config files into the active cluster directory."""
        for f in ['ipcontroller_config.py', 'ipengine_config.py',
                  'ipcluster_config.py']:
            self.copy_config_file(f, path=path, overwrite=overwrite)

    @classmethod
    def create_cluster_dir(csl, cluster_dir):
        """Create a new cluster directory given a full path.

        Parameters
        ----------
        cluster_dir : str
            The full path to the cluster directory.  If it does exist, it will
            be used.  If not, it will be created.
        """
        return ClusterDir(cluster_dir)

    @classmethod
    def create_cluster_dir_by_profile(cls, path, profile='default'):
        """Create a cluster dir by profile name and path.

        Parameters
        ----------
        path : str
            The path (directory) to put the cluster directory in.
        profile : str
            The name of the profile.  The name of the cluster directory will
            be "cluster_<profile>".
        """
        if not os.path.isdir(path):
            raise ClusterDirError('Directory not found: %s' % path)
        cluster_dir = os.path.join(path, 'cluster_' + profile)
        return ClusterDir(cluster_dir)

    @classmethod
    def find_cluster_dir_by_profile(cls, ipythondir, profile='default'):
        """Find an existing cluster dir by profile name, return its ClusterDir.

        This searches through a sequence of paths for a cluster dir.  If it
        is not found, a :class:`ClusterDirError` exception will be raised.

        The search path algorithm is:
        1. ``os.getcwd()``
        2. ``ipythondir``
        3. The directories found in the ":" separated 
           :env:`IPCLUSTERDIR_PATH` environment variable.

        Parameters
        ----------
        ipythondir : unicode or str
            The IPython directory to use.
        profile : unicode or str
            The name of the profile.  The name of the cluster directory
            will be "cluster_<profile>".
        """
        dirname = 'cluster_' + profile
        cluster_dir_paths = os.environ.get('IPCLUSTERDIR_PATH','')
        if cluster_dir_paths:
            cluster_dir_paths = cluster_dir_paths.split(':')
        else:
            cluster_dir_paths = []
        paths = [os.getcwd(), ipythondir] + cluster_dir_paths
        for p in paths:
            cluster_dir = os.path.join(p, dirname)
            if os.path.isdir(cluster_dir):
                return ClusterDir(cluster_dir)
        else:
            raise ClusterDirError('Cluster directory not found in paths: %s' % dirname)

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
        if not os.path.isdir(cluster_dir):
            raise ClusterDirError('Cluster directory not found: %s' % cluster_dir)
        return ClusterDir(cluster_dir)


class AppWithClusterDirArgParseConfigLoader(ArgParseConfigLoader):
    """Default command line options for IPython cluster applications."""

    def _add_other_arguments(self):
        self.parser.add_argument('-ipythondir', '--ipython-dir', 
            dest='Global.ipythondir',type=str,
            help='Set to override default location of Global.ipythondir.',
            default=NoConfigDefault,
            metavar='Global.ipythondir'
        )
        self.parser.add_argument('-p','-profile', '--profile',
            dest='Global.profile',type=str,
            help='The string name of the profile to be used. This determines '
            'the name of the cluster dir as: cluster_<profile>. The default profile '
            'is named "default".  The cluster directory is resolve this way '
            'if the --cluster-dir option is not used.',
            default=NoConfigDefault,
            metavar='Global.profile'
        )
        self.parser.add_argument('-log_level', '--log-level',
            dest="Global.log_level",type=int,
            help='Set the log level (0,10,20,30,40,50).  Default is 30.',
            default=NoConfigDefault,
            metavar="Global.log_level"
        )
        self.parser.add_argument('-cluster_dir', '--cluster-dir',
            dest='Global.cluster_dir',type=str,
            help='Set the cluster dir. This overrides the logic used by the '
            '--profile option.',
            default=NoConfigDefault,
            metavar='Global.cluster_dir'
        )
        self.parser.add_argument('-clean_logs', '--clean-logs',
            dest='Global.clean_logs', action='store_true',
            help='Delete old log flies before starting.',
            default=NoConfigDefault
        )
        self.parser.add_argument('-noclean_logs', '--no-clean-logs',
            dest='Global.clean_logs', action='store_false',
            help="Don't Delete old log flies before starting.",
            default=NoConfigDefault
        )

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

    auto_create_cluster_dir = True

    def create_default_config(self):
        super(ApplicationWithClusterDir, self).create_default_config()
        self.default_config.Global.profile = 'default'
        self.default_config.Global.cluster_dir = ''
        self.default_config.Global.log_to_file = False
        self.default_config.Global.clean_logs = False

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return AppWithClusterDirArgParseConfigLoader(
            description=self.description, 
            version=release.version
        )

    def find_resources(self):
        """This resolves the cluster directory.

        This tries to find the cluster directory and if successful, it will
        have done:
        * Sets ``self.cluster_dir_obj`` to the :class:`ClusterDir` object for 
          the application.
        * Sets ``self.cluster_dir`` attribute of the application and config
          objects.

        The algorithm used for this is as follows:
        1. Try ``Global.cluster_dir``.
        2. Try using ``Global.profile``.
        3. If both of these fail and ``self.auto_create_cluster_dir`` is
           ``True``, then create the new cluster dir in the IPython directory.
        4. If all fails, then raise :class:`ClusterDirError`.
        """

        try:
            cluster_dir = self.command_line_config.Global.cluster_dir
        except AttributeError:
            cluster_dir = self.default_config.Global.cluster_dir
        cluster_dir = os.path.expandvars(os.path.expanduser(cluster_dir))
        try:
            self.cluster_dir_obj = ClusterDir.find_cluster_dir(cluster_dir)
        except ClusterDirError:
            pass
        else:
            self.log.info('Using existing cluster dir: %s' % \
                self.cluster_dir_obj.location
            )
            self.finish_cluster_dir()
            return

        try:
            self.profile = self.command_line_config.Global.profile
        except AttributeError:
            self.profile = self.default_config.Global.profile
        try:
            self.cluster_dir_obj = ClusterDir.find_cluster_dir_by_profile(
                self.ipythondir, self.profile)
        except ClusterDirError:
            pass
        else:
            self.log.info('Using existing cluster dir: %s' % \
                self.cluster_dir_obj.location
            )
            self.finish_cluster_dir()
            return

        if self.auto_create_cluster_dir:
            self.cluster_dir_obj = ClusterDir.create_cluster_dir_by_profile(
                self.ipythondir, self.profile
            )
            self.log.info('Creating new cluster dir: %s' % \
                self.cluster_dir_obj.location
            )
            self.finish_cluster_dir()
        else:
            raise ClusterDirError('Could not find a valid cluster directory.')

    def finish_cluster_dir(self):
        # Set the cluster directory
        self.cluster_dir = self.cluster_dir_obj.location
        
        # These have to be set because they could be different from the one
        # that we just computed.  Because command line has the highest
        # priority, this will always end up in the master_config.
        self.default_config.Global.cluster_dir = self.cluster_dir
        self.command_line_config.Global.cluster_dir = self.cluster_dir

        # Set the search path to the cluster directory
        self.config_file_paths = (self.cluster_dir,)

    def find_config_file_name(self):
        """Find the config file name for this application."""
        # For this type of Application it should be set as a class attribute.
        if not hasattr(self, 'config_file_name'):
            self.log.critical("No config filename found")

    def find_config_file_paths(self):
        # Set the search path to the cluster directory
        self.config_file_paths = (self.cluster_dir,)

    def pre_construct(self):
        # The log and security dirs were set earlier, but here we put them
        # into the config and log them.
        config = self.master_config
        sdir = self.cluster_dir_obj.security_dir
        self.security_dir = config.Global.security_dir = sdir
        ldir = self.cluster_dir_obj.log_dir
        self.log_dir = config.Global.log_dir = ldir
        self.log.info("Cluster directory set to: %s" % self.cluster_dir)

    def start_logging(self):
        # Remove old log files
        if self.master_config.Global.clean_logs:
            log_dir = self.master_config.Global.log_dir
            for f in os.listdir(log_dir):
                if f.startswith(self.name + '-') and f.endswith('.log'):
                    os.remove(os.path.join(log_dir, f))
        # Start logging to the new log file
        if self.master_config.Global.log_to_file:
            log_filename = self.name + '-' + str(os.getpid()) + '.log'
            logfile = os.path.join(self.log_dir, log_filename)
            open_log_file = open(logfile, 'w')
        else:
            open_log_file = sys.stdout
        log.startLogging(open_log_file)

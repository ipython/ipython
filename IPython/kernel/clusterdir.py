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

from __future__ import with_statement

import os
import shutil
import sys
import warnings

from twisted.python import log

from IPython.config.loader import PyFileConfigLoader
from IPython.core.application import Application, BaseAppConfigLoader
from IPython.core.component import Component
from IPython.core.crashhandler import CrashHandler
from IPython.core import release
from IPython.utils.path import (
    get_ipython_package_dir,
    expand_path
)
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Warnings control
#-----------------------------------------------------------------------------
# Twisted generates annoying warnings with Python 2.6, as will do other code
# that imports 'sets' as of today
warnings.filterwarnings('ignore', 'the sets module is deprecated',
                        DeprecationWarning )

# This one also comes from Twisted
warnings.filterwarnings('ignore', 'the sha module is deprecated',
                        DeprecationWarning)

#-----------------------------------------------------------------------------
# Module errors
#-----------------------------------------------------------------------------

class ClusterDirError(Exception):
    pass


class PIDFileError(Exception):
    pass


#-----------------------------------------------------------------------------
# Class for managing cluster directories
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
    pid_dir_name = Unicode('pid')
    security_dir = Unicode(u'')
    log_dir = Unicode(u'')
    pid_dir = Unicode(u'')
    location = Unicode(u'')

    def __init__(self, location):
        super(ClusterDir, self).__init__(None)
        self.location = location

    def _location_changed(self, name, old, new):
        if not os.path.isdir(new):
            os.makedirs(new)
        self.security_dir = os.path.join(new, self.security_dir_name)
        self.log_dir = os.path.join(new, self.log_dir_name)
        self.pid_dir = os.path.join(new, self.pid_dir_name)
        self.check_dirs()

    def _log_dir_changed(self, name, old, new):
        self.check_log_dir()

    def check_log_dir(self):
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

    def _security_dir_changed(self, name, old, new):
        self.check_security_dir()

    def check_security_dir(self):
        if not os.path.isdir(self.security_dir):
            os.mkdir(self.security_dir, 0700)
        os.chmod(self.security_dir, 0700)

    def _pid_dir_changed(self, name, old, new):
        self.check_pid_dir()

    def check_pid_dir(self):
        if not os.path.isdir(self.pid_dir):
            os.mkdir(self.pid_dir, 0700)
        os.chmod(self.pid_dir, 0700)

    def check_dirs(self):
        self.check_security_dir()
        self.check_log_dir()
        self.check_pid_dir()

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
        for f in [u'ipcontroller_config.py', u'ipengine_config.py',
                  u'ipcluster_config.py']:
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
    def create_cluster_dir_by_profile(cls, path, profile=u'default'):
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
        cluster_dir = os.path.join(path, u'cluster_' + profile)
        return ClusterDir(cluster_dir)

    @classmethod
    def find_cluster_dir_by_profile(cls, ipython_dir, profile=u'default'):
        """Find an existing cluster dir by profile name, return its ClusterDir.

        This searches through a sequence of paths for a cluster dir.  If it
        is not found, a :class:`ClusterDirError` exception will be raised.

        The search path algorithm is:
        1. ``os.getcwd()``
        2. ``ipython_dir``
        3. The directories found in the ":" separated 
           :env:`IPCLUSTER_DIR_PATH` environment variable.

        Parameters
        ----------
        ipython_dir : unicode or str
            The IPython directory to use.
        profile : unicode or str
            The name of the profile.  The name of the cluster directory
            will be "cluster_<profile>".
        """
        dirname = u'cluster_' + profile
        cluster_dir_paths = os.environ.get('IPCLUSTER_DIR_PATH','')
        if cluster_dir_paths:
            cluster_dir_paths = cluster_dir_paths.split(':')
        else:
            cluster_dir_paths = []
        paths = [os.getcwd(), ipython_dir] + cluster_dir_paths
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
            :func:`IPython.utils.genutils.expand_path`.
        """
        cluster_dir = expand_path(cluster_dir)
        if not os.path.isdir(cluster_dir):
            raise ClusterDirError('Cluster directory not found: %s' % cluster_dir)
        return ClusterDir(cluster_dir)


#-----------------------------------------------------------------------------
# Command line options
#-----------------------------------------------------------------------------

class ClusterDirConfigLoader(BaseAppConfigLoader):

    def _add_cluster_profile(self, parser):
        paa = parser.add_argument
        paa('-p', '--profile',
            dest='Global.profile',type=unicode,
            help=
            """The string name of the profile to be used. This determines the name
            of the cluster dir as: cluster_<profile>. The default profile is named
            'default'.  The cluster directory is resolve this way if the
            --cluster-dir option is not used.""",
            metavar='Global.profile')

    def _add_cluster_dir(self, parser):
        paa = parser.add_argument
        paa('--cluster-dir',
            dest='Global.cluster_dir',type=unicode,
            help="""Set the cluster dir. This overrides the logic used by the
            --profile option.""",
            metavar='Global.cluster_dir')

    def _add_work_dir(self, parser):
        paa = parser.add_argument
        paa('--work-dir',
            dest='Global.work_dir',type=unicode,
            help='Set the working dir for the process.',
            metavar='Global.work_dir')

    def _add_clean_logs(self, parser):
        paa = parser.add_argument
        paa('--clean-logs',
            dest='Global.clean_logs', action='store_true',
            help='Delete old log flies before starting.')

    def _add_no_clean_logs(self, parser):
        paa = parser.add_argument
        paa('--no-clean-logs',
            dest='Global.clean_logs', action='store_false',
            help="Don't Delete old log flies before starting.")

    def _add_arguments(self):
        super(ClusterDirConfigLoader, self)._add_arguments()
        self._add_cluster_profile(self.parser)
        self._add_cluster_dir(self.parser)
        self._add_work_dir(self.parser)
        self._add_clean_logs(self.parser)
        self._add_no_clean_logs(self.parser)


#-----------------------------------------------------------------------------
# Crash handler for this application
#-----------------------------------------------------------------------------


_message_template = """\
Oops, $self.app_name crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the crash traceback.
  - Data on your current $self.app_name configuration.

It was left in the file named:
\t'$self.crash_report_fname'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to: $self.contact_name at $self.contact_email
with the subject '$self.app_name Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s '$self.app_name Crash Report' $self.contact_email < $self.crash_report_fname

To ensure accurate tracking of this issue, please file a report about it at:
$self.bug_tracker
"""

class ClusterDirCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    message_template = _message_template

    def __init__(self, app):
        contact_name = release.authors['Brian'][0]
        contact_email = release.authors['Brian'][1]
        bug_tracker = 'https://bugs.launchpad.net/ipython/+filebug'
        super(ClusterDirCrashHandler,self).__init__(
            app, contact_name, contact_email, bug_tracker
        )


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------

class ApplicationWithClusterDir(Application):
    """An application that puts everything into a cluster directory.

    Instead of looking for things in the ipython_dir, this type of application
    will use its own private directory called the "cluster directory"
    for things like config files, log files, etc.

    The cluster directory is resolved as follows:

    * If the ``--cluster-dir`` option is given, it is used.
    * If ``--cluster-dir`` is not given, the application directory is 
      resolve using the profile name as ``cluster_<profile>``. The search 
      path for this directory is then i) cwd if it is found there
      and ii) in ipython_dir otherwise.

    The config file for the application is to be put in the cluster
    dir and named the value of the ``config_file_name`` class attribute.
    """

    command_line_loader = ClusterDirConfigLoader
    crash_handler_class = ClusterDirCrashHandler
    auto_create_cluster_dir = True

    def create_default_config(self):
        super(ApplicationWithClusterDir, self).create_default_config()
        self.default_config.Global.profile = u'default'
        self.default_config.Global.cluster_dir = u''
        self.default_config.Global.work_dir = os.getcwd()
        self.default_config.Global.log_to_file = False
        self.default_config.Global.clean_logs = False

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
        cluster_dir = expand_path(cluster_dir)
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
                self.ipython_dir, self.profile)
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
                self.ipython_dir, self.profile
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

    def find_config_file_name(self):
        """Find the config file name for this application."""
        # For this type of Application it should be set as a class attribute.
        if not hasattr(self, 'config_file_name'):
            self.log.critical("No config filename found")

    def find_config_file_paths(self):
        # Set the search path to to the cluster directory. We should NOT
        # include IPython.config.default here as the default config files
        # are ALWAYS automatically moved to the cluster directory.
        conf_dir = os.path.join(get_ipython_package_dir(), 'config', 'default')
        self.config_file_paths = (self.cluster_dir,)

    def pre_construct(self):
        # The log and security dirs were set earlier, but here we put them
        # into the config and log them.
        config = self.master_config
        sdir = self.cluster_dir_obj.security_dir
        self.security_dir = config.Global.security_dir = sdir
        ldir = self.cluster_dir_obj.log_dir
        self.log_dir = config.Global.log_dir = ldir
        pdir = self.cluster_dir_obj.pid_dir
        self.pid_dir = config.Global.pid_dir = pdir
        self.log.info("Cluster directory set to: %s" % self.cluster_dir)
        config.Global.work_dir = unicode(expand_path(config.Global.work_dir))
        # Change to the working directory. We do this just before construct
        # is called so all the components there have the right working dir.
        self.to_work_dir()

    def to_work_dir(self):
        wd = self.master_config.Global.work_dir
        if unicode(wd) != unicode(os.getcwd()):
            os.chdir(wd)
            self.log.info("Changing to working dir: %s" % wd)

    def start_logging(self):
        # Remove old log files
        if self.master_config.Global.clean_logs:
            log_dir = self.master_config.Global.log_dir
            for f in os.listdir(log_dir):
                if f.startswith(self.name + u'-') and f.endswith('.log'):
                    os.remove(os.path.join(log_dir, f))
        # Start logging to the new log file
        if self.master_config.Global.log_to_file:
            log_filename = self.name + u'-' + str(os.getpid()) + u'.log'
            logfile = os.path.join(self.log_dir, log_filename)
            open_log_file = open(logfile, 'w')
        else:
            open_log_file = sys.stdout
        log.startLogging(open_log_file)

    def write_pid_file(self, overwrite=False):
        """Create a .pid file in the pid_dir with my pid.

        This must be called after pre_construct, which sets `self.pid_dir`.
        This raises :exc:`PIDFileError` if the pid file exists already.
        """
        pid_file = os.path.join(self.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            pid = self.get_pid_from_file()
            if not overwrite:
                raise PIDFileError(
                    'The pid file [%s] already exists. \nThis could mean that this '
                    'server is already running with [pid=%s].' % (pid_file, pid)
                )
        with open(pid_file, 'w') as f:
            self.log.info("Creating pid file: %s" % pid_file)
            f.write(repr(os.getpid())+'\n')

    def remove_pid_file(self):
        """Remove the pid file.

        This should be called at shutdown by registering a callback with
        :func:`reactor.addSystemEventTrigger`. This needs to return
        ``None``.
        """
        pid_file = os.path.join(self.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            try:
                self.log.info("Removing pid file: %s" % pid_file)
                os.remove(pid_file)
            except:
                self.log.warn("Error removing the pid file: %s" % pid_file)

    def get_pid_from_file(self):
        """Get the pid from the pid file.

        If the  pid file doesn't exist a :exc:`PIDFileError` is raised.
        """
        pid_file = os.path.join(self.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                return pid
        else:
            raise PIDFileError('pid file not found: %s' % pid_file)

